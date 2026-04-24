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

从源码目录使用模型前，先统一编译原生库。

```bash
cmake --preset native-release
cmake --build --preset native-release
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

MSIS2 和 HWM14 需要外部模型数据。默认情况下，UpperAtmPy 会解析当前项目目录下的
`.upperatmpy`，并在首次实例化模型时根据项目维护的 release manifest 下载缺失文件。离线使用时，
可以传入 `data_dir=...`，或设置 `UPPERATMPY_DATA_DIR` 指向包含 `msis2data/`
和 `hwm14data/` 子目录的数据根目录。源码树中的统一数据根目录是 `data/`。

## API

`model` 顶层只导出：

- `MSIS2`
- `MSIS00`
- `HWM14`
- `HWM93`

每个类都提供 `calculate(...)`，返回普通字典。
模型计算方法同时支持标量和可广播数组输入，输入标量返回标量结果，输入数组会按 numpy 广播返回对应形状。

### 时间工具

```python
from utils.time import doy, seconds_of_day
```

- `doy(year, month, day)`：返回一年中的第几天（1-366）。
- `seconds_of_day(hour, minute=0, second=0.0)`：返回当日秒数。

### MSIS2.calculate

签名：

```python
MSIS2.calculate(*, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, ap7=None)
```

输入字段：

- `day`：年内日序号（`doy(...)` 的返回值），范围 1~366。
- `utsec`：UTC 秒，0~86400。
- `alt_km`：高度（公里），标量或数组。
- `lat_deg`：纬度（度）。
- `lon_deg`：经度（度）。
- `f107a`：81 天平均 F10.7 太阳通量。
- `f107`：当日 F10.7 太阳通量。
- `ap7`：可选，长度为 7 的地磁活动指数序列。缺省时默认 `[4.0] * 7`。

返回字段：

- `alt_km`：输出高度（同广播后的形状）。
- `T_local_K`：局地温度（K）。
- `T_exo_K`：外逸层温度（K）。
- `densities`：形状为 `(..., 10)` 的密度数组，物种顺序为：
  `N2, O2, O, He, H, Ar, N, AnomalousO, NO, NPlus`。

### MSIS00.calculate

签名：

```python
MSIS00.calculate(*, iyd, sec, alt_km, lat_deg, lon_deg, stl_hours, f107a, f107, ap7=None, mass=48, use_anomalous_o=False)
```

输入字段：

- `iyd`：日期，整数格式 `YYYYDDD`（如 `2023001`）。
- `sec`：UTC 秒，0~86400。
- `alt_km`：高度（公里），标量或数组。
- `lat_deg`：纬度（度）。
- `lon_deg`：经度（度）。
- `stl_hours`：地方太阳时（小时）。
- `f107a`：81 天平均 F10.7。
- `f107`：当日 F10.7。
- `ap7`：可选，长度为 7 的地磁活动指数序列。
- `mass`：可选，目标质量数选择，默认 `48`。
- `use_anomalous_o`：是否启用异常氧版本核算。

返回字段：

- `alt_km`：输出高度（同广播后的形状）。
- `T_local_K`：局地温度（K）。
- `T_exo_K`：外逸层温度（K）。
- `densities`：形状为 `(..., 9)` 的密度数组，物种顺序为：
  `He, O, N2, O2, Ar, H, N, AnomalousO, TotalMass`。

### HWM14.calculate 与 HWM93.calculate

二者签名一致：

```python
calculate(*, iyd, sec, alt_km, glat_deg, glon_deg, stl_hours, f107a, f107, ap2=(0.0, 20.0))
```

输入字段：

- `iyd`：日期，整数格式 `YYYYDDD`。
- `sec`：UTC 秒，0~86400。
- `alt_km`：高度（公里）。
- `glat_deg`：纬度（度）。
- `glon_deg`：经度（度）。
- `stl_hours`：地方太阳时（小时）。
- `f107a`：81 天平均 F10.7。
- `f107`：当日 F10.7。
- `ap2`：可选，长度为 2 的指数序列。

返回字段：

- `alt_km`：输出高度（同广播后的形状）。
- `meridional_wind_ms`：子午向风速（m/s）。
- `zonal_wind_ms`：纬向风速（m/s）。

### 可选工具模块

这些模块不会在 `import model` 时自动加载，需要时按需导入。

- `utils.cache`
- `utils.parallel`
- `utils.space_weather`
- `utils.xarray_output`
- `utils.netcdf2csv`

#### `utils.space_weather`

作用：拉取并缓存空间天气索引，用于构造模型地磁/太阳辐照参数。

- `get_indices(date=None, source="celestrak")`：返回当天（默认昨天 UTC）指数对象。
- `get_indices_celestrak(date)`：从 CelesTrak 获取指定日期。
- `clear_cache()`：清理本地缓存文件。
- `SpaceWeatherIndices`：
  - `as_msis_params()` 返回 `{ "f107", "f107a", "ap7" }`
  - `as_hwm_params()` 返回 `{ "f107", "f107a", "ap2" }`

示例：

```python
from model import MSIS2
from utils.time import doy, seconds_of_day
from utils.space_weather import get_indices

