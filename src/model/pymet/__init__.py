"""
Marshall Engineering Thermosphere (MET) model wrapper.

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

_MET_ARGTYPES = [
    C.POINTER(_C_FLOAT),  # indata (12 elements)
    C.POINTER(_C_FLOAT),  # outdata (12 elements)
    C.POINTER(_C_FLOAT),  # auxdata (5 elements)
]


class Model:
    """Marshall Engineering Thermosphere (MET) ctypes wrapper."""

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "met.dll" if os.name == "nt" else "libmet.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._met = self._dll.met_eval
        self._met.restype = None
        self._met.argtypes = _MET_ARGTYPES

    def calculate(
        self,
        *,
        alt_km: Union[float, np.ndarray],
        lat_deg: Union[float, np.ndarray],
        lon_deg: Union[float, np.ndarray],
        year: Union[int, np.ndarray],
        month: Union[int, np.ndarray],
        day: Union[int, np.ndarray],
        hour: Union[int, np.ndarray],
        minute: Union[int, np.ndarray],
        geo_index_type: Union[int, np.ndarray],
        f107: Union[float, np.ndarray],
        f107a: Union[float, np.ndarray],
        ap: Union[float, np.ndarray],
    ) -> dict:
        """
        计算 Marshall Engineering Thermosphere (MET) 模型大气参数。

        参数：
            alt_km: 高度（km），标量或数组。
            lat_deg: 地理纬度（度），标量或数组。
            lon_deg: 地理经度（度），标量或数组。
            year: 年份（2位数），标量或数组。
            month: 月份，标量或数组。
            day: 日，标量或数组。
            hour: 时，标量或数组。
            minute: 分，标量或数组。
            geo_index_type: 地磁指数类型（1=Kp, 2=Ap），标量或数组。
            f107: F10.7 太阳射电噪声通量，标量或数组。
            f107a: 162天平均 F10.7，标量或数组。
            ap: 地磁活动指数 Ap，标量或数组。

        返回：
            包含温度、密度和其他大气参数的字典。
        """
        return _calculate_met(
            self._met,
            alt_km=alt_km,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            geo_index_type=geo_index_type,
            f107=f107,
            f107a=f107a,
            ap=ap,
        )


def _calculate_one(met_func, alt_km, lat_deg, lon_deg, year, month, day,
                   hour, minute, geo_index_type, f107, f107a, ap):
    """计算单个点的值。"""
    # 准备输入数组 (12 elements)
    indata = (_C_FLOAT * 12)()
    indata[0] = _C_FLOAT(float(alt_km))
    indata[1] = _C_FLOAT(float(lat_deg))
    indata[2] = _C_FLOAT(float(lon_deg))
    indata[3] = _C_FLOAT(float(year))
    indata[4] = _C_FLOAT(float(month))
    indata[5] = _C_FLOAT(float(day))
    indata[6] = _C_FLOAT(float(hour))
    indata[7] = _C_FLOAT(float(minute))
    indata[8] = _C_FLOAT(float(geo_index_type))
    indata[9] = _C_FLOAT(float(f107))
    indata[10] = _C_FLOAT(float(f107a))
    indata[11] = _C_FLOAT(float(ap))

    # 准备输出数组
    outdata = (_C_FLOAT * 12)()
    auxdata = (_C_FLOAT * 5)()

    # 调用模型
    met_func(indata, outdata, auxdata)

    # 提取结果
    return {
        "T_exo_K": float(outdata[0]),
        "T_local_K": float(outdata[1]),
        "N2_m3": float(outdata[2]),
        "O2_m3": float(outdata[3]),
        "O_m3": float(outdata[4]),
        "Ar_m3": float(outdata[5]),
        "He_m3": float(outdata[6]),
        "H_m3": float(outdata[7]),
        "mean_molecular_weight": float(outdata[8]),
        "total_density_kg_m3": float(outdata[9]),
        "log10_density": float(outdata[10]),
        "pressure_Pa": float(outdata[11]),
        "gravity_m_s2": float(auxdata[0]),
        "gamma": float(auxdata[1]),
        "scale_height_m": float(auxdata[2]),
        "cp": float(auxdata[3]),
        "cv": float(auxdata[4]),
    }


def _calculate_met(met_func, *, alt_km, lat_deg, lon_deg, year, month, day,
                   hour, minute, geo_index_type, f107, f107a, ap) -> dict:
    """计算多个点的值。"""
    # 广播所有输入数组
    alt_arr, lat_arr, lon_arr, year_arr, month_arr, day_arr, hour_arr, \
        minute_arr, geo_type_arr, f107_arr, f107a_arr, ap_arr = \
        np.broadcast_arrays(
            np.asarray(alt_km, dtype=float),
            np.asarray(lat_deg, dtype=float),
            np.asarray(lon_deg, dtype=float),
            np.asarray(year, dtype=float),
            np.asarray(month, dtype=float),
            np.asarray(day, dtype=float),
            np.asarray(hour, dtype=float),
            np.asarray(minute, dtype=float),
            np.asarray(geo_index_type, dtype=float),
            np.asarray(f107, dtype=float),
            np.asarray(f107a, dtype=float),
            np.asarray(ap, dtype=float),
        )

    shape = alt_arr.shape
    scalar_input = alt_arr.ndim == 0
    flat_count = int(alt_arr.size)

    # 准备输出数组
    T_exo = np.empty(flat_count, dtype=float)
    T_local = np.empty(flat_count, dtype=float)
    N2 = np.empty(flat_count, dtype=float)
    O2 = np.empty(flat_count, dtype=float)
    O = np.empty(flat_count, dtype=float)
    Ar = np.empty(flat_count, dtype=float)
    He = np.empty(flat_count, dtype=float)
    H = np.empty(flat_count, dtype=float)
    mol_weight = np.empty(flat_count, dtype=float)
    density = np.empty(flat_count, dtype=float)
    log10_density = np.empty(flat_count, dtype=float)
    pressure = np.empty(flat_count, dtype=float)
    gravity = np.empty(flat_count, dtype=float)
    gamma = np.empty(flat_count, dtype=float)
    scale_height = np.empty(flat_count, dtype=float)
    cp = np.empty(flat_count, dtype=float)
    cv = np.empty(flat_count, dtype=float)

    # 展平输入数组
    flat_inputs = (
        alt_arr.reshape(-1),
        lat_arr.reshape(-1),
        lon_arr.reshape(-1),
        year_arr.reshape(-1),
        month_arr.reshape(-1),
        day_arr.reshape(-1),
        hour_arr.reshape(-1),
        minute_arr.reshape(-1),
        geo_type_arr.reshape(-1),
        f107_arr.reshape(-1),
        f107a_arr.reshape(-1),
        ap_arr.reshape(-1),
    )

    # 逐点计算
    for i, values in enumerate(zip(*flat_inputs)):
        result = _calculate_one(met_func, *values)
        T_exo[i] = result["T_exo_K"]
        T_local[i] = result["T_local_K"]
        N2[i] = result["N2_m3"]
        O2[i] = result["O2_m3"]
        O[i] = result["O_m3"]
        Ar[i] = result["Ar_m3"]
        He[i] = result["He_m3"]
        H[i] = result["H_m3"]
        mol_weight[i] = result["mean_molecular_weight"]
        density[i] = result["total_density_kg_m3"]
        log10_density[i] = result["log10_density"]
        pressure[i] = result["pressure_Pa"]
        gravity[i] = result["gravity_m_s2"]
        gamma[i] = result["gamma"]
        scale_height[i] = result["scale_height_m"]
        cp[i] = result["cp"]
        cv[i] = result["cv"]

    if scalar_input:
        return {
            "alt_km": float(alt_arr),
            "lat_deg": float(lat_arr),
            "lon_deg": float(lon_arr),
            "T_exo_K": float(T_exo[0]),
            "T_local_K": float(T_local[0]),
            "N2_m3": float(N2[0]),
            "O2_m3": float(O2[0]),
            "O_m3": float(O[0]),
            "Ar_m3": float(Ar[0]),
            "He_m3": float(He[0]),
            "H_m3": float(H[0]),
            "mean_molecular_weight": float(mol_weight[0]),
            "total_density_kg_m3": float(density[0]),
            "log10_density": float(log10_density[0]),
            "pressure_Pa": float(pressure[0]),
            "gravity_m_s2": float(gravity[0]),
            "gamma": float(gamma[0]),
            "scale_height_m": float(scale_height[0]),
            "cp": float(cp[0]),
            "cv": float(cv[0]),
        }

    return {
        "alt_km": alt_arr.astype(float),
        "lat_deg": lat_arr.astype(float),
        "lon_deg": lon_arr.astype(float),
        "T_exo_K": T_exo.reshape(shape),
        "T_local_K": T_local.reshape(shape),
        "N2_m3": N2.reshape(shape),
        "O2_m3": O2.reshape(shape),
        "O_m3": O.reshape(shape),
        "Ar_m3": Ar.reshape(shape),
        "He_m3": He.reshape(shape),
        "H_m3": H.reshape(shape),
        "mean_molecular_weight": mol_weight.reshape(shape),
        "total_density_kg_m3": density.reshape(shape),
        "log10_density": log10_density.reshape(shape),
        "pressure_Pa": pressure.reshape(shape),
        "gravity_m_s2": gravity.reshape(shape),
        "gamma": gamma.reshape(shape),
        "scale_height_m": scale_height.reshape(shape),
        "cp": cp.reshape(shape),
        "cv": cv.reshape(shape),
    }
