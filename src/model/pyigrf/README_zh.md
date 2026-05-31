# IGRF — 国际地磁参考场模型

[English](README.md)

## 模型背景

国际地磁参考场（International Geomagnetic Reference Field, IGRF）是国际标准化的地球主磁场球谐模型。本模块将 Fortran 实现编译为共享库，并通过 `ctypes` 封装为 `IGRF` 类，遵循项目统一的 `Model.calculate(...)` 接口。

该封装同时支持 IGRF-13 和 IGRF-14。默认使用 IGRF-14，其 2025.0 历元系数和长期变化项可用于 2030.0 之前的外推估计。L-shell 参数由随源码提供的 `SHELLG` 子程序计算。

模型需要外部系数文件。数据路径统一通过 `utils.model_data.ensure_model_data()` 解析，因此可以使用自动下载、`UPPERATMPY_DATA_DIR` 环境变量，或构造函数中的 `data_dir` 参数。

## 目录结构

```text
pyigrf/
├── igrf.for           # Fortran 77 IGRF 与 SHELLG 子程序
├── igrf_cshim.F90     # 供 ctypes 调用的 C ABI shim
├── CMakeLists.txt     # CMake 构建目标 igrf
├── __init__.py        # Python Model 类
├── README.md          # 英文文档
└── README_zh.md       # 中文文档
```

## Fortran 接口

`igrf.for` 中的核心子程序：

| 子程序 | 功能 |
|--------|------|
| `FELDCOF(YEAR, DIMO)` | 读取 DGRF/IGRF 系数并计算偶极矩。 |
| `FELDG(GLAT, GLON, ALT, BNORTH, BEAST, BDOWN, BABS)` | 球谐合成北向、东向、下向和总磁场分量，单位为 Gauss。 |
| `SHELLG(GLAT, GLON, ALT, DIMO, FL, ICODE, B0)` | 计算 L-shell 参数。 |
| `GETSHC(IU, FSPEC, NMAX, ERAD, GH, IER)` | 从配置的数据目录读取系数文件。 |

C ABI 适配层导出：

```c
void igrf_set_data_root(const char *path);
void igrf_set_version(int ver);
void igrf_eval(float xlat, float xlong, float year, float height,
               float *bnorth, float *beast, float *bdown, float *babs,
               float *xl, int *icode);
```

Fortran 层返回的磁场分量单位为 Gauss。Python 封装会转换为 nT，并计算水平强度、磁倾角和磁偏角。

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `year` | float / array | 十进制年份，例如 `2024.5`。 |
| `lat_deg` | float / array | 地理纬度，单位为度，北纬为正。 |
| `lon_deg` | float / array | 地理经度，单位为度，东经为正。 |
| `alt_km` | float / array | 海拔高度，单位为 km。 |

标量输入返回标量结果；数组输入会按 NumPy 广播规则计算，并返回同广播形状的数组。

## 输出

`calculate()` 返回一个字典，包含以下字段：

| 字段 | 单位 / 类型 | 说明 |
|------|-------------|------|
| `year` | float / ndarray | 广播后的输入年份。 |
| `lat_deg` | float / ndarray | 广播后的输入纬度。 |
| `lon_deg` | float / ndarray | 广播后的输入经度。 |
| `alt_km` | float / ndarray | 广播后的输入高度。 |
| `B_north_nT` | nT | 北向磁场分量。 |
| `B_east_nT` | nT | 东向磁场分量。 |
| `B_down_nT` | nT | 下向磁场分量，垂直向下为正。 |
| `B_abs_nT` | nT | 总磁场强度。 |
| `H_nT` | nT | 水平磁场强度。 |
| `inclination_deg` | 度 | 磁倾角，向下为正。 |
| `declination_deg` | 度 | 磁偏角，东偏为正。 |
| `L_value` | 无量纲 | `SHELLG` 计算得到的 L-shell 参数。 |
| `icode` | int / ndarray | L 值状态码：`1` 正常，`2` 共轭点异常，`3` 近似值。 |

## 用法示例

### 单点计算

```python
from model import IGRF

model = IGRF(igrf_version=14)
result = model.calculate(
    year=2024.5,
    lat_deg=39.9,
    lon_deg=116.4,
    alt_km=0.0,
)

print(f"总磁场: {result['B_abs_nT']:.1f} nT")
print(f"磁偏角: {result['declination_deg']:.2f} deg")
print(f"L 值:   {result['L_value']:.3f}")
```

### 批量计算

```python
from model import IGRF

model = IGRF()
result = model.calculate(
    year=2024.5,
    lat_deg=[30.0, 40.0, 50.0],
    lon_deg=[116.0, 116.0, 116.0],
    alt_km=[0.0, 100.0, 200.0],
)

print(result["B_abs_nT"].shape)  # (3,)
print(result["L_value"])
```

### 离线使用本地数据

```python
from model import IGRF

model = IGRF(
    igrf_version=14,
    data_dir="C:/path/to/UPPERATMPY_DATA_DIR",
    auto_download=False,
)
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 `igrf.dll` 或 `libigrf.so` 路径。 |
| `igrf_version` | `14` | IGRF 版本，可选 `13` 或 `14`。 |
| `data_dir` | 自动解析 | 包含 `igrf13data/` 或 `igrf14data/` 的数据根目录。 |
| `auto_download` | `True` | 缺失系数文件时是否自动下载。 |

## 系数数据

数据根目录中包含按版本划分的系数文件目录：

```text
UPPERATMPY_DATA_DIR/
├── igrf13data/
└── igrf14data/
```

IGRF-13 使用到 2020.0 的 DGRF/IGRF 系数，并包含 2020-2025 的长期变化项。IGRF-14 使用更新后的 DGRF-2020、IGRF-2025 以及 2025-2030 的长期变化系数。

## 参考文献

- Alken, P., Thébault, E., Beggan, C. D., et al. (2021). International Geomagnetic Reference Field: the thirteenth generation. *Earth, Planets and Space*, 73, 49. https://doi.org/10.1186/s40623-020-01288-x
- IGRF-14 专题合辑：https://link.springer.com/collections/jecafgcbaf
