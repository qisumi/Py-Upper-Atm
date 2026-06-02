# SOLPRO — 行星际太阳质子通量模型

## 背景

SOLPRO 计算行星际积分太阳质子通量（1 AU），基于任务持续时间（最长 72 个月）
和用户指定的置信水平。模型由 E. G. Stassinopoulos（NASA/GSFC）开发，
基于 King（1974）和 Stassinopoulos & King（1974）的太阳质子通量模型。

模型输出 10 个能阈值（10–100 MeV）的积分通量，并考虑两类太阳质子事件：

- **OR（普通复发）事件**：正常太阳质子事件，使用第 20 太阳活动周期
  （1964–1972）数据的多项式拟合建模。
- **AL（异常大）事件**：极罕见事件（如 1972 年 8 月事件），其强度比第 20
  周期中任何其他事件大 10 倍以上。模型预测给定任务持续时间和置信水平下的
  AL 事件数。

所有经验系数硬编码在 Fortran 源文件中——**无需外部数据文件**。

## 目录结构

```text
pysolpro/
├── solpro.for              # SOLPRO Fortran IV 源码（子程序 SOLPRO）
├── solpro_cshim.F90        # C ABI 桥接层
├── CMakeLists.txt          # 构建 solpro.dll / libsolpro.so
├── __init__.py             # Python Model 类
├── README.md               # 英文文档
└── README_zh.md            # 本文件（中文文档）
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 编译 DLL 的自定义路径 |

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `duration_months` | float / array | 任务持续时间（月），范围 1–72 |
| `confidence_pct` | int / array | 置信水平（%），范围 80–99。表示计算通量不被超越的概率。 |

两个参数均支持 numpy 广播。

## 输出

`calculate()` 返回字典：

| 字段 | 类型 | 说明 |
|------|------|------|
| `duration_months` | float / ndarray | 输入持续时间（回显） |
| `confidence_pct` | int / ndarray | 输入置信水平（回显） |
| `fluence_cm2` | ndarray | 积分通量（protons/cm²）。标量输入形状 `(10,)`，批量输入形状 `(N, 10)`。列对应能阈 10, 20, 30, …, 100 MeV。 |
| `n_al_events` | int / ndarray | 预测的异常大事件（AL events）数量 |

## 使用示例

### 单点计算

```python
from model import SOLPRO

model = SOLPRO()
result = model.calculate(duration_months=12, confidence_pct=90)

print(f"AL 事件数: {result['n_al_events']}")
print(f"E > 10 MeV 通量: {result['fluence_cm2'][0]:.3e} protons/cm²")
print(f"E > 100 MeV 通量: {result['fluence_cm2'][9]:.3e} protons/cm²")
```

### 批量计算

```python
import numpy as np

model = SOLPRO()
durations = np.array([1, 3, 6, 12, 24, 48, 72], dtype=float)
result = model.calculate(duration_months=durations, confidence_pct=90)

print(result["fluence_cm2"].shape)    # (7, 10)
print(result["n_al_events"].shape)    # (7,)
```

### 比较不同置信水平

```python
model = SOLPRO()
for conf in [80, 90, 95, 99]:
    r = model.calculate(duration_months=24, confidence_pct=conf)
    print(f"  {conf}%: {r['fluence_cm2'][0]:.3e} protons/cm² (>10 MeV), "
          f"{r['n_al_events']} 个 AL 事件")
```

## 注意事项

- 模型基于第 20 太阳活动周期数据（1964–1972），对后续太阳周期的预测可能偏高。
- 标量输入返回标量 `n_al_events` 和一维 `fluence_cm2`（形状 `(10,)`）；
  数组输入返回数组 `n_al_events` 和二维 `fluence_cm2`（形状 `(N, 10)`）。
- 能量阈值硬编码为 E = 10, 20, 30, …, 100 MeV。

## 参考文献

1. King, J. H., "Solar Proton Fluences for 1977-1983 Space Missions",
   J. Spacecraft & Rockets 11, 401, 1974.

2. Stassinopoulos, E. G., and J. H. King, "A Method for Rapid Estimation
   of Solar Proton Fluences for NASA Missions", NASA TM X-71140, 1974.

3. King, J. H., and E. G. Stassinopoulos, "A Model for the Calculation
   of Interplanetary Solar Proton Fluences", NASA TM X-71139, 1975.

4. Stassinopoulos, E. G., "SOLPRO: A Computer Code for the Calculation
   of Interplanetary Solar Proton Fluences", NASA TM X-71141, 1975.
