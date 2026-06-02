"""
SOLPRO 行星际太阳质子通量模型 ctypes 封装。

基于 King (1974) 和 Stassinopoulos & King (1974) 太阳质子通量模型，
计算给定任务持续时间和置信水平下的行星际积分太阳质子通量（1 AU）。

输出 10 个能阈（10, 20, ..., 100 MeV）的质子积分通量（protons/cm²），
以及预测的异常大事件（Anomalously Large events）数量。

参考文献：
  - King, J. H., J. Spacecraft & Rockets 11, 401, 1974
  - Stassinopoulos, E. G., and J. H. King, NASA TM X-71140, 1974

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

_SOLPRO_ARGTYPES = [
    _C_FLOAT,                       # tau (by value)
    _C_INT,                         # iq  (by value)
    C.POINTER(_C_FLOAT),            # f(10) output
    C.POINTER(_C_INT),              # inale output
]

# Energy thresholds in MeV (hard-coded in the model)
ENERGY_THRESHOLDS_MEV = np.array([10.0 * n for n in range(1, 11)])


class Model:
    """SOLPRO 行星际太阳质子通量模型 ctypes 封装。

    计算给定任务持续时间和置信水平下的太阳质子积分通量（1 AU）。
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "solpro.dll" if os.name == "nt" else "libsolpro.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._solpro = self._dll.solpro_eval
        self._solpro.restype = None
        self._solpro.argtypes = _SOLPRO_ARGTYPES

    def calculate(
        self,
        *,
        duration_months: Union[float, "np.ndarray"],
        confidence_pct: Union[int, "np.ndarray"],
    ) -> dict:
        """
        计算行星际太阳质子积分通量。

        参数：
            duration_months: 任务持续时间（月），范围 1–72。
            confidence_pct: 置信水平（%），范围 80–99。
                表示计算通量不被超越的概率。

        返回：
            包含以下键的字典：
                duration_months: 输入持续时间（月）
                confidence_pct: 输入置信水平（%）
                fluence_cm2: 积分通量（protons/cm²），形状 (10,) 或 (N, 10)
                n_al_events: 异常大事件数量，标量或形状 (N,)
        """
        return _calculate_solpro(
            self._solpro,
            duration_months=duration_months,
            confidence_pct=confidence_pct,
        )


def _calculate_one(
    solpro_func,
    duration_months: float,
    confidence_pct: int,
) -> tuple[np.ndarray, int]:
    """Call the DLL for a single point, return (fluence[10], n_al_events)."""
    f_arr = (_C_FLOAT * 10)()
    inale = _C_INT()

    solpro_func(
        _C_FLOAT(float(duration_months)),
        _C_INT(int(confidence_pct)),
        f_arr,
        C.byref(inale),
    )

    fluence = np.array([float(f_arr[i]) for i in range(10)], dtype=float)
    return fluence, int(inale.value)


def _calculate_solpro(
    solpro_func,
    *,
    duration_months,
    confidence_pct,
) -> dict:
    """Broadcast inputs, call DLL per element, assemble result dict."""
    dur = np.asarray(duration_months, dtype=float)
    conf = np.asarray(confidence_pct, dtype=float)

    # Validate ranges
    if np.any(dur < 1) or np.any(dur > 72):
        raise ValueError("duration_months 必须在 1–72 范围内")
    if np.any(conf < 80) or np.any(conf > 99):
        raise ValueError("confidence_pct 必须在 80–99 范围内")

    arrays = np.broadcast_arrays(dur, conf)
    scalar_input = all(
        np.asarray(v).ndim == 0 for v in [duration_months, confidence_pct]
    )
    flat_count = arrays[0].size
    shape = arrays[0].shape

    fluence = np.empty((flat_count, 10), dtype=float)
    n_al = np.empty(flat_count, dtype=int)

    flat_dur = arrays[0].reshape(-1)
    flat_conf = arrays[1].reshape(-1)
    for i in range(flat_count):
        fl, na = _calculate_one(
            solpro_func,
            float(flat_dur[i]),
            int(flat_conf[i]),
        )
        fluence[i] = fl
        n_al[i] = na

    if scalar_input:
        return {
            "duration_months": float(np.asarray(duration_months)),
            "confidence_pct": int(np.asarray(confidence_pct)),
            "fluence_cm2": fluence[0],
            "n_al_events": int(n_al[0]),
        }

    return {
        "duration_months": arrays[0].astype(float),
        "confidence_pct": arrays[1].astype(int),
        "fluence_cm2": fluence.reshape(shape + (10,)),
        "n_al_events": n_al.reshape(shape),
    }
