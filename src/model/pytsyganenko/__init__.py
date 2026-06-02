"""
Tsyganenko 磁层磁场模型 (T89/T96/T01/TS04) wrapper。

基于 Geopack-2005，计算外部（磁层电流）磁场贡献。
GSM 坐标系，单位为 nT。

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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_C_INT = C.c_int
_C_DOUBLE = C.c_double

_VALID_VERSIONS = ("T89", "T96", "T01", "TS04")

_DLL_NAMES = {
    "T89": ("tsyganenko_t89.dll", "libtsyganenko_t89.so"),
    "T96": ("tsyganenko_t96.dll", "libtsyganenko_t96.so"),
    "T01": ("tsyganenko_t01.dll", "libtsyganenko_t01.so"),
    "TS04": ("tsyganenko_ts04.dll", "libtsyganenko_ts04.so"),
}

# Number of meaningful PARMOD elements per model version
_PARMOD_SLOTS = {"T89": 0, "T96": 4, "T01": 6, "TS04": 10}

# ---------------------------------------------------------------------------
# argtypes
# ---------------------------------------------------------------------------

_RECALC_ARGTYPES = [
    _C_INT,        # iyear
    _C_INT,        # iday
    _C_INT,        # ihour
    _C_INT,        # imin
    _C_INT,        # isec
    C.POINTER(_C_DOUBLE),  # ps (out)
]

_EVAL_DIP_ARGTYPES = [
    _C_DOUBLE,              # x
    _C_DOUBLE,              # y
    _C_DOUBLE,              # z
    C.POINTER(_C_DOUBLE),   # bx (out)
    C.POINTER(_C_DOUBLE),   # by (out)
    C.POINTER(_C_DOUBLE),   # bz (out)
]

_EVAL_ARGTYPES = [
    _C_INT,                 # iopt
    C.POINTER(_C_DOUBLE),   # parmod(10)
    _C_DOUBLE,              # ps
    _C_DOUBLE,              # x
    _C_DOUBLE,              # y
    _C_DOUBLE,              # z
    C.POINTER(_C_DOUBLE),   # bx (out)
    C.POINTER(_C_DOUBLE),   # by (out)
    C.POINTER(_C_DOUBLE),   # bz (out)
]


# ======================================================================
# Public Model class
# ======================================================================

class Model:
    """Tsyganenko 磁层磁场模型 ctypes wrapper。

    支持四个模型版本：T89、T96、T01、TS04。

    参数：
        model_version: 模型版本，"T89" | "T96" | "T01" | "TS04"。
        dll_path: 显式指定 DLL 路径（通常自动检测）。
    """

    def __init__(
        self,
        *,
        model_version: str = "TS04",
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        ver = model_version.upper()
        if ver not in _VALID_VERSIONS:
            raise ValueError(
                f"model_version 必须为 {_VALID_VERSIONS} 之一，"
                f"当前值: {model_version!r}"
            )
        self._version = ver

        # Resolve DLL path
        if dll_path is None:
            dll_win, dll_linux = _DLL_NAMES[ver]
            dll_name = dll_win if os.name == "nt" else dll_linux
            dll_path = Path(__file__).resolve().parent / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))

        # Set up ctypes signatures
        self._recalc = self._dll.tsyganenko_recalc
        self._recalc.restype = None
        self._recalc.argtypes = _RECALC_ARGTYPES

        self._eval_dip = self._dll.tsyganenko_eval_dip
        self._eval_dip.restype = None
        self._eval_dip.argtypes = _EVAL_DIP_ARGTYPES

        self._eval = self._dll.tsyganenko_eval
        self._eval.restype = None
        self._eval.argtypes = _EVAL_ARGTYPES

    # ------------------------------------------------------------------
    # Public calculate method
    # ------------------------------------------------------------------

    def calculate(
        self,
        *,
        # Position: GSM coordinates, Earth radii
        x_re,
        y_re,
        z_re,
        # Time (for dipole tilt computation via RECALC)
        year=None,
        doy=None,
        hour=0,
        minute=0,
        second=0,
        # Or specify tilt angle directly
        tilt_rad=None,
        # T89-specific
        kp_index=None,
        # T96/T01/TS04 common solar wind parameters
        pdyn_nPa=None,
        dst_nT=None,
        by_imf_nT=None,
        bz_imf_nT=None,
        # T01-specific indices
        g1=None,
        g2=None,
        # TS04-specific storm-time indices
        w1=None,
        w2=None,
        w3=None,
        w4=None,
        w5=None,
        w6=None,
        # Optional: include internal dipole field
        include_dipole=False,
    ) -> dict:
        """
        计算磁层外部磁场。

        位置输入为 GSM 坐标系（地球半径 Re），输出磁场单位为 nT。

        必须指定 ``tilt_rad`` 或 ``year + doy`` 二选一，
        前者直接给出地磁偶极倾角，后者通过 RECALC 计算。

        各模型所需参数：
          - T89: kp_index (1-7)
          - T96: pdyn_nPa, dst_nT, by_imf_nT, bz_imf_nT
          - T01: 上述 + g1, g2
          - TS04: 上述 + w1~w6

        参数：
            x_re, y_re, z_re: GSM 位置（地球半径），标量或数组。
            year: 年份（如 2000）。
            doy: 年内天数（1-366）。
            hour, minute, second: 时刻。
            tilt_rad: 地磁偶极倾角（弧度），与 year/doy 二选一。
            kp_index: Kp 指数级别（1-7），仅 T89 使用。
            pdyn_nPa: 太阳风动压（nPa）。
            dst_nT: Dst 指数（nT）。
            by_imf_nT: IMF By 分量（nT, GSM）。
            bz_imf_nT: IMF Bz 分量（nT, GSM）。
            g1, g2: T01 专用指数。
            w1~w6: TS04 专用风暴时间参数。
            include_dipole: 是否叠加内部偶极场。

        返回：
            包含外部磁场分量（Bx_ext_nT 等）的字典。
            若 include_dipole=True，还包含偶极场和总场。
        """
        # --- Resolve tilt angle ---
        ps = self._resolve_tilt(tilt_rad, year, doy, hour, minute, second)

        # --- Validate and build model parameters ---
        iopt, parmod = self._build_params(
            kp_index=kp_index,
            pdyn_nPa=pdyn_nPa,
            dst_nT=dst_nT,
            by_imf_nT=by_imf_nT,
            bz_imf_nT=bz_imf_nT,
            g1=g1, g2=g2,
            w1=w1, w2=w2, w3=w3, w4=w4, w5=w5, w6=w6,
        )

        # --- Compute ---
        return _calculate_field(
            self._eval,
            self._eval_dip if include_dipole else None,
            iopt=iopt,
            parmod=parmod,
            ps=ps,
            x_re=x_re,
            y_re=y_re,
            z_re=z_re,
            include_dipole=include_dipole,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_tilt(self, tilt_rad, year, doy, hour, minute, second):
        """Return dipole tilt angle in radians."""
        if tilt_rad is not None:
            return tilt_rad
        if year is None or doy is None:
            raise ValueError(
                "必须提供 tilt_rad 或 year+doy 二选一，"
                "用于确定地磁偶极倾角。"
            )
        ps = _C_DOUBLE()
        self._recalc(
            _C_INT(int(year)),
            _C_INT(int(doy)),
            _C_INT(int(hour)),
            _C_INT(int(minute)),
            _C_INT(int(second)),
            C.byref(ps),
        )
        return float(ps.value)

    def _build_params(self, **kw):
        """Validate model-specific params and return (iopt, parmod[10])."""
        ver = self._version
        parmod = (C.c_double * 10)()

        if ver == "T89":
            kp = kw["kp_index"]
            if kp is None:
                raise ValueError("T89 模型需要 kp_index 参数（1-7）。")
            kp = int(kp)
            if kp < 1 or kp > 7:
                raise ValueError(f"kp_index 必须为 1-7，当前值: {kp}")
            return kp, parmod

        # T96/T01/TS04 — check solar wind params
        required = ["pdyn_nPa", "dst_nT", "by_imf_nT", "bz_imf_nT"]
        for name in required:
            if kw[name] is None:
                raise ValueError(
                    f"{ver} 模型需要 {name} 参数。"
                )

        parmod[0] = _C_DOUBLE(float(kw["pdyn_nPa"]))
        parmod[1] = _C_DOUBLE(float(kw["dst_nT"]))
        parmod[2] = _C_DOUBLE(float(kw["by_imf_nT"]))
        parmod[3] = _C_DOUBLE(float(kw["bz_imf_nT"]))

        if ver == "T01":
            for name in ("g1", "g2"):
                if kw[name] is None:
                    raise ValueError(f"T01 模型需要 {name} 参数。")
            parmod[4] = _C_DOUBLE(float(kw["g1"]))
            parmod[5] = _C_DOUBLE(float(kw["g2"]))

        if ver == "TS04":
            # TS04: PARMOD(1:10) = Pdyn, Dst, ByIMF, BzIMF, W1-W6
            for i, name in enumerate(["w1", "w2", "w3", "w4", "w5", "w6"], start=4):
                if kw[name] is None:
                    raise ValueError(f"TS04 模型需要 {name} 参数。")
                parmod[i] = _C_DOUBLE(float(kw[name]))

        return 0, parmod  # IOPT is dummy for T96/T01/TS04


# ======================================================================
# Internal computation helpers
# ======================================================================

def _calculate_one(
    eval_func,
    dip_func,
    iopt: int,
    parmod,
    ps: float,
    x: float,
    y: float,
    z: float,
):
    """Evaluate one point; returns dict with field components."""
    bx = _C_DOUBLE()
    by = _C_DOUBLE()
    bz = _C_DOUBLE()

    eval_func(
        _C_INT(iopt),
        parmod,
        _C_DOUBLE(ps),
        _C_DOUBLE(x),
        _C_DOUBLE(y),
        _C_DOUBLE(z),
        C.byref(bx),
        C.byref(by),
        C.byref(bz),
    )

    result = {
        "Bx_ext_nT": float(bx.value),
        "By_ext_nT": float(by.value),
        "Bz_ext_nT": float(bz.value),
    }

    if dip_func is not None:
        bx_d = _C_DOUBLE()
        by_d = _C_DOUBLE()
        bz_d = _C_DOUBLE()
        dip_func(
            _C_DOUBLE(x),
            _C_DOUBLE(y),
            _C_DOUBLE(z),
            C.byref(bx_d),
            C.byref(by_d),
            C.byref(bz_d),
        )
        result["Bx_dip_nT"] = float(bx_d.value)
        result["By_dip_nT"] = float(by_d.value)
        result["Bz_dip_nT"] = float(bz_d.value)
        result["Bx_total_nT"] = result["Bx_ext_nT"] + result["Bx_dip_nT"]
        result["By_total_nT"] = result["By_ext_nT"] + result["By_dip_nT"]
        result["Bz_total_nT"] = result["Bz_ext_nT"] + result["Bz_dip_nT"]

    return result


def _calculate_field(
    eval_func,
    dip_func,
    *,
    iopt: int,
    parmod,
    ps,
    x_re,
    y_re,
    z_re,
    include_dipole: bool,
) -> dict:
    """Broadcast inputs, loop per-point, return dict."""
    x_arr, y_arr, z_arr = np.broadcast_arrays(
        np.asarray(x_re, dtype=float),
        np.asarray(y_re, dtype=float),
        np.asarray(z_re, dtype=float),
    )
    shape = x_arr.shape
    flat_count = int(x_arr.size)
    ps_val = float(ps)

    # Pre-allocate output arrays
    bx_ext = np.empty(flat_count, dtype=float)
    by_ext = np.empty(flat_count, dtype=float)
    bz_ext = np.empty(flat_count, dtype=float)
    if include_dipole:
        bx_dip = np.empty(flat_count, dtype=float)
        by_dip = np.empty(flat_count, dtype=float)
        bz_dip = np.empty(flat_count, dtype=float)

    flat_x = x_arr.reshape(-1)
    flat_y = y_arr.reshape(-1)
    flat_z = z_arr.reshape(-1)

    for i in range(flat_count):
        r = _calculate_one(
            eval_func, dip_func,
            iopt, parmod, ps_val,
            flat_x[i], flat_y[i], flat_z[i],
        )
        bx_ext[i] = r["Bx_ext_nT"]
        by_ext[i] = r["By_ext_nT"]
        bz_ext[i] = r["Bz_ext_nT"]
        if include_dipole:
            bx_dip[i] = r["Bx_dip_nT"]
            by_dip[i] = r["By_dip_nT"]
            bz_dip[i] = r["Bz_dip_nT"]

    scalar_input = shape == ()

    def _out(arr):
        return float(arr[0]) if scalar_input else arr.reshape(shape)

    result = {
        "tilt_rad": ps_val,
        "Bx_ext_nT": _out(bx_ext),
        "By_ext_nT": _out(by_ext),
        "Bz_ext_nT": _out(bz_ext),
    }

    if include_dipole:
        result["Bx_dip_nT"] = _out(bx_dip)
        result["By_dip_nT"] = _out(by_dip)
        result["Bz_dip_nT"] = _out(bz_dip)
        result["Bx_total_nT"] = _out(bx_ext + bx_dip)
        result["By_total_nT"] = _out(by_ext + by_dip)
        result["Bz_total_nT"] = _out(bz_ext + bz_dip)

    return result
