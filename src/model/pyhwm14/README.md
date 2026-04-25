# HWM14 — 水平风模型（2014 版）

## 模型背景

HWM14（Horizontal Wind Model 2014）是美国海军研究实验室（NRL）开发的经验水平风场模型，用于计算从地面到约 500 km 高度的中性大气水平风速。它是 HWM 系列模型（HWM87、HWM90、HWM93、HWM07）的最新版本。

HWM14 的主要特点：

- **更广的高度覆盖**：将模型上界从 HWM07 的 ~500 km 略作扩展，向下延伸至地面。
- **大量新观测数据**：利用了卫星测风数据（如 DE-2、UARS/WINDII、TIMED/TIDI、CHAMP/STAR 等）以及地面雷达和激光雷达数据。
- **改进的经向风和纬向风**：修正了先前版本在高纬度和中间层的系统性偏差。
- **全大气层一致性**：可与 NRLMSIS 2.0 搭配使用，提供温度-密度-风场的一致性描述。

**参考文献**：
> Drob, D. P., Emmert, J. T., Meriwether, J. W., Makela, J. J., Doornbos, E., et al. (2015). An update to the Horizontal Wind Model (HWM): The quiet time thermosphere. *Earth and Space Science*, 2(7), 301-319.

**适用高度范围**：地面 ~ 500 km

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `iyd` | int / array | 年积日，格式为 YYYYDDD（如 `2025290`） |
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
from model import HWM14

model = HWM14()

result = model.calculate(
    iyd=2025290,
    sec=43200.0,
    alt_km=250.0,
    glat_deg=30.0,
    glon_deg=114.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
    ap2=(0.0, 20.0),
)

print(f"经向风: {result['meridional_wind_ms']:.3f} m/s")
print(f"纬向风: {result['zonal_wind_ms']:.3f} m/s")
```

### 批量计算（经纬度网格）

```python
import numpy as np

lat = np.linspace(-60, 60, 5)
lon = np.linspace(0, 360, 9)
lat_grid, lon_grid = np.meshgrid(lat, lon, indexing="ij")

result = model.calculate(
    iyd=2025290,
    sec=43200.0,
    alt_km=250.0,
    glat_deg=lat_grid,
    glon_deg=lon_grid,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
)

# result["meridional_wind_ms"].shape == (5, 9)
# result["zonal_wind_ms"].shape == (5, 9)
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |
| `data_dir` | 自动下载 | HWM14 数据文件目录 |
| `auto_download` | `True` | 是否在数据缺失时自动下载 |
