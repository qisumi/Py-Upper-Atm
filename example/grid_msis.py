from __future__ import annotations

import math
from typing import List, Optional, Sequence, Any, Dict

import numpy as np

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

from model.pymsis2 import NRLMSIS2, doy, seconds_of_day


def compute_region_msis(
    msis: Optional[NRLMSIS2],
    lat0: float,
    lat1: float,
    lon0: float,
    lon1: float,
    lat_steps: int,
    lon_steps: int,
    alt_km_list: Sequence[float],
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    second: float = 0.0,
    f107: float = 150.0,
    f107a: float = 150.0,
    ap7: Optional[Sequence[float]] = None,
    out_numpy: bool = False,
) -> List[Dict[str, Any]]:

    if msis is None:
        msis = NRLMSIS2(precision="single")

    # normalize steps
    lat_steps = max(1, int(lat_steps))
    lon_steps = max(1, int(lon_steps))

    lat0, lat1 = float(lat0), float(lat1)
    lon0, lon1 = float(lon0), float(lon1)

    lats = np.linspace(lat0, lat1, lat_steps)
    lons = np.linspace(lon0, lon1, lon_steps)

    alt_km_arr = np.asarray(list(alt_km_list), dtype=float)
    day_val = doy(year, month, day)
    utsec = seconds_of_day(hour, minute, second)

    total = lat_steps * lon_steps
    use_tqdm = tqdm is not None

    results: List[Dict[str, Any]] = []

    iterator = ((ilat, ilon) for ilat in lats for ilon in lons)
    if use_tqdm:
        iterator = tqdm(iterator, total=total, desc="MSIS grid")

    for lat, lon in iterator:
        # msis.calc_many 接受向量高度，返回每个高度的多分量结果
        try:
            out = msis.calc_many(
                day=day_val,
                utsec=utsec,
                alt_km=alt_km_arr,
                lat_deg=lat,
                lon_deg=lon,
                f107a=f107a,
                f107=f107,
                ap7=ap7,
                out_numpy=True,
            )
        except Exception:
            # 如果 calc_many 不可用或出错，回退到逐高度 calc
            T_local = []
            dn10_list = []
            for h in alt_km_arr:
                r = msis.calc(
                    day=day_val,
                    utsec=utsec,
                    alt_km=float(h),
                    lat_deg=lat,
                    lon_deg=lon,
                    f107a=f107a,
                    f107=f107,
                    ap7=ap7,
                )
                T_local.append(r.T_local_K)
                dn10_list.append(r.dn10)

            T_local = np.asarray(T_local)
            dn10 = np.asarray(dn10_list)
            out = {
                "alt_km": alt_km_arr,
                "T_local_K": T_local,
                "dn10": dn10,
            }

        # 标准化输出结构
        res_entry: Dict[str, Any] = {
            "lat": float(lat),
            "lon": float(lon),
            "alt_km": np.asarray(out["alt_km"]) if out_numpy else list(out["alt_km"]),
            "T_local_K": np.asarray(out["T_local_K"]) if out_numpy else list(out["T_local_K"]),
            "dn10": np.asarray(out["dn10"]) if out_numpy else [list(row) for row in out["dn10"]],
        }

        results.append(res_entry)

    return results


if __name__ == "__main__":
    # 简单示例：小网格，演示调用和进度条
    msis = NRLMSIS2(precision="single")
    lat0, lat1 = 39.5, 40.3
    lon0, lon1 = 116.0, 117.0
    lat_steps, lon_steps = 4, 5
    alt_km_list = [100, 200, 300]
    year, month, day = 2020, 7, 18

    results = compute_region_msis(
        msis,
        lat0,
        lat1,
        lon0,
        lon1,
        lat_steps,
        lon_steps,
        alt_km_list,
        year,
        month,
        day,
        hour=12,
        out_numpy=False,
    )

    print(f"Computed {len(results)} grid points. Example first point:")
    if results:
        r0 = results[0]
        print(r0["lat"], r0["lon"])
        print("alt_km:", r0["alt_km"])
        print("T_local_K:", r0["T_local_K"])
        # dn10 是 [n_alt, n_species]
        print("dn10 shape:", np.asarray(r0["dn10"]).shape)
