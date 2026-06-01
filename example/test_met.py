from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import MET


def test_single_point(model: MET) -> None:
    """测试单点计算。"""
    result = model.calculate(
        alt_km=200.0,
        lat_deg=35.0,
        lon_deg=116.0,
        year=23,  # 2023
        month=7,
        day=15,
        hour=12,
        minute=0,
        geo_index_type=2,  # Ap
        f107=100.0,
        f107a=100.0,
        ap=15.0,
    )
    print(
        "[Single Point] "
        f"alt={result['alt_km']:.1f} km, "
        f"T_exo={result['T_exo_K']:.2f} K, "
        f"T_local={result['T_local_K']:.2f} K, "
        f"density={result['total_density_kg_m3']:.2e} kg/m³"
    )
    assert np.isfinite(result["T_exo_K"])
    assert np.isfinite(result["T_local_K"])
    assert result["T_exo_K"] > 0
    assert result["T_local_K"] > 0


def test_profile(model: MET) -> None:
    """测试剖面计算。"""
    alts = np.arange(100, 501, 50)  # 100-500 km, 每50 km
    result = model.calculate(
        alt_km=alts,
        lat_deg=35.0,
        lon_deg=116.0,
        year=23,
        month=7,
        day=15,
        hour=12,
        minute=0,
        geo_index_type=2,
        f107=100.0,
        f107a=100.0,
        ap=15.0,
    )
    print(
        "[Profile] "
        f"shape={result['T_local_K'].shape}, "
        f"T range=[{result['T_local_K'].min():.1f}, {result['T_local_K'].max():.1f}] K"
    )
    assert result["T_local_K"].shape == alts.shape
    assert np.all(result["T_local_K"] > 0)


def test_different_solar_activity(model: MET) -> None:
    """测试不同太阳活动水平。"""
    alt = 300.0
    for f107 in [70.0, 100.0, 150.0, 200.0]:
        result = model.calculate(
            alt_km=alt,
            lat_deg=35.0,
            lon_deg=116.0,
            year=23,
            month=7,
            day=15,
            hour=12,
            minute=0,
            geo_index_type=2,
            f107=f107,
            f107a=f107,
            ap=15.0,
        )
        print(
            f"  f107={f107:.0f}: "
            f"T_exo={result['T_exo_K']:.2f} K, "
            f"density={result['total_density_kg_m3']:.2e} kg/m³"
        )
        assert np.isfinite(result["T_exo_K"])
        assert result["T_exo_K"] > 0


def test_species_densities(model: MET) -> None:
    """测试各成分密度。"""
    result = model.calculate(
        alt_km=200.0,
        lat_deg=35.0,
        lon_deg=116.0,
        year=23,
        month=7,
        day=15,
        hour=12,
        minute=0,
        geo_index_type=2,
        f107=100.0,
        f107a=100.0,
        ap=15.0,
    )
    print("[Species] at 200 km:")
    for species in ["N2_m3", "O2_m3", "O_m3", "Ar_m3", "He_m3", "H_m3"]:
        print(f"  {species}: {result[species]:.2e} /m³")
        assert result[species] >= 0

    print(f"  mean_molecular_weight: {result['mean_molecular_weight']:.3f}")
    print(f"  pressure: {result['pressure_Pa']:.2e} Pa")


if __name__ == "__main__":
    print("Running Marshall Engineering Thermosphere (MET) model smoke test...")
    model = MET()
    test_single_point(model)
    test_profile(model)
    test_different_solar_activity(model)
    test_species_densities(model)
    print("All MET tests passed.")
