#!/usr/bin/env python
"""
GSFC geomagnetic field model smoke tests.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
MODEL_DATA = ROOT / "data"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import GSFC


def test_gsfc87_single():
    """Test GSFC-87 single-point calculation at Beijing."""
    model = GSFC(gsfc_version=87, data_dir=MODEL_DATA, auto_download=False)
    result = model.calculate(year=1985.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)

    print("\n=== GSFC-87 Single Point (Beijing 39.9N 116.4E, 0km, 1985.0) ===")
    for key in sorted(result):
        val = result[key]
        if isinstance(val, float):
            print(f"  {key:20s}: {val:12.4f}")
        else:
            print(f"  {key:20s}: {val}")


def test_gsfc83_single():
    """Test GSFC-83 single-point calculation at the equator."""
    model = GSFC(gsfc_version=83, data_dir=MODEL_DATA, auto_download=False)
    result = model.calculate(year=1980.0, lat_deg=0.0, lon_deg=0.0, alt_km=0.0)

    print("\n=== GSFC-83 Single Point (Equator 0N 0E, 0km, 1980.0) ===")
    for key in sorted(result):
        val = result[key]
        if isinstance(val, float):
            print(f"  {key:20s}: {val:12.4f}")
        else:
            print(f"  {key:20s}: {val}")


def test_gsfc80_single():
    """Test GSFC-80 single-point calculation."""
    model = GSFC(gsfc_version=80, data_dir=MODEL_DATA, auto_download=False)
    result = model.calculate(year=1980.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)

    print("\n=== GSFC-80 Single Point (Beijing 39.9N 116.4E, 0km, 1980.0) ===")
    for key in sorted(result):
        val = result[key]
        if isinstance(val, float):
            print(f"  {key:20s}: {val:12.4f}")
        else:
            print(f"  {key:20s}: {val}")


def test_batch():
    """Test GSFC-87 batch calculation."""
    model = GSFC(gsfc_version=87, data_dir=MODEL_DATA, auto_download=False)

    result = model.calculate(
        year=1985.0,
        lat_deg=[30.0, 40.0, 50.0],
        lon_deg=[116.0, 116.0, 116.0],
        alt_km=[0.0, 100.0, 200.0],
    )

    print("\n=== GSFC-87 Batch (3 points) ===")
    for key in sorted(result):
        val = result[key]
        print(f"  {key:20s}: {val}")


if __name__ == "__main__":
    test_gsfc87_single()
    test_gsfc83_single()
    test_gsfc80_single()
    test_batch()
    print("\nAll smoke tests passed.")
