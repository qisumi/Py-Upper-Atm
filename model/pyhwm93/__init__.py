"""
HWM93 Python wrapper (ctypes) — __init__.py
DLL 与本包同级。
导出：
  - hwm93_eval(...): 单点评估，返回 (meridional, zonal) [m/s]
  - hwm93_eval_many(...): 支持广播的批量评估，返回 shape 对齐的 (wm, wz)
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

__all__ = ["hwm93_eval", "hwm93_eval_many", "__version__"]
__version__ = "0.1.0"

# ──────────────────────────────────────────────────────────────────────────────
# 位置与环境变量
# ──────────────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).resolve().parent

# ──────────────────────────────────────────────────────────────────────────────
# 加载 DLL 并绑定函数签名
# ──────────────────────────────────────────────────────────────────────────────
_DLL_NAME = "hwm93.dll" if os.name == "nt" else "libhwm93.so"
_DLL_PATH = _BASE / _DLL_NAME

print(f"[DEBUG] DLL 路径: {_DLL_PATH}")
print(f"[DEBUG] DLL 存在: {_DLL_PATH.exists()}")
print(f"[DEBUG] 当前工作目录: {os.getcwd()}")

if not _DLL_PATH.exists():
    raise FileNotFoundError(f"HWM93 DLL not found at: {_DLL_PATH}")

# 在 Windows 上，确保 mingw64 运行时库在 PATH 中
if os.name == "nt":
    mingw_bin = "C:\Program Files\mingw64\bin"
    if os.path.isdir(mingw_bin) and mingw_bin not in os.environ["PATH"]:
        print(f"[DEBUG] 添加 mingw64 路径到 PATH: {mingw_bin}")
        os.environ["PATH"] = mingw_bin + ";" + os.environ["PATH"]
    
    # 也将当前 DLL 目录添加到 PATH
    dll_dir = str(_BASE)
    if dll_dir not in os.environ["PATH"]:
        print(f"[DEBUG] 添加 DLL 目录到 PATH: {dll_dir}")
        os.environ["PATH"] = dll_dir + ";" + os.environ["PATH"]

# 尝试直接使用绝对路径加载
_dll_path_str = str(_DLL_PATH)
print(f"[DEBUG] 尝试加载 DLL: {_dll_path_str}")

# 在 Windows 上尝试使用 WinDLL 而不是 cdll
if os.name == "nt":
    try:
        print("[DEBUG] 尝试使用 WinDLL 加载")
        _dll = C.WinDLL(_dll_path_str, winmode=0)
    except Exception as e:
        print(f"[DEBUG] WinDLL 加载失败: {e}")
        print("[DEBUG] 回退到 cdll 加载")
        _dll = C.cdll.LoadLibrary(_dll_path_str)
else:
    _dll = C.cdll.LoadLibrary(_dll_path_str)

# 原型：void hwm93_eval(int, float, float, float, float, float, float, float, const float[2], float[2])
_hwm = _dll.hwm93_eval
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

def hwm93_eval(
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
    评估 HWM93 风场模型在指定条件下的风速。

    参数:
        iyd: 年日格式，如 2023365（2023年12月31日）
        sec: UTC 秒数（0-86400）
        alt_km: 高度（公里）
        glat_deg: 地理纬度（度，-90 到 90）
        glon_deg: 地理经度（度，0 到 360）
        stl_hours: 地方视太阳时（小时，0 到 24）
        f107a: 3个月平均 F10.7 太阳辐射通量（在低层大气可使用 150）
        f107: 前一天 F10.7 太阳辐射通量（在低层大气可使用 150）
        ap2: 地磁指数数组，包含：
            ap2[0]: 日地磁指数（在低层大气可使用 4）
            ap2[1]: 当前3小时 ap 指数（仅在 SW(9)=-1 时使用）

    返回:
        (meridional_wind, zonal_wind): 经向风和纬向风速度（m/s）
            - 经向风：正值表示北
            - 纬向风：正值表示东

    注意:
        - 对于最符合物理实际的计算，UT、地方时和经度应该保持一致
        - HWM93 覆盖所有高度区域
    """
    # 参数验证与转换
    iyd = int(iyd)
    sec = _as_f32_scalar(sec)
    alt_km = _as_f32_scalar(alt_km)
    glat_deg = _as_f32_scalar(glat_deg)
    glon_deg = _as_f32_scalar(glon_deg)
    stl_hours = _as_f32_scalar(stl_hours)
    f107a = _as_f32_scalar(f107a)
    f107 = _as_f32_scalar(f107)
    
    # 准备 ap 数组
    ap_vals = tuple(ap2)
    if len(ap_vals) != 2:
        raise ValueError(f"Expected ap2 to have 2 elements, got {len(ap_vals)}")
    
    ap_arr = (C.c_float * 2)(*(float(x) for x in ap_vals))
    
    # 准备输出数组
    w_out = (C.c_float * 2)(0.0, 0.0)
    
    # 调用 DLL 函数
    _hwm(iyd, sec, alt_km, glat_deg, glon_deg, stl_hours, f107a, f107, ap_arr, w_out)
    
    # 返回结果（Python float）
    return float(w_out[0]), float(w_out[1])


