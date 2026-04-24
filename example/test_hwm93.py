from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import HWM93


def test_single_point(model: HWM93) -> None:
    result = model.calculate(
        iyd=2023001,
        sec=0.0,
        alt_km=100.0,
        glat_deg=40.0,
        glon_deg=116.0,
        stl_hours=0.0,
        f107a=150.0,
        f107=150.0,
        ap2=(4.0, 4.0),
    )
    print(
        "[HWM93 单点] "
        f"经向风={result['meridional_wind_ms']:.3f} m/s, "
        f"纬向风={result['zonal_wind_ms']:.3f} m/s"
    )
    assert np.isfinite(result["meridional_wind_ms"])
    assert np.isfinite(result["zonal_wind_ms"])


def test_different_altitudes(model: HWM93) -> None:
    print("\n[HWM93 不同高度测试]")
    result = model.calculate(
        iyd=2023001,
        sec=43200.0,
        alt_km=[50.0, 100.0, 150.0, 200.0, 250.0],
        glat_deg=40.0,
        glon_deg=116.0,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
        ap2=(4.0, 4.0),
    )
    for alt, wm, wz in zip(
        result["alt_km"],
        result["meridional_wind_ms"],
        result["zonal_wind_ms"],
    ):
        print(f"高度 {alt} km: 经向风={wm:.3f} m/s, 纬向风={wz:.3f} m/s")


def test_broadcast_eval(model: HWM93) -> None:
    print("\n[HWM93 批量计算测试]")
    lat = np.linspace(-60, 60, 5, dtype=np.float32)
    lon = np.linspace(0, 360, 9, dtype=np.float32)
    lat_grid, lon_grid = np.meshgrid(lat, lon, indexing="ij")

    result = model.calculate(
        iyd=2023001,
        sec=43200.0,
        alt_km=100.0,
        glat_deg=lat_grid,
        glon_deg=lon_grid,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
        ap2=(4.0, 4.0),
    )
    print(
        "批量计算结果形状: "
        f"wm={result['meridional_wind_ms'].shape}, "
        f"wz={result['zonal_wind_ms'].shape}"
    )
    assert result["meridional_wind_ms"].shape == lat_grid.shape
    assert result["zonal_wind_ms"].shape == lat_grid.shape


if __name__ == "__main__":
    print("Running HWM93 wrapper smoke test...")
    model = HWM93()
    test_single_point(model)
    test_different_altitudes(model)
    test_broadcast_eval(model)
    print("\nAll HWM93 tests passed.")
