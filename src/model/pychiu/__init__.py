"""
Chiu 电离层电子密度模型 (1975) ctypes 封装。

经验电离层模型，基于 50 个测高仪台站 1957–1970 年数据，
使用三个修正 Chapman 函数（E、F1、F2 层）叠加计算电子密度剖面。

参考文献：
  - Ching & Chiu, J. Atmos. Terr. Phys. 35, 1615, 1973
  - Chiu, J. Atmos. Terr. Phys. 37, 1563, 1975

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

__all__ = ["Model"]

_C_FLOAT = C.c_float

_CHIU_ARGTYPES = [
    C.POINTER(_C_FLOAT),  # indata(8)
    C.POINTER(_C_FLOAT),  # outdata(4)
]

# Unit conversion factor: model outputs in units of 1.E+5 cm^-3
_UNIT = 1.0e5  # cm^-3


class Model:
    """Chiu 电离层电子密度模型 (1975) ctypes 封装。

    计算 E、F1、F2 层电子密度剖面（90–500 km）。
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "chiu.dll" if os.name == "nt" else "libchiu.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._chiu = self._dll.chiu_eval
        self._chiu.restype = None
        self._chiu.argtypes = _CHIU_ARGTYPES

    def calculate(
        self,
        *,
        alt_km: Union[float, "np.ndarray"],
        sunspot_number: Union[float, "np.ndarray"],
        local_time_rad: Union[float, "np.ndarray"],
        month_from_dec15: Union[float, "np.ndarray"],
        geo_lat_rad: Union[float, "np.ndarray"],
        geo_mag_lat_rad: Union[float, "np.ndarray"],
        geo_mag_lon_rad: Union[float, "np.ndarray"],
        dip_angle_rad: Union[float, "np.ndarray"],
    ) -> dict:
        """
        计算电离层电子密度剖面。

        参数：
            alt_km: 高度（km），范围 90–500。设为 0 可获取各层峰值密度。
            sunspot_number: 苏黎世平滑太阳黑子数（Rz）。
            local_time_rad: 地方时角（弧度），从午夜起算（0 = 午夜，π = 正午）。
            month_from_dec15: 年度时间（月），从上年 12 月 15 日起算。
            geo_lat_rad: 地理纬度（弧度）。
            geo_mag_lat_rad: 地磁纬度（弧度）。
            geo_mag_lon_rad: 地磁东经（弧度）。
            dip_angle_rad: 地磁磁倾角（弧度）。

        返回：
            包含以下键的字典：
                alt_km: 输入高度（km）
                sunspot_number: 输入太阳黑子数
                Ne_total_cm3: 总电子密度（cm⁻³）
                Ne_E_cm3: E 层电子密度（cm⁻³）
                Ne_F1_cm3: F1 层电子密度（cm⁻³）
                Ne_F2_cm3: F2 层电子密度（cm⁻³）
        """
        return _calculate_chiu(
            self._chiu,
            alt_km=alt_km,
            sunspot_number=sunspot_number,
            local_time_rad=local_time_rad,
            month_from_dec15=month_from_dec15,
            geo_lat_rad=geo_lat_rad,
            geo_mag_lat_rad=geo_mag_lat_rad,
            geo_mag_lon_rad=geo_mag_lon_rad,
            dip_angle_rad=dip_angle_rad,
        )


def _calculate_one(
    chiu_func,
    alt_km: float,
    sunspot_number: float,
    local_time_rad: float,
    month_from_dec15: float,
    geo_lat_rad: float,
    geo_mag_lat_rad: float,
    geo_mag_lon_rad: float,
    dip_angle_rad: float,
) -> tuple[float, float, float, float]:
    """Call the DLL for a single point, return (Ne_total, Ne_E, Ne_F1, Ne_F2) in cm^-3."""
    indata = (_C_FLOAT * 8)(
        float(alt_km),
        float(sunspot_number),
        float(local_time_rad),
        float(month_from_dec15),
        float(geo_lat_rad),
        float(geo_mag_lat_rad),
        float(geo_mag_lon_rad),
        float(dip_angle_rad),
    )
    outdata = (_C_FLOAT * 4)()

    chiu_func(indata, outdata)

    ne_total = float(outdata[0]) * _UNIT
    ne_e = float(outdata[1]) * _UNIT
    ne_f1 = float(outdata[2]) * _UNIT
    ne_f2 = float(outdata[3]) * _UNIT
    return ne_total, ne_e, ne_f1, ne_f2


def _calculate_chiu(
    chiu_func,
    *,
    alt_km,
    sunspot_number,
    local_time_rad,
    month_from_dec15,
    geo_lat_rad,
    geo_mag_lat_rad,
    geo_mag_lon_rad,
    dip_angle_rad,
) -> dict:
    """Broadcast all inputs, call DLL per element, assemble result dict."""
    arrays = np.broadcast_arrays(
        np.asarray(alt_km, dtype=float),
        np.asarray(sunspot_number, dtype=float),
        np.asarray(local_time_rad, dtype=float),
        np.asarray(month_from_dec15, dtype=float),
        np.asarray(geo_lat_rad, dtype=float),
        np.asarray(geo_mag_lat_rad, dtype=float),
        np.asarray(geo_mag_lon_rad, dtype=float),
        np.asarray(dip_angle_rad, dtype=float),
    )
    scalar_input = all(np.asarray(v).ndim == 0 for v in [
        alt_km, sunspot_number, local_time_rad, month_from_dec15,
        geo_lat_rad, geo_mag_lat_rad, geo_mag_lon_rad, dip_angle_rad,
    ])
    flat_count = arrays[0].size
    shape = arrays[0].shape

    ne_total = np.empty(flat_count, dtype=float)
    ne_e = np.empty(flat_count, dtype=float)
    ne_f1 = np.empty(flat_count, dtype=float)
    ne_f2 = np.empty(flat_count, dtype=float)

    flat = [a.reshape(-1) for a in arrays]
    for i in range(flat_count):
        t, e, f1, f2 = _calculate_one(
            chiu_func,
            float(flat[0][i]),
            float(flat[1][i]),
            float(flat[2][i]),
            float(flat[3][i]),
            float(flat[4][i]),
            float(flat[5][i]),
            float(flat[6][i]),
            float(flat[7][i]),
        )
        ne_total[i] = t
        ne_e[i] = e
        ne_f1[i] = f1
        ne_f2[i] = f2

    if scalar_input:
        return {
            "alt_km": float(np.asarray(alt_km)),
            "sunspot_number": float(np.asarray(sunspot_number)),
            "Ne_total_cm3": float(ne_total[0]),
            "Ne_E_cm3": float(ne_e[0]),
            "Ne_F1_cm3": float(ne_f1[0]),
            "Ne_F2_cm3": float(ne_f2[0]),
        }

    return {
        "alt_km": arrays[0].astype(float),
        "sunspot_number": arrays[1].astype(float),
        "Ne_total_cm3": ne_total.reshape(shape),
        "Ne_E_cm3": ne_e.reshape(shape),
        "Ne_F1_cm3": ne_f1.reshape(shape),
        "Ne_F2_cm3": ne_f2.reshape(shape),
    }
