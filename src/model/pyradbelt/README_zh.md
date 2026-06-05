# RADBELT — AP-8 / AE-8 捕获辐射模型

[English](README.md)

## 模型背景

RADBELT 模型实现了由 NSSDC 的 J. I. Vette 等人开发的 NASA AP-8 和 AE-8 地球辐射带捕获辐射环境模型。这些模型提供辐射带中捕获质子（AP-8）和电子（AE-8）的全向积分通量，以 L 值（McIlwain 参数）、磁场强度比（B/B0）和粒子能量为自变量。

每种粒子类型有两个太阳活动变化：
- **AP8MAX / AP8MIN**：太阳活动极大年 / 极小年的质子通量
- **AE8MAX / AE8MIN**：太阳活动极大年 / 极小年的电子通量

模型使用经验推导的通量图，通过 TRARA1/TRARA2 子例程在 L-B/B0-能量空间进行插值（Bilitza, 1988）。

本模块将 Fortran 子例程编译为共享库，通过 `ctypes` 封装为 `RADBELT` 类，遵循项目统一的 `Model.calculate(...)` 接口。

**参考文献**：

> Vette, J. I., *The AE-8 Trapped Electron Model Environment*, NSSDC Report 91-24, 1991.

> Vette, J. I., *The AP-8 Trapped Proton Environment for Solar Maximum and Solar Minimum*, NSSDC Report, 1991.

> Bilitza, D., *Radbelt - Trapped radiation models*, NSSDC-ID: PT-14A, 1988.

## 目录结构

```
pyradbelt/
├── trmfun.for           # Fortran 77 核心插值子例程（TRARA1、TRARA2）
├── radbelt_cshim.F90    # C ABI shim，导出 radbelt_load_data() 和 radbelt_calc_flux()
├── CMakeLists.txt       # CMake 构建目标 radbelt
├── __init__.py          # Python Model 类
└── README_zh.md         # 本文件
```

## Fortran 接口

### `trmfun.for` — 核心子例程

```fortran
SUBROUTINE TRARA1(DESCR, MAP, FL, BB0, E, F, N)
```

| 参数    | 方向 | 类型          | 说明                                      |
|---------|------|---------------|-------------------------------------------|
| `DESCR` | 入参 | `INTEGER(8)`  | 数据文件头数组                             |
| `MAP`   | 入参 | `INTEGER(*)`  | 数据文件通量图数组                         |
| `FL`    | 入参 | `REAL`        | L 值（McIlwain 参数）                      |
| `BB0`   | 入参 | `REAL`        | B/B0 — 磁场强度与赤道值之比                |
| `E`     | 入参 | `REAL(N)`     | 能量数组（MeV）                            |
| `F`     | 出参 | `REAL(N)`     | log10(积分通量) [particles/(cm²·s)]        |
| `N`     | 入参 | `INTEGER`     | 能量个数                                   |

### `radbelt_cshim.F90` — C ABI

```c
void radbelt_load_data(int *ihead, int nmap, int *map);
void radbelt_calc_flux(float l_value, float bb0, float *energies, float *flux, int n);
```

## 输入参数

| 参数          | 类型 | 说明 |
|---------------|------|------|
| `l_value`     | float / array | L 值（McIlwain 磁壳参数），1.0–15.6 |
| `bb0`         | float / array | B/B0 比值（磁场强度 / 赤道磁场强度），≥ 1.0 |
| `energy_mev`  | float / array | 粒子能量（MeV） |

### 能量范围

| 模型类型 | 粒子 | 有效能量范围（MeV） |
|---------|------|---------------------|
| AP8MAX、AP8MIN | 质子 | 0.1 – 400 |
| AE8MAX、AE8MIN | 电子 | 0.04 – 7.0 |

## 输出

`calculate()` 返回一个字典，包含以下字段：

| 字段           | 类型 | 说明 |
|----------------|------|------|
| `l_value`      | float / ndarray | 输入 L 值 |
| `bb0`          | float / ndarray | 输入 B/B0 值 |
| `energy_mev`   | float / ndarray | 输入能量值（MeV） |
| `flux`         | float / ndarray | log10(全向积分通量) [particles/(cm²·s)] |

注意：当通量为零或负值（超出模型覆盖范围）时，`flux` 返回 0.0。

## 用法示例

### 单点计算

```python
from model import RADBELT

model = RADBELT("AE8MIN")
result = model.calculate(l_value=3.0, bb0=1.0, energy_mev=1.0)

import math
flux_linear = 10 ** result["flux"]
print(f"log10(flux) = {result['flux']:.4f}")
print(f"flux = {flux_linear:.2e} particles/(cm²·s)")
```

### 批量计算不同 L 值

```python
import numpy as np

l_vals = [1.5, 2.0, 3.0, 4.0, 6.0]
result = model.calculate(l_value=l_vals, bb0=1.0, energy_mev=0.5)

for l, f in zip(l_vals, result["flux"]):
    print(f"L={l:.1f}: log10(flux)={f:.4f}")
```

### 比较质子和电子模型

```python
from model import RADBELT

proton_model = RADBELT("AP8MIN")
electron_model = RADBELT("AE8MIN")

p = proton_model.calculate(l_value=3.0, bb0=1.0, energy_mev=10.0)
e = electron_model.calculate(l_value=3.0, bb0=1.0, energy_mev=1.0)

print(f"质子通量 (>10 MeV): {10**p['flux']:.2e} cm⁻²s⁻¹")
print(f"电子通量 (>1 MeV): {10**e['flux']:.2e} cm⁻²s⁻¹")
```

## 构造参数

| 参数           | 默认值     | 说明 |
|----------------|------------|------|
| `model_type`   | （必填）   | `"AP8MAX"`、`"AP8MIN"`、`"AE8MAX"`、`"AE8MIN"` 之一 |
| `dll_path`     | 自动检测   | 自定义 DLL 路径 |
| `data_dir`     | `None`     | 自定义数据目录（未设置时自动下载） |
| `auto_download`| `True`     | 是否自动下载缺失的数据文件 |

## 坐标说明

- **L 值**：McIlwain 磁壳参数。L=1 对应地球表面；L≈6.6 对应地球同步轨道。
- **B/B0**：局地磁场强度与同一磁力线赤道处磁场强度之比。B/B0=1 在磁赤道面；B/B0>1 远离磁赤道。
- 如需从地理坐标计算 L 值和 B/B0，可使用 `IGRF` 模型的 `L_value` 输出。

## 致谢

在基于此软件发表的论文或包含此模型代码的应用程序中，请注明软件提供方（NSSDC）和模型作者（J. I. Vette 等）。
