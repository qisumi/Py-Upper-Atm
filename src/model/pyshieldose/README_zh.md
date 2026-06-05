# SHIELDOSE — 铝屏蔽后辐射剂量模型

## 概述

SHIELDOSE 计算空间应用中铝屏蔽层后的辐射吸收剂量。支持四种探测器材料（Al、H₂O、Si、SiO₂）和三种几何构型：

- **平板**：有限铝平板透射面的剂量
- **半无限介质**：半无限铝介质中的剂量
- **球体中心**：铝球体中心的剂量

该模型将用户提供的粒子能谱（太阳质子、捕获质子、电子）与预计算的单能深度-剂量查找表进行积分。

## 目录结构

```text
src/model/pyshieldose/
├── shieldose_cshim.F90    # Fortran 计算核心（样条插值、积分、球体转换）
├── CMakeLists.txt          # 构建配置
├── __init__.py             # Python 封装
├── README.md               # 英文文档
└── README_zh.md            # 本文件
```

## 数据文件

模型需要 `shieldose.dat` 数据文件，包含：
- 质子剂量数据（28 个能量 × 51 个深度点）
- 电子剂量数据（9 个能量 × 41 个深度点 × 2 个表）
- 轫致辐射剂量数据（10 个能量 × 60 个深度点 × 2 个表）

首次使用时通过 `ensure_model_data()` 自动下载。

## 构造函数参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `detector` | `int` | `1` | 探测器材料：1=Al, 2=H₂O, 3=Si, 4=SiO₂ |
| `unit` | `int` | `2` | 深度单位：1=mils, 2=g/cm², 3=mm |
| `data_dir` | `str/Path` | `None` | 自定义数据目录 |
| `auto_download` | `bool` | `True` | 是否自动下载缺失的数据文件 |
| `dll_path` | `str/Path` | `None` | 自定义 DLL 路径 |

## `calculate(...)` 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `depths` | `float/array` | 正值屏蔽深度 |
| `solar_proton_energies` | `array` | 太阳质子能谱能量点 (MeV)，3–101 个 |
| `solar_proton_flux` | `array` | 太阳质子能谱通量 (/Energy/cm²) |
| `trapped_proton_energies` | `array` | 捕获质子能谱能量点 (MeV)，3–101 个 |
| `trapped_proton_flux` | `array` | 捕获质子能谱通量 (/Energy/cm²/Time) |
| `electron_energies` | `array` | 电子能谱能量点 (MeV)，3–101 个 |
| `electron_flux` | `array` | 电子能谱通量 (/Energy/cm²/Time) |
| `eunit` | `float` | 能量单位转换因子（默认 1.0 表示 /MeV） |
| `tinter` | `float` | 任务持续时间（单位时间倍数，默认 1.0） |

## 返回字典

| 键 | 形状 | 说明 |
|----|------|------|
| `depths` | 标量或 (N,) | 输入深度 |
| `detector` | dict | `{"id": int, "name": str}` |
| `unit` | dict | `{"id": int, "name": str}` |
| `dose_slab` | (5,) 或 (N,5) | 平板几何剂量 (rads) |
| `dose_semi` | (5,) 或 (N,5) | 半无限介质剂量 (rads) |
| `dose_sphere` | (5,) 或 (N,5) | 球体中心剂量 (rads) |

每个剂量数组有 5 列：
1. 电子剂量
2. 轫致辐射剂量
3. 电子 + 轫致辐射
4. 捕获质子剂量
5. 太阳质子剂量

## 使用示例

```python
from model import SHIELDOSE
import numpy as np

model = SHIELDOSE(detector=1, unit=2)

result = model.calculate(
    depths=np.array([0.1, 0.5, 1.0, 5.0]),
    electron_energies=[0.1, 1.0, 5.0],
    electron_flux=[1e4, 1e3, 1e2],
    trapped_proton_energies=[0.1, 1.0, 10.0, 100.0],
    trapped_proton_flux=[1e4, 1e3, 1e2, 1e1],
    tinter=86400.0,  # 1 天
)

print(result["dose_slab"])  # [N, 5] 数组，单位 rads
```

## 参考文献

- Seltzer, S. M. (1980). *SHIELDOSE: A Computer Code for Space-Shielding Radiation Dose Calculations*. NBS Technical Note 1116.
- Seltzer, S. M. (1979). *Calculation of Photonuclear Reaction Products and Their Contributions to Dose Behind Shielding*. IEEE Trans. Nuclear Sci. NS-26, 4896.
