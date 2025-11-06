# DQZNMX-interface 开发指南

## 项目概述

DQZNMX-interface 是一个大气环境模型接口项目，提供了对多个经典大气模型的 Python 封装，主要包括：

- **HWM93** - 1993年版本的水平风场模型 (Horizontal Wind Model)
- **HWM14** - 2014年版本的水平风场模型，是 HWM93 的更新版本
- **NRLMSIS-2.0** - 美国海军研究实验室质谱非相干散射雷达模型，用于计算大气温度和密度

该项目通过 C 接口封装 Fortran 模型，提供了简洁易用的 Python API，支持单点计算和批量计算功能，适用于大气科学研究和相关应用开发。

## 目录结构

项目采用清晰的分层结构，将模型实现、接口封装和测试代码分离。整体架构设计遵循模块化原则，便于维护和扩展。

```plaintext
DQZNMX-interface/
├── interface/               # 模型接口层
│   ├── pyhwm14interface.py  # HWM14 模型接口
│   └── pymsis2interface.py  # NRLMSIS-2.0 模型接口
├── model/                   # 核心模型实现
│   ├── pyhwm14/             # HWM14 模型封装
│   │   ├── __init__.py      # Python 接口入口
│   │   ├── hwm14.f90        # 原始 Fortran 模型代码
│   │   ├── hwm_cshim.F90    # C 接口封装
│   │   ├── compile.ps1      # PowerShell 编译脚本
│   │   └── hwm14.dll        # 编译后的动态链接库
│   ├── pyhwm93/             # HWM93 模型封装
│   │   ├── __init__.py      # Python 接口入口
│   │   ├── hwm93.f          # 原始 Fortran 模型代码
│   │   ├── hwm93_cshim.F90  # C 接口封装
│   │   └── compile.ps1      # PowerShell 编译脚本
│   └── pymsis2/             # NRLMSIS-2.0 模型封装
│       ├── __init__.py      # Python 接口入口
│       ├── msis_calc.F90    # 模型计算核心
│       ├── msis_cshim.F90   # C 接口封装
│       ├── compile.ps1      # PowerShell 编译脚本
│       └── msis2.0.parm     # 模型参数文件
├── hwm123114.bin            # HWM14 模型所需数据文件
├── dwm07b104i.dat           # DWM07 模型数据文件
├── gd2qd.dat                # 地理坐标转换数据文件
├── msis2.0.parm             # MSIS2.0 模型参数文件
├── test_hwm14.py            # HWM14 测试脚本
├── test_hwm93.py            # HWM93 测试脚本
├── test_msis20.py           # MSIS2.0 测试脚本
├── 使用方法.md              # 使用说明文档
└── DEVELOP_GUIDE.md         # 开发指南（本文档）
```

## 核心模块功能介绍

### 1. HWM93 (Horizontal Wind Model 1993)

HWM93 是一个经典的水平风场模型，用于计算中层和上层大气的风速。

- **主要功能**：计算指定位置、时间和太阳活动条件下的经向风和纬向风分量
- **适用高度范围**：约 50-2000 km
- **输入参数**：年积日、UTC秒、高度、地理纬度、地理经度、地方视太阳时、F10.7太阳辐射通量、地磁指数
- **输出结果**：经向风速 (wm) 和纬向风速 (wz)，单位为 m/s

### 2. HWM14 (Horizontal Wind Model 2014)

HWM14 是 HWM93 的更新版本，提供了更精确的风场预测。

- **主要功能**：与 HWM93 类似，但模型精度和适用范围有所提升
- **新增特性**：包含了更多的观测数据校准，改进了低纬度和高纬度地区的模型表现
- **输入输出**：与 HWM93 保持一致，便于用户从旧版本迁移

### 3. NRLMSIS-2.0 (Naval Research Laboratory Mass Spectrometer and Incoherent Scatter Radar Model)

NRLMSIS-2.0 是一个用于计算中性大气温度和成分密度的经验模型。

- **主要功能**：计算指定条件下的大气温度和各成分密度
- **适用高度范围**：约 0-1000 km
- **可计算成分**：包含 N₂、O₂、O、He、Ar、H、N、O₊、NO₊、电子密度等
- **输入参数**：年积日、UTC秒、高度、地理纬度、地理经度、F10.7太阳辐射通量、地磁指数
- **输出结果**：局地温度、外层温度和各成分密度

## 关键文件用途说明

### 接口文件

- **interface/pyhwm14interface.py**：HWM14 模型的高级接口封装
- **interface/pymsis2interface.py**：NRLMSIS-2.0 模型的高级接口封装

### 模型实现文件

