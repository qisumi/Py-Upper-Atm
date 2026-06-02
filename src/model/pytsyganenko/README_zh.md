# Tsyganenko 地磁场模型（T89 / T96 / T01 / TS04）

## 模型背景

Tsyganenko 系列模型是基于卫星观测数据构建的经验磁层磁场模型，用于计算地球磁层中外部磁场（非地球内部偶极场）对磁场总量的贡献。该系列包含四个版本：

- **T89**（Tsyganenko 1989）：使用 Kp 指数控制磁场形变的最简版本，适合快速估算。
- **T96**（Tsyganenko 1996）：引入太阳风动压、IMF By/Bz 和 Dst 指数作为输入参数。
- **T01**（Tsyganenko 2001）：在 T96 基础上增加 G1、G2 两个磁层活动参数。
- **TS04**（Tsyganenko & Sitnov 2004）：最新版本，使用 6 个加权参数（W1-W6）描述磁层状态。

本模块基于 **Geopack-2005** 子程序库完成坐标变换（GEI ↔ GSM）和地球偶极子磁场计算。Fortran 源码编译为共享库后，通过 `ctypes` 封装为 `Tsyganenko` 类，遵循项目统一的 `Model.calculate(...)` 接口。

**无需外部数据文件** — 所有经验系数均硬编码在 Fortran 源码中。

## 目录结构

```text
pytsyganenko/
├── tsyganenko.for        # Fortran 77 T89/T96/T01/TS04 模型源码
├── geopack.for            # Fortran 77 Geopack-2005 坐标变换与偶极子场
├── tsyganenko_cshim.F90   # C ABI shim，导出 tsyganenko_eval()
├── CMakeLists.txt         # CMake 目标 tsyganenko
├── __init__.py            # Python Model 类
├── README.md              # 中文文档
```

## Fortran 接口

### `tsyganenko_cshim.F90` - C ABI

```c
void tsyganenko_eval(float *indata, float *outdata);
```

`indata` 包含 18 个输入值，`outdata` 包含 6 个输出值（外源场 3 分量 + 偶极场 3 分量）。

## 构造函数参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `model_version` | 必填 | 模型版本，可选 `"T89"`、`"T96"`、`"T01"`、`"TS04"` |
| `include_dipole` | `False` | 是否同时计算地球内部偶极子磁场 |
| `dll_path` | 自动检测 | 自定义 DLL 路径 |

## 输入参数

### 通用位置参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `x_re` | float / array | GSM 坐标系 X 分量（地球半径 Re） |
| `y_re` | float / array | GSM 坐标系 Y 分量（地球半径 Re） |
| `z_re` | float / array | GSM 坐标系 Z 分量（地球半径 Re） |

### 时间参数（二选一）

方式一：提供日期时间分量，由模型自动计算偶极倾角和坐标变换：

| 参数 | 类型 | 说明 |
|------|------|------|
| `year` | int | 年份 |
| `doy` | int | 年内日序号（1-366） |
| `hour` | int | 小时（0-23） |
| `minute` | int | 分钟（0-59） |
| `second` | float | 秒（0-60） |

方式二：直接提供偶极倾角（跳过内部坐标变换）：

| 参数 | 类型 | 说明 |
|------|------|------|
| `tilt_rad` | float | 偶极倾角（弧度） |

### 模型特有参数

#### T89

| 参数 | 类型 | 说明 |
|------|------|------|
| `kp_index` | int (1-7) | Kp 地磁活动指数等级 |

#### T96

| 参数 | 类型 | 说明 |
|------|------|------|
| `pdyn_nPa` | float | 太阳风动压（nPa） |
| `dst_nT` | float | Dst 指数（nT） |
| `by_imf_nT` | float | 行星际磁场 By 分量（nT, GSM） |
| `bz_imf_nT` | float | 行星际磁场 Bz 分量（nT, GSM） |

#### T01

T01 需要 T96 的全部参数，外加：

| 参数 | 类型 | 说明 |
|------|------|------|
| `g1` | float | 磁层活动参数 G1 |
| `g2` | float | 磁层活动参数 G2 |

#### TS04

| 参数 | 类型 | 说明 |
|------|------|------|
| `pdyn_nPa` | float | 太阳风动压（nPa） |
| `dst_nT` | float | Dst 指数（nT） |
| `by_imf_nT` | float | 行星际磁场 By 分量（nT, GSM） |
| `bz_imf_nT` | float | 行际磁场 Bz 分量（nT, GSM） |
| `w1`–`w6` | float | 6 个磁层状态加权参数 |

## 输出

`calculate()` 返回包含以下字段的字典：

### 默认输出（`include_dipole=False`）

