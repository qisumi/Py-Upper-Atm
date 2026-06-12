"""
Xu-Li Neutral Sheet Model (Xu & Li, CAS Beijing) ctypes wrapper.

Computes the position of the geomagnetic tail neutral sheet along the Z-axis
in GSM (Geocentric Solar Magnetospheric) coordinates using three variants:
  - AEN (Analytical Equatorial Neutral)
  - SEN (Standard Equatorial Neutral)
  - DEN (Displaced Equatorial Neutral)

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

_XULI_EVAL_ARGTYPES = [
    _C_FLOAT,             # tila (tilt angle, degrees)
    _C_FLOAT,             # xsm  (GSM X, Earth Radii)
    _C_FLOAT,             # ysm  (GSM Y, Earth Radii)
    C.POINTER(_C_FLOAT),  # zaen (out)
    C.POINTER(_C_FLOAT),  # zsen (out)
    C.POINTER(_C_FLOAT),  # zden (out)
    C.POINTER(_C_FLOAT),  # rmp  (out)
    C.POINTER(_C_INT),    # ie_aen (out)
    C.POINTER(_C_INT),    # ie_sen (out)
    C.POINTER(_C_INT),    # ie_den (out)
]

_XULI_TILT_ARGTYPES = [
    _C_FLOAT,             # doy
    _C_FLOAT,             # ut_hours
    C.POINTER(_C_FLOAT),  # tilt_deg (out)
]


class Model:
    """Xu-Li Neutral Sheet Model (Xu & Li, CAS Beijing) ctypes wrapper."""

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "xuli.dll" if os.name == "nt" else "libxuli.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._eval = self._dll.xuli_eval
        self._eval.restype = None
        self._eval.argtypes = _XULI_EVAL_ARGTYPES
        self._tilt = self._dll.xuli_tilt
        self._tilt.restype = None
        self._tilt.argtypes = _XULI_TILT_ARGTYPES

    def calculate(
        self,
        *,
        x_re: Union[float, "np.ndarray"],
        y_re: Union[float, "np.ndarray"],
        doy: Optional[Union[float, "np.ndarray"]] = None,
        ut_hours: Optional[Union[float, "np.ndarray"]] = None,
        tilt_angle_deg: Optional[Union[float, "np.ndarray"]] = None,
    ) -> dict:
        """
        计算磁尾中性片位置（GSM 坐标系，地球半径单位）。

        可通过两种方式提供偶极倾角：
          1. 传入 tilt_angle_deg 直接指定倾角（度）。
          2. 传入 doy 和 ut_hours，由模型内部计算倾角。

        参数：
            x_re: GSM X 坐标（地球半径），标量或数组。磁尾方向为负值。
            y_re: GSM Y 坐标（地球半径），标量或数组。
            doy: 年积日（1.0–366.0），标量或数组。
                 当 tilt_angle_deg 未提供时必填。
            ut_hours: 世界时（小时），标量或数组。
                      当 tilt_angle_deg 未提供时必填。
            tilt_angle_deg: 地磁偶极倾角（度），标量或数组。
                            若提供则忽略 doy 和 ut_hours。

        返回：
            包含以下键的字典：
                x_re: GSM X 坐标输入
                y_re: GSM Y 坐标输入
                tilt_angle_deg: 使用的偶极倾角（度）
                zaen_re: AEN 中性片 Z 位置（地球半径）
                zsen_re: SEN 中性片 Z 位置（地球半径）
                zden_re: DEN 中性片 Z 位置（地球半径）
                rmp_re: 磁层顶截面半径（地球半径）
                ie_aen: AEN 在磁层顶内/外标志（1=内, 2=外）
                ie_sen: SEN 在磁层顶内/外标志（1=内, 2=外）
                ie_den: DEN 在磁层顶内/外标志（1=内, 2=外）
        """
        if tilt_angle_deg is not None:
            return _calculate_xuli(
                self._eval,
                x_re=x_re,
                y_re=y_re,
                tilt_angle_deg=tilt_angle_deg,
            )
        if doy is None or ut_hours is None:
            raise ValueError(
                "必须提供 tilt_angle_deg 或同时提供 doy 和 ut_hours"
            )
        return _calculate_xuli_with_time(
            self._eval,
            self._tilt,
            x_re=x_re,
            y_re=y_re,
            doy=doy,
            ut_hours=ut_hours,
        )


def _compute_tilt(tilt_func, doy_val: float, ut_val: float) -> float:
    """调用 DLL 计算单个点的偶极倾角。"""
    tilt = _C_FLOAT()
    tilt_func(
        _C_FLOAT(float(doy_val)),
        _C_FLOAT(float(ut_val)),
        C.byref(tilt),
    )
    return float(tilt.value)


def _calculate_one(eval_func, tila: float, xsm: float, ysm: float):
    """单点 DLL 调用，返回 (zaen, zsen, zden, rmp, ie_aen, ie_sen, ie_den)。"""
    zaen = _C_FLOAT()
    zsen = _C_FLOAT()
    zden = _C_FLOAT()
    rmp = _C_FLOAT()
    ie_aen = _C_INT()
    ie_sen = _C_INT()
    ie_den = _C_INT()
    eval_func(
        _C_FLOAT(float(tila)),
        _C_FLOAT(float(xsm)),
        _C_FLOAT(float(ysm)),
        C.byref(zaen),
        C.byref(zsen),
        C.byref(zden),
        C.byref(rmp),
        C.byref(ie_aen),
        C.byref(ie_sen),
        C.byref(ie_den),
    )
    return (
        float(zaen.value),
        float(zsen.value),
        float(zden.value),
        float(rmp.value),
        int(ie_aen.value),
        int(ie_sen.value),
        int(ie_den.value),
    )


def _calculate_xuli(eval_func, *, x_re, y_re, tilt_angle_deg) -> dict:
    """tilt_angle_deg 直接提供时的广播计算。"""
    arrays = np.broadcast_arrays(
        np.asarray(x_re, dtype=float),
        np.asarray(y_re, dtype=float),
        np.asarray(tilt_angle_deg, dtype=float),
    )
    scalar_input = all(
        np.asarray(v).ndim == 0
        for v in [x_re, y_re, tilt_angle_deg]
    )
    flat_count = arrays[0].size
    shape = arrays[0].shape

    zaen_arr = np.empty(flat_count, dtype=float)
    zsen_arr = np.empty(flat_count, dtype=float)
    zden_arr = np.empty(flat_count, dtype=float)
    rmp_arr = np.empty(flat_count, dtype=float)
    ie_aen_arr = np.empty(flat_count, dtype=int)
    ie_sen_arr = np.empty(flat_count, dtype=int)
    ie_den_arr = np.empty(flat_count, dtype=int)

    flat = [a.reshape(-1) for a in arrays]
    for i in range(flat_count):
        za, zs, zd, rm, iea, ies, ied = _calculate_one(
            eval_func,
            float(flat[2][i]),  # tilt_angle_deg
            float(flat[0][i]),  # x_re
            float(flat[1][i]),  # y_re
        )
        zaen_arr[i] = za
        zsen_arr[i] = zs
        zden_arr[i] = zd
        rmp_arr[i] = rm
        ie_aen_arr[i] = iea
        ie_sen_arr[i] = ies
        ie_den_arr[i] = ied

    result = {
        "x_re": arrays[0],
        "y_re": arrays[1],
        "tilt_angle_deg": arrays[2],
        "zaen_re": zaen_arr.reshape(shape),
        "zsen_re": zsen_arr.reshape(shape),
        "zden_re": zden_arr.reshape(shape),
        "rmp_re": rmp_arr.reshape(shape),
        "ie_aen": ie_aen_arr.reshape(shape),
        "ie_sen": ie_sen_arr.reshape(shape),
        "ie_den": ie_den_arr.reshape(shape),
    }
    if scalar_input:
        return {k: float(v) if k not in (
            "ie_aen", "ie_sen", "ie_den"
        ) else int(v) for k, v in result.items()}
    return result


def _calculate_xuli_with_time(eval_func, tilt_func, *, x_re, y_re,
                               doy, ut_hours) -> dict:
    """通过 doy + ut_hours 计算倾角后再求中性片。"""
    arrays = np.broadcast_arrays(
        np.asarray(x_re, dtype=float),
        np.asarray(y_re, dtype=float),
        np.asarray(doy, dtype=float),
        np.asarray(ut_hours, dtype=float),
    )
    scalar_input = all(
        np.asarray(v).ndim == 0
        for v in [x_re, y_re, doy, ut_hours]
    )
    flat_count = arrays[0].size
    shape = arrays[0].shape

    tilt_arr = np.empty(flat_count, dtype=float)
    zaen_arr = np.empty(flat_count, dtype=float)
    zsen_arr = np.empty(flat_count, dtype=float)
    zden_arr = np.empty(flat_count, dtype=float)
    rmp_arr = np.empty(flat_count, dtype=float)
    ie_aen_arr = np.empty(flat_count, dtype=int)
    ie_sen_arr = np.empty(flat_count, dtype=int)
    ie_den_arr = np.empty(flat_count, dtype=int)

    flat = [a.reshape(-1) for a in arrays]
    for i in range(flat_count):
        tilt_val = _compute_tilt(
            tilt_func, float(flat[2][i]), float(flat[3][i])
        )
        tilt_arr[i] = tilt_val
        za, zs, zd, rm, iea, ies, ied = _calculate_one(
            eval_func,
            tilt_val,
            float(flat[0][i]),  # x_re
            float(flat[1][i]),  # y_re
        )
        zaen_arr[i] = za
        zsen_arr[i] = zs
        zden_arr[i] = zd
        rmp_arr[i] = rm
        ie_aen_arr[i] = iea
        ie_sen_arr[i] = ies
        ie_den_arr[i] = ied

    result = {
        "x_re": arrays[0],
        "y_re": arrays[1],
        "tilt_angle_deg": tilt_arr.reshape(shape),
        "zaen_re": zaen_arr.reshape(shape),
        "zsen_re": zsen_arr.reshape(shape),
        "zden_re": zden_arr.reshape(shape),
        "rmp_re": rmp_arr.reshape(shape),
        "ie_aen": ie_aen_arr.reshape(shape),
        "ie_sen": ie_sen_arr.reshape(shape),
        "ie_den": ie_den_arr.reshape(shape),
    }
    if scalar_input:
        return {k: float(v) if k not in (
            "ie_aen", "ie_sen", "ie_den"
        ) else int(v) for k, v in result.items()}
    return result
