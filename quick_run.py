#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速运行示例：分别展示四个模型的单类接口。
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import HWM14, HWM93, MSIS00, MSIS2
from utils.time import doy, seconds_of_day


def run_msis2_example() -> None:
    print("\n=== NRLMSIS-2.0 温度密度示例 ===")
    try:
        model = MSIS2(precision="single")
        result = model.calculate(
            day=doy(2023, 1, 1),
            utsec=seconds_of_day(12, 0, 0),
            alt_km=100.0,
            lat_deg=35.0,
            lon_deg=116.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"局部温度: {result['T_local_K']:.2f} K")
        print(f"外温度: {result['T_exo_K']:.2f} K")
        print(f"N2密度: {result['densities'][0]:.2e}")

        batch = model.calculate(
            day=doy(2023, 1, 1),
            utsec=seconds_of_day(12, 0, 0),
            alt_km=[80.0, 100.0, 120.0, 150.0],
            lat_deg=35.0,
            lon_deg=116.0,
            f107a=100.0,
            f107=100.0,
        )
        print(f"批量输出形状: densities={batch['densities'].shape}")
    except Exception as exc:
        print(f"NRLMSIS-2.0 运行失败: {exc}")


def run_msis00_example() -> None:
    print("\n=== NRLMSISE-00 温度密度示例 ===")
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
        print(f"局部温度: {result['T_local_K']:.2f} K")
        print(f"外温度: {result['T_exo_K']:.2f} K")
        print(f"He密度: {result['densities'][0]:.2e}")

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
        print(f"批量输出形状: densities={batch['densities'].shape}")
    except Exception as exc:
        print(f"NRLMSISE-00 运行失败: {exc}")


def run_hwm14_example() -> None:
    print("\n=== HWM14 风场示例 ===")
    try:
        model = HWM14()
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
        print(f"经向风: {result['meridional_wind_ms']:.2f} m/s")
        print(f"纬向风: {result['zonal_wind_ms']:.2f} m/s")

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
        print(f"批量输出形状: meridional={batch['meridional_wind_ms'].shape}")
    except Exception as exc:
        print(f"HWM14 运行失败: {exc}")


def run_hwm93_example() -> None:
    print("\n=== HWM93 风场示例 ===")
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
        print(f"经向风: {result['meridional_wind_ms']:.2f} m/s")
        print(f"纬向风: {result['zonal_wind_ms']:.2f} m/s")

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
        print(f"批量输出形状: meridional={batch['meridional_wind_ms'].shape}")
    except Exception as exc:
        print(f"HWM93 运行失败: {exc}")


def main() -> None:
    print("UpperAtmPy 单模型单接口示例")
    print("===========================")
    run_msis2_example()
    run_msis00_example()
    run_hwm14_example()
    run_hwm93_example()
    print("\n示例运行完成。")


if __name__ == "__main__":
    main()
