"""
Smoke test for HWM93 Python wrapper.

确保以下条件成立：
1. DLL 与 __init__.py 同级；
2. hwm93_eval 与 hwm93_eval_many 返回合理输出。
"""

import model.pyhwm93 as pyhwm93
import numpy as np
import sys
from pathlib import Path

# 导入包（确保可以正确导入）
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_single_point():
    """测试单点计算功能"""
    wm, wz = pyhwm93.hwm93_eval(
        iyd=2023001,      # YYYYDDD
        sec=0.0,          # UTC 秒
        alt_km=100.0,     # 高度（公里）
        glat_deg=40.0,    # 地理纬度（度）
        glon_deg=116.0,   # 地理经度（度）
        stl_hours=0.0,    # 地方视太阳时（小时）
        f107a=150.0,      # 3个月平均F10.7太阳辐射通量
        f107=150.0,       # 前一天F10.7太阳辐射通量
        ap2=(4.0, 4.0),   # 地磁指数（HWM93低层大气推荐值）
    )
    print(f"[HWM93 单点] 经向风={wm:.3f} m/s, 纬向风={wz:.3f} m/s")
    assert np.isfinite(wm) and np.isfinite(wz), "结果包含 NaN 或 Inf"
    assert abs(wm) < 1000 and abs(wz) < 1000, "风速数值异常"

def test_different_altitudes():
    """测试不同高度的计算结果"""
    altitudes = [50.0, 100.0, 150.0, 200.0, 250.0]
    print("\n[HWM93 不同高度测试]")
    
    for alt in altitudes:
        wm, wz = pyhwm93.hwm93_eval(
            iyd=2023001, sec=43200.0, alt_km=alt,
            glat_deg=40.0, glon_deg=116.0, stl_hours=12.0,
            f107a=150.0, f107=150.0, ap2=(4.0, 4.0)
        )
        print(f"高度 {alt} km: 经向风={wm:.3f} m/s, 纬向风={wz:.3f} m/s")
        assert np.isfinite(wm) and np.isfinite(wz), f"高度 {alt} km 结果异常"

def test_broadcast_eval():
    """测试批量计算功能"""
    if np is None:
        print("\n⚠️  numpy 未安装，跳过批量计算测试")
        return
    
    print("\n[HWM93 批量计算测试]")
    
    # 创建网格数据
    lat = np.linspace(-60, 60, 5, dtype=np.float32)
    lon = np.linspace(0, 360, 9, dtype=np.float32)
    LAT, LON = np.meshgrid(lat, lon, indexing="ij")

    wm, wz = pyhwm93.hwm93_eval_many(
        iyd=2023001,
        sec=43200.0,
        alt_km=100.0,
        glat_deg=LAT,
        glon_deg=LON,
        stl_hours=12.0,
        f107a=150.0,
        f107=150.0,
        ap2=(4.0, 4.0),
    )
    
    print(f"批量计算结果形状: wm={wm.shape}, wz={wz.shape}")
    assert wm.shape == LAT.shape, "结果形状不匹配"
    assert wz.shape == LAT.shape, "结果形状不匹配"
    assert np.all(np.isfinite(wm)) and np.all(np.isfinite(wz)), "批量结果包含 NaN 或 Inf"
    
    # 打印部分结果示例
    print("部分结果示例:")
    for i in range(min(3, wm.shape[0])):
        for j in range(min(3, wm.shape[1])):
            print(f"  lat={lat[i]:.1f}, lon={lon[j]:.1f}: ({wm[i,j]:.2f}, {wz[i,j]:.2f})")

if __name__ == "__main__":
    print("Running HWM93 wrapper smoke test...")
    try:
        test_single_point()
        test_different_altitudes()
        test_broadcast_eval()
        print("\n✅ All HWM93 tests passed.")
    except Exception as e:
        print(f"\n❌ HWM93 test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
