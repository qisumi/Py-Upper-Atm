#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import MSIS00


def test_single_point(model: MSIS00) -> None:
    print("\n=== MSIS00 单点计算 ===")
    result = model.calculate(
        iyd=2023001,
        sec=12.0 * 3600,
        alt_km=200.0,
        lat_deg=40.0,
        lon_deg=-75.0,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
        ap7=np.array([4.0] * 7, dtype=np.float32),
    )

    print(f"局部温度: {result['T_local_K']:.1f} K")
    print(f"外温度: {result['T_exo_K']:.1f} K")
    print(f"He密度: {result['densities'][0]:.2e}")
    print(f"O密度: {result['densities'][1]:.2e}")
    assert result["densities"].shape == (9,)
    assert result["T_local_K"] > 0


def test_batch(model: MSIS00) -> None:
    print("\n=== MSIS00 批量计算 ===")
    altitudes = np.linspace(100.0, 500.0, 5)
    result = model.calculate(
        iyd=2023001,
        sec=12.0 * 3600,
        alt_km=altitudes,
        lat_deg=40.0,
        lon_deg=-75.0,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
    )

    for alt, temp, oxygen in zip(
        result["alt_km"],
        result["T_local_K"],
        result["densities"][:, 1],
    ):
        print(f"{alt:6.1f} km: O={oxygen:.2e}, T={temp:.1f} K")

    assert result["densities"].shape == (5, 9)
    assert result["T_local_K"].shape == (5,)


def test_anomalous_o(model: MSIS00) -> None:
    print("\n=== MSIS00 GTD7D ===")
    result = model.calculate(
        iyd=2023001,
        sec=12.0 * 3600,
        alt_km=500.0,
        lat_deg=0.0,
        lon_deg=0.0,
        stl_hours=12.0,
        f107a=200.0,
        f107=200.0,
        ap7=[10.0] * 7,
        use_anomalous_o=True,
    )
    print(f"Total mass density: {result['densities'][8]:.2e}")
    assert result["densities"][8] >= 0


def main() -> None:
    print("MSIS00 Python Interface Test Suite")
    print("=" * 50)
    model = MSIS00()
    test_single_point(model)
    test_batch(model)
    test_anomalous_o(model)
    print("\nAll MSIS00 tests passed.")


if __name__ == "__main__":
    main()
