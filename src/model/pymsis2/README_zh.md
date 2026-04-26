# NRLMSIS 2.0 — 全大气层经验温度与中性粒子密度模型

[English](README.md)

## 模型背景

NRLMSIS 2.0 是美国海军研究实验室（NRL）开发的全大气层经验模型，用于计算从地表到低外逸层的温度和中性粒子密度。它是 NRLMSISE-00 的重大升级版本，于 2020 年正式发布。

与上一代 NRLMSISE-00 相比，NRLMSIS 2.0 的主要改进包括：

- **全大气层覆盖**：将模型从高层大气扩展至整个大气层（地面至低外逸层），引入了大量对流层、平流层和中间层的新观测数据。
- **改进的物种分离表示**：通过高度相关的有效质量来表示从完全混合大气到扩散分离的过渡。
- **C² 连续的温度剖面**：温度剖面在所有高度上二阶连续可导。
- **全局重力位高度函数**：内部采用全局重力位高度函数。
- **扩展的原子氧**：原子氧延伸至 50 km；85 km 以下使用与温度解耦的三次 B 样条表示。
- **新增 NO 密度输出**（预留，当前版本尚未激活）。

**参考文献**：
> Emmert, J.T., Drob, D. P., Picone, J. M., Siskind, D. E., Jones Jr., M., et al. (2020). NRLMSIS 2.0: A whole-atmosphere empirical model of temperature and neutral species densities. *Earth and Space Science*.

**适用高度范围**：地面 ~ 1000 km

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `day` | float / array | 年内积日（1.0 ~ 365/366），可使用 `utils.time.doy(year, month, day)` 获取 |
| `utsec` | float / array | 世界时秒数（0 ~ 86400），可使用 `utils.time.seconds_of_day(h, m, s)` 获取 |
| `alt_km` | float / array | 地理高度（km） |
| `lat_deg` | float / array | 地理纬度（度，-90 ~ 90） |
| `lon_deg` | float / array | 地理经度（度，-180 ~ 180） |
| `f107a` | float / array | F10.7 太阳射电流量 81 天均值（sfu） |
| `f107` | float / array | 前一日 F10.7 太阳射电流量日值（sfu） |
| `ap7` | list / array | 地磁活动指数数组，长度 7（可选，默认全为 4.0） |

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
| `densities` | ndarray | 密度数组，形状为 `(10,)` 或 `(N, 10)` |

### `densities` 数组各元素含义

| 索引 | 含义 | 单位 |
|------|------|------|
| `[0]` | 总质量密度 | kg/m³ |
| `[1]` | N₂ 数密度 | m⁻³ |
| `[2]` | O₂ 数密度 | m⁻³ |
| `[3]` | O 数密度 | m⁻³ |
| `[4]` | He 数密度 | m⁻³ |
| `[5]` | H 数密度 | m⁻³ |
| `[6]` | Ar 数密度 | m⁻³ |
| `[7]` | N 数密度 | m⁻³ |
| `[8]` | 异常氧数密度 | m⁻³ |
| `[9]` | 预留（NO 数密度，未来版本启用） | m⁻³ |

> **注意**：NRLMSIS 2.0 的密度输出单位为 **国际单位制**（kg/m³、m⁻³），与 NRLMSISE-00 的 CGS 单位制（g/cm³、cm⁻³）不同，使用时请注意区分。

## 用法示例

```python
from model import MSIS2
from utils.time import doy, seconds_of_day

model = MSIS2(precision="single")

result = model.calculate(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=250.0,
    lat_deg=39.9,
    lon_deg=116.4,
    f107a=150.0,
    f107=150.0,
    ap7=[4.0] * 7,
)

print(f"局地温度: {result['T_local_K']:.1f} K")
print(f"外逸层温度: {result['T_exo_K']:.1f} K")
print(f"总质量密度: {result['densities'][0]:.2e} kg/m³")
print(f"O 数密度: {result['densities'][3]:.2e} m⁻³")
```

### 批量计算

所有输入参数均支持 NumPy 数组，自动进行广播：

```python
import numpy as np

batch = model.calculate(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=np.linspace(50, 500, 10),
    lat_deg=39.9,
    lon_deg=116.4,
    f107a=150.0,
    f107=150.0,
)

# batch["T_local_K"] 的形状为 (10,)
# batch["densities"] 的形状为 (10, 10)
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `precision` | `"single"` | 计算精度，可选 `"single"` 或 `"double"` |
| `dll_path` | 自动检测 | 自定义 DLL 路径 |
| `data_dir` | 自动下载 | MSIS2 参数数据目录 |
| `auto_download` | `True` | 是否在数据缺失时自动下载 |
| `add_mingw_bin` | `False` | 是否添加 MinGW bin 目录到 DLL 搜索路径（Windows） |
