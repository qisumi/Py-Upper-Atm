#!/usr/bin/env python
"""
CIRA-86 smoke tests.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MODEL_DATA = ROOT / "data"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import CIRA86


def test_height_coordinate(model: CIRA86) -> None:
    result = model.calculate(month=1, lat_deg=0.0, alt_km=100.0)
    print("\n=== CIRA-86 Height Coordinate (Jan, 0N, 100 km) ===")
    for key in sorted(result):
        print(f"  {key:24s}: {result[key]}")
    assert 100.0 < result["T_K"] < 500.0
    assert result["pressure_mb"] > 0.0


def test_pressure_coordinate(model: CIRA86) -> None:
    result = model.calculate(month=1, lat_deg=0.0, pressure_mb=3.10e-4)
    print("\n=== CIRA-86 Pressure Coordinate (Jan, 0N, 3.10e-4 mb) ===")
    for key in sorted(result):
        print(f"  {key:24s}: {result[key]}")
    assert 90000.0 < result["geopotential_height_m"] < 110000.0


def test_batch(model: CIRA86) -> None:
    result = model.calculate(
        month=[1, 4, 7, 10],
        lat_deg=[-40.0, 0.0, 40.0, 80.0],
        alt_km=[20.0, 50.0, 80.0, 110.0],
    )
    print("\n=== CIRA-86 Batch ===")
    print(f"  T_K shape: {result['T_K'].shape}")
    print(f"  pressure_mb: {result['pressure_mb']}")
    assert result["T_K"].shape == (4,)
    assert np.all(np.isfinite(result["T_K"]))


if __name__ == "__main__":
    print("Running CIRA-86 wrapper smoke test...")
    cira = CIRA86(data_dir=MODEL_DATA, auto_download=False)
    test_height_coordinate(cira)
    test_pressure_coordinate(cira)
    test_batch(cira)
    print("\nAll CIRA-86 tests passed.")
