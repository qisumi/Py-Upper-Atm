"""
MSISE-90 中性大气模型封装。

Public API:
    Model
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
from typing import Optional, Sequence, Union

import numpy as np
from utils.dll_loader import configure_dll_directories, resolve_dll_path

__all__ = ["Model"]

# 密度物种名称（索引 1-8 对应 D(1)-D(8)）
_DENSITY_SPECIES = ["He", "O", "N2", "O2", "Ar", "TotalMass", "H", "N"]
NumericInput = Union[int, float, np.ndarray]
ApInput = Optional[Union[Sequence[float], np.ndarray]]

_ARGTYPES = [
    ctypes.c_int,                                                          # iyd
    ctypes.c_float,                                                        # sec
    ctypes.c_float,                                                        # alt
    ctypes.c_float,                                                        # glat
    ctypes.c_float,                                                        # glong
    ctypes.c_float,                                                        # stl
    ctypes.c_float,                                                        # f107a
    ctypes.c_float,                                                        # f107
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags="C_CONTIGUOUS"),  # ap(7)
    ctypes.c_int,                                                          # mass
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags="C_CONTIGUOUS"),  # d_out(8)
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags="C_CONTIGUOUS"),  # t_out(2)
]


class Model:
    """MSISE-90 中性大气模型 ctypes 封装。

    MSISE-90 将 MSIS-86 向下延伸至地面，可计算从地表到低热层的中性大气温度和物种数密度。
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        if dll_path is None:
            base = Path(__file__).resolve().parent
            if os.name == "nt":
                candidates = (base / "build" / "msise90.dll", base / "msise90.dll")
            else:
                candidates = (base / "build" / "libmsise90.so", base / "libmsise90.so")
            dll_path = next(
                (candidate for candidate in candidates if candidate.exists()),
                candidates[0],
            )
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)
        self._dll = ctypes.CDLL(str(self._dll_path))

        # 绑定 gtd6_eval
        self._gtd6_eval = self._dll.gtd6_eval
        self._gtd6_eval.restype = None
        self._gtd6_eval.argtypes = _ARGTYPES

    def calculate(
        self,
        *,
        iyd: NumericInput,
        sec: NumericInput,
        alt_km: NumericInput,
        lat_deg: NumericInput,
        lon_deg: NumericInput,
        stl_hours: NumericInput,
        f107a: NumericInput,
        f107: NumericInput,
        ap7: ApInput = None,
        mass: int = 48,
    ) -> dict:
        """
        计算 MSISE-90 温度和密度。

        标量输入返回标量输出；数组输入按 numpy 广播后返回数组输出。

        参数
        ----------
        iyd : int
            日期，格式 YYYYDDD（如 2023001）。
        sec : float
            世界时秒数（0-86400）。
        alt_km : float or array
            高度（km），可从地表（0 km）到热层。
        lat_deg : float or array
            地理纬度（度）。
        lon_deg : float or array
            地理经度（度）。
        stl_hours : float
            地方太阳时（小时）。
        f107a : float
            81 天平均 F10.7 太阳通量。
        f107 : float
            前一天的 F10.7 太阳通量。
        ap7 : array-like, optional
            长度为 7 的地磁活动指数序列。默认 [4.0] * 7。
        mass : int
            质量数选择器。48 = 所有物种，0 = 仅温度。默认 48。

        返回
        -------
        dict
            包含 alt_km, T_local_K, T_exo_K, densities 字段。
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

        densities = np.empty((flat_count, 8), dtype=float)
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
            "densities": densities.reshape(shape + (8,)),
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
    ):
        ap_array = np.asarray(ap7, dtype=np.float32)
        d_out = np.zeros(8, dtype=np.float32)
        t_out = np.zeros(2, dtype=np.float32)

        self._gtd6_eval(
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


def _normalize_ap7(ap7, count: int) -> np.ndarray:
    """将 ap7 参数规范化为 (count, 7) 数组。"""
    if ap7 is None:
        return np.full((count, 7), 4.0, dtype=float)

    arr = np.asarray(ap7, dtype=float)
    if arr.ndim == 1:
        if arr.shape[0] != 7:
            raise ValueError("ap7 长度必须为 7")
        return np.tile(arr, (count, 1))

    if arr.ndim == 2:
        if arr.shape[1] != 7:
            raise ValueError("二维 ap7 输入必须具有形状 (N, 7)")
        if arr.shape[0] == 1:
            return np.tile(arr[0], (count, 1))
        if arr.shape[0] == count:
            return arr
        raise ValueError("二维 ap7 输入的行数必须为 1 或与广播后的样本数相同")

    raise ValueError("ap7 维度错误")
