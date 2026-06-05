"""SHIELDOSE 模型示例脚本。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
from model import SHIELDOSE


def test_basic():
    """基本功能测试。"""
    m = SHIELDOSE(detector=1, unit=2, data_dir="data")
    print(f"探测器: {m.detector_name}, 单位: {m.unit_name}")

    # 单点计算
    result = m.calculate(depths=1.0)
    print(f"单点计算 (无能谱): {result['dose_slab']}")


def test_electron_spectrum():
    """电子能谱测试。"""
    m = SHIELDOSE(detector=1, unit=2, data_dir="data")

    result = m.calculate(
        depths=np.array([0.1, 0.5, 1.0, 5.0]),
        electron_energies=[0.1, 1.0, 5.0],
        electron_flux=[1e4, 1e3, 1e2],
        tinter=1.0,
    )

    print("\n电子能谱测试:")
    print("深度(g/cm²) | 电子剂量 | 轫致辐射 | 总计")
    print("-" * 50)
    for i in range(len(result["depths"])):
        d = result["depths"][i]
        s = result["dose_slab"][i]
        print(f"{d:10.2f} | {s[0]:10.3e} | {s[1]:10.3e} | {s[2]:10.3e}")


def test_proton_spectrum():
    """质子能谱测试。"""
    m = SHIELDOSE(detector=1, unit=2, data_dir="data")

    result = m.calculate(
        depths=np.array([0.1, 0.5, 1.0, 5.0]),
        trapped_proton_energies=[0.1, 1.0, 10.0, 100.0],
        trapped_proton_flux=[1e4, 1e3, 1e2, 1e1],
        tinter=86400.0,  # 1 天
    )

    print("\n质子能谱测试 (1 天):")
    print("深度(g/cm²) | 捕获质子 | 太阳质子")
    print("-" * 40)
    for i in range(len(result["depths"])):
        d = result["depths"][i]
        s = result["dose_slab"][i]
        print(f"{d:10.2f} | {s[3]:10.3e} | {s[4]:10.3e}")


def test_geometry_comparison():
    """不同几何构型比较。"""
    m = SHIELDOSE(detector=1, unit=2, data_dir="data")

    result = m.calculate(
        depths=np.array([0.5, 1.0, 5.0]),
        electron_energies=[0.1, 1.0, 5.0],
        electron_flux=[1e4, 1e3, 1e2],
        tinter=1.0,
    )

    print("\n几何构型比较 (电子+轫致辐射):")
    print("深度(g/cm²) | 平板透射 | 半无限介质 | 球体中心")
    print("-" * 55)
    for i in range(len(result["depths"])):
        d = result["depths"][i]
        slab = result["dose_slab"][i][2]
        semi = result["dose_semi"][i][2]
        sphere = result["dose_sphere"][i][2]
        print(f"{d:10.2f} | {slab:10.3e} | {semi:10.3e} | {sphere:10.3e}")


if __name__ == "__main__":
    test_basic()
    test_electron_spectrum()
    test_proton_spectrum()
    test_geometry_comparison()
