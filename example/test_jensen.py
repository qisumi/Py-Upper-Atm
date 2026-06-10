#!/usr/bin/env python
"""Smoke test for Jensen & Cain (1962) geomagnetic field model."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on the import path when running from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np


def _assert_finite(result):
    for key, value in result.items():
        if isinstance(value, np.ndarray):
            assert np.all(np.isfinite(value)), f"{key} contains non-finite values"
        else:
            assert np.isfinite(value), f"{key} is not finite: {value}"


def test_single_point():
    """Single-point calculation at mid-latitude."""
    from model import JensenCain

    model = JensenCain(data_dir="data", auto_download=False)
    result = model.calculate(
        year=1960.0,
        lat_deg=45.0,
        lon_deg=0.0,
        alt_km=0.0,
    )
    print("=== Single Point (45N, 0E, 0 km, epoch 1960.0) ===")
    for key, val in result.items():
        print(f"  {key}: {val}")
    _assert_finite(result)
    print()


def test_equator():
    """Calculation at the equator."""
    from model import JensenCain

    model = JensenCain(data_dir="data", auto_download=False)
    result = model.calculate(
        year=1960.0,
        lat_deg=0.0,
        lon_deg=0.0,
        alt_km=0.0,
    )
    print("=== Equator (0N, 0E, 0 km, epoch 1960.0) ===")
    for key, val in result.items():
        print(f"  {key}: {val}")
    _assert_finite(result)
    print()


def test_high_latitude():
    """Calculation near the North Pole.

    The legacy FIELDG routine has a singularity at the exact poles.
    """
    from model import JensenCain

    model = JensenCain(data_dir="data", auto_download=False)
    result = model.calculate(
        year=1960.0,
        lat_deg=89.0,
        lon_deg=0.0,
        alt_km=0.0,
    )
    print("=== High Latitude (89N, 0E, 0 km, epoch 1960.0) ===")
    for key, val in result.items():
        print(f"  {key}: {val}")
    _assert_finite(result)
    print()


def test_batch():
    """Batch calculation over a grid of latitudes."""
    from model import JensenCain

    model = JensenCain(data_dir="data", auto_download=False)
    lats = np.linspace(-80, 80, 17)
    result = model.calculate(
        year=1960.0,
        lat_deg=lats,
        lon_deg=0.0,
        alt_km=0.0,
    )
    print("=== Batch (latitudes -80 to 80, step 10) ===")
    print(f"  Shape: {result['F_nT'].shape}")
    print(f"  F_nT range: {result['F_nT'].min():.1f} to {result['F_nT'].max():.1f}")
    _assert_finite(result)
    print()


def test_different_nmx():
    """Test different maximum degree values."""
    from model import JensenCain

    model = JensenCain(data_dir="data", auto_download=False)
    print("=== Different nmx values (45N, 0E, 0 km) ===")
    for nmx in [2, 4, 6]:
        result = model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
            nmx=nmx,
        )
        print(f"  nmx={nmx}: F_nT = {result['F_nT']:.1f}")
        _assert_finite(result)
    print()


def test_altitude_profile():
    """Calculate field at different altitudes."""
    from model import JensenCain

    model = JensenCain(data_dir="data", auto_download=False)
    alts = [0, 100, 200, 500, 1000]
    print("=== Altitude Profile (45N, 0E, epoch 1960.0) ===")
    for alt in alts:
        result = model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=alt,
        )
        print(f"  {alt:5d} km: F_nT = {result['F_nT']:.1f}")
        _assert_finite(result)
    print()


if __name__ == "__main__":
    test_single_point()
    test_equator()
    test_high_latitude()
    test_batch()
    test_different_nmx()
    test_altitude_profile()
    print("All tests passed!")
