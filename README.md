# Py-Upper-Atm

Python高层大气模型库，提供温度、密度和风场参数计算功能。

## 简介

UpperAtmPy 是一个用于计算高层大气参数的Python库，集成了国际知名的大气模型：

- **NRLMSIS-2.0** - 用于计算大气的温度和各成分密度（氮气、氧气、原子氧等）
- **HWM14/HWM93** - 用于计算高层大气的经向风和纬向风

该项目通过Fortran-to-Python接口封装，提供易用的Python API，支持单点和批量计算，适用于大气物理学、空间天气、卫星轨道研究等领域。

## 特性

- 🌡️ **温度密度模型** - 基于NRLMSIS-2.0，计算0-1000km高度的温度和10种大气成分密度
- 💨 **风场模型** - 基于HWM14/HWM93，计算80-500km高度的经向风和纬向风
- 🚀 **高性能计算** - 支持Fortran编译的DLL，提供高效的数值计算
- 📊 **批量处理** - 支持向量化批量计算，可处理大规模数据
- 🔧 **简单易用** - 提供简洁的Python接口，支持单精度和双精度计算
- 📚 **文档完善** - 包含详细的使用文档和示例代码

## 安装

### 前置条件

- Python 3.7+
- numpy

### 安装步骤

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/Py-Upper-Atm.git
cd Py-Upper-Atm
```

2. 编译Fortran模型（可选，如已提供预编译DLL可跳过）：

```bash
# 编译MSIS2模型
cd model/pymsis2
./compile.sh  # Linux/Mac
# 或
compile.ps1  # Windows

# 编译HWM14模型
cd ../pyhwm14
./compile.sh  # Linux/Mac
# 或
compile.ps1  # Windows
```

3. 验证安装：

```bash
python quick_run.py
```

## 快速开始

### 温度密度模型

```python
from model import TempDensityModel, convert_date_to_day, calculate_seconds_of_day

# 创建模型实例
model = TempDensityModel()

# 准备时间参数
day_of_year = convert_date_to_day(2023, 1, 1)  # 2023年1月1日
seconds_of_day = calculate_seconds_of_day(12, 0, 0)  # 12:00:00 UTC

# 单点计算
result = model.calculate_point(
    day=day_of_year,
    utsec=seconds_of_day,
    alt_km=100.0,       # 高度（公里）
    lat_deg=35.0,       # 纬度（度）
    lon_deg=116.0,      # 经度（度）
    f107a=100.0,        # 81天平均F10.7太阳通量
    f107=100.0,         # 当天F10.7太阳通量
)

# 获取结果
print(f"局部温度: {result.T_local_K:.2f} K")
print(f"外温度: {result.T_exo_K:.2f} K")
print(f"N2密度: {result.densities[0]:.2e} cm^-3")
print(f"O密度: {result.densities[2]:.2e} cm^-3")
```

### 风场模型

```python
from model import WindModel

# 创建模型实例
model = WindModel()

# 单点计算
meridional_wind, zonal_wind = model.calculate_point(
    iyd=2023001,        # 日历年+儒略日（YYYYDDD）
    sec=43200.0,        # UTC秒（0-86400）
    alt_km=100.0,       # 高度（公里）
    glat_deg=35.0,      # 纬度（度）
    glon_deg=116.0,     # 经度（度）
    stl_hours=12.0,     # 本地太阳时（小时）
    f107a=100.0,        # 81天平均F10.7太阳通量
    f107=100.0,         # 当天F10.7太阳通量
    ap2=(0.0, 20.0)     # 地磁活动指数
)

print(f"经向风: {meridional_wind:.2f} m/s")
print(f"纬向风: {zonal_wind:.2f} m/s")
```

### 批量计算

```python
# 批量计算多个高度
altitudes = [80.0, 100.0, 120.0, 150.0]

batch_results = model.calculate_batch(
    day=day_of_year,
    utsec=seconds_of_day,
    alt_km=altitudes,
    lat_deg=35.0,
    lon_deg=116.0,
    f107a=100.0,
    f107=100.0,
)

for res in batch_results:
    print(f"高度: {res.alt_km} km, 温度: {res.T_local_K} K")
