# Chiu 电离层电子密度模型

## 模型背景

Chiu 电离层模型是一个经验电子密度模型，使用 E、F1、F2 三个修正 Chapman 函数叠加描述 90-500 km 高度范围内的电离层电子密度剖面。

模型输入包含太阳活动、地方时、季节、地理纬度、地磁纬度/经度和磁倾角。本模块将 Fortran 源码编译为共享库，并通过 `ctypes` 封装为 `Chiu` 类，遵循项目统一的 `Model.calculate(...)` 接口。

**无需外部数据文件** - 所有经验系数均硬编码在 Fortran 源码中。

## 目录结构

```text
pychiu/
├── chiu.for          # Fortran 77 原始模型子程序
├── chiu_cshim.F90    # C ABI shim，导出 chiu_eval()
├── CMakeLists.txt    # CMake 目标 chiu
├── __init__.py       # Python Model 类
└── README.md         # 本文件
```

## Fortran 接口

### `chiu.for` - `IONDEN` 子程序

```fortran
SUBROUTINE IONDEN(QTOT, QI, Z, RZUR, PHI, TMO, RLT, RLTM, RLGM, DIP)
```

| 参数 | 方向 | 类型 | 说明 |
|------|------|------|------|
| `QTOT` | 输出 | `real` | 总电子密度，单位为 `1.0E5 cm^-3` |
| `QI` | 输出 | `real(3)` | E、F1、F2 层电子密度，单位为 `1.0E5 cm^-3` |
| `Z` | 输入 | `real` | 高度（km），90-500；设为 0 时返回层峰值密度 |
| `RZUR` | 输入 | `real` | 苏黎世平滑太阳黑子数 |
| `PHI` | 输入 | `real` | 从午夜起算的地方时角（弧度），0 为午夜，pi 为正午 |
| `TMO` | 输入 | `real` | 从上年 12 月 15 日起算的月份数 |
| `RLT` | 输入 | `real` | 地理纬度（弧度） |
| `RLTM` | 输入 | `real` | 地磁纬度（弧度） |
| `RLGM` | 输入 | `real` | 地磁东经（弧度） |
| `DIP` | 输入 | `real` | 地磁磁倾角（弧度） |

### `chiu_cshim.F90` - C ABI

```c
void chiu_eval(float *indata, float *outdata);
```

`indata` 包含 8 个输入值：`Z, RZUR, PHI, TMO, RLT, RLTM, RLGM, DIP`。`outdata` 包含 4 个输出值：`QTOT, QI_E, QI_F1, QI_F2`。

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `alt_km` | float / array | 高度（km），90-500；设为 0 时返回层峰值密度 |
| `sunspot_number` | float / array | 苏黎世平滑太阳黑子数 |
| `local_time_rad` | float / array | 从午夜起算的地方时角（弧度），0 为午夜，pi 为正午 |
| `month_from_dec15` | float / array | 从上年 12 月 15 日起算的月份数 |
| `geo_lat_rad` | float / array | 地理纬度（弧度） |
| `geo_mag_lat_rad` | float / array | 地磁纬度（弧度） |
| `geo_mag_lon_rad` | float / array | 地磁东经（弧度） |
| `dip_angle_rad` | float / array | 地磁磁倾角（弧度） |

## 输出

`calculate()` 返回包含以下字段的字典：

| 字段 | 类型 | 说明 |
|------|------|------|
| `alt_km` | float / ndarray | 输入高度 |
| `sunspot_number` | float / ndarray | 输入太阳黑子数 |
| `Ne_total_cm3` | float / ndarray | 总电子密度（cm^-3） |
| `Ne_E_cm3` | float / ndarray | E 层电子密度（cm^-3） |
| `Ne_F1_cm3` | float / ndarray | F1 层电子密度（cm^-3） |
| `Ne_F2_cm3` | float / ndarray | F2 层电子密度（cm^-3） |

## 使用示例

### 单点计算

```python
import math
from model import Chiu

model = Chiu()
result = model.calculate(
    alt_km=300.0,
    sunspot_number=100.0,
    local_time_rad=math.pi,
    month_from_dec15=6.0,
    geo_lat_rad=math.radians(35.0),
    geo_mag_lat_rad=math.radians(25.0),
    geo_mag_lon_rad=math.radians(120.0),
    dip_angle_rad=math.radians(45.0),
)

print(f"总电子密度: {result['Ne_total_cm3']:.1f} cm^-3")
print(f"F2 层电子密度: {result['Ne_F2_cm3']:.1f} cm^-3")
```

### 高度剖面

```python
alts = [100.0, 200.0, 300.0, 400.0, 500.0]
result = model.calculate(
    alt_km=alts,
    sunspot_number=100.0,
    local_time_rad=math.pi,
    month_from_dec15=6.0,
    geo_lat_rad=math.radians(35.0),
    geo_mag_lat_rad=math.radians(25.0),
    geo_mag_lon_rad=math.radians(120.0),
    dip_angle_rad=math.radians(45.0),
)

print(result["Ne_total_cm3"].shape)  # (5,)
```

### 峰值密度模式

```python
result = model.calculate(
    alt_km=0.0,
    sunspot_number=100.0,
    local_time_rad=math.pi,
    month_from_dec15=6.0,
    geo_lat_rad=math.radians(35.0),
    geo_mag_lat_rad=math.radians(25.0),
    geo_mag_lon_rad=math.radians(120.0),
    dip_angle_rad=math.radians(45.0),
)

print(result["Ne_E_cm3"], result["Ne_F1_cm3"], result["Ne_F2_cm3"])
```

## 构造函数参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |

## 模型说明

- `alt_km=0` 是原始模型定义的特殊模式：`Ne_total_cm3` 返回 0，分层字段返回 E、F1、F2 层峰值密度。
- Fortran 原始输出单位为 `1.0E5 cm^-3`，Python wrapper 已转换为 `cm^-3`。
- 所有输入都支持 numpy 广播；标量输入返回 Python 标量，数组输入返回 `numpy.ndarray`。

## 参考文献

1. Ching, B. K., and Chiu, Y. T., "A phenomenological model of global ionospheric electron density in the E-, F1- and F2-regions", Journal of Atmospheric and Terrestrial Physics, 35, 1615, 1973.

2. Chiu, Y. T., "An improved phenomenological model of ionospheric density", Journal of Atmospheric and Terrestrial Physics, 37, 1563, 1975.
