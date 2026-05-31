# MSISE-90 — MSISE-90 中性大气模型

[English Version](README.md)

## 模型背景

MSISE-90（质谱仪非相干散射扩展模型，1990）是由 A.E. Hedin 开发的经验中性大气模型。它将 MSIS-86 模型向下延伸至地面，可计算从地表到低热层的中性大气温度和物种数密度。

该模型通过球谐展开考虑了太阳活动（F10.7 通量）、地磁活动（Ap 指数）、地方时、纬度、经度和季节变化。

本模块将 Fortran 源码编译为共享库，并通过 `ctypes` 封装为 `MSISE90` 类，遵循项目统一的 `Model.calculate(...)` 接口。

**参考文献**：

> Hedin, A.E., *Extension of the MSIS Thermosphere Model into the Middle and Lower Atmosphere*, J. Geophys. Res. **96**, 1159-1172, 1991.

## 目录结构

```
pymsise90/
├── msise90.for         # Fortran 77 源码（GTD6 及辅助子程序）
├── msise90_cshim.F90   # C ABI shim，导出 gtd6_eval()
├── CMakeLists.txt      # CMake 目标 msise90
├── __init__.py         # Python Model 类
├── build/              # 编译生成的 DLL（由 CMake 创建）
└── README_zh.md        # 本文件
```

## Fortran 接口

### `msise90.for` — `GTD6` 子程序

```fortran
SUBROUTINE GTD6(IYD, SEC, ALT, GLAT, GLONG, STL, F107A, F107, AP, MASS, D, T)
```

| 参数      | 方向 | 类型      | 描述                                              |
|-----------|------|-----------|---------------------------------------------------|
| `IYD`     | 输入 | `INTEGER` | 日期，格式 YYYYDDD（如 1990172）                  |
| `SEC`     | 输入 | `REAL`    | 世界时秒数                                        |
| `ALT`     | 输入 | `REAL`    | 高度（km），可从地表到热层                        |
| `GLAT`    | 输入 | `REAL`    | 地理纬度（度）                                    |
| `GLONG`   | 输入 | `REAL`    | 地理经度（度）                                    |
| `STL`     | 输入 | `REAL`    | 地方太阳时（小时）                                |
| `F107A`   | 输入 | `REAL`    | 81 天平均 F10.7 太阳通量                         |
| `F107`    | 输入 | `REAL`    | 前一天的 F10.7 太阳通量                          |
| `AP`      | 输入 | `REAL(7)` | 地磁活动指数（日 Ap 或 7 元素历史）               |
| `MASS`    | 输入 | `INTEGER` | 质量数选择器（48 = 所有物种）                     |
| `D`       | 输出 | `REAL(8)` | 物种数密度（见下表）                              |
| `T`       | 输出 | `REAL(2)` | 温度（外逸层、局部）                              |

输出密度 `D(1..8)`：

| 索引 | 物种        | 单位    |
|------|-------------|---------|
| 1    | He          | cm⁻³    |
| 2    | O           | cm⁻³    |
| 3    | N2          | cm⁻³    |
| 4    | O2          | cm⁻³    |
| 5    | Ar          | cm⁻³    |
| 6    | 总质量      | g/cm³   |
| 7    | H           | cm⁻³    |
| 8    | N           | cm⁻³    |

输出温度 `T(1..2)`：

| 索引 | 描述                | 单位 |
|------|---------------------|------|
| 1    | 外逸层温度          | K    |
| 2    | 高度处温度          | K    |

### `msise90_cshim.F90` — C ABI

```c
void gtd6_eval(int iyd, float sec, float alt, float glat, float glong,
               float stl, float f107a, float f107,
               const float ap[7], int mass, float d_out[8], float t_out[2]);
```

## 输入参数

| 参数         | 类型          | 描述                                              |
|-------------|---------------|---------------------------------------------------|
| `iyd`       | int           | 日期，格式 YYYYDDD（如 1990172）                  |
| `sec`       | float         | 世界时秒数（0-86400）                             |
| `alt_km`    | float / array | 高度（km），可从地表（0 km）到热层                |
| `lat_deg`   | float / array | 地理纬度（度）                                    |
| `lon_deg`   | float / array | 地理经度（度）                                    |
| `stl_hours` | float         | 地方太阳时（小时）                                |
| `f107a`     | float         | 81 天平均 F10.7 太阳通量                         |
| `f107`      | float         | 前一天的 F10.7 太阳通量                          |
| `ap7`       | array-like    | 可选 7 元素 Ap 历史；默认 `[4.0] * 7`            |
| `mass`      | int           | 质量数选择器；默认 `48`（所有物种）               |

## 输出

`calculate()` 返回包含以下字段的字典：

| 字段         | 类型          | 描述                              |
|-------------|---------------|-----------------------------------|
| `alt_km`    | float / ndarray | 输出高度                        |
| `T_local_K` | float / ndarray | 高度处温度（K）                 |
| `T_exo_K`   | float / ndarray | 外逸层温度（K）                 |
| `densities` | ndarray       | 形状 `(..., 8)`：He, O, N2, O2, Ar, 总质量, H, N |

## 使用示例

### 单点计算

```python
from model import MSISE90

model = MSISE90()
result = model.calculate(
    iyd=1990172,
    sec=29000.0,
    alt_km=400.0,
    lat_deg=60.0,
    lon_deg=-70.0,
    stl_hours=16.0,
    f107a=150.0,
    f107=150.0,
)

print(f"外逸层温度: {result['T_exo_K']:.1f} K")
print(f"局部温度: {result['T_local_K']:.1f} K")
print(f"O 密度: {result['densities'][1]:.3e} cm-3")
```

### 地面计算

```python
result = model.calculate(
    iyd=1990172,
    sec=29000.0,
    alt_km=0.0,  # 地面
    lat_deg=60.0,
    lon_deg=-70.0,
    stl_hours=16.0,
    f107a=150.0,
    f107=150.0,
)

print(f"地面温度: {result['T_local_K']:.1f} K")
print(f"N2 密度: {result['densities'][2]:.3e} cm-3")
```

### 批量计算

```python
import numpy as np

altitudes = np.linspace(0.0, 500.0, 11)
result = model.calculate(
    iyd=1990172,
    sec=29000.0,
    alt_km=altitudes,
    lat_deg=60.0,
    lon_deg=-70.0,
    stl_hours=16.0,
    f107a=150.0,
    f107=150.0,
)

print(result["T_local_K"].shape)    # (11,)
print(result["densities"].shape)    # (11, 8)
```

## 构造函数参数

| 参数         | 默认值        | 描述                      |
|-------------|---------------|---------------------------|
| `dll_path`  | 自动检测      | 自定义 DLL 路径           |

## MASS 参数

`mass` 参数选择要计算的物种：

| 值  | 描述                        |
|-----|-----------------------------|
| 0   | 仅温度                      |
| 1   | H                           |
| 4   | He                          |
| 14  | N                           |
| 16  | O                           |
| 28  | N2                          |
| 32  | O2                          |
| 40  | Ar                          |
| 48  | 所有物种 + 总质量           |
| 49  | O2 + 总质量                 |