```

## 项目结构

```
Py-Upper-Atm/
├── model/                    # 主模型代码
│   ├── temp_density_model.py # 温度密度模型接口
│   ├── wind_model.py         # 风场模型接口
│   ├── pymsis2/              # NRLMSIS-2.0 Fortran源码和封装
│   ├── pymsis00/             # NRLMSIS-00 Fortran源码和封装
│   ├── pyhwm14/              # HWM14 Fortran源码和封装
│   └── pyhwm93/              # HWM93 Fortran源码和封装
├── example/                  # 示例代码
│   ├── test_hwm14.py         # HWM14测试
│   ├── test_hwm93.py         # HWM93测试
│   ├── test_msis00.py        # MSIS00测试
│   ├── test_msis20.py        # MSIS20测试
│   └── grid_*.py             # 网格计算示例
├── docs/                     # 文档
│   └── QUICK_START.md        # 快速开始指南
├── utils/                    # 工具函数
│   └── netcdf2csv.py         # NetCDF转CSV工具
├── hwm14data/                # HWM14模型数据文件
├── msis2data/                # MSIS2模型数据文件
├── quick_run.py              # 快速运行示例
└── README.md                 # 本文件
```

## 参数说明

### 时间参数

- **温度密度模型**：
  - `day`: 年内日数（1-366），可通过 `convert_date_to_day(year, month, day)` 计算
  - `utsec`: UTC时间（秒，0-86400），可通过 `calculate_seconds_of_day(hour, minute, second)` 计算

- **风场模型**：
  - `iyd`: 日历年+儒略日（格式为YYYYDDD）
  - `sec`: UTC时间（秒，0-86400）
  - `stl_hours`: 本地太阳时（小时，0-24）

### 位置参数

- `alt_km`: 高度（公里）
- `lat_deg`/`glat_deg`: 纬度（度，北纬为正）
- `lon_deg`/`glon_deg`: 经度（度，东经为正）

### 太阳活动和地磁参数

- `f107a`: 81天平均F10.7太阳通量
- `f107`: 当天F10.7太阳通量
- `ap7`（温度密度模型）: 长度为7的地磁活动指数数组
- `ap2`（风场模型）: 长度为2的地磁活动指数数组

## 结果说明

### 温度密度模型结果

`TempDensityResult` 对象包含以下属性：

- `alt_km`: 高度（公里）
- `T_local_K`: 局部温度（开尔文）
- `T_exo_K`: 外温度（开尔文）
- `densities`: 各成分数密度（10^6 cm^-3），顺序为：
  1. N2（氮气）
  2. O2（氧气）
  3. O（原子氧）
  4. He（氦气）
  5. H（氢气）
  6. Ar（氩气）
  7. N（原子氮）
  8. AnomalousO（异常氧）
  9. NO（一氧化氮）
  10. NPlus（氮离子）

### 风场模型结果

- 返回值为元组 `(经向风, 纬向风)`，单位均为 m/s
- **经向风**（南北向）：正值表示向北，负值表示向南
- **纬向风**（东西向）：正值表示向东，负值表示向西

## 注意事项

1. 确保模型DLL文件在正确的位置或通过参数指定
2. 对于批量计算，所有数组参数需要能够广播到共同形状
3. 输入参数单位必须正确：高度为公里，角度为度，时间为秒
4. 太阳活动和地磁指数应使用实际观测值以获得准确结果
5. HWM模型需要设置 `HWMPATH` 环境变量指向数据文件目录

## 文档

详细的使用文档请查看 [docs/QUICK_START.md](docs/QUICK_START.md)

## 示例代码

完整的使用示例：

- [`quick_run.py`](quick_run.py) - 快速运行示例，展示基本用法
- [`example/test_hwm14.py`](example/test_hwm14.py) - HWM14模型测试
- [`example/test_msis20.py`](example/test_msis20.py) - NRLMSIS-2.0模型测试
- [`example/grid_hwm.py`](example/grid_hwm.py) - 风场网格计算示例
- [`example/grid_msis.py`](example/grid_msis.py) - 温度密度网格计算示例

## 模型来源

本项目集成的模型来自以下开源项目：

- **NRLMSIS-2.0**: [NRLMSIS-2.0](https://ccmc.gsfc.nasa.gov/models/modelinfo.php?model=NRLMSIS-2.0) - NASA Community Coordinated Modeling Center
- **HWM14**: [HWM14](https://ccmc.gsfc.nasa.gov/models/modelinfo.php?model=HWM14) - NASA Community Coordinated Modeling Center
- **HWM93**: HWM93 经典风场模型
- **NRLMSIS-00**: NRLMSIS-00 经典模型

## 许可证

本项目遵循相关模型的许可协议。请参考各子模块的许可证文件。

## 贡献

欢迎提交问题和拉取请求！

## 联系方式

如有问题或建议，请提交Issue或Pull Request。