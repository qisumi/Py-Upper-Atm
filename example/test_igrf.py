#!/usr/bin/env python
"""
IGRF (International Geomagnetic Reference Field) smoke tests.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MODEL_DATA = ROOT / "data"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import IGRF


def test_igrf14_single():
    """Test IGRF-14 single-point calculation at Beijing."""
    model = IGRF(igrf_version=14, data_dir=MODEL_DATA, auto_download=False)
    result = model.calculate(year=2024.5, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)

    print("\n=== IGRF-14 Single Point (Beijing 39.9N 116.4E, 0km, 2024.5) ===")
    for key in sorted(result):
        val = result[key]
        if isinstance(val, float):
            print(f"  {key:20s}: {val:12.4f}")
        else:
            print(f"  {key:20s}: {val}")


def test_igrf13_single():
    """Test IGRF-13 single-point calculation."""
    model = IGRF(igrf_version=13, data_dir=MODEL_DATA, auto_download=False)
    result = model.calculate(year=2020.0, lat_deg=0.0, lon_deg=0.0, alt_km=0.0)

    print("\n=== IGRF-13 Single Point (Equator 0N 0E, 0km, 2020.0) ===")
    for key in sorted(result):
        val = result[key]
        if isinstance(val, float):
            print(f"  {key:20s}: {val:12.4f}")
        else:
            print(f"  {key:20s}: {val}")


def test_batch():
    """Test IGRF-14 batch calculation."""
    model = IGRF(igrf_version=14, data_dir=MODEL_DATA, auto_download=False)

    result = model.calculate(
        year=2024.5,
        lat_deg=[30.0, 40.0, 50.0],
        lon_deg=[116.0, 116.0, 116.0],
        alt_km=[0.0, 100.0, 200.0],
    )

    print("\n=== IGRF-14 Batch (3 points) ===")
    for key in sorted(result):
        val = result[key]
        print(f"  {key:20s}: {val}")


def test_version_compare():
    """Compare IGRF-13 and IGRF-14 at epoch 2020.0."""
    m13 = IGRF(igrf_version=13, data_dir=MODEL_DATA, auto_download=False)
    m14 = IGRF(igrf_version=14, data_dir=MODEL_DATA, auto_download=False)

    r13 = m13.calculate(year=2020.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
    r14 = m14.calculate(year=2020.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)

    print("\n=== IGRF-13 vs IGRF-14 (Beijing, 2020.0, 0km) ===")
    print(f"  IGRF-13 B_abs: {r13['B_abs_nT']:.2f} nT")
    print(f"  IGRF-14 B_abs: {r14['B_abs_nT']:.2f} nT")
    print(f"  Difference:     {abs(r13['B_abs_nT'] - r14['B_abs_nT']):.2f} nT")


if __name__ == "__main__":
    test_igrf14_single()
    test_igrf13_single()
    test_batch()
    test_version_compare()
    print("\nAll smoke tests passed.")
