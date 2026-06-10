"""
MGST (MAGSAT Geomagnetic Spherical Topology) field model wrappers.

Supports MGST(6/80) and MGST(4/81) spherical harmonic models of Earth's
main magnetic field from MAGSAT satellite data.

Public API:
    MGST80  — MGST(6/80) model, epoch 1979.85
    MGST81  — MGST(4/81) model, epoch 1980.0
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

__all__ = ["MGST80", "MGST81"]

_C_INT = C.c_int
_C_FLOAT = C.c_float

_MGST_ARGTYPES = [
    _C_INT,     # version
    _C_FLOAT,   # dlat
    _C_FLOAT,   # dlong
    _C_FLOAT,   # alt
    _C_FLOAT,   # tm
    _C_INT,     # nmx, FIELDG internal maximum index
    C.POINTER(_C_FLOAT),  # x
    C.POINTER(_C_FLOAT),  # y
    C.POINTER(_C_FLOAT),  # z
    C.POINTER(_C_FLOAT),  # f
]


class _MGSTBase:
    """Shared ctypes wrapper for MGST geomagnetic field models."""

    _version: int
    _default_year: float

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "mgst.dll" if os.name == "nt" else "libmgst.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._mgst_eval = self._dll.mgst_eval
        self._mgst_eval.restype = None
        self._mgst_eval.argtypes = _MGST_ARGTYPES

        data_root = ensure_model_data(
            "mgst",
            data_dir=data_dir,
            auto_download=auto_download,
        )
        self._data_root = data_root / "mgst"
        self._set_data_root(self._data_root)

    def _set_data_root(self, data_dir: Path) -> None:
        set_data_root = self._dll.mgst_set_data_root
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
        nmx: int = 13,
    ) -> dict:
        """
        计算地磁场分量。

        参数：
            year: 十进制年份（如 1980.0），标量或数组。
            lat_deg: 地理纬度（度，北正），标量或数组。
            lon_deg: 地理经度（度，东正），标量或数组。
            alt_km: 海拔高度（km），标量或数组。
            nmx: 最大球谐阶数（默认 13，最大 13）。

        返回：
            包含地磁场分量（nT）的字典。
        """
        if not 1 <= nmx <= 13:
            raise ValueError(f"nmx 必须在 1-13 之间，当前值: {nmx}")

        # Re-set data root before each call in case multiple instances share
        # the same DLL but were configured with different data directories.
        self._set_data_root(self._data_root)
        return _calculate_mgst(
            self._mgst_eval,
            version=self._version,
            nmx=nmx,
            year=year,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            alt_km=alt_km,
        )


class MGST80(_MGSTBase):
    """MGST(6/80) geomagnetic field model, epoch 1979.85.

    MAGSAT scalar + fine attitude data, November 5-6 1979.
    Spherical harmonics to degree and order 13, no secular variation.
    """

    _version = 80
    _default_year = 1979.85


class MGST81(_MGSTBase):
    """MGST(4/81) geomagnetic field model, epoch 1980.0.

    MAGSAT 15-day data set. Spherical harmonics to degree and order 13
    in constant terms, degree 7 in first derivative terms.
    """

    _version = 81
    _default_year = 1980.0


def _calculate_one(
    mgst_func,
    *,
    version: int,
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

    # FIELDG stores degree 1 at internal index N=2, so pass nmx + 1 while
    # keeping the public nmx argument as the mathematical maximum degree.
    mgst_func(
        _C_INT(version),
        _C_FLOAT(float(lat_deg)),
        _C_FLOAT(float(lon_deg)),
        _C_FLOAT(float(alt_km)),
        _C_FLOAT(float(year)),
        _C_INT(nmx + 1),
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


def _calculate_mgst(
    mgst_func,
    *,
    version: int,
    nmx: int,
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
        la, lo, yr, al = vals
        result = _calculate_one(
            mgst_func,
            version=version,
            nmx=nmx,
            lat_deg=float(la),
            lon_deg=float(lo),
            year=float(yr),
            alt_km=float(al),
        )
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
