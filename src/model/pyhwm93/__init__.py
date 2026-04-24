"""
HWM93 wrapper.

Public API:
    Model
"""

from __future__ import annotations

import ctypes as C
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np

__all__ = ["Model"]


class Model:
    """HWM93 ctypes wrapper."""

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        del data_dir, auto_download
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "hwm93.dll" if os.name == "nt" else "libhwm93.so"
            dll_path = base / dll_name
        self._dll_path = Path(dll_path)

        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(self._dll_path.parent))

        if os.name == "nt":
            try:
                self._dll = C.WinDLL(str(self._dll_path), winmode=0)
            except Exception:
                self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        else:
            self._dll = C.cdll.LoadLibrary(str(self._dll_path))

        self._hwm = self._dll.hwm93_eval
        self._hwm.restype = None
        self._hwm.argtypes = _HWM_ARGTYPES

    def calculate(
        self,
        *,
        iyd,
        sec,
        alt_km,
        glat_deg,
        glon_deg,
        stl_hours,
        f107a,
        f107,
        ap2=(0.0, 20.0),
    ) -> dict:
        """
        Calculate HWM93 horizontal wind field.

        Scalar inputs return scalar outputs; array inputs are broadcast and return array outputs.
        """
        return _calculate_hwm(
            self._hwm,
            iyd=iyd,
            sec=sec,
            alt_km=alt_km,
            glat_deg=glat_deg,
            glon_deg=glon_deg,
            stl_hours=stl_hours,
            f107a=f107a,
            f107=f107,
            ap2=ap2,
        )


def _calculate_hwm(
    hwm_func,
    *,
    iyd,
    sec,
    alt_km,
    glat_deg,
    glon_deg,
    stl_hours,
    f107a,
    f107,
    ap2,
) -> dict:
    iyd_arr, sec_arr, alt_arr, lat_arr, lon_arr, stl_arr, f107a_arr, f107_arr = (
        np.broadcast_arrays(
            np.asarray(iyd),
            np.asarray(sec),
            np.asarray(alt_km),
            np.asarray(glat_deg),
            np.asarray(glon_deg),
            np.asarray(stl_hours),
            np.asarray(f107a),
            np.asarray(f107),
        )
    )
    shape = iyd_arr.shape
    flat_count = int(iyd_arr.size)
    ap_matrix = _normalize_ap2(ap2, flat_count)

    meridional = np.empty(flat_count, dtype=float)
    zonal = np.empty(flat_count, dtype=float)

    flat_inputs = (
        iyd_arr.reshape(-1),
        sec_arr.reshape(-1),
        alt_arr.reshape(-1),
        lat_arr.reshape(-1),
        lon_arr.reshape(-1),
        stl_arr.reshape(-1),
        f107a_arr.reshape(-1),
        f107_arr.reshape(-1),
    )

    for index, values in enumerate(zip(*flat_inputs)):
        meridional[index], zonal[index] = _calculate_one(hwm_func, *values, ap2=ap_matrix[index])

    if shape == ():
        return {
            "alt_km": float(alt_arr),
            "meridional_wind_ms": float(meridional[0]),
            "zonal_wind_ms": float(zonal[0]),
        }

    return {
        "alt_km": alt_arr.astype(float),
        "meridional_wind_ms": meridional.reshape(shape),
        "zonal_wind_ms": zonal.reshape(shape),
    }


def _calculate_one(hwm_func, iyd, sec, alt_km, glat_deg, glon_deg, stl_hours, f107a, f107, *, ap2):
    ap_arr = (_C_FLOAT * 2)(*(float(value) for value in ap2))
    w_out = (_C_FLOAT * 2)(0.0, 0.0)
    hwm_func(
        _C_INT(int(iyd)),
        _C_FLOAT(float(sec)),
        _C_FLOAT(float(alt_km)),
        _C_FLOAT(float(glat_deg)),
        _C_FLOAT(float(glon_deg)),
        _C_FLOAT(float(stl_hours)),
        _C_FLOAT(float(f107a)),
        _C_FLOAT(float(f107)),
        ap_arr,
        w_out,
    )
    return float(w_out[0]), float(w_out[1])


def _normalize_ap2(ap2, count: int) -> np.ndarray:
    arr = np.asarray(ap2, dtype=float)
    if arr.ndim == 1:
        if arr.shape[0] != 2:
            raise ValueError("ap2 length must be 2")
        return np.tile(arr, (count, 1))

    if arr.ndim == 2:
        if arr.shape[1] != 2:
            raise ValueError("2D ap2 input must have shape (N, 2)")
        if arr.shape[0] == 1:
            return np.tile(arr[0], (count, 1))
        if arr.shape[0] == count:
            return arr
        raise ValueError("2D ap2 input row count must be 1 or broadcast sample count")

    raise ValueError("ap2 dimension error")


_C_INT = C.c_int
_C_FLOAT = C.c_float
_HWM_ARGTYPES = [
    _C_INT,
    _C_FLOAT,
    _C_FLOAT,
    _C_FLOAT,
    _C_FLOAT,
    _C_FLOAT,
    _C_FLOAT,
    _C_FLOAT,
    C.POINTER(_C_FLOAT),
    C.POINTER(_C_FLOAT),
]
