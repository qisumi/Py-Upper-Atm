# test.py — NRLMSIS2 C-ABI smoke test aligned to your signature
import ctypes as C
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
DLL = BUILD / "nrlmsis2.dll"

msis = C.CDLL(str(DLL))

# === 精度：若 rp=REAL(4) 用 c_float；若启用 -DDBLE 则改成 c_double ===
FT = C.c_float   # 若库为双精度，改：FT = C.c_double

# 解析稳定导出名（来自 shim 的 bind(C,name="msiscalc")）
msiscalc = getattr(msis, "msiscalc")

# void msiscalc(FT day, FT utsec, FT z, FT lat, FT lon,
#               FT f107a, FT f107, const FT ap7[7],
#               FT* t_local, FT dn10[10], FT* t_exo)
msiscalc.argtypes = [FT, FT, FT, FT, FT, FT, FT, C.POINTER(FT),
                     C.POINTER(FT), C.POINTER(FT), C.POINTER(FT)]
msiscalc.restype = None

# ==== 输入/输出缓冲 ====
ap7 = (FT * 7)(*([4.0] * 7))     # 简单示例：Kp≈2 的近似
dn10 = (FT * 10)()
t_local = FT()
t_exo = FT()


def call_msiscalc(day: float, utsec: float, z_km: float,
                  lat_deg: float, lon_deg: float,
                  f107a: float, f107: float,
                  ap_seq=None):
    if ap_seq is not None:
        assert len(ap_seq) == 7
        for i, v in enumerate(ap_seq):
            ap7[i] = FT(v)

    msiscalc(FT(day), FT(utsec), FT(z_km), FT(lat_deg), FT(lon_deg),
             FT(f107a), FT(f107), ap7,
             C.byref(t_local), dn10, C.byref(t_exo))

    # 输出打包
    return {
        "inputs": {"day": day, "utsec": utsec, "alt_km": z_km, "lat": lat_deg, "lon": lon_deg,
                   "f107a": f107a, "f107": f107, "ap7": [float(x) for x in ap7]},
        "T_local_K": float(t_local.value),
        "T_exo_K":   float(t_exo.value),
        "densities": [float(dn10[i]) for i in range(10)]  # 具体物种顺序以实现为准（10 元）
    }


# ==== 冒烟：北京上空 250 km，2020 年第 200 天中午 ====
res = call_msiscalc(day=200.0, utsec=12*3600.0, z_km=250.0,
                    lat_deg=39.9, lon_deg=116.4,
                    f107a=150.0, f107=150.0)
print("--- single point @250 km ---")
print(res)

# ==== 剖面：50~500 km，每 50 km ====
print("--- profile 50~500 km step 50 ---")
for h in range(50, 501, 50):
    out = call_msiscalc(day=200.0, utsec=12*3600.0, z_km=float(h),
                        lat_deg=39.9, lon_deg=116.4, f107a=150.0, f107=150.0)
    print(
        f"{h:4d} km  T_local={out['T_local_K']:.1f}  dn[O?]={out['densities'][1]:.3e}")
