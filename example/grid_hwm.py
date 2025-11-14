from __future__ import annotations

from typing import Sequence, Optional, Any, Dict, List
import numpy as np
from datetime import date

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

import model.pyhwm14 as pyhwm14


def compute_region_hwm(
    hwm_module=None,
    lat0: float = -90.0,
    lat1: float = 90.0,
    lon0: float = 0.0,
    lon1: float = 360.0,
    lat_steps: int = 1,
    lon_steps: int = 1,
    alt_km_list: Sequence[float] = (250.0,),
    year: int = 2020,
    month: int = 1,
    day: int = 1,
    hour: int = 12,
    minute: int = 0,
    second: float = 0.0,
    stl_hours: float = 12.0,
    f107: float = 150.0,
    f107a: float = 150.0,
    ap2: Optional[Sequence[float]] = None,
    out_numpy: bool = False,
) -> List[Dict[str, Any]]:

    if hwm_module is None:
        hwm_module = pyhwm14

    lat_steps = max(1, int(lat_steps))
    lon_steps = max(1, int(lon_steps))

    lat0, lat1 = float(lat0), float(lat1)
    lon0, lon1 = float(lon0), float(lon1)

    lats = np.linspace(lat0, lat1, lat_steps)
    lons = np.linspace(lon0, lon1, lon_steps)

    alt_km_arr = np.asarray(list(alt_km_list), dtype=float)

    # 构造 iyd (YYYYDDD) 和 seconds
    doy = date(year, month, day).timetuple().tm_yday
    iyd = int(year) * 1000 + int(doy)
    sec = float(hour) * 3600.0 + float(minute) * 60.0 + float(second)

    total = lat_steps * lon_steps
    use_tqdm = tqdm is not None

    results: List[Dict[str, Any]] = []

    iterator = ((ilat, ilon) for ilat in lats for ilon in lons)
    if use_tqdm:
        iterator = tqdm(iterator, total=total, desc="HWM grid")

    for lat, lon in iterator:
        # hwm14_eval_many 支持广播高度数组
        try:
            wm, wz = hwm_module.hwm14_eval_many(
                iyd=iyd,
                sec=sec,
                alt_km=alt_km_arr,
                glat_deg=lat,
                glon_deg=lon,
                stl_hours=stl_hours,
                f107a=f107a,
                f107=f107,
                ap2=ap2,
            )
            wm_arr = np.asarray(wm)
            wz_arr = np.asarray(wz)
        except Exception:
            # 回退到逐高度调用
            wm_list = []
            wz_list = []
            for h in alt_km_arr:
                wm_val, wz_val = hwm_module.hwm14_eval(
                    iyd=iyd,
                    sec=sec,
                    alt_km=float(h),
                    glat_deg=float(lat),
                    glon_deg=float(lon),
                    stl_hours=stl_hours,
                    f107a=f107a,
                    f107=f107,
                    ap2=ap2,
                )
                wm_list.append(wm_val)
                wz_list.append(wz_val)

            wm_arr = np.asarray(wm_list)
            wz_arr = np.asarray(wz_list)

        entry: Dict[str, Any] = {
            "lat": float(lat),
            "lon": float(lon),
            "alt_km": alt_km_arr if out_numpy else list(alt_km_arr),
            "wm": wm_arr if out_numpy else list(wm_arr),
            "wz": wz_arr if out_numpy else list(wz_arr),
        }

        results.append(entry)

    return results


if __name__ == "__main__":
    # 简单示例：小网格，演示调用和进度条
    lat0, lat1 = 30.0, 31.0
    lon0, lon1 = 114.0, 115.0
    lat_steps, lon_steps = 3, 4
    alt_km_list = [100, 200, 300]
    year, month, day = 2025, 10, 17

    results = compute_region_hwm(
        None,
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
        stl_hours=12.0,
        out_numpy=False,
    )

    print(f"Computed {len(results)} grid points. Example first point:")
    if results:
        r0 = results[0]
        print(r0["lat"], r0["lon"])
        print("alt_km:", r0["alt_km"])
        print("wm:", r0["wm"])
        print("wz:", r0["wz"])
