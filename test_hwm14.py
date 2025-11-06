"""
Smoke test for HWM14 Python wrapper.

确保以下条件成立：
1. DLL 与 __init__.py 同级；
2. ./data 包含 HWM 所需的 Meta 数据；
3. HWMPATH 自动设置为 ./data；
4. hwm14_eval 与 hwm14_eval_many 返回合理输出。
"""

import model.pyhwm14 as pyhwm14
import os
import numpy as np
import sys
from pathlib import Path

# 导入包（自动设置 HWMPATH）
sys.path.insert(0, str(Path(__file__).resolve().parent))


def test_single_point():
    wm, wz = pyhwm14.hwm14_eval(
        iyd=2025290,      # YYYYDDD
        sec=43200.0,      # 正午 UTC 秒
        alt_km=250.0,
        glat_deg=30.0,
        glon_deg=114.0,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
        ap2=(0.0, 20.0),
    )
    print(f"[Single Point] wm={wm:.3f} m/s, wz={wz:.3f} m/s")
    assert np.isfinite(wm) and np.isfinite(wz), "结果包含 NaN 或 Inf"
    assert abs(wm) < 1000 and abs(wz) < 1000, "风速数值异常"


def test_broadcast_eval():
    lat = np.linspace(-60, 60, 5, dtype=np.float32)
    lon = np.linspace(0, 360, 9, dtype=np.float32)
    LAT, LON = np.meshgrid(lat, lon, indexing="ij")

    wm, wz = pyhwm14.hwm14_eval_many(
        iyd=2025290,
        sec=43200.0,
        alt_km=250.0,
        glat_deg=LAT,
        glon_deg=LON,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
        ap2=(0.0, 20.0),
    )
    print(f"[Broadcast] wm shape={wm.shape}, wz shape={wz.shape}")
    assert wm.shape == LAT.shape
    assert wz.shape == LAT.shape
    assert np.all(np.isfinite(wm)) and np.all(np.isfinite(wz))


if __name__ == "__main__":
    print("Running HWM14 wrapper smoke test...")
    print("HWMPATH =", os.environ.get("HWMPATH"))
    test_single_point()
    test_broadcast_eval()
    print("✅ All tests passed.")
