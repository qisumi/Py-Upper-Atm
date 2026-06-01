# MET — 马歇尔工程热层模型

## 模型背景

马歇尔工程热层（MET）模型是由 NASA 马歇尔太空飞行中心的 Mike Hickey 于 1987 年开发的工程热层模型。该模型基于修改的 Jacchia 1970 模型，专为工程应用优化。

该模型提供了 90–2500 km 高度范围内的温度剖面、主要中性成分（N2, O2, O, Ar, He, H）的数密度剖面、总密度、压力和其他热力学参数。

本模块将 Fortran 源码编译为共享库，并通过 `ctypes` 封装为 `MET` 类，遵循项目统一的 `Model.calculate(...)` 接口。

**无需外部数据文件** — 所有系数均硬编码在 Fortran 源码中。

**参考文献**：

> Hickey, M. P., "Marshall Engineering Thermosphere Model," NASA/MSFC, 1987.

## 目录结构

```
pymet/
├── met.for              # Fortran 77 原始模型子程序
├── met_cshim.F90        # C ABI shim，导出 met_eval()
├── CMakeLists.txt       # CMake 目标 met
├── __init__.py          # Python Model 类
└── README.md            # 本文件
```

## Fortran 接口

### `met.for` — `J70` 子程序

```fortran
SUBROUTINE J70(INDATA, OUTDATA)
```

| 参数 | 方向 | 类型 | 说明 |
|------|------|------|------|
| `INDATA` | 输入 | `REAL*4(12)` | 输入数据数组 |
| `OUTDATA` | 输出 | `REAL*4(12)` | 输出数据数组 |

**输入数组元素**：

| 索引 | 说明 |
|------|------|
| 1 | 高度（km） |
| 2 | 纬度（度） |
| 3 | 经度（度） |
| 4 | 年份（2位数） |
| 5 | 月份 |
| 6 | 日 |
| 7 | 时 |
| 8 | 分 |
| 9 | 地磁指数类型（1=Kp, 2=Ap） |
| 10 | F10.7 太阳射电噪声通量 |
| 11 | 162天平均 F10.7 |
| 12 | 地磁活动指数 |

**输出数组元素**：

| 索引 | 说明 |
|------|------|
| 1 | 外逸层温度（K） |
| 2 | 高度 Z 处的温度（K） |
| 3 | N2 数密度（每立方米） |
| 4 | O2 数密度（每立方米） |
| 5 | O 数密度（每立方米） |
| 6 | Ar 数密度（每立方米） |
| 7 | He 数密度（每立方米） |
| 8 | H 数密度（每立方米） |
| 9 | 平均分子量 |
| 10 | 总密度（kg/m³） |
| 11 | log10(总密度) |
| 12 | 总压力（Pa） |

### `met_cshim.F90` — C ABI

```c
void met_eval(
    float *indata,   // 输入数组 (12 elements)
    float *outdata,  // 输出数组 (12 elements)
    float *auxdata   // 辅助输出数组 (5 elements)
);
```

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `alt_km` | float / array | 高度（km） |
| `lat_deg` | float / array | 地理纬度（度） |
| `lon_deg` | float / array | 地理经度（度） |
| `year` | float / array | 年份（2位数） |
| `month` | float / array | 月份（1-12） |
| `day` | float / array | 日 |
| `hour` | float / array | 时（0-23） |
| `minute` | float / array | 分（0-59） |
| `geo_index_type` | float / array | 地磁指数类型（1=Kp, 2=Ap） |
| `f107` | float / array | F10.7 太阳射电噪声通量 |
| `f107a` | float / array | 162天平均 F10.7 |
| `ap` | float / array | 地磁活动指数 Ap |

## 输出

`calculate()` 返回包含以下字段的字典：

| 字段 | 类型 | 说明 |
|------|------|------|
| `alt_km` | float / ndarray | 输出高度 |
| `lat_deg` | float / ndarray | 纬度（度） |
| `lon_deg` | float / ndarray | 经度（度） |
| `T_exo_K` | float / ndarray | 外逸层温度（K） |
| `T_local_K` | float / ndarray | 局地温度（K） |
| `N2_m3` | float / ndarray | N2 数密度（每立方米） |
| `O2_m3` | float / ndarray | O2 数密度（每立方米） |
| `O_m3` | float / ndarray | O 数密度（每立方米） |
| `Ar_m3` | float / ndarray | Ar 数密度（每立方米） |
| `He_m3` | float / ndarray | He 数密度（每立方米） |
| `H_m3` | float / ndarray | H 数密度（每立方米） |
| `mean_molecular_weight` | float / ndarray | 平均分子量 |
| `total_density_kg_m3` | float / ndarray | 总质量密度（kg/m³） |
| `log10_density` | float / ndarray | log10(总密度) |
| `pressure_Pa` | float / ndarray | 总压力（Pa） |
| `gravity_m_s2` | float / ndarray | 重力加速度（m/s²） |
| `gamma` | float / ndarray | 比热比 |
| `scale_height_m` | float / ndarray | 气压标高（m） |
| `cp` | float / ndarray | 定压比热 |
| `cv` | float / ndarray | 定容比热 |

## 使用示例

### 单点计算

```python
from model import MET

model = MET()
result = model.calculate(
    alt_km=200.0,
    lat_deg=35.0,
    lon_deg=116.0,
    year=23,  # 2023
    month=7,
    day=15,
    hour=12,
    minute=0,
    geo_index_type=2,  # Ap
    f107=100.0,
    f107a=100.0,
    ap=15.0,
)

print(f"外逸层温度: {result['T_exo_K']:.2f} K")
print(f"局地温度: {result['T_local_K']:.2f} K")
print(f"总密度: {result['total_density_kg_m3']:.2e} kg/m³")
```

### 剖面计算

```python
import numpy as np

alts = np.arange(100, 501, 50)  # 100-500 km，每50 km
result = model.calculate(
    alt_km=alts,
    lat_deg=35.0,
    lon_deg=116.0,
    year=23,
    month=7,
    day=15,
    hour=12,
    minute=0,
    geo_index_type=2,
    f107=100.0,
    f107a=100.0,
    ap=15.0,
)

print(f"温度范围: [{result['T_local_K'].min():.1f}, {result['T_local_K'].max():.1f}] K")
```

## 构造函数参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |

## 模型说明

- 该模型适用于 90–2500 km 高度范围
- 基于修改的 Jacchia 1970 模型
- 包含季节-纬度变化修正
- 包含氦密度的季节-纬度变化修正
- 所有输出均为 MKS 单位制

## 参考文献

1. Jacchia, L. G., "New Static Models of the Thermosphere and Exosphere with Empirical Temperature Profiles," SAO Special Report No. 313, 1970.

2. Hickey, M. P., "Marshall Engineering Thermosphere Model," NASA/MSFC, ED44, 1987.
