"""Revised SERF2 (EUV91) solar irradiance model."""

from __future__ import annotations

import ctypes as C
import os
import re
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from utils.dll_loader import configure_dll_directories, resolve_dll_path
from utils.model_data import ensure_model_data

__all__ = ["Model"]

_W1 = np.asarray([18.62,30.02,50.52,100.54,150.10,200.02,256.32,284.15,251.10,303.31,303.78,303.31,368.07,356.01,401.14,465.22,453.00,500.00,554.37,584.33,554.37,609.76,629.73,609.76,650.30,703.36,701.00,765.15,770.41,787.71,750.01,801.00,851.00,901.00,977.02,951.00,1025.72,1031.91,1001.00], dtype=float)
_W2 = np.asarray([29.52,49.22,99.99,148.40,198.58,249.18,256.32,284.15,299.50,303.31,303.78,349.85,368.07,399.82,436.70,465.22,499.37,550.00,554.37,584.33,599.60,609.76,629.73,644.10,700.00,703.36,750.00,765.15,770.41,790.15,800.00,850.00,900.00,950.00,977.02,1000.00,1025.72,1031.91,1050.00], dtype=float)
_INDEX_RE = re.compile(r"^\s*(\d{5})\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d{5})\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)")
_MIN_DATE = (1968, 173)
_MAX_DATE = (1988, 366)


class Model:
    """EUV91 历史太阳 EUV 辐照度模型。"""

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_path = base / ("euv91.dll" if os.name == "nt" else "libeuv91.so")
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)
        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._eval = self._dll.euv91_eval
        pointer = C.POINTER(C.c_float)
        self._eval.argtypes = [pointer, pointer, pointer, pointer, pointer]
        self._eval.restype = None
        root = ensure_model_data("euv91", data_dir=data_dir, auto_download=auto_download)
        data_path = root / "euv91data"
        coeff = _parse_coefficients(data_path / "euv91coe.txt")
        self._coeff = (C.c_float * coeff.size)(*coeff.reshape(-1, order="F"))
        self._indices = _parse_indices(data_path / "euv91ix2.dat")
        midpoint = (_W1 + _W2) / 2.0
        self._wavelength = (C.c_float * 39)(*midpoint)

    def calculate(self, *, year: Any, day_of_year: Any) -> dict:
        """按历史日期计算 39 个 EUV 波段。"""
        year_arr, day_arr = np.broadcast_arrays(np.asarray(year), np.asarray(day_of_year))
        year_int = _integer_array(year_arr, "year")
        day_int = _integer_array(day_arr, "day_of_year")
        photon = np.empty((year_arr.size, 39), dtype=float)
        energy = np.empty_like(photon)
        for i, (yr, doy) in enumerate(zip(year_int.reshape(-1), day_int.reshape(-1))):
            key = (int(yr), int(doy))
            if key not in self._indices:
                raise ValueError(f"EUV91 没有日期 {yr:04d}-{doy:03d} 的代理指数")
            proxy = (C.c_float * 4)(*self._indices[key])
            pbuf = (C.c_float * 39)()
            ebuf = (C.c_float * 39)()
            self._eval(self._coeff, proxy, self._wavelength, pbuf, ebuf)
            photon[i] = np.ctypeslib.as_array(pbuf)
            energy[i] = np.ctypeslib.as_array(ebuf)
        shape = year_arr.shape
        return {
            "year": int(year_int) if shape == () else year_int,
            "day_of_year": int(day_int) if shape == () else day_int,
            "wavelength_start_angstrom": _W1.copy(),
            "wavelength_end_angstrom": _W2.copy(),
            "photon_flux_cm2_s": photon.reshape(shape + (39,)),
            "energy_flux_erg_cm2_s": energy.reshape(shape + (39,)),
        }


def _parse_coefficients(path: Path) -> np.ndarray:
    rows = []
    with path.open("r", encoding="ascii", errors="ignore") as fh:
        for line in fh:
            fields = line.split()
            if len(fields) != 12:
                continue
            try:
                rows.append([float(value) for value in fields])
            except ValueError:
                pass
    if len(rows) < 52:
        raise ValueError(f"EUV91 系数文件应包含 52 行：{path}")
    return np.asarray(rows[:52], dtype=np.float32).T


def _parse_indices(path: Path):
    result = {}
    with path.open("r", encoding="ascii", errors="ignore") as fh:
        for line in fh:
            match = _INDEX_RE.match(line)
            if match is None:
                continue
            values = match.groups()
            for offset in (0, 5):
                yyddd = int(values[offset])
                year = 1900 + yyddd // 1000
                day = yyddd % 1000
                key = (year, day)
                if _MIN_DATE <= key <= _MAX_DATE:
                    result[key] = tuple(
                        float(values[offset + j]) for j in range(1, 5)
                    )
    if not result:
        raise ValueError(f"无法解析 EUV91 指数文件：{path}")
    return result


def _integer_array(values, name):
    array = np.asarray(values, dtype=float)
    if np.any(~np.isfinite(array)) or np.any(array != np.floor(array)):
        raise ValueError(f"{name} 必须是整数")
    return array.astype(int)
