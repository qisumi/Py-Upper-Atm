# test.py — MSIS2 C-ABI smoke test aligned to the shim signature
import ctypes as C
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
DLL = BUILD / "nrlmsis2.dll"

msis = C.CDLL(str(DLL))

# === Precision: use c_float if rp=REAL(4); use c_double when compiled with -DDBLE ===
FT = C.c_float   # Use C.c_double if the library is double-precision

# Parse the stable export name (from shim bind(C, name="msiscalc"))
msiscalc = getattr(msis, "msiscalc")

# void msiscalc(FT day, FT utsec, FT z, FT lat, FT lon,
#               FT f107a, FT f107, const FT ap7[7],
#               FT* t_local, FT dn10[10], FT* t_exo)
msiscalc.argtypes = [FT, FT, FT, FT, FT, FT, FT, C.POINTER(FT),
                     C.POINTER(FT), C.POINTER(FT), C.POINTER(FT)]
msiscalc.restype = None

# ==== Input/output buffers ====
ap7 = (FT * 7)(*([4.0] * 7))     # Simple example: Kp≈2 approximation
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

    # Pack output
    return {
        "inputs": {"day": day, "utsec": utsec, "alt_km": z_km, "lat": lat_deg, "lon": lon_deg,
                   "f107a": f107a, "f107": f107, "ap7": [float(x) for x in ap7]},
        "T_local_K": float(t_local.value),
        "T_exo_K":   float(t_exo.value),
        "densities": [float(dn10[i]) for i in range(10)]  # Species order is implementation-specific (10 entries)
    }


# ==== Smoke test: 250 km above Beijing on the 200th day of 2020 at noon ====
res = call_msiscalc(day=200.0, utsec=12*3600.0, z_km=250.0,
                    lat_deg=39.9, lon_deg=116.4,
                    f107a=150.0, f107=150.0)
print("--- single point @250 km ---")
print(res)

# ==== Profile: 50~500 km, every 50 km ====
print("--- profile 50~500 km step 50 ---")
for h in range(50, 501, 50):
    out = call_msiscalc(day=200.0, utsec=12*3600.0, z_km=float(h),
                        lat_deg=39.9, lon_deg=116.4, f107a=150.0, f107=150.0)
    print(
        f"{h:4d} km  T_local={out['T_local_K']:.1f}  dn[O?]={out['densities'][1]:.3e}")
