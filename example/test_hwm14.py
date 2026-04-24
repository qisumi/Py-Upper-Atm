from __future__ import annotations

from pathlib import Path
import os
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL_DATA = ROOT / "data"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import HWM14


def test_single_point(model: HWM14) -> None:
    result = model.calculate(
        iyd=2025290,
        sec=43200.0,
        alt_km=250.0,
        glat_deg=30.0,
        glon_deg=114.0,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
        ap2=(0.0, 20.0),
    )
    print(
        "[Single Point] "
        f"wm={result['meridional_wind_ms']:.3f} m/s, "
        f"wz={result['zonal_wind_ms']:.3f} m/s"
    )
    assert np.isfinite(result["meridional_wind_ms"])
    assert np.isfinite(result["zonal_wind_ms"])


def test_broadcast_eval(model: HWM14) -> None:
    lat = np.linspace(-60, 60, 5, dtype=np.float32)
    lon = np.linspace(0, 360, 9, dtype=np.float32)
    lat_grid, lon_grid = np.meshgrid(lat, lon, indexing="ij")

    result = model.calculate(
        iyd=2025290,
        sec=43200.0,
        alt_km=250.0,
        glat_deg=lat_grid,
        glon_deg=lon_grid,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
        ap2=(0.0, 20.0),
    )
    print(
        "[Broadcast] "
        f"wm shape={result['meridional_wind_ms'].shape}, "
        f"wz shape={result['zonal_wind_ms'].shape}"
    )
    assert result["meridional_wind_ms"].shape == lat_grid.shape
    assert result["zonal_wind_ms"].shape == lat_grid.shape


if __name__ == "__main__":
    print("Running HWM14 wrapper smoke test...")
    model = HWM14(data_dir=MODEL_DATA, auto_download=False)
    print("HWMPATH =", os.environ.get("HWMPATH"))
    test_single_point(model)
    test_broadcast_eval(model)
    print("All HWM14 tests passed.")
