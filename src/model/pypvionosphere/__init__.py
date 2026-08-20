"""Pioneer Venus ionosphere empirical model."""

from __future__ import annotations

import ctypes as C
import math
import os
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from utils.dll_loader import configure_dll_directories, resolve_dll_path
from utils.model_data import ensure_model_data

__all__ = ["Model"]


class Model:
    """Pioneer Venus 电子密度与电子温度模型。"""

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_path = base / ("pvionosphere.dll" if os.name == "nt" else "libpvionosphere.so")
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)
        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._eval = self._dll.pvionosphere_eval
        pointer = C.POINTER(C.c_float)
        self._eval.argtypes = [C.c_float, C.c_float, pointer, pointer, pointer, pointer]
        self._eval.restype = None
        root = ensure_model_data("pvionosphere", data_dir=data_dir, auto_download=auto_download)
        data_path = root / "pvionospheredata"
        self._density_coeff = _read_coefficients(data_path / "fsmod.dat", 26)
        self._temperature_coeff = _read_coefficients(data_path / "fsmodt.dat", 28)

    def calculate(self, *, alt_km: Any, sza_deg: Any) -> dict:
        """计算金星电离层电子密度和电子温度。"""
        alt, sza = np.broadcast_arrays(
            np.asarray(alt_km, dtype=float), np.asarray(sza_deg, dtype=float)
        )
        _range(alt, 150.0, 3000.0, "alt_km")
        _range(sza, -180.0, 180.0, "sza_deg")
        log_density = np.empty(alt.size, dtype=float)
        log_temperature = np.empty(alt.size, dtype=float)
        for i, (height, angle) in enumerate(zip(alt.reshape(-1), sza.reshape(-1))):
            density_out = C.c_float()
            temperature_out = C.c_float()
            self._eval(
                float(height), math.radians(float(angle)), self._density_coeff,
                self._temperature_coeff, C.byref(density_out), C.byref(temperature_out)
            )
            log_density[i] = density_out.value
            log_temperature[i] = temperature_out.value
        shape = alt.shape
        log_density = log_density.reshape(shape)
        log_temperature = log_temperature.reshape(shape)
        density = np.power(10.0, log_density)
        temperature = np.power(10.0, log_temperature)
        if shape == ():
            return {
                "alt_km": float(alt), "sza_deg": float(sza),
                "log10_electron_density_cm3": float(log_density),
                "electron_density_cm3": float(density),
                "log10_electron_temperature_K": float(log_temperature),
                "electron_temperature_K": float(temperature),
            }
        return {
            "alt_km": alt.astype(float), "sza_deg": sza.astype(float),
            "log10_electron_density_cm3": log_density,
            "electron_density_cm3": density,
            "log10_electron_temperature_K": log_temperature,
            "electron_temperature_K": temperature,
        }


def _read_coefficients(path: Path, count: int):
    values = [float(value) for value in path.read_text(encoding="ascii").split()]
    if len(values) != count:
        raise ValueError(f"{path.name} 应包含 {count} 个系数")
    return (C.c_float * count)(*values)


def _range(values, minimum, maximum, name):
    if np.any(~np.isfinite(values)) or np.any(values < minimum) or np.any(values > maximum):
        raise ValueError(f"{name} 必须在 {minimum:g} 至 {maximum:g} 之间")
