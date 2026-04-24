#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick run example for the four single-model interfaces.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
MODEL_DATA = ROOT / "data"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import HWM14, HWM93, MSIS00, MSIS2
from utils.time import doy, seconds_of_day


def run_msis2_example() -> None:
    print("\n=== NRLMSIS-2.0 temperature and density example ===")
    try:
        model = MSIS2(precision="single", data_dir=MODEL_DATA, auto_download=False)
        result = model.calculate(
            day=doy(2023, 1, 1),
            utsec=seconds_of_day(12, 0, 0),
            alt_km=100.0,
            lat_deg=35.0,
            lon_deg=116.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"Local temperature: {result['T_local_K']:.2f} K")
        print(f"Exospheric temperature: {result['T_exo_K']:.2f} K")
        print(f"N2 density: {result['densities'][0]:.2e}")

        batch = model.calculate(
            day=doy(2023, 1, 1),
            utsec=seconds_of_day(12, 0, 0),
            alt_km=[80.0, 100.0, 120.0, 150.0],
            lat_deg=35.0,
            lon_deg=116.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"Batch output shape: densities={batch['densities'].shape}")
    except Exception as exc:
        print(f"NRLMSIS-2.0 failed: {exc}")


def run_msis00_example() -> None:
    print("\n=== NRLMSISE-00 temperature and density example ===")
    try:
        model = MSIS00()
        result = model.calculate(
            iyd=2023001,
            sec=43200.0,
            alt_km=100.0,
            lat_deg=35.0,
            lon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"Local temperature: {result['T_local_K']:.2f} K")
        print(f"Exospheric temperature: {result['T_exo_K']:.2f} K")
        print(f"He density: {result['densities'][0]:.2e}")

        batch = model.calculate(
            iyd=2023001,
            sec=43200.0,
            alt_km=np.array([100.0, 150.0, 200.0]),
            lat_deg=35.0,
            lon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"Batch output shape: densities={batch['densities'].shape}")
    except Exception as exc:
        print(f"NRLMSISE-00 failed: {exc}")


def run_hwm14_example() -> None:
    print("\n=== HWM14 wind field example ===")
    try:
        model = HWM14(data_dir=MODEL_DATA, auto_download=False)
        result = model.calculate(
            iyd=2023001,
            sec=43200.0,
            alt_km=100.0,
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"Meridional wind: {result['meridional_wind_ms']:.2f} m/s")
        print(f"Zonal wind: {result['zonal_wind_ms']:.2f} m/s")

        batch = model.calculate(
            iyd=2023001,
            sec=43200.0,
            alt_km=[80.0, 100.0, 120.0, 150.0],
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"Batch output shape: meridional={batch['meridional_wind_ms'].shape}")
    except Exception as exc:
        print(f"HWM14 failed: {exc}")


def run_hwm93_example() -> None:
    print("\n=== HWM93 wind field example ===")
    try:
        model = HWM93()
        result = model.calculate(
            iyd=2023001,
            sec=43200.0,
            alt_km=100.0,
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"Meridional wind: {result['meridional_wind_ms']:.2f} m/s")
        print(f"Zonal wind: {result['zonal_wind_ms']:.2f} m/s")

        batch = model.calculate(
            iyd=2023001,
            sec=43200.0,
            alt_km=np.array([100.0, 150.0, 200.0]),
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"Batch output shape: meridional={batch['meridional_wind_ms'].shape}")
    except Exception as exc:
        print(f"HWM93 failed: {exc}")


def main() -> None:
    print("UpperAtmPy single-model interface examples")
    print("==========================================")
    run_msis2_example()
    run_msis00_example()
    run_hwm14_example()
    run_hwm93_example()
    print("\nExamples completed.")


if __name__ == "__main__":
    main()
