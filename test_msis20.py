from model.pymsis2 import NRLMSIS2, doy, seconds_of_day

msis = NRLMSIS2(precision="single")  # 如果 DLL/shim 用双精度：precision="double"

# 单点
res = msis.calc(
    day=doy(2020, 7, 18),                 # 2020-07-18 → 200.0
    utsec=seconds_of_day(12, 0, 0.0),     # 12:00:00
    alt_km=250.0, lat_deg=39.9, lon_deg=116.4,
    f107a=150.0, f107=150.0,
    ap7=[4.0]*7,                          # 可省略，默认 7*4.0
)
print(res)

# 批量（向量化）
out = msis.calc_many(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12),
    alt_km=[50, 100, 150, 200, 250, 300, 350, 400, 450, 500],
    lat_deg=39.9, lon_deg=116.4, f107a=150.0, f107=150.0,
    out_numpy=False,  # True 则返回 dict of numpy arrays
)
for r in out:
    print(r.alt_km, r.T_local_K, r.dn10[1])  # 例：第二个分量（如 O）密度
