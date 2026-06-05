"""
Smoke test for SOFIP (Short Orbital Flux Integration Program).

Generates a simple circular orbit trajectory and computes orbit-averaged
trapped radiation fluxes using the AP-8 / AE-8 models.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import SOFIP

DATA_DIR = ROOT / "data"


def make_circular_orbit(
    altitude_km: float = 500.0,
    inclination_deg: float = 51.6,
    n_points: int = 200,
    n_orbits: float = 5.0,
):
    """生成一个简单的圆轨道轨迹数据（时间、L、B）。

    使用偶极磁场模型近似计算 B 和 L。
    周期由开普勒第三定律估算。
    """
    R_E = 6371.0  # 地球半径 (km)
    r = R_E + altitude_km  # 轨道半径 (km)
    L = r / R_E  # L 声明值 (圆轨道，赤道)

    # 开普勒第三定律: T = 2π * sqrt(r³/μ)
    mu = 398600.4418  # km³/s²
    period_s = 2 * np.pi * np.sqrt(r**3 / mu)
    period_h = period_s / 3600.0

    total_time = n_orbits * period_h
    times = np.linspace(0, total_time, n_points, dtype=np.float32)

    # 纬度随轨道周期变化
    lat = inclination_deg * np.sin(2 * np.pi * times / period_h)

    # L 值：圆轨道近似为 L = r/R_E (赤道)，
    # 偏离赤道时略有变化，但简化为常数
    l_shell = np.full(n_points, L, dtype=np.float32)

    # B 场：偶极近似 B = B0/L³ * sqrt(1 + 3*sin²(λ))
    # B0 = 0.311653 gauss (赤道表面)
    B0 = 0.311653
    lat_rad = np.radians(lat)
    b_field = (B0 / L**3) * np.sqrt(1 + 3 * np.sin(lat_rad)**2)
    b_field = b_field.astype(np.float32)

    return times, b_field, l_shell, period_h


def test_proton_orbit():
    """测试 AP8MAX 质子模型沿圆轨道的积分通量。"""
    print("=== AP8MAX (protons, solar maximum) — 500 km circular orbit ===")
    model = SOFIP("AP8MAX", data_dir=DATA_DIR, auto_download=False)

    times, b_field, l_shell, period = make_circular_orbit(
        altitude_km=500.0, inclination_deg=51.6, n_points=200, n_orbits=5.0,
    )

    result = model.calculate(
        times=times,
        b_field=b_field,
        l_shell=l_shell,
        duration_months=12.0,
        confidence_pct=90,
    )

    energies = result["energy_levels"]
    flux = result["integral_flux"]

    print(f"  Orbit period: {period:.3f} hours")
    print(f"  Total time: {result['total_time_hours']:.2f} hours")
    print(f"  Time step: {result['time_step_minutes']:.2f} minutes")
    print(f"  L-zone counts: {result['lzone_counts']}")
    print(f"  Solar proton AL events: {result['n_al_events']}")
    print(f"  Exposure factor: {result['exposure_factor']:.4f}")
    print()
    print("  Energy (MeV)  Integral Flux (#/cm²/s)")
    print("  " + "-" * 42)
    for e, f in zip(energies, flux):
        if f > 0:
            print(f"  {e:8.1f}      {f:12.4e}")

    # Basic sanity checks
    assert result["total_time_hours"] > 0
    assert result["energy_levels"].shape == (30,)
    assert result["integral_flux"].shape == (30,)
    assert result["differential_flux"].shape == (30,)
    assert result["solar_proton_energy"].shape == (20,)
    assert result["solar_proton_fluence"].shape == (20,)
    print("\n  ✓ All assertions passed.")


def test_electron_orbit():
    """测试 AE8MIN 电子模型沿高轨圆轨道的积分通量。"""
    print("\n=== AE8MIN (electrons, solar minimum) — 2000 km circular orbit ===")
    model = SOFIP("AE8MIN", data_dir=DATA_DIR, auto_download=False)

    times, b_field, l_shell, period = make_circular_orbit(
        altitude_km=2000.0, inclination_deg=89.0, n_points=200, n_orbits=3.0,
    )

    result = model.calculate(
        times=times,
        b_field=b_field,
        l_shell=l_shell,
        duration_months=12.0,
        confidence_pct=90,
    )

    energies = result["energy_levels"]
    flux = result["integral_flux"]

    print(f"  Orbit period: {period:.3f} hours")
    print(f"  Total time: {result['total_time_hours']:.2f} hours")
    print(f"  L-zone counts: {result['lzone_counts']}")
    print()
    print("  Energy (MeV)  Integral Flux (#/cm²/s)")
    print("  " + "-" * 42)
    for e, f in zip(energies, flux):
        if f > 0:
            print(f"  {e:8.3f}      {f:12.4e}")

    assert result["total_time_hours"] > 0
    assert result["energy_levels"].shape == (30,)
    print("\n  ✓ All assertions passed.")


if __name__ == "__main__":
    print("Running SOFIP smoke test...\n")
    test_proton_orbit()
    test_electron_orbit()
    print("\nAll SOFIP tests passed.")
