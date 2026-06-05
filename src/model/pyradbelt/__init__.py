"""
RADBELT (AP-8 / AE-8 trapped radiation) wrapper.

Supports AP8MAX, AP8MIN, AE8MAX, AE8MIN flux map models.

Public API:
    Model
"""

from __future__ import annotations

import ctypes as C
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np
from utils.dll_loader import configure_dll_directories, resolve_dll_path
from utils.model_data import ensure_model_data

__all__ = ["Model"]

_C_INT = C.c_int
_C_FLOAT = C.c_float

_VALID_MODEL_TYPES = ("AP8MAX", "AP8MIN", "AE8MAX", "AE8MIN")

_MODEL_FILE_MAP = {
    "AP8MAX": "ap8max.asc",
    "AP8MIN": "ap8min.asc",
    "AE8MAX": "ae8max.asc",
    "AE8MIN": "ae8min.asc",
}


def _read_data_file(filepath: Path):
    """读取 RADBELT ASCII 数据文件，返回 (ihead, map_data)。

    文件格式与 Fortran FORMAT(1X,12I6) 一致：每行首字符跳过，
    后续每 6 个字符为一个整数。首行包含 8 个整数（IHEAD），
    之后的所有行包含 12 个整数（MAP 数据）。
    """
    values = []
    with open(filepath) as f:
        for line in f:
            line = line.rstrip("\n")
            if len(line) < 2:
                continue
            # Skip first character (Fortran 1X), then read 6-char fields
            pos = 1
            while pos + 6 <= len(line):
                token = line[pos:pos + 6].strip()
                if token:
                    values.append(int(token))
                pos += 6
    data = np.array(values, dtype=np.int32)
    if data.size < 8:
        raise ValueError(f"数据文件太短，无法读取 IHEAD: {filepath}")
    ihead = data[:8]
    map_data = data[8:]
    expected = ihead[7]
    if map_data.size < expected:
        raise ValueError(
            f"MAP 数据不足: 期望 {expected} 个元素，实际 {map_data.size} 个"
        )
    return ihead, map_data[:expected]


class Model:
    """RADBELT (AP-8 / AE-8 trapped radiation) ctypes wrapper."""

    def __init__(
        self,
        model_type: str,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        if model_type not in _VALID_MODEL_TYPES:
            raise ValueError(
                f"model_type 必须为 {_VALID_MODEL_TYPES} 之一，"
                f"当前值: {model_type!r}"
            )
        self._model_type = model_type

        self._data_root = ensure_model_data(
            "radbelt",
            data_dir=data_dir,
            auto_download=auto_download,
        )

        data_file = self._data_root / "radbeltdata" / _MODEL_FILE_MAP[model_type]
        if not data_file.exists():
            raise FileNotFoundError(f"RADBELT 数据文件不存在: {data_file}")

        self._ihead, self._map_data = _read_data_file(data_file)

        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "radbelt.dll" if os.name == "nt" else "libradbelt.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))

        self._load_data = self._dll.radbelt_load_data
        self._load_data.restype = None
        self._load_data.argtypes = [
            C.POINTER(_C_INT),   # ihead
            _C_INT,              # nmap
            C.POINTER(_C_INT),   # map
        ]

        self._calc_flux = self._dll.radbelt_calc_flux
        self._calc_flux.restype = None
        self._calc_flux.argtypes = [
            _C_FLOAT,            # l_value
            _C_FLOAT,            # bb0
            C.POINTER(_C_FLOAT), # energies
            C.POINTER(_C_FLOAT), # flux
            _C_INT,              # n
        ]

        ihead_arr = (_C_INT * 8)(*self._ihead.tolist())
        nmap = len(self._map_data)
        map_arr = (_C_INT * nmap)(*self._map_data.tolist())
        self._load_data(ihead_arr, _C_INT(nmap), map_arr)

    def calculate(
        self,
        *,
        l_value,
        bb0,
        energy_mev,
    ) -> dict:
        """
        计算捕获辐射粒子积分通量。

        参数：
            l_value: L 值（磁壳参数），标量或数组。
            bb0: B/B0（磁场强度与赤道值之比），标量或数组，≥1.0。
            energy_mev: 能量（MeV），标量或数组。

        返回：
            包含 l_value, bb0, energy_mev, flux 的字典。
            flux 为 log10(积分通量) [particles/(cm²·s)]，
            当通量 ≤ 0 时返回 0.0。
        """
        return _calculate_radbelt(
            self._calc_flux,
            l_value=l_value,
            bb0=bb0,
            energy_mev=energy_mev,
        )


def _calculate_one(calc_flux, l_value: float, bb0: float, energy_arr):
    """调用 Fortran DLL 计算单组参数的通量。"""
    n = len(energy_arr)
    e_arr = (_C_FLOAT * n)(*energy_arr.tolist())
    f_arr = (_C_FLOAT * n)()
    calc_flux(
        _C_FLOAT(float(l_value)),
        _C_FLOAT(float(bb0)),
        e_arr,
        f_arr,
        _C_INT(n),
    )
    return np.array(f_arr[:n], dtype=float)


def _calculate_radbelt(calc_flux, *, l_value, bb0, energy_mev) -> dict:
    """批量计算 RADBELT 通量，支持 numpy 广播。"""
    l_arr = np.asarray(l_value, dtype=float)
    bb_arr = np.asarray(bb0, dtype=float)
    e_arr = np.asarray(energy_mev, dtype=float)

    scalar_input = l_arr.ndim == 0 and bb_arr.ndim == 0 and e_arr.ndim == 0

    l_b, bb_b, e_b = np.broadcast_arrays(l_arr, bb_arr, e_arr)
    shape = l_b.shape
    l_flat = l_b.reshape(-1)
    bb_flat = bb_b.reshape(-1)
    e_flat = e_b.reshape(-1)

    flat_count = l_flat.size
    flux_out = np.empty(flat_count, dtype=float)

    for i in range(flat_count):
        flux_out[i] = _calculate_one(
            calc_flux,
            float(l_flat[i]),
            float(bb_flat[i]),
            np.array([e_flat[i]], dtype=float),
        )[0]

    if scalar_input:
        return {
            "l_value": float(l_arr),
            "bb0": float(bb_arr),
            "energy_mev": float(e_arr),
            "flux": float(flux_out[0]),
        }

    return {
        "l_value": l_b.astype(float),
        "bb0": bb_b.astype(float),
        "energy_mev": e_b.astype(float),
        "flux": flux_out.reshape(shape),
    }
