# UpperAtmPy

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Placeholder-lightgrey)

**UpperAtmPy** 是一个用于高层大气模型的统一 Python 接口，封装了标准的 Fortran 实现，用于高效计算中性温度、密度和水平风场。

该库通过 `ctypes` 绑定支持以下模型：
- **NRLMSIS-2.0** (美国海军研究实验室质谱仪和非相干散射雷达模型, 2020)
- **NRLMSISE-00** (传统的 MSIS-00 模型)
- **HWM14** (水平风场模型 2014)
- **HWM93** (水平风场模型 1993)

## 特性

- **统一的 Python API**: 为所有温度/密度和风场模型提供一致的接口。
- **跨平台支持**: 支持 Windows、Linux 和 macOS，提供 PowerShell 和 Bash 编译脚本。
- **高性能**: 通过 `ctypes` 直接调用 Fortran 动态库。
- **批量处理**: 内置支持使用 `numpy` 进行向量化处理。
- **并行计算**: 提供多线程并行计算支持，加速大规模批量计算。
- **结果缓存**: 内置 LRU 缓存机制，避免重复计算。
- **空间天气数据**: 自动获取 F10.7、Ap 等地磁活动指数。
- **xarray 集成**: 将计算结果转换为 xarray Dataset，便于后续分析。
- **类型安全**: 提供全面的类型提示 (Type Hints) 和结果数据类 (Dataclasses)。
- **无重依赖**: 核心功能仅依赖 `numpy`。

## 环境要求

- **操作系统**: Windows / Linux / macOS
- **Python**: 3.8+
- **编译器**: gfortran (MinGW on Windows)
- **Python 依赖**:
  - `numpy` (必须)
  - `xarray` (可选，用于数据转换)
  - `pandas` (可选，用于数据工具)
  - `tqdm` (可选，用于进度条显示)

## 安装与构建

本项目直接从源码运行。在使用库之前，您必须编译 Fortran DLL。

### 1. 克隆仓库
```bash
git clone https://github.com/qisumi/Py-Upper-Atm.git
cd Py-Upper-Atm
```

### 2. 编译动态库
本项目包含 PowerShell (Windows) 和 Bash (Linux/macOS) 编译脚本。

**Windows (PowerShell):**
```powershell
# 编译 NRLMSIS-2.0
cd model/pymsis2
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../..

# 编译 HWM14
cd model/pyhwm14
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../..
```

**Linux / macOS (Bash):**
```bash
# 编译 NRLMSIS-2.0
cd model/pymsis2
chmod +x compile.sh && ./compile.sh
cd ../..

# 编译 HWM14
cd model/pyhwm14
chmod +x compile.sh && ./compile.sh
cd ../..
```

*(如果需要，请重复此步骤以编译 `pyhwm93` 和 `pymsis00`)*

## 快速开始

### 温度和密度 (NRLMSIS-2.0)

```python
from model import TempDensityModel, convert_date_to_day, calculate_seconds_of_day

# Initialize model
model = TempDensityModel()

# Calculate parameters
day_of_year = convert_date_to_day(2023, 1, 1)
ut_seconds = calculate_seconds_of_day(12, 0, 0)  # 12:00:00 UTC

# Calculate for a single point
result = model.calculate_point(
    day=day_of_year,    # Day of year (1-366)
    utsec=ut_seconds,   # UTC seconds
    alt_km=100.0,       # Altitude in km
    lat_deg=35.0,       # Latitude
    lon_deg=116.0,      # Longitude
    f107a=100.0,        # 81-day average F10.7
    f107=100.0,         # Daily F10.7
    ap7=None            # Optional: Geomagnetic indices
)

print(f"Temperature: {result.T_local_K:.2f} K")
print(f"N2 Density: {result.densities[0]:.2e} cm^-3")
```

### 水平风场 (HWM14)

```python
from model import WindModel

# Initialize model
wind_model = WindModel()

# Calculate for a single point
# iyd format: YYYYDDD (e.g., 2023001 for Jan 1, 2023)
meridional, zonal = wind_model.calculate_point(
    iyd=2023001,
    sec=43200.0,        # 12:00:00 UTC
    alt_km=100.0,
    glat_deg=35.0,
    glon_deg=116.0,
    stl_hours=12.0,     # Local solar time
    f107a=100.0,
    f107=100.0,
    ap2=(0.0, 20.0)     # Geomagnetic indices
)

print(f"Meridional Wind (North/South): {meridional:.2f} m/s")
print(f"Zonal Wind (East/West): {zonal:.2f} m/s")
```

## API 概览

该库在 `model/__init__.py` 中暴露以下组件：

### 核心模型类

#### `TempDensityModel`
- `calculate_point(...)`: 计算单个位置/时间的温度和密度。
- `calculate_batch(...)`: 针对输入数组（例如高度剖面）的向量化计算。

#### `WindModel`
- `calculate_point(...)`: 计算经向和纬向风分量。
- `calculate_batch(...)`: 针对输入数组的向量化计算。

### 结果数据类
- `TempDensityResult`: 温度密度计算结果
- `WindResult`: 风场计算结果

### 缓存模型
- `CachedModel`: 带 LRU 缓存的温度密度模型包装器
- `CachedWindModel`: 带 LRU 缓存的风场模型包装器

### 空间天气
- `SpaceWeatherIndices`: 空间天气指数数据类
- `get_indices(date)`: 获取指定日期的空间天气指数

### 并行计算
- `parallel_map(func, items)`: 并行映射函数
- `parallel_batch_compute(compute_func, param_dicts)`: 并行批量计算

### xarray 集成
- `temp_density_results_to_xarray(results)`: 将温度密度结果转换为 xarray Dataset
- `wind_results_to_xarray(results)`: 将风场结果转换为 xarray Dataset

### 辅助函数
- `convert_date_to_day(year, month, day)`: 日期转年内日数
- `calculate_seconds_of_day(hour, minute, second)`: 时间转秒数
- `calculate_wind_at_point(...)`: 便捷风场计算函数
- `calculate_wind_batch(...)`: 便捷批量风场计算函数

## 项目结构

```
UpperAtmPy/
├── model/
│   ├── __init__.py           # 公共 API 导出
│   ├── temp_density_model.py # MSIS 的主封装类
│   ├── wind_model.py         # HWM 的主封装类
│   ├── cache.py              # 结果缓存模块
│   ├── parallel.py           # 并行计算模块
│   ├── space_weather.py      # 空间天气指数获取
│   ├── xarray_output.py      # xarray 数据转换
│   ├── pymsis2/              # NRLMSIS-2.0 Fortran 源码及构建脚本
│   ├── pymsis00/             # NRLMSISE-00 Fortran 源码及构建脚本
│   ├── pyhwm14/              # HWM14 Fortran 源码及构建脚本
│   └── pyhwm93/              # HWM93 Fortran 源码及构建脚本
├── example/                  # 使用脚本和测试
├── utils/                    # 数据处理工具
├── hwm14data/               # HWM14 的数据文件
└── quick_run.py             # 演示脚本
```

## 许可证 (License)
