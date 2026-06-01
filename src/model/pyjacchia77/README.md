# Jacchia 1977 参考大气模型

## 模型背景

Jacchia 1977 参考大气模型是由 L. G. Jacchia 于 1977 年发布的经验热层模型。该模型提供了 90–2500+ km 高度范围内的温度剖面和主要中性成分（N2, O2, O, Ar, He, H）的数密度剖面。

该模型基于以下参考文献：

> Jacchia, L. G., "Thermospheric Temperature, Density and Composition: New Models," SAO Special Report No. 375 (Smithsonian Institution Astrophysical Observatory, Cambridge, MA, March 15, 1977).

本模块将 Fortran 源码编译为共享库，并通过 `ctypes` 封装为 `Jacchia77` 类，遵循项目统一的 `Model.calculate(...)` 接口。

**无需外部数据文件** — 所有系数均硬编码在 Fortran 源码中。

## 目录结构

```
pyjacchia77/
├── j77sri.for              # Fortran 77 原始模型子程序
├── jacchia77_cshim.F90     # C ABI shim，导出 jacchia77_eval()
├── CMakeLists.txt          # CMake 目标 jacchia77
├── __init__.py             # Python Model 类
└── README.md               # 本文件
```

## Fortran 接口

### `j77sri.for` — `j77sri` 子程序

```fortran
subroutine j77sri(maxz, Tinf, Z, T, CN2, CO2, CO, CAr, CHe, CH, CM, WM)
```

| 参数 | 方向 | 类型 | 说明 |
|------|------|------|------|
| `maxz` | 输入 | `integer` | 最高高度（km），决定数组大小 |
| `Tinf` | 输入 | `real` | 外逸层温度（K） |
| `Z` | 输出 | `real(0:maxz)` | 高度数组（km） |
| `T` | 输出 | `real(0:maxz)` | 温度数组（K） |
| `CN2` | 输出 | `real(0:maxz)` | N2 数密度（cm⁻³） |
| `CO2` | 输出 | `real(0:maxz)` | O2 数密度（cm⁻³） |
| `CO` | 输出 | `real(0:maxz)` | O 数密度（cm⁻³） |
| `CAr` | 输出 | `real(0:maxz)` | Ar 数密度（cm⁻³） |
| `CHe` | 输出 | `real(0:maxz)` | He 数密度（cm⁻³） |
| `CH` | 输出 | `real(0:maxz)` | H 数密度（cm⁻³） |
| `CM` | 输出 | `real(0:maxz)` | 总数密度（cm⁻³） |
| `WM` | 输出 | `real(0:maxz)` | 平均分子量（g/mol） |

### `jacchia77_cshim.F90` — C ABI

```c
void jacchia77_eval(
    float Tinf,        // 外逸层温度（K）
    float *alt_km,     // 高度数组（km）
    int n_alt,         // 高度数组长度
    float *T_out,      // 温度输出（K）
    float *N2_out,     // N2 数密度输出（cm⁻³）
    float *O2_out,     // O2 数密度输出（cm⁻³）
    float *O_out,      // O 数密度输出（cm⁻³）
    float *Ar_out,     // Ar 数密度输出（cm⁻³）
    float *He_out,     // He 数密度输出（cm⁻³）
    float *H_out,      // H 数密度输出（cm⁻³）
    float *rho_out,    // 总数密度输出（cm⁻³）
    float *W_out       // 平均分子量输出（g/mol）
);
```

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `alt_km` | float / array | 高度（km），范围 0–2500 |
| `Tinf_K` | float | 外逸层温度（K），标量 |

## 输出

`calculate()` 返回包含以下字段的字典：

| 字段 | 类型 | 说明 |
|------|------|------|
| `alt_km` | float / ndarray | 输出高度（同广播后的形状） |
| `Tinf_K` | float | 外逸层温度（K） |
| `T_local_K` | float / ndarray | 局地温度（K） |
| `N2_cm3` | float / ndarray | N2 数密度（cm⁻³） |
| `O2_cm3` | float / ndarray | O2 数密度（cm⁻³） |
| `O_cm3` | float / ndarray | O 数密度（cm⁻³） |
| `Ar_cm3` | float / ndarray | Ar 数密度（cm⁻³） |
| `He_cm3` | float / ndarray | He 数密度（cm⁻³） |
| `H_cm3` | float / ndarray | H 数密度（cm⁻³） |
| `total_density_cm3` | float / ndarray | 总数密度（cm⁻³） |
| `mean_molecular_weight` | float / ndarray | 平均分子量（g/mol） |

## 使用示例

### 单点计算

```python
from model import Jacchia77

model = Jacchia77()
result = model.calculate(alt_km=200.0, Tinf_K=1000.0)

print(f"温度: {result['T_local_K']:.2f} K")
print(f"N2: {result['N2_cm3']:.2e} cm⁻³")
print(f"O: {result['O_cm3']:.2e} cm⁻³")
```

### 剖面计算

```python
import numpy as np

alts = np.arange(90, 501, 10)  # 90-500 km，每10 km
result = model.calculate(alt_km=alts, Tinf_K=1000.0)

print(f"温度范围: [{result['T_local_K'].min():.1f}, {result['T_local_K'].max():.1f}] K")
```

### 不同外逸层温度

```python
for Tinf in [600.0, 800.0, 1000.0, 1200.0, 1500.0]:
    result = model.calculate(alt_km=200.0, Tinf_K=Tinf)
    print(f"Tinf={Tinf:.0f} K: T={result['T_local_K']:.2f} K")
```

## 构造函数参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |

## 模型说明

- 该模型适用于 90–2500 km 高度范围
- 对于 90 km 以下，使用美国标准大气 1976
- 对于 86–89 km，使用气压方程连接
- 对于 90 km 以上，使用 Jacchia 1977 模型
- H 原子密度仅在最高高度 ≥ 500 km 且高度 ≥ 150 km 时计算

## 参考文献

1. Jacchia, L. G., "Thermospheric Temperature, Density and Composition: New Models," SAO Special Report No. 375, Smithsonian Institution Astrophysical Observatory, Cambridge, MA, March 15, 1977.

2. U.S. Committee on Extension to the Standard Atmosphere, "U.S. Standard Atmospheres 1976," USGPO, Washington, DC, 1976.

3. Chamberlain, J. W., and D. M. Hunten, "Theory of Planetary Atmospheres," Academic Press, NY, 1987.
