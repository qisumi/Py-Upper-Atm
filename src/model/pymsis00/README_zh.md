# NRLMSISE-00 — 经验中性大气模型

[English](README.md)

## 模型背景

NRLMSISE-00 是美国海军研究实验室（NRL）开发的经验中性大气模型，用于计算从地表到低外逸层的温度和中性粒子密度。该模型发布于 2000 年，是 MSIS 系列模型（MSIS-86、MSISE-90）的后续版本。

NRLMSISE-00 的主要特点：

- **丰富的数据基础**：使用了大量卫星阻力数据对模型进行拟合，显著改善了热层密度的精度。
- **修订的低热层 O₂ 和 O**：改进了低热层区域氧分子和氧原子的密度分布。
- **新增非线性太阳活动项**：引入了额外的太阳活动非线性修正。
- **异常氧（Anomalous Oxygen）**：在高海拔（> 500 km），热原子氧或电离氧对卫星阻力有显著影响。模型将这些物种统称为"异常氧"，其数密度通过输出数组 `D(9)` 返回。

**参考文献**：
> Picone, J. M., Hedin, A. E., Drob, D. P., & Aikin, A. C. (2002). NRLMSISE-00 empirical model of the atmosphere: Statistical comparisons and scientific issues. *Journal of Geophysical Research: Space Physics*, 107(A12).

**适用高度范围**：地面 ~ 1000 km

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `iyd` | int / array | 年积日，格式为 YYYYDDD（如 `2023001`），年份在当前模型中实际被忽略 |
| `sec` | float / array | 世界时秒数（0 ~ 86400） |
| `alt_km` | float / array | 海拔高度（km） |
| `lat_deg` | float / array | 地理纬度（度） |
| `lon_deg` | float / array | 地理经度（度） |
| `stl_hours` | float / array | 地方视太阳时（小时，0 ~ 24）。通常可取 `sec/3600 + lon_deg/15` |
| `f107a` | float / array | F10.7 太阳射电流量 81 天均值（sfu） |
| `f107` | float / array | 前一日 F10.7 太阳射电流量日值（sfu） |
| `ap7` | list / array | 地磁活动指数数组，长度 7（可选，默认全为 4.0） |
| `mass` | int | 质量数，默认 48 表示计算所有物种；设为特定物种的质量数则只计算该物种（可选） |
| `use_anomalous_o` | bool | 是否在总质量密度中包含异常氧的贡献（默认 `False`） |

### `ap7` 数组含义

| 索引 | 含义 |
|------|------|
| `[0]` | 当日 Ap 日均值 |
| `[1]` | 当前时刻的 3 小时 ap 指数 |
| `[2]` | 当前时刻前 3 小时的 3 小时 ap 指数 |
| `[3]` | 当前时刻前 6 小时的 3 小时 ap 指数 |
| `[4]` | 当前时刻前 9 小时的 3 小时 ap 指数 |
| `[5]` | 前 12~33 小时内 8 个 3 小时 ap 指数的均值 |
| `[6]` | 前 36~57 小时内 8 个 3 小时 ap 指数的均值 |

## 输出

`calculate()` 返回一个字典，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `alt_km` | float / ndarray | 输入高度 |
| `T_local_K` | float / ndarray | 指定高度处的局地温度（K） |
| `T_exo_K` | float / ndarray | 外逸层温度（K） |
| `densities` | ndarray | 密度数组，形状为 `(9,)` 或 `(N, 9)` |

### `densities` 数组各元素含义

| 索引 | 含义 | 单位 |
|------|------|------|
| `[0]` | He 数密度 | cm⁻³ |
| `[1]` | O 数密度 | cm⁻³ |
| `[2]` | N₂ 数密度 | cm⁻³ |
| `[3]` | O₂ 数密度 | cm⁻³ |
| `[4]` | Ar 数密度 | cm⁻³ |
| `[5]` | 总质量密度 | g/cm³ |
| `[6]` | H 数密度 | cm⁻³ |
| `[7]` | N 数密度 | cm⁻³ |
| `[8]` | 异常氧数密度 | cm⁻³ |

> **关于 D(6) 总质量密度**：当 `use_anomalous_o=False`（默认，调用 GTD7）时，总质量密度包含 He、O、N₂、O₂、Ar、H、N 的质量密度之和，**不包含**异常氧。当 `use_anomalous_o=True`（调用 GTD7D）时，总质量密度为"有效阻力总质量密度"，**包含**异常氧的贡献。

> **注意**：NRLMSISE-00 的密度输出使用 **CGS 单位制**（g/cm³、cm⁻³），与 NRLMSIS 2.0 的国际单位制不同，使用时请注意区分。

## 用法示例

```python
from model import MSIS00

model = MSIS00()

result = model.calculate(
    iyd=2023001,
    sec=12.0 * 3600,
    alt_km=200.0,
    lat_deg=40.0,
    lon_deg=-75.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
)

print(f"局地温度: {result['T_local_K']:.1f} K")
print(f"外逸层温度: {result['T_exo_K']:.1f} K")
print(f"O 数密度: {result['densities'][1]:.2e} cm⁻³")
print(f"总质量密度: {result['densities'][5]:.2e} g/cm³")
```

### 包含异常氧的高海拔计算

```python
result = model.calculate(
    iyd=2023001,
    sec=43200.0,
    alt_km=600.0,
    lat_deg=0.0,
    lon_deg=0.0,
    stl_hours=12.0,
    f107a=200.0,
    f107=200.0,
    use_anomalous_o=True,
)
# result["densities"][5] 包含异常氧的有效总质量密度
```

### 批量计算

```python
import numpy as np

batch = model.calculate(
    iyd=2023001,
    sec=43200.0,
    alt_km=np.linspace(100, 500, 5),
    lat_deg=40.0,
    lon_deg=-75.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
)
# batch["densities"] 的形状为 (5, 9)
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |
| `data_dir` | — | 预留参数（MSISE-00 不需要外部数据文件） |
| `auto_download` | `True` | 预留参数 |