def hwm93_eval_many(
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
    批量评估 HWM93 风场模型在多个位置/时间点的风速。
    支持 numpy 数组输入，自动广播。

    参数:
        与 hwm93_eval 相同，但所有参数都可以是 numpy 数组。
        ap2 可以是长度为 2 的序列或广播兼容的数组。

    返回:
        (wm_arr, wz_arr): 经向风和纬向风的 numpy 数组
            形状与广播后的输入一致

    依赖:
        需要 numpy
    """
    if np is None:
        raise RuntimeError(
            "numpy is required for hwm93_eval_many. Please install numpy.")
    
    # 统一转换为数组
    iyd = np.asarray(iyd, dtype=np.int32)
    sec = np.asarray(sec, dtype=np.float32)
    alt_km = np.asarray(alt_km, dtype=np.float32)
    glat_deg = np.asarray(glat_deg, dtype=np.float32)
    glon_deg = np.asarray(glon_deg, dtype=np.float32)
    stl_hours = np.asarray(stl_hours, dtype=np.float32)
    f107a = np.asarray(f107a, dtype=np.float32)
    f107 = np.asarray(f107, dtype=np.float32)
    
    # 处理 ap2 参数
    if hasattr(ap2, 'shape'):
        # 如果是数组，确保形状兼容
        ap_arr = np.asarray(ap2, dtype=np.float32)
        if ap_arr.shape[-1] != 2:
            raise ValueError(f"Last dimension of ap2 must be 2, got {ap_arr.shape[-1]}")
    else:
        # 如果是序列，转为形状为 (2,) 的数组并广播
        ap_vals = tuple(ap2)
        if len(ap_vals) != 2:
            raise ValueError(f"Expected ap2 to have 2 elements, got {len(ap_vals)}")
        ap_arr = np.array(ap_vals, dtype=np.float32)
    
    # 计算广播后的形状
    inputs = [iyd, sec, alt_km, glat_deg, glon_deg, stl_hours, f107a, f107]
    try:
        # 尝试广播以确定输出形状
        shape = np.broadcast_shapes(*(inp.shape for inp in inputs))
        # 计算广播后的总元素数量
        total_elements = int(np.prod(shape))
    except ValueError as e:
        raise ValueError(f"Input shapes are not broadcastable: {e}")
    
    # 创建广播后的网格
    try:
        # 使用 meshgrid 广播所有参数
        grid = np.broadcast_arrays(
            iyd, sec, alt_km, glat_deg, glon_deg, stl_hours, f107a, f107
        )
        # 扁平化广播后的网格
        iyd_flat = grid[0].reshape(-1)
        sec_flat = grid[1].reshape(-1)
        alt_km_flat = grid[2].reshape(-1)
        glat_deg_flat = grid[3].reshape(-1)
        glon_deg_flat = grid[4].reshape(-1)
        stl_hours_flat = grid[5].reshape(-1)
        f107a_flat = grid[6].reshape(-1)
        f107_flat = grid[7].reshape(-1)
    except ValueError as e:
        raise ValueError(f"Failed to create broadcast arrays: {e}")
    
    # 处理 ap2
    if len(ap_arr.shape) == 1:
        # 如果是 (2,) 形状，为所有点使用相同的 ap2
        ap_flat = np.tile(ap_arr, (total_elements, 1))
    else:
        # 如果是多维数组，重塑为 (-1, 2) 并确保长度正确
        ap_flat = ap_arr.reshape(-1, 2)
        if ap_flat.shape[0] != total_elements and ap_flat.shape[0] == 1:
            # 如果只有一个 ap2 数组但需要多个，重复它
            ap_flat = np.tile(ap_flat[0], (total_elements, 1))
    
    # 初始化输出数组
    wm_flat = np.zeros(total_elements, dtype=np.float32)
    wz_flat = np.zeros(total_elements, dtype=np.float32)
    
    # 批量调用 DLL 函数
    for i in range(total_elements):
        # 准备参数
        ap_ptr = ap_flat[i].ctypes.data_as(C.POINTER(C.c_float))
        w_out = (C.c_float * 2)(0.0, 0.0)
        
        # 调用 DLL
        _hwm(
            int(iyd_flat[i]),
            float(sec_flat[i]),
            float(alt_km_flat[i]),
            float(glat_deg_flat[i]),
            float(glon_deg_flat[i]),
            float(stl_hours_flat[i]),
            float(f107a_flat[i]),
            float(f107_flat[i]),
            ap_ptr,
            w_out
        )
        
        # 存储结果
        wm_flat[i] = w_out[0]
        wz_flat[i] = w_out[1]
    
    # 重塑结果到原始广播形状
    wm = wm_flat.reshape(shape)
    wz = wz_flat.reshape(shape)
    
    return wm, wz