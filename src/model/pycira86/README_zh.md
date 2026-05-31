# CIRA-86 模型封装

本目录提供 COSPAR International Reference Atmosphere 1986（CIRA-86）的
Python 表格封装，对外类名为 `model.CIRA86`。

## 模型背景

CIRA-86 是 COSPAR 推荐的国际参考大气模型。当前封装使用 `TODO/CIRA/cira86ascii`
中的 ASCII 修订表格，覆盖 0-120 km、80S-80N 的月平均纬向平均温度、纬向风、
气压和位势高度。

## 目录结构

```text
src/model/pycira86/
├── __init__.py      # CIRA86 的 Model 类和表格解析/插值逻辑
├── README.md
└── README_zh.md
```

实际数据表位于数据根目录的 `cira86data/` 子目录，例如源码树中的
`data/cira86data/`。

## 接口说明

CIRA-86 原始 Fortran `cirat.for` 是交互式表格显示程序，并依赖旧式 VAX/VMS
二进制文件。此封装直接读取官方 ASCII 修订表格，因此不需要额外 DLL。

```python
from model import CIRA86

cira = CIRA86(data_dir="data", auto_download=False)
result = cira.calculate(month=1, lat_deg=0.0, alt_km=100.0)
```

## 输入参数

`calculate` 只接受关键字参数：

```python
CIRA86.calculate(*, month, lat_deg, alt_km=None, pressure_mb=None)
```

- `month`：月份，1 至 12。
- `lat_deg`：地理纬度，北纬为正，范围 -80 至 80。
- `alt_km`：高度坐标，单位 km，范围 0 至 120。
- `pressure_mb`：气压坐标，单位 mb。

`alt_km` 与 `pressure_mb` 必须二选一，不能同时指定。

## 输出字段

高度坐标模式返回：

- `month`
- `alt_km`
- `lat_deg`
- `T_K`
- `zonal_wind_ms`
- `pressure_mb`

气压坐标模式返回：

- `month`
- `pressure_mb`
- `lat_deg`
- `T_K`
- `zonal_wind_ms`
- `geopotential_height_m`

标量输入返回 Python 标量；数组输入会按 numpy 广播返回同形状数组。

## 构造参数

- `data_dir`：可选数据根目录，应包含 `cira86data/`。
- `auto_download`：与其他数据模型保持一致的参数；当前本地源码树已包含数据表。

## 示例

```python
from pathlib import Path
from model import CIRA86

model = CIRA86(data_dir=Path("data"), auto_download=False)

height_result = model.calculate(month=7, lat_deg=40.0, alt_km=80.0)
print(height_result["T_K"], height_result["pressure_mb"])

pressure_result = model.calculate(month=1, lat_deg=0.0, pressure_mb=3.10e-4)
print(pressure_result["T_K"], pressure_result["geopotential_height_m"])
```

## 参考文献

- CIRA 1986, D. Rees (ed.), Advances in Space Research, Volume 8, Numbers 5-6, 1988.
- E. L. Fleming, S. Chandra, M. R. Schoeberl, and J. J. Barnett, NASA TM 100697, 1988.