- **model/pyhwm14/__init__.py**：HWM14 Python 接口入口，提供 `hwm14_eval()` 和 `hwm14_eval_many()` 函数
- **model/pyhwm93/__init__.py**：HWM93 Python 接口入口，提供 `hwm93_eval()` 和 `hwm93_eval_many()` 函数
- **model/pymsis2/__init__.py**：NRLMSIS-2.0 Python 接口入口，提供 `NRLMSIS2` 类及相关方法
- **model/pyhwm14/hwm14.f90**：HWM14 模型的核心 Fortran 实现
- **model/pyhwm93/hwm93.f**：HWM93 模型的核心 Fortran 实现
- **model/pymsis2/msis_calc.F90**：NRLMSIS-2.0 模型的计算核心

### 接口封装文件

- **model/pyhwm14/hwm_cshim.F90**：HWM14 的 C 接口封装，实现 Fortran 到 C 的转换
- **model/pyhwm93/hwm93_cshim.F90**：HWM93 的 C 接口封装
- **model/pymsis2/msis_cshim.F90**：NRLMSIS-2.0 的 C 接口封装

### 编译脚本

- **model/pyhwm14/compile.ps1**：HWM14 模型的 PowerShell 编译脚本
- **model/pyhwm93/compile.ps1**：HWM93 模型的 PowerShell 编译脚本
- **model/pymsis2/compile.ps1**：NRLMSIS-2.0 模型的 PowerShell 编译脚本

### 测试文件

- **test_hwm14.py**：HWM14 模型的功能测试脚本
- **test_hwm93.py**：HWM93 模型的功能测试脚本
- **test_msis20.py**：NRLMSIS-2.0 模型的功能测试脚本

### 数据文件

- **hwm123114.bin**：HWM14 模型所需的参数数据文件
- **dwm07b104i.dat**：DWM07 模型数据文件，用于地磁活动期间的风场修正
- **gd2qd.dat**：地理坐标到地磁坐标转换的数据文件
- **msis2.0.parm**：NRLMSIS-2.0 模型的参数数据文件

## 技术栈构成

### 编程语言

- **Fortran**：原始模型实现语言，高性能科学计算
- **Python**：提供用户友好的接口和数据处理功能
- **C**：用于实现 Fortran 和 Python 之间的接口转换

### 核心依赖

- **Python 3.8+**：运行环境
- **NumPy**：用于数值计算和数组处理（可选，但推荐）
- **gfortran**：Fortran 编译器，用于编译模型代码
- **ctypes**：Python 标准库，用于调用 C 接口

## 开发环境配置指南

### 1. 安装 Python

确保安装 Python 3.8 或更高版本，并安装 pip 包管理器。

### 2. 安装依赖

```bash
pip install numpy
```

### 3. 安装 Fortran 编译器

在 Windows 系统上，推荐使用 MinGW-w64 提供的 gfortran 编译器：

1. 下载并安装 MinGW-w64
2. 将 MinGW-w64 的 bin 目录添加到系统 PATH 环境变量中

### 4. 编译模型

进入每个模型目录，运行相应的编译脚本：

```powershell
# 编译 HWM93
cd model/pyhwm93
./compile.ps1

# 编译 HWM14
cd ../pyhwm14
./compile.ps1

# 编译 NRLMSIS-2.0
cd ../pymsis2
./compile.ps1
```

### 5. 环境变量配置

- **HWMPATH**：指向 HWM 模型数据文件所在目录（默认自动设置为 `model/pyhwm14/data`）

## 代码规范要求

### Python 代码规范

1. **命名规范**：
   - 模块名：使用小写字母，单词间用下划线分隔
   - 函数名：使用小写字母，单词间用下划线分隔
   - 类名：使用驼峰命名法
   - 变量名：使用小写字母，单词间用下划线分隔

2. **代码格式**：
   - 使用 4 个空格进行缩进
   - 每行不超过 100 个字符
   - 函数和方法之间用两个空行分隔
   - 导入语句分组，标准库在前，第三方库次之，本地模块最后

3. **文档字符串**：
   - 所有模块、函数和类都应有文档字符串
   - 文档字符串应说明功能、参数、返回值和示例用法

### Fortran 代码规范

1. **命名规范**：
   - 模块名和子程序名使用有意义的英文名称
   - 变量名应反映其物理意义或用途

2. **注释规范**：
   - 关键算法和参数应有详细注释
   - 子例程和函数应有功能说明

3. **接口规范**：
   - C 接口应使用 `bind(C)` 属性
   - 参数类型应明确指定

## 使用指南

### 1. HWM93 使用示例

