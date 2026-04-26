# HWM93 — 水平风模型（1993 版）

[English](README.md)

## 模型背景

HWM93（Horizontal Wind Model 1993）是美国海军研究实验室（NRL）与 NASA/GSFC 合作开发的早期经验水平风场模型，用于计算中间层和低热层的中性大气水平风速。它是 HWM 系列模型中广泛使用的一个版本。

HWM93 的主要特点：

- **专注中间层和低热层**：模型对 0 ~ 500 km 高度范围的水平风进行了经验拟合，但在中间层和低热层（~80 ~ 200 km）的数据约束最为充分。
- **多数据源融合**：使用了包括 AE-C、AE-D、AE-E、DE-2 等卫星的质谱仪/非相干散射数据，以及地面非相干散射雷达观测。
- **地磁活动修正**：支持通过地磁指数（Ap）对高纬度风场进行修正。

> **注意**：HWM93 是较早版本的模型，在高纬度、高海拔以及强地磁活动条件下的精度有限。如果需要更高的精度，建议使用 HWM14。

**参考文献**：
> Hedin, A. E., Fleming, E. L., Manson, A. H., Schmidlin, F. J., Avery, S. K., et al. (1996). Empirical wind model for the upper, middle and lower atmosphere. *Journal of Atmospheric and Terrestrial Physics*, 58(13), 1421-1447.

**适用高度范围**：地面 ~ 500 km

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `iyd` | int / array | 年积日，格式为 YYYYDDD（如 `2023001`） |
| `sec` | float / array | 世界时秒数（0 ~ 86400） |
| `alt_km` | float / array | 海拔高度（km） |
| `glat_deg` | float / array | 地理纬度（度） |
| `glon_deg` | float / array | 地理经度（度） |
| `stl_hours` | float / array | 地方视太阳时（小时，0 ~ 24） |
| `f107a` | float / array | F10.7 太阳射电流量 81 天均值（sfu） |
| `f107` | float / array | 前一日 F10.7 太阳射电流量日值（sfu） |
| `ap2` | tuple / array | 地磁活动指数，长度 2（可选，默认 `(0.0, 20.0)`） |

### `ap2` 数组含义

| 索引 | 含义 |
|------|------|
| `[0]` | 当日 Ap 日均值 |
| `[1]` | 当前 3 小时 ap 指数 |

## 输出

`calculate()` 返回一个字典，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `alt_km` | float / ndarray | 输入高度 |
| `meridional_wind_ms` | float / ndarray | 经向风速（m/s），正值表示北向风 |
| `zonal_wind_ms` | float / ndarray | 纬向风速（m/s），正值表示东向风 |

## 用法示例

```python
from model import HWM93

model = HWM93()

result = model.calculate(
    iyd=2023001,
    sec=0.0,
    alt_km=100.0,
    glat_deg=40.0,
    glon_deg=116.0,
    stl_hours=0.0,
    f107a=150.0,
    f107=150.0,
    ap2=(4.0, 4.0),
)

print(f"经向风: {result['meridional_wind_ms']:.3f} m/s")
print(f"纬向风: {result['zonal_wind_ms']:.3f} m/s")
```

### 多高度批量计算

```python
result = model.calculate(
    iyd=2023001,
    sec=43200.0,
    alt_km=[50.0, 100.0, 150.0, 200.0, 250.0],
    glat_deg=40.0,
    glon_deg=116.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
    ap2=(4.0, 4.0),
)

for alt, wm, wz in zip(
    result["alt_km"],
    result["meridional_wind_ms"],
    result["zonal_wind_ms"],
):
    print(f"高度 {alt:.0f} km: 经向风={wm:.3f} m/s, 纬向风={wz:.3f} m/s")
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |
| `data_dir` | — | 预留参数（HWM93 不需要外部数据文件） |
| `auto_download` | `True` | 预留参数 |

## 与 HWM14 的对比

| 特性 | HWM93 | HWM14 |
|------|-------|-------|
| 发布年份 | 1993 | 2014 |
| 观测数据量 | 较少 | 大幅增加 |
| 高纬度精度 | 有限 | 显著改善 |
| 低热层精度 | 良好 | 良好 |
| 地磁修正 | 基础 | 更完善 |
| 外部数据文件 | 不需要 | 需要 |
