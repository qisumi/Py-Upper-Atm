"""
NRLMSIS-2.0 wrapper.

Public API:
    Model
"""

from __future__ import annotations

import ctypes as C
import os
import sys
from pathlib import Path
from typing import Optional, Sequence, Union

import numpy as np

__all__ = ["Model"]


class Model:
    """
    NRLMSIS-2.0 ctypes wrapper.

    Use `calculate(...)` for both single-point and broadcast batch computation.
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        precision: str = "single",
        add_mingw_bin: bool = False,
        extra_dll_dirs: Optional[Sequence[Union[str, Path]]] = None,
    ) -> None:
        self._precision = precision.lower().strip()
        if self._precision not in ("single", "double"):
            raise ValueError("precision 必须是 'single' 或 'double'")

        if dll_path is None:
            dll_path = Path(__file__).resolve().parent / "build" / "nrlmsis2.dll"
        self._dll_path = Path(dll_path)

        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(self._dll_path.parent))
            if add_mingw_bin and sys.platform.startswith("win"):
                mingw_bin = Path(r"C:\mingw64\bin")
                if mingw_bin.exists():
                    os.add_dll_directory(str(mingw_bin))
            if extra_dll_dirs:
                for path in extra_dll_dirs:
                    resolved = Path(path)
                    if resolved.exists():
                        os.add_dll_directory(str(resolved))

        self._dll = C.CDLL(str(self._dll_path))
        self._FT = C.c_double if self._precision == "double" else C.c_float

        try:
            self._msiscalc = getattr(self._dll, "msiscalc")
        except AttributeError:
            self._msiscalc = getattr(self._dll, "MSISCALC")

        FT = self._FT
        self._msiscalc.argtypes = [
            FT,
            FT,
            FT,
            FT,
            FT,
            FT,
            FT,
            C.POINTER(FT),
            C.POINTER(FT),
            C.POINTER(FT),
            C.POINTER(FT),
        ]
        self._msiscalc.restype = None

    def calculate(
        self,
        *,
        day,
        utsec,
        alt_km,
        lat_deg,
        lon_deg,
        f107a,
        f107,
        ap7=None,
    ) -> dict:
        """
        计算温度和密度。

        标量输入返回标量结果；数组输入按 numpy 广播后返回数组结果。
        """
        day_arr, utsec_arr, alt_arr, lat_arr, lon_arr, f107a_arr, f107_arr = (
            np.broadcast_arrays(
                np.asarray(day),
                np.asarray(utsec),
                np.asarray(alt_km),
                np.asarray(lat_deg),
                np.asarray(lon_deg),
                np.asarray(f107a),
                np.asarray(f107),
            )
        )
        shape = day_arr.shape
        flat_count = int(day_arr.size)
        ap_matrix = _normalize_ap7(ap7, flat_count)

        t_local = np.empty(flat_count, dtype=float)
        t_exo = np.empty(flat_count, dtype=float)
        densities = np.empty((flat_count, 10), dtype=float)

        flat_inputs = (
            day_arr.reshape(-1),
            utsec_arr.reshape(-1),
            alt_arr.reshape(-1),
            lat_arr.reshape(-1),
            lon_arr.reshape(-1),
            f107a_arr.reshape(-1),
            f107_arr.reshape(-1),
        )

        for index, values in enumerate(zip(*flat_inputs)):
            t_local[index], t_exo[index], densities[index] = self._calculate_one(
                *values,
                ap7=ap_matrix[index],
            )

        if shape == ():
            return {
                "alt_km": float(alt_arr),
                "T_local_K": float(t_local[0]),
                "T_exo_K": float(t_exo[0]),
                "densities": densities[0],
            }

        return {
            "alt_km": alt_arr.astype(float),
            "T_local_K": t_local.reshape(shape),
            "T_exo_K": t_exo.reshape(shape),
            "densities": densities.reshape(shape + (10,)),
        }

    def _calculate_one(self, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, *, ap7):
        FT = self._FT
        ap_buf = (FT * 7)(*(FT(float(value)) for value in ap7))
        dn10_buf = (FT * 10)()
        t_local = FT()
        t_exo = FT()

        self._msiscalc(
            FT(float(day)),
            FT(float(utsec)),
            FT(float(alt_km)),
            FT(float(lat_deg)),
            FT(float(lon_deg)),
            FT(float(f107a)),
            FT(float(f107)),
            ap_buf,
            C.byref(t_local),
            dn10_buf,
            C.byref(t_exo),
        )

        return (
            float(t_local.value),
            float(t_exo.value),
            np.array([float(dn10_buf[i]) for i in range(10)], dtype=float),
        )


def _normalize_ap7(ap7, count: int) -> np.ndarray:
    if ap7 is None:
        return np.full((count, 7), 4.0, dtype=float)

    arr = np.asarray(ap7, dtype=float)
    if arr.ndim == 1:
        if arr.shape[0] != 7:
            raise ValueError("ap7 长度必须为 7")
        return np.tile(arr, (count, 1))

    if arr.ndim == 2:
        if arr.shape[1] != 7:
            raise ValueError("ap7 二维输入必须为 (N, 7)")
        if arr.shape[0] == 1:
            return np.tile(arr[0], (count, 1))
        if arr.shape[0] == count:
            return arr
        raise ValueError("ap7 二维输入的行数必须为 1 或广播后的样本数")

    raise ValueError("ap7 维度错误")
