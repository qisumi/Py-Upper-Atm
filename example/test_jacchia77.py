from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import Jacchia77


def test_single_point(model: Jacchia77) -> None:
    """测试单点计算。"""
    result = model.calculate(alt_km=100.0, Tinf_K=1000.0)
    print(
        "[Single Point] "
        f"alt={result['alt_km']:.1f} km, "
        f"T={result['T_local_K']:.2f} K, "
        f"N2={result['N2_cm3']:.2e} cm-3, "
        f"O={result['O_cm3']:.2e} cm-3"
    )
    assert np.isfinite(result["T_local_K"])
    assert np.isfinite(result["N2_cm3"])
    assert result["T_local_K"] > 0
    assert result["N2_cm3"] > 0


def test_profile(model: Jacchia77) -> None:
    """测试剖面计算。"""
    alts = np.arange(90, 501, 10)  # 90-500 km, 每10 km
    result = model.calculate(alt_km=alts, Tinf_K=1000.0)
    print(
        "[Profile] "
        f"shape={result['T_local_K'].shape}, "
        f"T range=[{result['T_local_K'].min():.1f}, {result['T_local_K'].max():.1f}] K"
    )
    assert result["T_local_K"].shape == alts.shape
    assert result["N2_cm3"].shape == alts.shape
    assert np.all(result["T_local_K"] > 0)
    assert np.all(result["N2_cm3"] > 0)


def test_different_Tinf(model: Jacchia77) -> None:
    """测试不同外逸层温度。"""
    alt = 200.0
    for Tinf in [600.0, 800.0, 1000.0, 1200.0, 1500.0]:
        result = model.calculate(alt_km=alt, Tinf_K=Tinf)
        print(
            f"  Tinf={Tinf:.0f} K: "
            f"T={result['T_local_K']:.2f} K, "
            f"O={result['O_cm3']:.2e} cm-3"
        )
        assert np.isfinite(result["T_local_K"])
        assert result["T_local_K"] > 0


def test_species_densities(model: Jacchia77) -> None:
    """测试各成分密度。"""
    result = model.calculate(alt_km=200.0, Tinf_K=1000.0)
    print("[Species] at 200 km, Tinf=1000 K:")
    for species in ["N2_cm3", "O2_cm3", "O_cm3", "Ar_cm3", "He_cm3", "H_cm3"]:
        print(f"  {species}: {result[species]:.2e} cm-3")
        assert result[species] >= 0

    # 总密度应等于各成分之和
    total = sum(result[s] for s in ["N2_cm3", "O2_cm3", "O_cm3", "Ar_cm3", "He_cm3", "H_cm3"])
    print(f"  total_density: {result['total_density_cm3']:.2e} cm-3")
    print(f"  sum of species: {total:.2e} cm-3")
    # 允许小的数值误差
    assert abs(result["total_density_cm3"] - total) / result["total_density_cm3"] < 0.01


if __name__ == "__main__":
    print("Running Jacchia 1977 Reference Atmosphere wrapper smoke test...")
    model = Jacchia77()
    test_single_point(model)
    test_profile(model)
    test_different_Tinf(model)
    test_species_densities(model)
    print("All Jacchia 77 tests passed.")
