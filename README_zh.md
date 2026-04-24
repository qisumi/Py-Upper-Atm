# UpperAtmPy

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Placeholder-lightgrey)

**UpperAtmPy** 为高层大气模型 DLL 提供 Python 直接调用封装。项目使用 `src/` 布局，每个模型只公开一个类接口。

支持模型：

- **MSIS2**：NRLMSIS-2.0 温度和密度
- **MSIS00**：NRLMSISE-00 温度和密度
- **HWM14**：水平风场模型 2014
- **HWM93**：水平风场模型 1993

## 特性

- 每个模型只有一个公开接口：`Model.calculate(...)`。
- `model` 顶层只懒加载导出：`MSIS2`、`MSIS00`、`HWM14`、`HWM93`。
- 单点和 numpy 广播批量输入共用同一个方法。
- 输出统一为普通 `dict`。
- 缓存、并行、时间、xarray 等工具放在 `utils` 包。

## 构建

使用哪个模型，就先编译对应 DLL。

```powershell
cd src/model/pymsis2
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../../..

cd src/model/pymsis00
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../../..

cd src/model/pyhwm14
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../../..

cd src/model/pyhwm93
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../../..
```

## 快速开始

```python
from model import HWM14, MSIS2
from utils.time import doy, seconds_of_day

msis = MSIS2(precision="single")
atmosphere = msis.calculate(
    day=doy(2023, 1, 1),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=[100.0, 200.0, 300.0],
    lat_deg=35.0,
    lon_deg=116.0,
    f107a=100.0,
    f107=100.0,
)
print(atmosphere["T_local_K"])
print(atmosphere["densities"])

hwm = HWM14()
wind = hwm.calculate(
    iyd=2023001,
    sec=43200.0,
    alt_km=100.0,
    glat_deg=35.0,
    glon_deg=116.0,
    stl_hours=12.0,
    f107a=100.0,
    f107=100.0,
)
print(wind["meridional_wind_ms"], wind["zonal_wind_ms"])
```

## API

`model` 顶层只导出：

- `MSIS2`
- `MSIS00`
- `HWM14`
- `HWM93`

每个类都提供 `calculate(...)`，返回字典。

MSIS 字典字段：

- `alt_km`
- `T_local_K`
- `T_exo_K`
- `densities`

HWM 字典字段：

- `alt_km`
- `meridional_wind_ms`
- `zonal_wind_ms`

时间工具：

```python
from utils.time import doy, seconds_of_day
```

可选工具模块：

- `utils.cache`
- `utils.parallel`
- `utils.space_weather`
- `utils.xarray_output`
- `utils.netcdf2csv`

## 项目结构

```text
UpperAtmPy/
├── src/
│   ├── model/
│   │   ├── __init__.py      # 懒加载别名：MSIS2, MSIS00, HWM14, HWM93
│   │   ├── pymsis2/         # NRLMSIS-2.0 封装和构建脚本
│   │   ├── pymsis00/        # NRLMSISE-00 封装和构建脚本
│   │   ├── pyhwm14/         # HWM14 封装和构建脚本
│   │   └── pyhwm93/         # HWM93 封装和构建脚本
│   └── utils/
│       ├── cache.py
│       ├── parallel.py
│       ├── space_weather.py
│       ├── time.py
│       └── xarray_output.py
├── example/
├── tests/
├── hwm14data/
└── quick_run.py
```

## 测试

```bash
python -m pytest
python quick_run.py
```
