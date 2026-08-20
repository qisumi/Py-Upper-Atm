"""Richards simple ionospheric photoelectron model."""

from __future__ import annotations

import ctypes as C
import os
import warnings
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from utils.dll_loader import configure_dll_directories, resolve_dll_path

__all__ = ["Model"]


class Model:
    """Richards（1992）简化光电子通量模型。"""

    def __init__(self, dll_path: Optional[Union[str, Path]] = None) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_path = base / ("photoelectron.dll" if os.name == "nt" else "libphotoelectron.so")
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)
        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._eval = self._dll.photoelectron_eval
        pointer = C.POINTER(C.c_float)
        self._eval.argtypes = [C.c_float] * 11 + [C.c_int, pointer, pointer, pointer]
        self._eval.restype = None

    def calculate(
        self,
        *,
        alt_km: Any,
        sza_deg: Any,
        electron_temperature_K: Any,
        neutral_temperature_K: Any,
        O_cm3: Any,
        O2_cm3: Any,
        N2_cm3: Any,
        electron_density_cm3: Any,
        N_2D_cm3: Any = 0.0,
        O_plus_2D_cm3: Any = 0.0,
        f107: Any = 71.0,
        euv_factors: Any = None,
    ) -> dict:
        """计算 100 个 1 eV 宽能量箱的光电子通量。"""
        if euv_factors is not None and f107 is not None:
            raise ValueError("f107 与 euv_factors 只能指定一个")
        raw = [
            alt_km, sza_deg, electron_temperature_K, neutral_temperature_K,
            O_cm3, O2_cm3, N2_cm3, electron_density_cm3,
            N_2D_cm3, O_plus_2D_cm3,
        ]
        if f107 is not None:
            raw.append(f107)
        arrays = np.broadcast_arrays(*[np.asarray(value, dtype=float) for value in raw])
        if f107 is None:
            point_arrays = arrays
            f107_arr = np.zeros(arrays[0].shape, dtype=float)
        else:
            point_arrays = arrays[:-1]
            f107_arr = arrays[-1]
        alt, sza, te, tn, oxygen, oxygen2, nitrogen2, electrons, n2d, op2d = point_arrays
        _range(alt, 120.0, 500.0, "alt_km")
        _range(sza, 0.0, 90.0, "sza_deg")
        for values, name in ((te, "electron_temperature_K"), (tn, "neutral_temperature_K")):
            if np.any(~np.isfinite(values)) or np.any(values <= 0.0):
                raise ValueError(f"{name} 必须为有限正数")
        for values, name in ((oxygen,"O_cm3"),(oxygen2,"O2_cm3"),(nitrogen2,"N2_cm3"),
                             (electrons,"electron_density_cm3"),(n2d,"N_2D_cm3"),(op2d,"O_plus_2D_cm3")):
            if np.any(~np.isfinite(values)) or np.any(values < 0.0):
                raise ValueError(f"{name} 必须为有限非负数")
        if f107 is not None and (np.any(~np.isfinite(f107_arr)) or np.any(f107_arr <= 60.0)):
            raise ValueError("f107 必须大于 60")

        shape = alt.shape
        if euv_factors is None:
            factors = np.ones(shape + (9,), dtype=float)
            use_f107 = 1
        else:
            supplied = np.asarray(euv_factors, dtype=float)
            if supplied.shape == (9,):
                factors = np.broadcast_to(supplied, shape + (9,))
            else:
                try:
                    factors = np.broadcast_to(supplied, shape + (9,))
                except ValueError as exc:
                    raise ValueError("euv_factors 的末维必须为 9") from exc
            if np.any(~np.isfinite(factors)) or np.any(factors < 0.0):
                raise ValueError("euv_factors 必须为 9 个有限非负数")
            use_f107 = 0

        if np.any(alt > 350.0):
            warnings.warn("高度超过 350 km，原模型未包含光电子输运，结果不确定性较大", RuntimeWarning)
        flux = np.empty((alt.size, 100), dtype=float)
        attenuation = np.empty(alt.size, dtype=float)
        flattened = [array.reshape(-1) for array in point_arrays]
        for i, values in enumerate(zip(*flattened)):
            factor_buffer = (C.c_float * 9)(*factors.reshape((-1, 9))[i])
            flux_buffer = (C.c_float * 100)()
            attenuation_out = C.c_float()
            args = [float(value) for value in values]
            self._eval(*args, float(f107_arr.reshape(-1)[i]), use_f107,
                       factor_buffer, flux_buffer, C.byref(attenuation_out))
            flux[i] = np.ctypeslib.as_array(flux_buffer)
            attenuation[i] = attenuation_out.value
        if np.any(attenuation < 0.14):
            warnings.warn("EUV 衰减因子低于 0.14，超出原模型可靠适用范围", RuntimeWarning)
        flux = flux.reshape(shape + (100,))
        attenuation = attenuation.reshape(shape)
        return {
            "energy_eV": np.arange(0.5, 100.0, 1.0),
            "photoelectron_flux_per_eV_cm2_s": flux,
            "photoelectron_flux_per_eV_cm2_s_sr": flux / (4.0 * np.pi),
            "attenuation_factor": float(attenuation) if shape == () else attenuation,
        }


def _range(values, minimum, maximum, name):
    if np.any(~np.isfinite(values)) or np.any(values < minimum) or np.any(values > maximum):
        raise ValueError(f"{name} 必须在 {minimum:g} 至 {maximum:g} 之间")
