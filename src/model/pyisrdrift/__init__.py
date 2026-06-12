"""
ISR Ion Drift Model (Richmond et al., 1980) ctypes wrapper.

Computes quiet-day ionospheric electrostatic pseudo-potential
and E x B drifts at 300 km for solar minimum conditions.

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

__all__ = ["Model"]

_C_FLOAT = C.c_float
_C_INT = C.c_int

_ISRDRIFT_ARGTYPES = [
    _C_FLOAT,             # xmlat
    _C_FLOAT,             # xmlon
    _C_FLOAT,             # dayno
    _C_FLOAT,             # ut
    _C_INT,               # isea
    _C_INT,               # iutav
    C.POINTER(_C_FLOAT),  # pot
    C.POINTER(_C_FLOAT),  # vu
    C.POINTER(_C_FLOAT),  # ve
]


class Model:
    """ISR Ion Drift Model (Richmond et al., 1980) ctypes wrapper."""

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "isr_drift.dll" if os.name == "nt" else "libisr_drift.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._eval = self._dll.isr_drift_eval
        self._eval.restype = None
        self._eval.argtypes = _ISRDRIFT_ARGTYPES

    def calculate(
        self,
        *,
        mlat_deg: Union[float, "np.ndarray"],
        mlon_deg: Union[float, "np.ndarray"],
        doy: Union[float, "np.ndarray"],
        ut_hours: Union[float, "np.ndarray"],
        seasonal_avg: int = 0,
        ut_avg: int = 0,
    ) -> dict:
        """
        计算静日电离层电伪势和 E x B 漂移速度（300 km）。

        参数：
            mlat_deg: 磁纬度（度），标量或数组。
            mlon_deg: 磁东经（度），标量或数组。
            doy: 年积日（1.0–365.24），1.0 = 1月1日，标量或数组。
            ut_hours: 世界时（小时），标量或数组。
            seasonal_avg: 季节平均模式（默认 0）。
                0 = 不做季节平均（使用 doy）
                1 = 11月–2月平均
                2 = 5月–8月平均
                3 = 3, 4, 9, 10月平均
                4 = 全年平均（此时 doy 被忽略）
            ut_avg: UT 平均模式（默认 0）。
                0 = 不做 UT 平均
                1 = 在固定地方时（UT + (MLON - 69)/15）上对所有 UT 平均

        返回：
            包含以下键的字典：
                mlat_deg: 磁纬度输入
                mlon_deg: 磁东经输入
                doy: 年积日输入
                ut_hours: 世界时输入
                potential_V: 电伪势（伏特）
                poleward_drift_ms: 极向漂移速度（m/s）
                eastward_drift_ms: 东向漂移速度（m/s）
        """
        if seasonal_avg not in range(5):
            raise ValueError(
                f"seasonal_avg 必须在 0–4 之间，当前值: {seasonal_avg}"
            )
        if ut_avg not in (0, 1):
            raise ValueError(
                f"ut_avg 必须为 0 或 1，当前值: {ut_avg}"
            )
        return _calculate_drift(
            self._eval,
            mlat_deg=mlat_deg,
            mlon_deg=mlon_deg,
            doy=doy,
            ut_hours=ut_hours,
            seasonal_avg=seasonal_avg,
            ut_avg=ut_avg,
        )


def _calculate_one(eval_func, mlat, mlon, dayno, ut, isea, iutav):
    """单点 DLL 调用，返回 (pot, vu, ve)。"""
    pot = _C_FLOAT()
    vu = _C_FLOAT()
    ve = _C_FLOAT()
    eval_func(
        _C_FLOAT(float(mlat)),
        _C_FLOAT(float(mlon)),
        _C_FLOAT(float(dayno)),
        _C_FLOAT(float(ut)),
        _C_INT(int(isea)),
        _C_INT(int(iutav)),
        C.byref(pot),
        C.byref(vu),
        C.byref(ve),
    )
    return float(pot.value), float(vu.value), float(ve.value)


def _calculate_drift(eval_func, *, mlat_deg, mlon_deg, doy, ut_hours,
                     seasonal_avg, ut_avg) -> dict:
    """广播输入，逐点调用 DLL，组装结果字典。"""
    arrays = np.broadcast_arrays(
        np.asarray(mlat_deg, dtype=float),
        np.asarray(mlon_deg, dtype=float),
        np.asarray(doy, dtype=float),
        np.asarray(ut_hours, dtype=float),
    )
    scalar_input = all(np.asarray(v).ndim == 0 for v in
                       [mlat_deg, mlon_deg, doy, ut_hours])
    flat_count = arrays[0].size
    shape = arrays[0].shape

    pot_arr = np.empty(flat_count, dtype=float)
    vu_arr = np.empty(flat_count, dtype=float)
    ve_arr = np.empty(flat_count, dtype=float)

    flat = [a.reshape(-1) for a in arrays]
    for i in range(flat_count):
        p, u, e = _calculate_one(
            eval_func,
            float(flat[0][i]),
            float(flat[1][i]),
            float(flat[2][i]),
            float(flat[3][i]),
            seasonal_avg,
            ut_avg,
        )
        pot_arr[i] = p
        vu_arr[i] = u
        ve_arr[i] = e

    if scalar_input:
        return {
            "mlat_deg": float(arrays[0]),
            "mlon_deg": float(arrays[1]),
            "doy": float(arrays[2]),
            "ut_hours": float(arrays[3]),
            "potential_V": float(pot_arr[0]),
            "poleward_drift_ms": float(vu_arr[0]),
            "eastward_drift_ms": float(ve_arr[0]),
        }

    return {
        "mlat_deg": arrays[0],
        "mlon_deg": arrays[1],
        "doy": arrays[2],
        "ut_hours": arrays[3],
        "potential_V": pot_arr.reshape(shape),
        "poleward_drift_ms": vu_arr.reshape(shape),
        "eastward_drift_ms": ve_arr.reshape(shape),
    }
