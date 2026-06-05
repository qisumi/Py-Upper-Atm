"""
SOFIP (Short Orbital Flux Integration Program) wrapper.

Computes mission-averaged trapped radiation fluxes along spacecraft
trajectories using the AP-8 / AE-8 radiation belt models.

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

# 1 = protons, 2 = electrons
_MODEL_ITYPE = {
    "AP8MAX": 1,
    "AP8MIN": 1,
    "AE8MAX": 2,
    "AE8MIN": 2,
}

# Standard energy levels (MeV) — 30 thresholds per particle type
_PROTON_ENERGIES = np.array([
    2., 3., 4., 5., 6., 8., 10., 15., 20., 25.,
    30., 35., 40., 45., 50., 55., 60., 70., 80., 90.,
    100., 125., 150., 175., 200., 250., 300., 350., 400., 500.,
], dtype=float)

_ELECTRON_ENERGIES = np.array([
    0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
    1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5,
    3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.5, 6.0, 6.5, 7.0,
], dtype=float)

_SOLAR_PROTON_ENERGIES = np.array([
    10., 20., 30., 40., 50., 60., 70., 80., 90., 100.,
    110., 120., 130., 140., 150., 160., 170., 180., 190., 200.,
], dtype=float)


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
    """SOFIP (Short Orbital Flux Integration Program) ctypes wrapper.

    计算沿航天器轨迹的任务平均捕获辐射通量，使用 AP-8/AE-8
    辐射带模型和 SOLPRO 太阳质子模型。

    参数:
        model_type: 辐射带模型类型，可选 "AP8MAX", "AP8MIN", "AE8MAX", "AE8MIN"。
        dll_path: DLL/SO 文件路径，默认自动检测。
        data_dir: 模型数据目录，默认自动下载。
        auto_download: 是否自动下载数据文件。
    """

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
        self._itype = _MODEL_ITYPE[model_type]

        self._data_root = ensure_model_data(
            "radbelt",
            data_dir=data_dir,
            auto_download=auto_download,
        )

        data_file = self._data_root / "radbeltdata" / _MODEL_FILE_MAP[model_type]
        if not data_file.exists():
            raise FileNotFoundError(f"SOFIP 数据文件不存在: {data_file}")

        self._ihead, self._map_data = _read_data_file(data_file)

        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "sofip.dll" if os.name == "nt" else "libsofip.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))

        # sofip_load_data(ihead, nmap, map)
        self._load_data = self._dll.sofip_load_data
        self._load_data.restype = None
        self._load_data.argtypes = [
            C.POINTER(_C_INT),   # ihead(8)
            _C_INT,              # nmap
            C.POINTER(_C_INT),   # map(nmap)
        ]

        # sofip_integrate(...)
        self._integrate = self._dll.sofip_integrate
        self._integrate.restype = None
        self._integrate.argtypes = [
            _C_INT,              # npts
            C.POINTER(_C_FLOAT), # times(npts)
            C.POINTER(_C_FLOAT), # l_vals(npts)
            C.POINTER(_C_FLOAT), # b_vals(npts)
            _C_INT,              # itype
            _C_FLOAT,            # dur_months
            _C_INT,              # conf_pct
            C.POINTER(_C_FLOAT), # energy_levels(30) [out]
            C.POINTER(_C_FLOAT), # integ_flux(30) [out]
            C.POINTER(_C_FLOAT), # diff_flux(30) [out]
            C.POINTER(_C_FLOAT), # diff_integ(30) [out]
            C.POINTER(_C_FLOAT), # sol_energy(20) [out]
            C.POINTER(_C_FLOAT), # sol_fluence(20) [out]
            C.POINTER(_C_INT),   # n_al_events [out]
            C.POINTER(_C_FLOAT), # exposure_factor [out]
            C.POINTER(_C_INT),   # lzone_counts(4) [out]
            C.POINTER(_C_FLOAT), # total_time [out]
            C.POINTER(_C_FLOAT), # kpstep_out [out]
        ]

        # Load data into DLL
        ihead_arr = (_C_INT * 8)(*self._ihead.tolist())
        nmap = len(self._map_data)
        map_arr = (_C_INT * nmap)(*self._map_data.tolist())
        self._load_data(ihead_arr, _C_INT(nmap), map_arr)

    def calculate(
        self,
        *,
        times,
        b_field,
        l_shell,
        duration_months: float = 12.0,
        confidence_pct: int = 90,
    ) -> dict:
        """计算沿轨迹的任务平均捕获辐射通量。

        参数:
            times: 轨迹时间数组（小时）。
            b_field: 磁场强度数组（高斯）。
            l_shell: 磁壳参数 L 数组（地球半径）。
            duration_months: 任务持续时间（月），用于太阳质子计算，默认 12。
            confidence_pct: 置信水平（%），用于太阳质子计算（80-99），默认 90。

        返回:
            包含以下键的字典:
            - energy_levels: 能量阈值数组（MeV），形状 (30,)
            - integral_flux: 平均积分通量（#/cm²/s），形状 (30,)
            - differential_flux: 微分通量（#/cm²/s/keV），形状 (30,)
            - difference_flux: 差分积分通量（#/cm²/s/DE），形状 (30,)
            - solar_proton_energy: 太阳质子能量（MeV），形状 (20,)
            - solar_proton_fluence: 太阳质子注量（#/cm²），形状 (20,)
            - n_al_events: AL 事件数
            - exposure_factor: 暴露因子
            - lzone_counts: L 壳区间点计数，形状 (4,)
              [0] L<1.1, [1] 1.1≤L<2.8, [2] 2.8≤L<11, [3] L≥11 或 L<0
            - total_time_hours: 总轨迹时间（小时）
            - time_step_minutes: 时间步长（分钟）
        """
        if not (80 <= confidence_pct <= 99):
            raise ValueError(
                f"confidence_pct 必须在 80-99 之间，当前值: {confidence_pct}"
            )
        if duration_months <= 0 or duration_months > 72:
            raise ValueError(
                f"duration_months 必须在 0-72 之间，当前值: {duration_months}"
            )

        times_arr = np.asarray(times, dtype=np.float32).ravel()
        b_arr = np.asarray(b_field, dtype=np.float32).ravel()
        l_arr = np.asarray(l_shell, dtype=np.float32).ravel()

        if times_arr.shape != b_arr.shape or times_arr.shape != l_arr.shape:
            raise ValueError(
                "times, b_field, l_shell 必须具有相同的形状"
            )

        npts = len(times_arr)
        if npts == 0:
            raise ValueError("轨迹数据不能为空")

        # Allocate output arrays
        energy_levels = (_C_FLOAT * 30)()
        integ_flux = (_C_FLOAT * 30)()
        diff_flux = (_C_FLOAT * 30)()
        diff_integ = (_C_FLOAT * 30)()
        sol_energy = (_C_FLOAT * 20)()
        sol_fluence = (_C_FLOAT * 20)()
        n_al_events = _C_INT()
        exposure_factor = _C_FLOAT()
        lzone_counts = (_C_INT * 4)()
        total_time = _C_FLOAT()
        kpstep_out = _C_FLOAT()

        # Prepare input arrays
        times_c = (_C_FLOAT * npts)(*times_arr.tolist())
        b_c = (_C_FLOAT * npts)(*b_arr.tolist())
        l_c = (_C_FLOAT * npts)(*l_arr.tolist())

        self._integrate(
            _C_INT(npts),
            times_c,
            l_c,
            b_c,
            _C_INT(self._itype),
            _C_FLOAT(float(duration_months)),
            _C_INT(int(confidence_pct)),
            energy_levels,
            integ_flux,
            diff_flux,
            diff_integ,
            sol_energy,
            sol_fluence,
            C.byref(n_al_events),
            C.byref(exposure_factor),
            lzone_counts,
            C.byref(total_time),
            C.byref(kpstep_out),
        )

        return {
            "energy_levels": np.array(energy_levels[:], dtype=float),
            "integral_flux": np.array(integ_flux[:], dtype=float),
            "differential_flux": np.array(diff_flux[:], dtype=float),
            "difference_flux": np.array(diff_integ[:], dtype=float),
            "solar_proton_energy": np.array(sol_energy[:], dtype=float),
            "solar_proton_fluence": np.array(sol_fluence[:], dtype=float),
            "n_al_events": int(n_al_events.value),
            "exposure_factor": float(exposure_factor.value),
            "lzone_counts": np.array(lzone_counts[:], dtype=int),
            "total_time_hours": float(total_time.value),
            "time_step_minutes": float(kpstep_out.value),
        }