| 字段 | 类型 | 说明 |
|------|------|------|
| `tilt_rad` | float | 偶极倾角（弧度） |
| `Bx_ext_nT` | float / ndarray | 外源磁场 GSM X 分量（nT） |
| `By_ext_nT` | float / ndarray | 外源磁场 GSM Y 分量（nT） |
| `Bz_ext_nT` | float / ndarray | 外源磁场 GSM Z 分量（nT） |

### 附加输出（`include_dipole=True` 时额外返回）

| 字段 | 类型 | 说明 |
|------|------|------|
| `Bx_dip_nT` | float / ndarray | 偶极子磁场 GSM X 分量（nT） |
| `By_dip_nT` | float / ndarray | 偶极子磁场 GSM Y 分量（nT） |
| `Bz_dip_nT` | float / ndarray | 偶极子磁场 GSM Z 分量（nT） |
| `Bx_total_nT` | float / ndarray | 总磁场 GSM X 分量（nT） |
| `By_total_nT` | float / ndarray | 总磁场 GSM Y 分量（nT） |
| `Bz_total_nT` | float / ndarray | 总磁场 GSM Z 分量（nT） |

## 使用示例

### T89 单点计算

```python
from model import Tsyganenko

model = Tsyganenko(model_version="T89")
result = model.calculate(
    year=2000, doy=180, hour=12, minute=0, second=0.0,
    x_re=-5.0, y_re=0.0, z_re=0.0,
    kp_index=3,
)

print(f"外源磁场 Bx: {result['Bx_ext_nT']:.2f} nT")
print(f"外源磁场 Bz: {result['Bz_ext_nT']:.2f} nT")
print(f"偶极倾角: {result['tilt_rad']:.4f} rad")
```

### T96 含偶极子场

```python
model = Tsyganenko(model_version="T96", include_dipole=True)
result = model.calculate(
    year=2000, doy=180, hour=12, minute=0, second=0.0,
    x_re=-6.6, y_re=0.0, z_re=0.0,
    pdyn_nPa=2.0, dst_nT=-20.0,
    by_imf_nT=0.5, bz_imf_nT=-2.0,
)

print(f"外源场: ({result['Bx_ext_nT']:.2f}, {result['By_ext_nT']:.2f}, {result['Bz_ext_nT']:.2f}) nT")
print(f"总磁场: ({result['Bx_total_nT']:.2f}, {result['By_total_nT']:.2f}, {result['Bz_total_nT']:.2f}) nT")
```

### T01 使用直接倾角输入

```python
model = Tsyganenko(model_version="T01")
result = model.calculate(
    tilt_rad=0.15,
    x_re=-10.0, y_re=2.0, z_re=1.0,
    pdyn_nPa=2.0, dst_nT=-20.0,
    by_imf_nT=0.5, bz_imf_nT=-2.0,
    g1=1.0, g2=1.0,
)
```

### TS04 批量计算

```python
import numpy as np

model = Tsyganenko(model_version="TS04")
result = model.calculate(
    year=2000, doy=180, hour=12, minute=0, second=0.0,
    x_re=np.array([-5.0, -6.6, -10.0]),
    y_re=np.array([0.0, 0.0, 0.0]),
    z_re=np.array([0.0, 0.0, 0.0]),
    pdyn_nPa=2.0, dst_nT=-20.0,
    by_imf_nT=0.5, bz_imf_nT=-2.0,
    w1=0.5, w2=0.5, w3=0.5, w4=0.5, w5=0.5, w6=0.5,
)

print(result["Bx_ext_nT"].shape)  # (3,)
```

## 模型说明

- 所有输入都支持 numpy 广播；标量输入返回 Python 标量，数组输入返回 `numpy.ndarray`。
- 位置坐标使用 GSM（太阳-磁层）坐标系，单位为地球半径 Re。
- 默认仅返回外源磁场（磁层电流产生的磁场）。设置 `include_dipole=True` 可同时计算地球内部偶极子磁场和总磁场。
- Geopack-2005 内置 IGRF 偶极子近似，不依赖外部 IGRF 系数文件。
- 当同时提供时间参数和 `tilt_rad` 时，`tilt_rad` 优先。

## 参考文献

1. Tsyganenko, N. A., "A magnetospheric magnetic field model with a warped tail current sheet", Planet. Space Sci., 37, 5-20, 1989.

2. Tsyganenko, N. A., "Effects of the solar wind conditions on the global magnetospheric configuration as deduced from data-based field models", Eur. Space Agency Spec. Publ., ESA SP-389, 181, 1996.

3. Tsyganenko, N. A., "A model of the near magnetosphere with a dawn-dusk asymmetry: 1. Mathematical structure", Space Sci. Rev., 108, 79, 2003.

4. Tsyganenko, N. A., and M. I. Sitnov, "Modeling the dynamics of the inner magnetosphere during strong geomagnetic storms", J. Geophys. Res., 110, A03208, 2005.
