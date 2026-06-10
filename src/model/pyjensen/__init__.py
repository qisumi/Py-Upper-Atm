"""
Jensen & Cain (1962) geomagnetic field model wrapper.

Spherical harmonic model of the Earth's main magnetic field, epoch 1960.0.
Coefficients to degree and order 6.

Public API:
    Model
"""

from __future__ import annotations

import ctypes as C
import math
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np
from utils.dll_loader import configure_dll_directories, resolve_dll_path
from utils.model_data import ensure_model_data

__all__ = ["Model"]

_C_INT = C.c_int
_C_FLOAT = C.c_float

_JENSEN_ARGTYPES = [
    _C_FLOAT,   # dlat
    _C_FLOAT,   # dlong
    _C_FLOAT,   # alt
    _C_FLOAT,   # tm
    _C_INT,     # nmx
    C.POINTER(_C_FLOAT),  # x
    C.POINTER(_C_FLOAT),  # y
    C.POINTER(_C_FLOAT),  # z
    C.POINTER(_C_FLOAT),  # f
]


class Model:
    """Jensen & Cain (1962) geomagnetic field model ctypes wrapper.

    Spherical harmonic model with coefficients to degree and order 6.
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        self._data_root = ensure_model_data(
            "jensen",
            data_dir=data_dir,
            auto_download=auto_download,
        )

        # Jensen-Cain data files live in jensen/cain/ subdirectory
        self._cain_data_dir = self._data_root / "jensen" / "cain"

        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "jensen.dll" if os.name == "nt" else "libjensen.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._set_data_root(self._cain_data_dir)

        self._jensen_eval = self._dll.jensen_eval
        self._jensen_eval.restype = None
        self._jensen_eval.argtypes = _JENSEN_ARGTYPES

    def _set_data_root(self, data_dir: Path) -> None:
        set_data_root = self._dll.jensen_set_data_root
        set_data_root.argtypes = [C.c_char_p]
        set_data_root.restype = None
        set_data_root(os.fsencode(str(data_dir)) + b"\x00")

    def calculate(
        self,
        *,
        year,
        lat_deg,
        lon_deg,
        alt_km,
        nmx: int = 6,
    ) -> dict:
        """
        计算地磁场分量。

        参数：
            year: 十进制年份（如 1960.0），标量或数组。
            lat_deg: 地理纬度（度，北正），标量或数组。
            lon_deg: 地理经度（度，东正），标量或数组。
            alt_km: 海拔高度（km），标量或数组。
            nmx: 最大阶数（默认 6，最大 6）。

        返回：
            包含地磁场分量（nT）的字典。
        """
        if nmx < 1 or nmx > 6:
            raise ValueError(f"nmx 必须在 1 到 6 之间，当前值: {nmx}")

        # Re-set data root before each call in case multiple
        # Model instances share the same DLL.
        self._set_data_root(self._cain_data_dir)
        return _calculate_jensen(
            self._jensen_eval,
            nmx=nmx,
            year=year,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            alt_km=alt_km,
        )


def _calculate_one(
    jensen_func,
    nmx: int,
    lat_deg: float,
    lon_deg: float,
    year: float,
    alt_km: float,
) -> dict:
    x = _C_FLOAT()
    y = _C_FLOAT()
    z = _C_FLOAT()
    f = _C_FLOAT()

    jensen_func(
        _C_FLOAT(float(lat_deg)),
        _C_FLOAT(float(lon_deg)),
        _C_FLOAT(float(alt_km)),
        _C_FLOAT(float(year)),
        _C_INT(nmx),
        C.byref(x),
        C.byref(y),
        C.byref(z),
        C.byref(f),
    )

    xn = float(x.value)
    yn = float(y.value)
    zn = float(z.value)
    fn = float(f.value)
    h = math.sqrt(xn * xn + yn * yn) if xn != 0.0 or yn != 0.0 else 0.0

    return {
        "X_nT": xn,
        "Y_nT": yn,
        "Z_nT": zn,
        "F_nT": fn,
        "H_nT": h,
        "inclination_deg": math.degrees(math.atan2(zn, h)) if h > 0 else 0.0,
        "declination_deg": math.degrees(math.atan2(yn, xn)),
    }


def _calculate_jensen(
    jensen_func,
    nmx: int,
    *,
    year,
    lat_deg,
    lon_deg,
    alt_km,
) -> dict:
    year_arr, lat_arr, lon_arr, alt_arr = np.broadcast_arrays(
        np.asarray(year, dtype=float),
        np.asarray(lat_deg, dtype=float),
        np.asarray(lon_deg, dtype=float),
        np.asarray(alt_km, dtype=float),
    )
    shape = year_arr.shape
    flat_count = int(year_arr.size)

    # Pre-allocate output arrays
    x_arr = np.empty(flat_count, dtype=float)
    y_arr = np.empty(flat_count, dtype=float)
    z_arr = np.empty(flat_count, dtype=float)
    f_arr = np.empty(flat_count, dtype=float)
    h_arr = np.empty(flat_count, dtype=float)
    incl = np.empty(flat_count, dtype=float)
    decl = np.empty(flat_count, dtype=float)

    flat_inputs = (
        lat_arr.reshape(-1),
        lon_arr.reshape(-1),
        year_arr.reshape(-1),
        alt_arr.reshape(-1),
    )

    for i, vals in enumerate(zip(*flat_inputs)):
        result = _calculate_one(jensen_func, nmx, *vals)
        x_arr[i] = result["X_nT"]
        y_arr[i] = result["Y_nT"]
        z_arr[i] = result["Z_nT"]
        f_arr[i] = result["F_nT"]
        h_arr[i] = result["H_nT"]
        incl[i] = result["inclination_deg"]
        decl[i] = result["declination_deg"]

    scalar_input = shape == ()
    if scalar_input:
        return {
            "year": float(year_arr),
            "lat_deg": float(lat_arr),
            "lon_deg": float(lon_arr),
            "alt_km": float(alt_arr),
            "X_nT": float(x_arr[0]),
            "Y_nT": float(y_arr[0]),
            "Z_nT": float(z_arr[0]),
            "F_nT": float(f_arr[0]),
            "H_nT": float(h_arr[0]),
            "inclination_deg": float(incl[0]),
            "declination_deg": float(decl[0]),
        }

    return {
        "year": year_arr.astype(float),
        "lat_deg": lat_arr.astype(float),
        "lon_deg": lon_arr.astype(float),
        "alt_km": alt_arr.astype(float),
        "X_nT": x_arr.reshape(shape),
        "Y_nT": y_arr.reshape(shape),
        "Z_nT": z_arr.reshape(shape),
        "F_nT": f_arr.reshape(shape),
        "H_nT": h_arr.reshape(shape),
        "inclination_deg": incl.reshape(shape),
        "declination_deg": decl.reshape(shape),
    }
