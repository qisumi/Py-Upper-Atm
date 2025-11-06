"""
HWM14 Python wrapper (ctypes) — __init__.py
DLL 与本包同级；数据目录位于 ./data（通过 HWMPATH 注入）。
导出：
  - hwm14_eval(...): 单点评估，返回 (meridional, zonal) [m/s]
  - hwm14_eval_many(...): 支持广播的批量评估，返回 shape 对齐的 (wm, wz)
"""
from __future__ import annotations

import os
import sys
import ctypes as C
from pathlib import Path
from typing import Iterable, Tuple

try:
    import numpy as np
except Exception as e:
    np = None  # 允许无 numpy 的极简运行（仅单点）。批量接口会抛错。

__all__ = ["hwm14_eval", "hwm14_eval_many", "__version__"]
__version__ = "0.1.0"

# ──────────────────────────────────────────────────────────────────────────────
# 位置与环境变量：HWMPATH -> ./data
# ──────────────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).resolve().parent
_DATA = _BASE / "data"

# 若用户未显式设置，则默认指向 ./data
os.environ.setdefault("HWMPATH", str(_DATA))

# ──────────────────────────────────────────────────────────────────────────────
# 加载 DLL 并绑定函数签名
# ──────────────────────────────────────────────────────────────────────────────
_DLL_NAME = "hwm14.dll" if os.name == "nt" else "libhwm14.so"
_DLL_PATH = _BASE / _DLL_NAME

if not _DLL_PATH.exists():
    raise FileNotFoundError(f"HWM14 DLL not found at: {_DLL_PATH}")

_dll = C.cdll.LoadLibrary(str(_DLL_PATH))

# 原型：void hwm14_eval(int, float, float, float, float, float, float, float, const float[2], float[2])
_hwm = _dll.hwm14_eval
_hwm.restype = None

# ctypes 与 numpy dtype 对齐（float32 / int32）
_c_int = C.c_int
_c_float = C.c_float

_argtypes = [_c_int, _c_float, _c_float, _c_float,
             _c_float, _c_float, _c_float, _c_float]
_hwm.argtypes = _argtypes + [
    C.POINTER(_c_float),  # ap[2]
    C.POINTER(_c_float),  # w[2]
]


def _as_f32_scalar(x: float) -> float:
    """确保数值可被安全地转为 float32，再返回 Python float（输入检查用）。"""
    try:
        return float(x)
    except Exception as e:
        raise TypeError(f"Expected a number, got {type(x)}") from e


def _prep_array_2_f32(x) -> "np.ndarray":
    if np is None:
        raise RuntimeError(
            "numpy is required for array-based operations. Please install numpy.")
    arr = np.asarray(x, dtype=np.float32)
    if arr.size != 2:
        raise ValueError(f"Expected array of length 2, got shape {arr.shape}")
    if not arr.flags["C_CONTIGUOUS"]:
        arr = np.ascontiguousarray(arr, dtype=np.float32)
    return arr


def _ensure_w_buffer() -> "np.ndarray":
    if np is None:
        raise RuntimeError(
            "numpy is required for array-based operations. Please install numpy.")
    return np.zeros(2, dtype=np.float32)

# ──────────────────────────────────────────────────────────────────────────────
# 公共 API
# ──────────────────────────────────────────────────────────────────────────────


