# SOFIP — 短轨道通量积分程序

## 概述

SOFIP 使用 AP-8 / AE-8 辐射带模型计算沿航天器轨迹的任务平均捕获辐射通量。由 Stassinopoulos 等人在 NASA/GSFC 开发，该程序在轨道每个点上积分通量贡献，生成能量依赖的平均积分、微分和差分积分谱。

该程序还使用 SOLPRO 模型为地磁屏蔽较弱（L >= 5）的轨迹段估算太阳质子注量，并按暴露因子加权。

SOFIP 支持四种辐射带地图类型：

- **AP8MAX** — 太阳极大期捕获质子模型
- **AP8MIN** — 太阳极小期捕获质子模型
- **AE8MAX** — 太阳极大期捕获电子模型
- **AE8MIN** — 太阳极小期捕获电子模型

## 目录结构

```text
src/model/pysofip/
├── sofip_legacy.for      # 原始 Fortran 77 源码（TRARA1, TRARA2, DSPCTR, SOFIP_SOLPRO）
├── sofip_cshim.F90       # Fortran 90 C ABI 垫片（数据加载、轨道积分）
├── CMakeLists.txt         # 构建配置
├── __init__.py            # Python 封装
├── README.md              # 英文文档
└── README_zh.md           # 本文件
```

## Fortran 接口

垫片暴露三个 C 可调用子程序：

| 子程序 | 说明 |
|--------|------|
| `sofip_load_data(ihead, nmap, map)` | 加载辐射带地图数据（与 RADBELT 相同格式） |
| `sofip_integrate(...)` | 主轨道平均通量积分 |
| `sofip_is_loaded(flag)` | 检查地图数据是否已加载 |

积分例程调用 `sofip_legacy.for` 中的遗留子程序：

- **TRARA1** — 从辐射带地图中对 30 个能级进行逐点通量查询
- **DSPCTR** — 从对数积分通量计算微分谱
- **SOFIP_SOLPRO** — 太阳质子注量计算（基于任务时长和置信水平）

## 数据文件

模型复用 RADBELT ASCII 数据文件（`ap8max.asc`、`ap8min.asc`、`ae8max.asc`、`ae8min.asc`），位于 `radbeltdata/` 目录下。构造时通过 `ensure_model_data("radbelt", ...)` 自动解析数据路径。

## 构造函数参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_type` | `str` | （必填） | 辐射带模型：`"AP8MAX"`、`"AP8MIN"`、`"AE8MAX"`、`"AE8MIN"` |
| `dll_path` | `str/Path` | `None` | 自定义 DLL/SO 路径 |
| `data_dir` | `str/Path` | `None` | 自定义数据目录 |
| `auto_download` | `bool` | `True` | 是否自动下载缺失的数据文件 |

## `calculate(...)` 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `times` | `array` | 轨迹时间数组（小时） |
| `b_field` | `array` | 沿轨迹的磁场强度（高斯） |
| `l_shell` | `array` | McIlwain 磁壳参数 L（地球半径） |
| `duration_months` | `float` | 任务持续时间（月），用于太阳质子计算，默认 12 |
| `confidence_pct` | `int` | 置信水平（%），用于太阳质子计算（80-99），默认 90 |

三个轨迹数组（`times`、`b_field`、`l_shell`）必须具有相同长度。

## 返回字典

| 键 | 形状 | 说明 |
|----|------|------|
| `energy_levels` | (30,) | 能量阈值 (MeV) |
| `integral_flux` | (30,) | 轨道平均积分通量 (#/cm^2/s) |
| `differential_flux` | (30,) | 微分通量 (#/cm^2/s/keV) |
| `difference_flux` | (30,) | 差分积分通量 (#/cm^2/s/DE) |
| `solar_proton_energy` | (20,) | 太阳质子能量等级 (MeV) |
| `solar_proton_fluence` | (20,) | 太阳质子注量 (#/cm^2)，按暴露因子加权 |
| `n_al_events` | 标量 | 异常大 (AL) 太阳质子事件数 |
| `exposure_factor` | 标量 | 地磁屏蔽较弱时段的轨道占比 |
| `lzone_counts` | (4,) | L 壳区间点计数：[0..1.1), [1.1..2.8), [2.8..11), [11+ 或负值] |
| `total_time_hours` | 标量 | 总轨迹时间（小时） |
| `time_step_minutes` | 标量 | 轨迹点间时间步长（分钟） |

### 能量等级

**质子模型（AP8MAX/AP8MIN）：** 2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 100, 125, 150, 175, 200, 250, 300, 350, 400, 500 MeV

**电子模型（AE8MAX/AE8MIN）：** 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.5, 6.0, 6.5, 7.0 MeV

**太阳质子能量：** 10, 20, 30, ..., 200 MeV（20 个等级）

## 使用示例

```python
from model import SOFIP
import numpy as np

# 创建太阳极大期质子模型
model = SOFIP(model_type="AP8MAX")

# 定义简单圆轨道轨迹
n_points = 100
times = np.linspace(0, 1.5, n_points)  # 1.5 小时
l_shell = np.full(n_points, 4.0)       # L = 4.0 地球半径
b_field = np.full(n_points, 0.005)     # 0.005 高斯

result = model.calculate(
    times=times,
    b_field=b_field,
    l_shell=l_shell,
    duration_months=12.0,
    confidence_pct=90,
)

print("能量等级 (MeV):", result["energy_levels"])
print("积分通量 (#/cm2/s):", result["integral_flux"])
print("太阳质子注量 (#/cm2):", result["solar_proton_fluence"])
print("暴露因子:", result["exposure_factor"])
print("L 壳区间计数:", result["lzone_counts"])
print("总时间（小时）:", result["total_time_hours"])
```

## 参考文献

- Stassinopoulos, E. G., Mead, G. D., Tykka, A. J., & Armstrong, T. W. (1977). *SOFIP: Short Orbital Flux Integration Program*. NASA/GSFC.
- Sawyer, D. M. & Vette, J. I. (1976). *AP-8 Trapped Proton Environment for Solar Maximum and Solar Minimum*. NSSDC/WDC-A-R&S 76-06.
- Vette, J. I. (1991). *The AE-8 Trapped Electron Model Environment*. NSSDC/WDC-A-R&S 91-24.
- King, J. H. (1974). *Solar Proton Fluences for 1977-1983 Space Missions*. J. Spacecraft Rockets, 11(6), 401-408.
