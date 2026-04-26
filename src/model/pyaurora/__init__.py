"""
Feldstein auroral oval wrapper (Holzworth & Meng parameterization).

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

_OVAL_ARGTYPES = [
    _C_FLOAT,
    _C_INT,
    C.POINTER(_C_FLOAT),
    C.POINTER(_C_FLOAT),
]


class Model:
    """Feldstein auroral oval (Holzworth & Meng) ctypes wrapper."""

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "aurora_oval.dll" if os.name == "nt" else "libaurora_oval.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._oval = self._dll.oval_eval
        self._oval.restype = None
        self._oval.argtypes = _OVAL_ARGTYPES

    def calculate(
        self,
        *,
        mlt_hours,
        activity_level,
    ) -> dict:
        """
        计算极光卵边界纬度。

        参数：
            mlt_hours: 磁地方时（小时），标量或数组。
            activity_level: 地磁活动等级，0（宁静）至 6（活跃），标量或数组。

        返回：
            包含 poleward_boundary_deg 和 equatorward_boundary_deg 的字典。
        """
        return _calculate_oval(
            self._oval,
            mlt_hours=mlt_hours,
            activity_level=activity_level,
        )


def _calculate_one(oval_func, mlt_hours: float, activity_level: int):
    if not (0 <= activity_level <= 6):
        raise ValueError(
            f"activity_level 必须在 0–6 之间，当前值: {activity_level}"
        )
    pcgl = _C_FLOAT()
    ecgl = _C_FLOAT()
    oval_func(
        _C_FLOAT(float(mlt_hours)),
        _C_INT(int(activity_level)),
        C.byref(pcgl),
        C.byref(ecgl),
    )
    return float(pcgl.value), float(ecgl.value)


def _calculate_oval(oval_func, *, mlt_hours, activity_level) -> dict:
    mlt_arr = np.asarray(mlt_hours, dtype=float)
    lvl_arr = np.asarray(activity_level, dtype=int)
    mlt_flat = mlt_arr.reshape(-1)
    lvl_flat = lvl_arr.reshape(-1)

    if mlt_flat.size != lvl_flat.size:
        mlt_flat, lvl_flat = np.broadcast_arrays(mlt_flat, lvl_flat)
        mlt_flat = mlt_flat.reshape(-1)
        lvl_flat = lvl_flat.reshape(-1)

    scalar_input = mlt_arr.ndim == 0 and lvl_arr.ndim == 0
    flat_count = mlt_flat.size

    poleward = np.empty(flat_count, dtype=float)
    equatorward = np.empty(flat_count, dtype=float)

    for i in range(flat_count):
        p, e = _calculate_one(oval_func, float(mlt_flat[i]), int(lvl_flat[i]))
        poleward[i] = p
        equatorward[i] = e

    if scalar_input:
        return {
            "mlt_hours": float(mlt_arr),
            "activity_level": int(lvl_arr),
            "poleward_boundary_deg": float(poleward[0]),
            "equatorward_boundary_deg": float(equatorward[0]),
        }

    return {
        "mlt_hours": mlt_arr.astype(float),
        "activity_level": lvl_arr.astype(int),
        "poleward_boundary_deg": poleward.reshape(mlt_arr.shape),
        "equatorward_boundary_deg": equatorward.reshape(mlt_arr.shape),
    }