sw = get_indices()
msis = MSIS2(precision="single")
result = msis.calculate(
    day=doy(2023, 1, 1),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=100.0,
    lat_deg=35.0,
    lon_deg=116.0,
    **sw.as_msis_params(),
)
```

#### `utils.cache`

作用：给任意可调用对象加缓存，减少重复计算。

- `cached_call(func, cache_size=10000)`：返回带缓存的可调用对象。
- 封装后的对象提供 `cache_info()` 与 `cache_clear()`。

示例：

```python
from model import MSIS2
from utils.cache import cached_call

msis = MSIS2(precision="single")
cached_calc = cached_call(msis.calculate)
cached_calc(...)
cached_calc(...)
print(cached_calc.cache_info())
```

#### `utils.parallel`

作用：对大量独立参数的批量计算做线程并行。

- `parallel_map(func, items, max_workers=None, show_progress=False)`
- `parallel_batch_compute(compute_func, param_dicts, max_workers=None, show_progress=False)`

示例：

```python
from model import MSIS2
from utils.parallel import parallel_batch_compute
from utils.time import doy, seconds_of_day

msis = MSIS2(precision="single")
jobs = [
    dict(day=doy(2023,1,1), utsec=seconds_of_day(12,0,0),
         alt_km=a, lat_deg=35.0, lon_deg=116.0,
         f107a=100.0, f107=100.0)
    for a in [80.0, 100.0, 120.0]
]
results = parallel_batch_compute(msis.calculate, jobs, max_workers=4, show_progress=True)
```

#### `utils.xarray_output`

作用：将模型输出字典转换为 `xarray.Dataset`，便于后续可视化和 NetCDF 导出。

- `msis_to_xarray(result, species_names=None, attrs=None)`
- `hwm_to_xarray(result, attrs=None)`

示例：

```python
from utils.xarray_output import msis_to_xarray

ds = msis_to_xarray(result, attrs={"model": "MSIS2"})
```

## 项目结构

```text
UpperAtmPy/
├── src/
│   ├── model/
│   │   ├── __init__.py      # 懒加载别名：MSIS2, MSIS00, HWM14, HWM93
│   │   ├── pymsis2/         # NRLMSIS-2.0 封装和 Fortran 源码
│   │   ├── pymsis00/        # NRLMSISE-00 封装和 Fortran 源码
│   │   ├── pyhwm14/         # HWM14 封装和 Fortran 源码
│   │   └── pyhwm93/         # HWM93 封装和 Fortran 源码
│   └── utils/
│       ├── cache.py
│       ├── parallel.py
│       ├── space_weather.py
│       ├── time.py
│       └── xarray_output.py
├── example/
├── tests/
├── data/
│   ├── hwm14data/
│   └── msis2data/
└── quick_run.py
```

## 测试

```bash
python -m pytest
python quick_run.py
```
