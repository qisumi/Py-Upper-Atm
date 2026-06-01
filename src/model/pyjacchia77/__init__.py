"""
Jacchia 1977 Reference Atmosphere wrapper.

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

_JACCHIA77_ARGTYPES = [
    _C_FLOAT,                      # Tinf
    C.POINTER(_C_FLOAT),           # alt_km
    _C_INT,                        # n_alt
    C.POINTER(_C_FLOAT),           # T_out
    C.POINTER(_C_FLOAT),           # N2_out
    C.POINTER(_C_FLOAT),           # O2_out
    C.POINTER(_C_FLOAT),           # O_out
    C.POINTER(_C_FLOAT),           # Ar_out
    C.POINTER(_C_FLOAT),           # He_out
    C.POINTER(_C_FLOAT),           # H_out
    C.POINTER(_C_FLOAT),           # rho_out
    C.POINTER(_C_FLOAT),           # W_out
]


class Model:
    """Jacchia 1977 Reference Atmosphere ctypes wrapper."""

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "jacchia77.dll" if os.name == "nt" else "libjacchia77.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._jacchia77 = self._dll.jacchia77_eval
        self._jacchia77.restype = None
        self._jacchia77.argtypes = _JACCHIA77_ARGTYPES

    def calculate(
        self,
        *,
        alt_km: Union[float, np.ndarray],
        Tinf_K: float,
    ) -> dict:
        """
        计算 Jacchia 1977 参考大气温度和密度剖面。

        参数：
            alt_km: 高度（km），标量或数组，范围 0–2500。
            Tinf_K: 外逸层温度（K），标量。

        返回：
            包含温度和各成分数密度的字典。
        """
        return _calculate_jacchia77(
            self._jacchia77,
            alt_km=alt_km,
            Tinf_K=Tinf_K,
        )


def _calculate_one(jacchia77_func, alt_km: float, Tinf_K: float):
    """计算单个高度点的值。"""
    n_alt = 1
    alt_arr = (_C_FLOAT * 1)(_C_FLOAT(float(alt_km)))
    T_out = (_C_FLOAT * 1)()
    N2_out = (_C_FLOAT * 1)()
    O2_out = (_C_FLOAT * 1)()
    O_out = (_C_FLOAT * 1)()
    Ar_out = (_C_FLOAT * 1)()
    He_out = (_C_FLOAT * 1)()
    H_out = (_C_FLOAT * 1)()
    rho_out = (_C_FLOAT * 1)()
    W_out = (_C_FLOAT * 1)()

    jacchia77_func(
        _C_FLOAT(float(Tinf_K)),
        alt_arr,
        _C_INT(n_alt),
        T_out,
        N2_out,
        O2_out,
        O_out,
        Ar_out,
        He_out,
        H_out,
        rho_out,
        W_out,
    )

    return {
        "T_local_K": float(T_out[0]),
        "N2_cm3": float(N2_out[0]),
        "O2_cm3": float(O2_out[0]),
        "O_cm3": float(O_out[0]),
        "Ar_cm3": float(Ar_out[0]),
        "He_cm3": float(He_out[0]),
        "H_cm3": float(H_out[0]),
        "total_density_cm3": float(rho_out[0]),
        "mean_molecular_weight": float(W_out[0]),
    }


def _calculate_jacchia77(jacchia77_func, *, alt_km, Tinf_K) -> dict:
    """计算多个高度点的值。"""
    alt_arr = np.asarray(alt_km, dtype=float)
    tinf_arr = np.asarray(Tinf_K, dtype=float)

    # Tinf must be scalar
    if tinf_arr.ndim != 0:
        raise ValueError("Tinf_K 必须是标量")

    scalar_input = alt_arr.ndim == 0
    alt_flat = alt_arr.reshape(-1)
    flat_count = alt_flat.size

    # Allocate output arrays
    T_out = np.empty(flat_count, dtype=np.float32)
    N2_out = np.empty(flat_count, dtype=np.float32)
    O2_out = np.empty(flat_count, dtype=np.float32)
    O_out = np.empty(flat_count, dtype=np.float32)
    Ar_out = np.empty(flat_count, dtype=np.float32)
    He_out = np.empty(flat_count, dtype=np.float32)
    H_out = np.empty(flat_count, dtype=np.float32)
    rho_out = np.empty(flat_count, dtype=np.float32)
    W_out = np.empty(flat_count, dtype=np.float32)

    # Keep the contiguous float32 buffer alive for the duration of the DLL call.
    alt32 = np.ascontiguousarray(alt_flat, dtype=np.float32)
    alt_ctypes = alt32.ctypes.data_as(C.POINTER(_C_FLOAT))

    jacchia77_func(
        _C_FLOAT(float(Tinf_K)),
        alt_ctypes,
        _C_INT(flat_count),
        T_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
        N2_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
        O2_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
        O_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
        Ar_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
        He_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
        H_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
        rho_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
        W_out.ctypes.data_as(C.POINTER(_C_FLOAT)),
    )

    if scalar_input:
        return {
            "alt_km": float(alt_arr),
            "Tinf_K": float(Tinf_K),
            "T_local_K": float(T_out[0]),
            "N2_cm3": float(N2_out[0]),
            "O2_cm3": float(O2_out[0]),
            "O_cm3": float(O_out[0]),
            "Ar_cm3": float(Ar_out[0]),
            "He_cm3": float(He_out[0]),
            "H_cm3": float(H_out[0]),
            "total_density_cm3": float(rho_out[0]),
            "mean_molecular_weight": float(W_out[0]),
        }

    return {
        "alt_km": alt_arr.astype(float),
        "Tinf_K": float(Tinf_K),
        "T_local_K": T_out.astype(float),
        "N2_cm3": N2_out.astype(float),
        "O2_cm3": O2_out.astype(float),
        "O_cm3": O_out.astype(float),
        "Ar_cm3": Ar_out.astype(float),
        "He_cm3": He_out.astype(float),
        "H_cm3": H_out.astype(float),
        "total_density_cm3": rho_out.astype(float),
        "mean_molecular_weight": W_out.astype(float),
    }
