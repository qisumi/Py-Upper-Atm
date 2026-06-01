#!/usr/bin/env python
"""Chiu 电离层电子密度模型冒烟测试。"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from model import Chiu


def test_single_point():
    """单点计算测试。"""
    model = Chiu()
    result = model.calculate(
        alt_km=300.0,
        sunspot_number=100.0,
        local_time_rad=math.pi,           # 正午
        month_from_dec15=6.0,              # 约六月
        geo_lat_rad=math.radians(35.0),
        geo_mag_lat_rad=math.radians(25.0),
        geo_mag_lon_rad=math.radians(120.0),
        dip_angle_rad=math.radians(45.0),
    )
    print("=== 单点计算 ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
    assert result["Ne_total_cm3"] > 0, "电子密度应为正值"
    assert result["Ne_F2_cm3"] > result["Ne_E_cm3"], "F2 层密度应大于 E 层"
    print()


def test_altitude_profile():
    """高度剖面测试。"""
    model = Chiu()
    altitudes = [100, 150, 200, 250, 300, 350, 400, 450, 500]
    result = model.calculate(
        alt_km=altitudes,
        sunspot_number=100.0,
        local_time_rad=math.pi,
        month_from_dec15=6.0,
        geo_lat_rad=math.radians(35.0),
        geo_mag_lat_rad=math.radians(25.0),
        geo_mag_lon_rad=math.radians(120.0),
        dip_angle_rad=math.radians(45.0),
    )
    print("=== 高度剖面 ===")
    print(f"{'Alt(km)':>8} {'Ne_total':>12} {'Ne_E':>12} {'Ne_F1':>12} {'Ne_F2':>12}")
    for i, alt in enumerate(altitudes):
        print(
            f"{alt:>8.0f} "
            f"{result['Ne_total_cm3'][i]:>12.1f} "
            f"{result['Ne_E_cm3'][i]:>12.1f} "
            f"{result['Ne_F1_cm3'][i]:>12.1f} "
            f"{result['Ne_F2_cm3'][i]:>12.1f}"
        )
    assert result["Ne_total_cm3"].shape == (9,)
    print()


def test_solar_activity():
    """太阳活动变化测试。"""
    model = Chiu()
    rz_values = [10, 50, 100, 150, 200]
    result = model.calculate(
        alt_km=300.0,
        sunspot_number=rz_values,
        local_time_rad=math.pi,
        month_from_dec15=6.0,
        geo_lat_rad=math.radians(35.0),
        geo_mag_lat_rad=math.radians(25.0),
        geo_mag_lon_rad=math.radians(120.0),
        dip_angle_rad=math.radians(45.0),
    )
    print("=== 太阳活动变化 ===")
    for i, rz in enumerate(rz_values):
        print(f"  Rz={rz:>3d}: Ne_total={result['Ne_total_cm3'][i]:.1f} cm^-3")
    # Electron density changes with solar activity; low-to-moderate Rz rises here.
    assert result["Ne_total_cm3"][-1] > result["Ne_total_cm3"][0]
    print()


def test_peak_density():
    """峰值密度模式（alt_km=0）。"""
    model = Chiu()
    result = model.calculate(
        alt_km=0.0,
        sunspot_number=100.0,
        local_time_rad=math.pi,
        month_from_dec15=6.0,
        geo_lat_rad=math.radians(35.0),
        geo_mag_lat_rad=math.radians(25.0),
        geo_mag_lon_rad=math.radians(120.0),
        dip_angle_rad=math.radians(45.0),
    )
    print("=== 峰值密度模式 (Z=0) ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
    # When Z=0, QTOT is 0 but layer peak densities are returned
    assert result["Ne_total_cm3"] == 0.0
    assert result["Ne_E_cm3"] > 0
    assert result["Ne_F1_cm3"] > 0
    assert result["Ne_F2_cm3"] > 0
    print()


if __name__ == "__main__":
    test_single_point()
    test_altitude_profile()
    test_solar_activity()
    test_peak_density()
    print("所有冒烟测试通过！")
