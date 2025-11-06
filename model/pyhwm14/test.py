import ctypes as C
import numpy as np
import os

# 若需要：告知 HWM 数据目录
os.environ["HWMPATH"] = r".\data"

dll = C.cdll.LoadLibrary(r".\hwm14.dll")

# 函数原型：void hwm14_eval(int, float, float, float, float, float, float, float, const float[2], float[2])
hwm = dll.hwm14_eval
hwm.restype = None
hwm.argtypes = [
    C.c_int,         # iyd (YYYYDDD, 如 2025290)
    C.c_float,       # sec (UTC秒，0..86400)
    C.c_float,       # alt (km)
    C.c_float,       # glat (deg)
    C.c_float,       # glon (deg, east+)
    C.c_float,       # stl (本地太阳时, 小时)
    C.c_float,       # f107a
    C.c_float,       # f107
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1,
                           shape=(2,), flags="C_CONTIGUOUS"),
    np.ctypeslib.ndpointer(dtype=np.float32, ndim=1,
                           shape=(2,), flags="C_CONTIGUOUS"),
]

ap = np.array([0.0, 20.0], dtype=np.float32)  # ap(1) 未用；ap(2)=当前3小时ap
# 输出：w[0]=meridional(+北), w[1]=zonal(+东)
w = np.zeros(2, dtype=np.float32)

hwm(
    2025290,               # iyd = 年+儒略日，比如 2025年 第290天
    np.float32(43200.0),   # 正午 UTC 秒
    np.float32(250.0),     # 高度 km
    np.float32(30.0),      # 纬度 deg
    np.float32(114.0),     # 经度 deg (东经为正)
    np.float32(12.0),      # 本地太阳时 小时
    np.float32(150.0),     # f107a
    np.float32(150.0),     # f107
    ap, w
)

print("Meridional, Zonal [m/s] =", w.tolist())
