"""
IGRF (International Geomagnetic Reference Field) wrapper.

Supports IGRF-13 and IGRF-14 with L-value computation via SHELLG.

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

_GAUSS_TO_NT = 1e5

_IGRF_ARGTYPES = [
    _C_FLOAT,   # xlat
    _C_FLOAT,   # xlong
    _C_FLOAT,   # year
    _C_FLOAT,   # height
    C.POINTER(_C_FLOAT),  # bnorth
    C.POINTER(_C_FLOAT),  # beast
    C.POINTER(_C_FLOAT),  # bdown
    C.POINTER(_C_FLOAT),  # babs
    C.POINTER(_C_FLOAT),  # xl
    C.POINTER(_C_INT),    # icode
]


class Model:
    """IGRF (International Geomagnetic Reference Field) ctypes wrapper.

    Supports IGRF-13 and IGRF-14 with L-value computation.
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        igrf_version: int = 14,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        if igrf_version not in (13, 14):
            raise ValueError(
                f"igrf_version 必须为 13 或 14，当前值: {igrf_version}"
            )
        self._igrf_version = igrf_version
        model_key = f"igrf{igrf_version}"

        self._data_root = ensure_model_data(
            model_key,
            data_dir=data_dir,
            auto_download=auto_download,
        )

        # The data_root for Fortran is the version-specific subdirectory
        version_data_dir = self._data_root / f"igrf{igrf_version}data"
        self._version_data_dir = version_data_dir

        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "igrf.dll" if os.name == "nt" else "libigrf.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._set_data_root(version_data_dir)
        self._set_version(igrf_version)

        self._igrf_eval = self._dll.igrf_eval
        self._igrf_eval.restype = None
        self._igrf_eval.argtypes = _IGRF_ARGTYPES

    def _set_data_root(self, data_dir: Path) -> None:
        set_data_root = self._dll.igrf_set_data_root
        set_data_root.argtypes = [C.c_char_p]
        set_data_root.restype = None
        set_data_root(os.fsencode(str(data_dir)))

    def _set_version(self, version: int) -> None:
        set_version = self._dll.igrf_set_version
        set_version.argtypes = [_C_INT]
        set_version.restype = None
        set_version(_C_INT(version))

    def calculate(
        self,
        *,
        year,
        lat_deg,
        lon_deg,
        alt_km,
    ) -> dict:
        """
        计算地磁场分量和 L 值。

        参数：
            year: 十进制年份（如 2024.5），标量或数组。
            lat_deg: 地理纬度（度，北正），标量或数组。
            lon_deg: 地理经度（度，东正），标量或数组。
            alt_km: 海拔高度（km），标量或数组。

        返回：
            包含地磁场分量（nT）、磁偏角、磁倾角、L 值的字典。
        """
        # Re-set module variables before each call in case multiple
        # Model instances share the same DLL.
        self._set_data_root(self._version_data_dir)
        self._set_version(self._igrf_version)
        return _calculate_igrf(
            self._igrf_eval,
            year=year,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            alt_km=alt_km,
        )


def _calculate_one(
    igrf_func,
    lat_deg: float,
    lon_deg: float,
    year: float,
    alt_km: float,
) -> dict:
    bnorth = _C_FLOAT()
    beast = _C_FLOAT()
    bdown = _C_FLOAT()
    babs = _C_FLOAT()
    xl = _C_FLOAT()
    icode = _C_INT()

    igrf_func(
        _C_FLOAT(float(lat_deg)),
        _C_FLOAT(float(lon_deg)),
        _C_FLOAT(float(year)),
        _C_FLOAT(float(alt_km)),
        C.byref(bnorth),
        C.byref(beast),
        C.byref(bdown),
        C.byref(babs),
        C.byref(xl),
        C.byref(icode),
    )

    bn = float(bnorth.value)
    be = float(beast.value)
    bd = float(bdown.value)
    ba = float(babs.value)
    h = math.sqrt(bn * bn + be * be) if bn != 0.0 or be != 0.0 else 0.0

    return {
        "B_north_nT": bn * _GAUSS_TO_NT,
        "B_east_nT": be * _GAUSS_TO_NT,
        "B_down_nT": bd * _GAUSS_TO_NT,
        "B_abs_nT": ba * _GAUSS_TO_NT,
        "H_nT": h * _GAUSS_TO_NT,
        "inclination_deg": math.degrees(math.atan2(bd, h)) if h > 0 else 0.0,
        "declination_deg": math.degrees(math.atan2(be, bn)),
        "L_value": float(xl.value),
        "icode": int(icode.value),
    }


def _calculate_igrf(
    igrf_func,
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
    b_north = np.empty(flat_count, dtype=float)
    b_east = np.empty(flat_count, dtype=float)
    b_down = np.empty(flat_count, dtype=float)
    b_abs = np.empty(flat_count, dtype=float)
    h_arr = np.empty(flat_count, dtype=float)
    incl = np.empty(flat_count, dtype=float)
    decl = np.empty(flat_count, dtype=float)
    l_val = np.empty(flat_count, dtype=float)
    ic = np.empty(flat_count, dtype=int)

    flat_inputs = (
        lat_arr.reshape(-1),
        lon_arr.reshape(-1),
        year_arr.reshape(-1),
        alt_arr.reshape(-1),
    )

    for i, vals in enumerate(zip(*flat_inputs)):
        result = _calculate_one(igrf_func, *vals)
        b_north[i] = result["B_north_nT"]
        b_east[i] = result["B_east_nT"]
        b_down[i] = result["B_down_nT"]
        b_abs[i] = result["B_abs_nT"]
        h_arr[i] = result["H_nT"]
        incl[i] = result["inclination_deg"]
        decl[i] = result["declination_deg"]
        l_val[i] = result["L_value"]
        ic[i] = result["icode"]

    scalar_input = shape == ()
    if scalar_input:
        return {
            "year": float(year_arr),
            "lat_deg": float(lat_arr),
            "lon_deg": float(lon_arr),
            "alt_km": float(alt_arr),
            "B_north_nT": float(b_north[0]),
            "B_east_nT": float(b_east[0]),
            "B_down_nT": float(b_down[0]),
            "B_abs_nT": float(b_abs[0]),
            "H_nT": float(h_arr[0]),
            "inclination_deg": float(incl[0]),
            "declination_deg": float(decl[0]),
            "L_value": float(l_val[0]),
            "icode": int(ic[0]),
        }

    return {
        "year": year_arr.astype(float),
        "lat_deg": lat_arr.astype(float),
        "lon_deg": lon_arr.astype(float),
        "alt_km": alt_arr.astype(float),
        "B_north_nT": b_north.reshape(shape),
        "B_east_nT": b_east.reshape(shape),
        "B_down_nT": b_down.reshape(shape),
        "B_abs_nT": b_abs.reshape(shape),
        "H_nT": h_arr.reshape(shape),
        "inclination_deg": incl.reshape(shape),
        "declination_deg": decl.reshape(shape),
        "L_value": l_val.reshape(shape),
        "icode": ic.reshape(shape),
    }
