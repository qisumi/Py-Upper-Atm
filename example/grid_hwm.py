from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import sys

import numpy as np

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import HWM14


def compute_region_hwm(
    hwm_model=None,
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
    if hwm_model is None:
        hwm_model = HWM14()

    lats = np.linspace(float(lat0), float(lat1), max(1, int(lat_steps)))
    lons = np.linspace(float(lon0), float(lon1), max(1, int(lon_steps)))
    alt_km_arr = np.asarray(list(alt_km_list), dtype=float)

    day_of_year = date(year, month, day).timetuple().tm_yday
    iyd = int(year) * 1000 + int(day_of_year)
    sec = float(hour) * 3600.0 + float(minute) * 60.0 + float(second)

    iterator = ((ilat, ilon) for ilat in lats for ilon in lons)
    total = len(lats) * len(lons)
    if tqdm is not None:
        iterator = tqdm(iterator, total=total, desc="HWM grid")

    results: List[Dict[str, Any]] = []
    for lat, lon in iterator:
        output = hwm_model.calculate(
            iyd=iyd,
            sec=sec,
            alt_km=alt_km_arr,
            glat_deg=float(lat),
            glon_deg=float(lon),
            stl_hours=stl_hours,
            f107a=f107a,
            f107=f107,
            ap2=(0.0, 20.0) if ap2 is None else ap2,
        )
        wm = output["meridional_wind_ms"]
        wz = output["zonal_wind_ms"]
        results.append(
            {
                "lat": float(lat),
                "lon": float(lon),
                "alt_km": alt_km_arr if out_numpy else list(alt_km_arr),
                "wm": wm if out_numpy else list(wm),
                "wz": wz if out_numpy else list(wz),
            }
        )

    return results


if __name__ == "__main__":
    results = compute_region_hwm(
        None,
        30.0,
        31.0,
        114.0,
        115.0,
        3,
        4,
        [100, 200, 300],
        2025,
        10,
        17,
        hour=12,
        stl_hours=12.0,
        out_numpy=False,
    )

    print(f"Computed {len(results)} grid points. Example first point:")
    if results:
        first = results[0]
        print(first["lat"], first["lon"])
        print("alt_km:", first["alt_km"])
        print("wm:", first["wm"])
        print("wz:", first["wz"])