def hwm14_eval(
    iyd: int,
    sec: float,
    alt_km: float,
    glat_deg: float,
    glon_deg: float,
    stl_hours: float,
    f107a: float,
    f107: float,
    ap2: Iterable[float] = (0.0, 20.0),
) -> Tuple[float, float]:
    """
    单点评估接口（ctypes）：
      iyd       : 日历年+儒略日（YYYYDDD），如 2025290
      sec       : UTC 秒（0..86400）
      alt_km    : 高度 km
      glat_deg  : 纬度 deg
      glon_deg  : 经度 deg（东经为正）
      stl_hours : 本地太阳时（小时）
      f107a     : 81日滑动平均 F10.7
      f107      : 日 F10.7
      ap2       : 长度为 2 的数组；ap2[0] 常未用，ap2[1]=当前 3h ap

    返回：(meridional, zonal) 速度，单位 m/s。
    """
    # 标量预检查（转 Python float 即可，ctypes 会再做 float32 拷贝）
    iyd = int(iyd)
    sec = _as_f32_scalar(sec)
    alt_km = _as_f32_scalar(alt_km)
    glat_deg = _as_f32_scalar(glat_deg)
    glon_deg = _as_f32_scalar(glon_deg)
    stl_hours = _as_f32_scalar(stl_hours)
    f107a = _as_f32_scalar(f107a)
    f107 = _as_f32_scalar(f107)

    if np is None:
        # 无 numpy 时，手动构造 2 元 float32 缓冲
        ap_arr = (_c_float * 2)()
        a0, a1 = list(ap2) if isinstance(
            ap2, (list, tuple)) else (ap2[0], ap2[1])  # 最小实现
        ap_arr[0] = _c_float(a0)
        ap_arr[1] = _c_float(a1)
        w_arr = (_c_float * 2)()
        _hwm(
            _c_int(iyd),
            _c_float(sec),
            _c_float(alt_km),
            _c_float(glat_deg),
            _c_float(glon_deg),
            _c_float(stl_hours),
            _c_float(f107a),
            _c_float(f107),
            ap_arr,
            w_arr,
        )
        return float(w_arr[0].value), float(w_arr[1].value)

    # 有 numpy：用 np.float32/ndpointer 等价的底层内存
    ap_arr = _prep_array_2_f32(ap2)
    w_arr = _ensure_w_buffer()

    _hwm(
        _c_int(iyd),
        _c_float(sec),
        _c_float(alt_km),
        _c_float(glat_deg),
        _c_float(glon_deg),
        _c_float(stl_hours),
        _c_float(f107a),
        _c_float(f107),
        ap_arr.ctypes.data_as(C.POINTER(_c_float)),
        w_arr.ctypes.data_as(C.POINTER(_c_float)),
    )
    return (float(w_arr[0]), float(w_arr[1]))


def hwm14_eval_many(
    iyd,
    sec,
    alt_km,
    glat_deg,
    glon_deg,
    stl_hours,
    f107a,
    f107,
    ap2=(0.0, 20.0),
):
    """
    广播批量评估：接受任意能广播到共同形状的数组/标量；返回 (wm, wz) 两个 np.ndarray。
    需要 numpy。
    """
    if np is None:
        raise RuntimeError(
            "hwm14_eval_many requires numpy. Please install numpy.")
    # 广播到统一 shape
    iyd = np.asarray(iyd, dtype=np.int32)
    sec = np.asarray(sec, dtype=np.float32)
    alt_km = np.asarray(alt_km, dtype=np.float32)
    glat_deg = np.asarray(glat_deg, dtype=np.float32)
    glon_deg = np.asarray(glon_deg, dtype=np.float32)
    stl_hours = np.asarray(stl_hours, dtype=np.float32)
    f107a = np.asarray(f107a, dtype=np.float32)
    f107 = np.asarray(f107, dtype=np.float32)

    b_i, b_sec, b_alt, b_glat, b_glon, b_stl, b_a, b_f = np.broadcast_arrays(
        iyd, sec, alt_km, glat_deg, glon_deg, stl_hours, f107a, f107
    )
    out_shape = b_sec.shape
    wm = np.empty(out_shape, dtype=np.float32)
    wz = np.empty(out_shape, dtype=np.float32)

    # 准备 ap2 缓冲（固定长度 2）
    ap_arr = _prep_array_2_f32(ap2)
    ap_ptr = ap_arr.ctypes.data_as(C.POINTER(_c_float))

    # 逐元素调用底层函数（Fortran 不是向量化接口）
    it = np.nditer(
        [b_i, b_sec, b_alt, b_glat, b_glon, b_stl, b_a, b_f, wm, wz],
        flags=["multi_index", "refs_ok", "zerosize_ok"],
        op_flags=[["readonly"]]*8 + [["writeonly"], ["writeonly"]],
    )
    w_buf = np.zeros(2, dtype=np.float32)
    w_ptr = w_buf.ctypes.data_as(C.POINTER(_c_float))

    for iyd_i, sec_i, alt_i, lat_i, lon_i, stl_i, a_i, f_i, wm_o, wz_o in it:
        _hwm(
            _c_int(int(iyd_i)),
            _c_float(float(sec_i)),
            _c_float(float(alt_i)),
            _c_float(float(lat_i)),
            _c_float(float(lon_i)),
            _c_float(float(stl_i)),
            _c_float(float(a_i)),
            _c_float(float(f_i)),
            ap_ptr,
            w_ptr,
        )
        wm_o[...] = w_buf[0]
        wz_o[...] = w_buf[1]

    return wm, wz
