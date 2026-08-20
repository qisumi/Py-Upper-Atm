"""Pioneer Venus thermosphere model."""

from __future__ import annotations

import ctypes as C
import os
import warnings
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from utils.dll_loader import configure_dll_directories, resolve_dll_path

__all__ = ["Model"]

_OUTPUTS = (
    "total_density_g_cm3", "CO2_cm3", "O_cm3", "CO_cm3",
    "He_cm3", "N_cm3", "N2_cm3", "T_exo_K", "T_local_K",
)


class Model:
    """Pioneer Venus 中性热层模型。"""

    def __init__(self, dll_path: Optional[Union[str, Path]] = None) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_path = base / ("pvthermosphere.dll" if os.name == "nt" else "libpvthermosphere.so")
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)
        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._eval = self._dll.pvthermosphere_eval
        pointer = C.POINTER(C.c_float)
        self._eval.argtypes = [C.c_float, C.c_float, C.c_float, C.c_float, C.c_float, pointer, pointer]
        self._eval.restype = None

    def calculate(
        self,
        *,
        alt_km: Any,
        lat_deg: Any,
        local_time_hours: Any,
        f107a: Any,
        f107: Any,
    ) -> dict:
        """计算金星中性大气温度和密度。"""
        arrays = np.broadcast_arrays(*[
            np.asarray(value, dtype=float)
            for value in (alt_km, lat_deg, local_time_hours, f107a, f107)
        ])
        alt, lat, local_time, average_flux, daily_flux = arrays
        _range(alt, 100.0, 250.0, "alt_km")
        if np.any(alt < 140.0):
            warnings.warn(
                "高度低于 140 km，超出 VTS3 文献给出的科学适用范围",
                RuntimeWarning,
            )
        _range(lat, -90.0, 90.0, "lat_deg")
        _range(local_time, 0.0, 24.0, "local_time_hours", upper_open=True)
        for values, name in ((average_flux, "f107a"), (daily_flux, "f107")):
            if np.any(~np.isfinite(values)) or np.any(values <= 0.0):
                raise ValueError(f"{name} 必须为有限正数")
        output = np.empty((alt.size, 9), dtype=float)
        for i, values in enumerate(zip(*(array.reshape(-1) for array in arrays))):
            density = (C.c_float * 7)()
            temperature = (C.c_float * 2)()
            self._eval(*(float(value) for value in values), density, temperature)
            output[i, :7] = np.ctypeslib.as_array(density)
            output[i, 7:] = np.ctypeslib.as_array(temperature)
        shape = alt.shape
        result = {
            "alt_km": float(alt) if shape == () else alt.astype(float),
            "lat_deg": float(lat) if shape == () else lat.astype(float),
            "local_time_hours": float(local_time) if shape == () else local_time.astype(float),
            "f107a": float(average_flux) if shape == () else average_flux.astype(float),
            "f107": float(daily_flux) if shape == () else daily_flux.astype(float),
        }
        for column, name in enumerate(_OUTPUTS):
            values = output[:, column].reshape(shape)
            result[name] = float(values) if shape == () else values
        return result


def _range(values, minimum, maximum, name, upper_open=False):
    invalid_upper = values >= maximum if upper_open else values > maximum
    if np.any(~np.isfinite(values)) or np.any(values < minimum) or np.any(invalid_upper):
        bracket = "小于" if upper_open else "不大于"
        raise ValueError(f"{name} 必须不小于 {minimum:g} 且{bracket} {maximum:g}")
