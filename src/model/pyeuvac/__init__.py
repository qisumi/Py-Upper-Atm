"""EUVAC solar EUV flux model."""

from __future__ import annotations

import ctypes as C
import os
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from utils.dll_loader import configure_dll_directories, resolve_dll_path

__all__ = ["Model"]


class Model:
    """EUVAC 太阳极紫外光子通量模型。"""

    def __init__(self, dll_path: Optional[Union[str, Path]] = None) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_path = base / ("euvac.dll" if os.name == "nt" else "libeuvac.so")
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)
        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._eval = self._dll.euvac_eval
        self._eval.restype = None
        self._eval.argtypes = [C.c_float, C.c_float, C.POINTER(C.c_float)]

    def calculate(self, *, f107: Any, f107a: Any) -> dict:
        """计算 Torr 等（1979）37 波段的光子通量。"""
        f107_arr, f107a_arr = np.broadcast_arrays(
            np.asarray(f107, dtype=float), np.asarray(f107a, dtype=float)
        )
        for values, name in ((f107_arr, "f107"), (f107a_arr, "f107a")):
            if np.any(~np.isfinite(values)) or np.any(values <= 0.0):
                raise ValueError(f"{name} 必须为有限正数")
        output = np.empty((f107_arr.size, 37), dtype=float)
        for i, (daily, average) in enumerate(
            zip(f107_arr.reshape(-1), f107a_arr.reshape(-1))
        ):
            buffer = (C.c_float * 37)()
            self._eval(float(daily), float(average), buffer)
            output[i] = np.ctypeslib.as_array(buffer)
        flux = output.reshape(f107_arr.shape + (37,))
        return {
            "f107": float(f107_arr) if f107_arr.shape == () else f107_arr.astype(float),
            "f107a": float(f107a_arr) if f107a_arr.shape == () else f107a_arr.astype(float),
            "bin_index": np.arange(1, 38, dtype=int),
            "photon_flux_cm2_s": flux,
        }
