# MSIS2H2O — 带 Aura MLS 水汽气候态的 NRLMSIS 2.0

[English](README.md)

`model.MSIS2H2O` 完整保留原 `MSIS2` 的四个输出，并增加水汽体积混合比和
水分子数密度。它将 NRLMSIS 2.0 干大气状态与 NASA Aura MLS
`ML3MBH2O` V005 在 2005–2024 年的年度 Level-3 文件构建成的确定性月气候态
结合起来。

这是固定的多年逐月气候态，不是输入年份的天气或逐日卫星实况。MLS 仅在建议的
316–0.00215 hPa 压力范围内作为观测气候态使用。更低压力处（通常约 90–120 km）
使用受约束的 log(VMR)-log(p) 尾部，并始终返回
`H2O_extrapolated=True`；这部分不能宣传为观测精度。

## 输入和构造参数

`calculate(...)` 与 `MSIS2` 使用相同的仅关键字输入并支持 NumPy 广播：`day`、
`utsec`、`alt_km`、`lat_deg`、`lon_deg`、`f107a`、`f107` 和可选
`ap7`。`alt_km` 限定为 20–120 km。

构造函数沿用所有 `MSIS2` 选项，并新增 `h2o_data_path=None`，可直接指定紧凑
气候态文件。默认通过 UpperAtmPy 模型数据机制解析
`msis2h2odata/mls_ml3mbh2o_v005_2005-2024_climatology.npz`。

## 输出

原 MSIS2 字段 `alt_km`、`T_local_K`、`T_exo_K` 和 `densities` 完全保留，
其中 `densities` 末维仍为 10。新增字段如下：

| 字段 | 单位 / 含义 |
|---|---|
| `total_number_density_m3` | N2、O2、O、He、H、Ar、N 和异常氧之和，m^-3 |
| `pressure_Pa` | `N_total * k_B * T_local`，Pa |
| `H2O_vmr_ppmv` | 水汽气候态体积混合比，ppmv |
| `H2O_number_density_m3` | 水分子数密度，m^-3 |
| `H2O_number_density_cm3` | 水分子数密度，cm^-3 |
| `H2O_extrapolated` | 压力低于 MLS 顶部 0.00215 hPa |
| `H2O_latitude_clamped` | 纬度被夹到最近的 ±82° MLS 边界 |
| `H2O_climatology_fallback` | 至少一个插值角点使用了纬圈加权均值修复 |

模型在月中点时间、纬度、周期经度和压力四维插值，并在
log(VMR)-log(p) 空间进行线性插值；`utsec` 提供日内小数部分。年度 Level-3
`average` 先在线性 VMR 空间按 `nvalues` 加权，合法的负年度检索均值不会被提前
丢弃。

## 示例

```python
from model import MSIS2H2O

model = MSIS2H2O(precision="single")
result = model.calculate(
    day=196, utsec=43200, alt_km=[50, 90, 120],
    lat_deg=35, lon_deg=116, f107a=100, f107=100,
)
print(result["H2O_number_density_cm3"])
print(result["H2O_extrapolated"])
```

## 可复现构建和致谢

开发期构建脚本为 `tools/build_msis2h2o_climatology.py`，运行时只依赖 NumPy。
固定源清单记录 20 个 CMR granule ID、URL、输入 SHA-256、输出 SHA-256 和产品
DOI。

使用结果时请同时引用 NRLMSIS 2.0 和 NASA Aura MLS。MLS 产品 DOI：
`10.5067/Aura/MLS/DATA/3538`。
