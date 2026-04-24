"""
NRLMSISE-00 wrapper.

Public API:
    Model
"""

from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Optional, Union

import numpy as np

__all__ = ["Model"]


class Model:
    """NRLMSISE-00 ctypes wrapper."""

    def __init__(self, dll_path: Optional[Union[str, Path]] = None) -> None:
        if dll_path is None:
            dll_path = Path(__file__).resolve().parent / "msis00.dll"
        self._dll_path = Path(dll_path)
        self._dll = ctypes.CDLL(str(self._dll_path))

        self._gtd7_eval = self._dll.gtd7_eval
        self._gtd7_eval.restype = None
        self._gtd7_eval.argtypes = _ARGTYPES

        self._gtd7d_eval = self._dll.gtd7d_eval
        self._gtd7d_eval.restype = None
        self._gtd7d_eval.argtypes = _ARGTYPES

    def calculate(
        self,
        *,
        iyd,
        sec,
        alt_km,
        lat_deg,
        lon_deg,
        stl_hours,
        f107a,
        f107,
        ap7=None,
        mass: int = 48,
        use_anomalous_o: bool = False,
    ) -> dict:
        """
        Calculate NRLMSISE-00 temperature and density.

        Scalar inputs return scalar outputs; array inputs are broadcast and return array outputs.
        """
        iyd_arr, sec_arr, alt_arr, lat_arr, lon_arr, stl_arr, f107a_arr, f107_arr = (
            np.broadcast_arrays(
                np.asarray(iyd),
                np.asarray(sec),
                np.asarray(alt_km),
                np.asarray(lat_deg),
                np.asarray(lon_deg),
                np.asarray(stl_hours),
                np.asarray(f107a),
                np.asarray(f107),
            )
        )
        shape = iyd_arr.shape
        flat_count = int(iyd_arr.size)
        ap_matrix = _normalize_ap7(ap7, flat_count)

        densities = np.empty((flat_count, 9), dtype=float)
        temperatures = np.empty((flat_count, 2), dtype=float)

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
            densities[index], temperatures[index] = self._calculate_one(
                *values,
                ap7=ap_matrix[index],
                mass=mass,
                use_anomalous_o=use_anomalous_o,
            )

        if shape == ():
            return {
                "alt_km": float(alt_arr),
                "T_local_K": float(temperatures[0, 1]),
                "T_exo_K": float(temperatures[0, 0]),
                "densities": densities[0],
            }

        return {
            "alt_km": alt_arr.astype(float),
            "T_local_K": temperatures[:, 1].reshape(shape),
            "T_exo_K": temperatures[:, 0].reshape(shape),
            "densities": densities.reshape(shape + (9,)),
        }

    def _calculate_one(
        self,
        iyd,
        sec,
        alt_km,
        lat_deg,
        lon_deg,
        stl_hours,
        f107a,
        f107,
        *,
        ap7,
        mass: int,
        use_anomalous_o: bool,
    ):
        ap_array = np.asarray(ap7, dtype=np.float32)
        d_out = np.zeros(9, dtype=np.float32)
        t_out = np.zeros(2, dtype=np.float32)
        func = self._gtd7d_eval if use_anomalous_o else self._gtd7_eval

        func(
            ctypes.c_int(int(iyd)),
            ctypes.c_float(float(sec)),
            ctypes.c_float(float(alt_km)),
            ctypes.c_float(float(lat_deg)),
            ctypes.c_float(float(lon_deg)),
            ctypes.c_float(float(stl_hours)),
            ctypes.c_float(float(f107a)),
            ctypes.c_float(float(f107)),
            ap_array,
            ctypes.c_int(int(mass)),
            d_out,
            t_out,
        )

        return d_out.astype(float), t_out.astype(float)


_ARGTYPES = [
    ctypes.c_int,
    ctypes.c_float,
    ctypes.c_float,
    ctypes.c_float,
    ctypes.c_float,
    ctypes.c_float,
    ctypes.c_float,
    ctypes.c_float,
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags="C_CONTIGUOUS"),
    ctypes.c_int,
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags="C_CONTIGUOUS"),
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags="C_CONTIGUOUS"),
]


def _normalize_ap7(ap7, count: int) -> np.ndarray:
    if ap7 is None:
        return np.full((count, 7), 4.0, dtype=float)

    arr = np.asarray(ap7, dtype=float)
    if arr.ndim == 1:
        if arr.shape[0] != 7:
            raise ValueError("ap7 length must be 7")
        return np.tile(arr, (count, 1))

    if arr.ndim == 2:
        if arr.shape[1] != 7:
            raise ValueError("2D ap7 input must have shape (N, 7)")
        if arr.shape[0] == 1:
            return np.tile(arr[0], (count, 1))
        if arr.shape[0] == count:
            return arr
        raise ValueError("2D ap7 input row count must be 1 or broadcast sample count")

    raise ValueError("ap7 dimension error")
