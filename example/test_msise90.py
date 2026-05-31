#!/usr/bin/env python3
"""MSISE-90 模型冒烟测试。"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import MSISE90


def test_single_point(model: MSISE90) -> None:
    print("\n=== MSISE90 单点计算 ===")
    result = model.calculate(
        iyd=1990172,
        sec=29000.0,
        alt_km=400.0,
        lat_deg=60.0,
        lon_deg=-70.0,
        stl_hours=16.0,
        f107a=150.0,
        f107=150.0,
    )

    print(f"外逸层温度: {result['T_exo_K']:.1f} K")
    print(f"局部温度: {result['T_local_K']:.1f} K")
    print(f"He 密度: {result['densities'][0]:.3e} cm-3")
    print(f"O2 密度: {result['densities'][3]:.3e} cm-3")
    print(f"Ar 密度: {result['densities'][4]:.3e} cm-3")
    print(f"H  密度: {result['densities'][6]:.3e} cm-3")
    assert result["densities"].shape == (8,)
    assert result["T_exo_K"] > 0


def test_surface(model: MSISE90) -> None:
    """测试地面高度（0 km）计算。"""
    print("\n=== MSISE90 地面计算 ===")
    result = model.calculate(
        iyd=1990172,
        sec=29000.0,
        alt_km=0.0,
        lat_deg=60.0,
        lon_deg=-70.0,
        stl_hours=16.0,
        f107a=150.0,
        f107=150.0,
    )

    print(f"局部温度: {result['T_local_K']:.1f} K")
    print(f"N2 密度: {result['densities'][2]:.3e} cm-3")
    print(f"O2 密度: {result['densities'][3]:.3e} cm-3")
    assert result["densities"].shape == (8,)
    assert result["T_local_K"] > 0


def test_batch(model: MSISE90) -> None:
    print("\n=== MSISE90 批量计算 ===")
    altitudes = np.linspace(0.0, 500.0, 11)
    result = model.calculate(
        iyd=1990172,
        sec=29000.0,
        alt_km=altitudes,
        lat_deg=60.0,
        lon_deg=-70.0,
        stl_hours=16.0,
        f107a=150.0,
        f107=150.0,
    )

    for alt, temp, he in zip(
        result["alt_km"],
        result["T_local_K"],
        result["densities"][:, 0],
    ):
        print(f"{alt:6.1f} km: He={he:.3e}, T={temp:.1f} K")

    assert result["densities"].shape == (11, 8)
    assert result["T_local_K"].shape == (11,)


def test_with_ap_array(model: MSISE90) -> None:
    print("\n=== MSISE90 7 元素 Ap 数组 ===")
    result = model.calculate(
        iyd=1990172,
        sec=29000.0,
        alt_km=200.0,
        lat_deg=60.0,
        lon_deg=-70.0,
        stl_hours=16.0,
        f107a=150.0,
        f107=150.0,
        ap7=[4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0],
    )

    print(f"外逸层温度: {result['T_exo_K']:.1f} K")
    print(f"局部温度: {result['T_local_K']:.1f} K")
    assert result["densities"].shape == (8,)


def main() -> None:
    print("MSISE-90 Python 接口测试")
    print("=" * 50)
    model = MSISE90()
    test_single_point(model)
    test_surface(model)
    test_batch(model)
    test_with_ap_array(model)
    print("\n所有 MSISE-90 测试通过。")


if __name__ == "__main__":
    main()
