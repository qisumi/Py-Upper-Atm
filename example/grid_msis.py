from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import sys

import numpy as np

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

ROOT = Path(__file__).resolve().parents[1]
MODEL_DATA = ROOT / "data"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import MSIS2
from utils.time import doy, seconds_of_day


def compute_region_msis(
    msis: Optional[MSIS2],
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
        msis = MSIS2(precision="single", data_dir=MODEL_DATA, auto_download=False)

    lats = np.linspace(float(lat0), float(lat1), max(1, int(lat_steps)))
    lons = np.linspace(float(lon0), float(lon1), max(1, int(lon_steps)))
    alt_km_arr = np.asarray(list(alt_km_list), dtype=float)
    day_val = doy(year, month, day)
    utsec = seconds_of_day(hour, minute, second)

    iterator = ((ilat, ilon) for ilat in lats for ilon in lons)
    total = len(lats) * len(lons)
    if tqdm is not None:
        iterator = tqdm(iterator, total=total, desc="MSIS grid")

    results: List[Dict[str, Any]] = []
    for lat, lon in iterator:
        output = msis.calculate(
            day=day_val,
            utsec=utsec,
            alt_km=alt_km_arr,
            lat_deg=float(lat),
            lon_deg=float(lon),
            f107a=f107a,
            f107=f107,
            ap7=ap7,
        )
        results.append(
            {
                "lat": float(lat),
                "lon": float(lon),
                "alt_km": output["alt_km"] if out_numpy else list(output["alt_km"]),
                "T_local_K": (
                    output["T_local_K"] if out_numpy else list(output["T_local_K"])
                ),
                "densities": (
                    output["densities"]
                    if out_numpy
                    else [list(row) for row in output["densities"]]
                ),
            }
        )

    return results


if __name__ == "__main__":
    model = MSIS2(precision="single", data_dir=MODEL_DATA, auto_download=False)
    results = compute_region_msis(
        model,
        39.5,
        40.3,
        116.0,
        117.0,
        4,
        5,
        [100, 200, 300],
        2020,
        7,
        18,
        hour=12,
        out_numpy=False,
    )

    print(f"Computed {len(results)} grid points. Example first point:")
    if results:
        first = results[0]
        print(first["lat"], first["lon"])
        print("alt_km:", first["alt_km"])
        print("T_local_K:", first["T_local_K"])
        print("densities shape:", np.asarray(first["densities"]).shape)