```python
import model.pyhwm93 as pyhwm93

# 单点计算
wm, wz = pyhwm93.hwm93_eval(
    iyd=2023001,      # 年积日
    sec=0.0,          # UTC 秒
    alt_km=100.0,     # 高度（公里）
    glat_deg=40.0,    # 地理纬度（度）
    glon_deg=116.0,   # 地理经度（度）
    stl_hours=0.0,    # 地方视太阳时（小时）
    f107a=150.0,      # 3个月平均F10.7太阳辐射通量
    f107=150.0,       # 前一天F10.7太阳辐射通量
    ap2=(4.0, 4.0),   # 地磁指数
)
print(f"经向风={wm:.3f} m/s, 纬向风={wz:.3f} m/s")

# 批量计算（需要 NumPy）
import numpy as np
lat = np.linspace(-60, 60, 5)
lon = np.linspace(0, 360, 9)
LAT, LON = np.meshgrid(lat, lon, indexing="ij")

wm, wz = pyhwm93.hwm93_eval_many(
    iyd=2023001,
    sec=43200.0,
    alt_km=100.0,
    glat_deg=LAT,
    glon_deg=LON,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
    ap2=(4.0, 4.0),
)
```

### 2. HWM14 使用示例

```python
import model.pyhwm14 as pyhwm14

# 单点计算
wm, wz = pyhwm14.hwm14_eval(
    iyd=2025290,      # 年积日
    sec=43200.0,      # UTC 秒（正午）
    alt_km=250.0,
    glat_deg=30.0,
    glon_deg=114.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
    ap2=(0.0, 20.0),
)
print(f"wm={wm:.3f} m/s, wz={wz:.3f} m/s")

# 批量计算
wm, wz = pyhwm14.hwm14_eval_many(
    iyd=2025290,
    sec=43200.0,
    alt_km=250.0,
    glat_deg=LAT,  # 使用上面定义的 LAT 数组
    glon_deg=LON,  # 使用上面定义的 LON 数组
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
    ap2=(0.0, 20.0),
)
```

### 3. NRLMSIS-2.0 使用示例

```python
from model.pymsis2 import NRLMSIS2, doy, seconds_of_day

msis = NRLMSIS2(precision="single")

# 单点计算
res = msis.calc(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12, 0, 0.0),
    alt_km=250.0, lat_deg=39.9, lon_deg=116.4,
    f107a=150.0, f107=150.0,
    ap7=[4.0]*7,
)
print(f"高度={res.alt_km} km, 局地温度={res.T_local_K} K, 外层温度={res.T_exo_K} K")

# 批量计算
results = msis.calc_many(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12),
    alt_km=[50, 100, 150, 200, 250],
    lat_deg=39.9, lon_deg=116.4,
    f107a=150.0, f107=150.0,
    out_numpy=True,  # 返回 NumPy 数组
)
```

## 测试

项目提供了三个测试脚本，用于验证各模型功能是否正常：

```powershell
# 测试 HWM93
python test_hwm93.py

# 测试 HWM14
python test_hwm14.py

# 测试 NRLMSIS-2.0
python test_msis20.py
```

测试脚本会检查以下内容：

1. 单点计算结果是否有效（非 NaN 或 Inf）
2. 批量计算是否正确处理数组输入
3. 计算结果是否在物理合理范围内

## 常见问题与解决方案

### 1. DLL 加载失败

**问题**：Python 无法加载模型 DLL

**解决方案**：
- 确保已成功编译模型，生成了对应的 DLL 文件
- 检查 DLL 文件是否在正确的位置
- 确保 MinGW-w64 的 bin 目录在系统 PATH 环境变量中

### 2. 数据文件找不到

**问题**：模型报告找不到数据文件

**解决方案**：
- 检查数据文件是否存在于正确的位置
- 对于 HWM14，确保 `HWMPATH` 环境变量指向包含数据文件的目录

### 3. 计算结果异常

**问题**：计算结果包含 NaN 或超出合理范围

**解决方案**：
- 检查输入参数是否在模型适用范围内
- 确保所有输入参数类型正确（应为浮点数）
- 对于批量计算，检查数组维度是否正确

## 开发与扩展

### 添加新模型

1. 在 `model/` 目录下创建新的模型文件夹
2. 将模型的 Fortran 代码放入该文件夹
3. 创建 C 接口封装文件（xxx_cshim.F90）
4. 编写 Python 接口（__init__.py）
5. 创建编译脚本
6. 编写测试脚本

### 改进现有接口

1. 修改相应的 Python 接口文件
2. 如需修改底层模型，更新 Fortran 代码并重新编译
3. 更新测试脚本以验证修改

## 版本历史

当前版本：0.1.0

## 许可信息

请参考各模型的原始许可协议。