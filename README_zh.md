# UpperAtmPy

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT%20%2B%20third--party%20terms-blue)

**UpperAtmPy** 为高层大气模型 DLL 和数据表提供 Python 直接调用封装。项目使用 `src/` 布局，每个模型只公开一个类接口。

支持模型：

- **MSIS2**：NRLMSIS-2.0 温度和密度
- **MSIS00**：NRLMSISE-00 温度和密度
- **HWM14**：水平风场模型 2014
- **HWM93**：水平风场模型 1993
- **AuroraOval**：Feldstein 极光卵边界模型（Holzworth & Meng 参数化）
- **IGRF**：国际地磁参考场 13/14，计算地磁场分量和 L 值
- **CIRA86**：COSPAR 国际参考大气 1986，0-120 km 月平均表格
- **MSIS86**：MSIS-86 / CIRA-86 热层模型 — 85 km 以上中性大气温度和密度
- **MSISE90**：MSISE-90 中性大气模型 — 将 MSIS-86 向下延伸至地面
- **Jacchia77**：Jacchia 1977 参考大气 — 90–2500 km 温度和数密度剖面（N2, O2, O, Ar, He, H）
- **MET**：马歇尔工程热层模型 — 改进的 Jacchia 1970 热层模型，面向工程应用
- **Chiu**：Chiu 电离层电子密度模型 — E、F1、F2 层电子密度（90–500 km）
- **Tsyganenko**：Tsyganenko 磁层磁场模型（T89/T96/T01/TS04）— GSM 坐标系外源磁场
- **SOLPRO**：1 AU 行星际太阳质子积分通量 — 基于任务时长和置信水平

## 特性

- 每个模型只有一个公开接口：`Model.calculate(...)`。
- `model` 顶层只懒加载导出：`MSIS2`、`MSIS00`、`HWM14`、`HWM93`、`AuroraOval`、`IGRF`、`CIRA86`、`MSIS86`、`MSISE90`、`Jacchia77`、`MET`、`Chiu`、`Tsyganenko`、`SOLPRO`。
- 单点和 numpy 广播批量输入共用同一个方法。
- 输出统一为普通 `dict`。
- 缓存、并行、时间、xarray 等工具放在 `utils` 包。

## 许可证

UpperAtmPy 原创的 Python 封装、构建文件、测试、示例和文档使用 MIT
License。第三方模型源码和数据不会被 UpperAtmPy 重新授权，仍受其上游条款约束；
详见 [LICENSE](LICENSE) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

特别是 `src/model/pymsis2/` 下的 NRLMSIS 2.0 文件带有美国政府 / Naval
Research Laboratory 的上游学术、非商业使用条款。重新分发或非学术使用前，请先检查
其上游声明。

## 构建

在源码环境下构建前，请先安装以下工具链与依赖。

### 构建前置依赖

- Python 3.8+
- CMake（3.20+）
- C/C++ 编译器工具链
- GNU Fortran 编译器（`gfortran`）
- `pip` 依赖库

通用安装命令：

```bash
python -m pip install -r requirements.txt
```

#### Linux（Ubuntu/Debian）

```bash
sudo apt update
sudo apt install -y python3 python3-pip cmake build-essential gfortran git
```

#### macOS

```bash
brew install python cmake gcc
```

#### Windows

请先安装：

- Python
- CMake
- MinGW-w64 工具链（提供 `gfortran`），并确保 MinGW 运行时目录（如
  `...\\mingw64\\bin`）在 `PATH` 中可见

示例：

```powershell
winget install -e --id Python.Python.3
winget install -e --id Kitware.CMake
winget install -e --id MSYS2.MSYS2
```

然后在 MSYS2/MinGW shell 中执行：

```bash
pacman -S --noconfirm --needed mingw-w64-x86_64-toolchain
```

### 源码构建

从源码目录使用模型前，先统一编译原生库。请确保执行 CMake 的终端已正确加载上述编译器。

```bash
cmake --preset native-release
cmake --build --preset native-release
```

### 预编译包安装

如果不方便自行编译，可直接从仓库的 `Releases` 页面下载对应平台的预编译 `.whl` 文件并安装。

1. 选择与当前系统和架构匹配的 wheel 文件，例如：
   - `upperatmpy-0.2.0-py3-none-win_amd64.whl`
   - `upperatmpy-0.2.0-py3-none-manylinux_x86_64.whl`
2. 安装本地 wheel 文件

```bash
python -m pip install /path/to/upperatmpy-0.2.0-py3-none-win_amd64.whl
```

快速判断规则：

- `py3-none-win_amd64`：可安装到 Windows x86_64 下任意支持的 Python 3.x（如 3.8~3.12）。
- `py3-none-manylinux_x86_64`：可安装到 Linux x86_64 下任意支持的 Python 3.x（如 3.8~3.12）。
- `py3-none-any`（若有）：可安装到任意平台且同 major Python 3 的解释器。

或者直接从 release 直链安装：

```bash
python -m pip install https://github.com/<OWNER>/<REPO>/releases/download/<TAG>/<WHEEL_FILENAME>.whl
```

安装完成后从 `model` 导入模型类。各模型的构造参数、`calculate(...)` 签名、输入输出字段和示例见
[模型文档](#模型文档)。

## 数据文件

MSIS2、HWM14、IGRF、CIRA86 和 MSIS86 需要外部模型数据。默认情况下，UpperAtmPy 会解析当前项目目录下的
`.upperatmpy`，并在存在下载清单时于首次实例化模型时按当前包版本的 release tag（如 `v0.2.0`）下载缺失文件。
CIRA86 当前使用本地 `cira86data/` ASCII 表。离线使用时，
可以传入 `data_dir=...`，或设置 `UPPERATMPY_DATA_DIR` 指向包含 `msis2data/`、
`hwm14data/`、`igrf13data/`、`igrf14data/` 和 `cira86data/` 子目录的数据根目录。源码树中的统一数据根目录是 `data/`。

可通过环境变量 `UPPERATMPY_DATA_TAG` 指定数据下载所用的 Release tag。

### 手动下载 release data 文件

如果不能在运行时联网自动下载模型数据，可直接从 `GitHub Releases` 手动下载：

1. 打开 release 页面，下载 `msis2data`、`hwm14data`、`igrf13data`、`igrf14data` 以及发布后可用的 `cira86data` 资源文件（或一个合并压缩包）。
2. 解压后确保目录结构如下（数据根目录中包含所需子目录）：

```text
UPPERATMPY_DATA_DIR/
├── msis2data/
├── msis86data/
├── hwm14data/
├── igrf13data/
├── igrf14data/
└── cira86data/
```

3. 设置环境变量或直接在构造模型时指定 `data_dir`。

Linux/macOS 示例：

```bash
export UPPERATMPY_DATA_DIR=/path/to/UPPERATMPY_DATA_DIR
```

Windows PowerShell 示例：

```powershell
$env:UPPERATMPY_DATA_DIR = "C:\path\to\UPPERATMPY_DATA_DIR"
```

## API

`model` 顶层只导出：

- `MSIS2`
- `MSIS00`
- `HWM14`
- `HWM93`
- `AuroraOval`
- `IGRF`
- `CIRA86`
- `MSIS86`
- `MSISE90`
- `Jacchia77`
- `MET`
- `Chiu`
- `Tsyganenko`
- `SOLPRO`

每个类都提供 `calculate(...)`，返回普通字典。
模型计算方法同时支持标量和可广播数组输入，输入标量返回标量结果，输入数组会按 numpy 广播返回对应形状。

### 时间工具

- `utils.time.doy(year, month, day)`：返回一年中的第几天（1-366）。
- `utils.time.seconds_of_day(hour, minute=0, second=0.0)`：返回当日秒数。

## 模型文档

`src/model/` 下每个模型目录都包含各自的 `README_zh.md`，详细说明模型背景、Fortran 接口、构造参数、输入输出参数和用法示例：

- [NRLMSIS 2.0](src/model/pymsis2/README_zh.md)
- [NRLMSISE-00](src/model/pymsis00/README_zh.md)
- [HWM14](src/model/pyhwm14/README_zh.md)
- [HWM93](src/model/pyhwm93/README_zh.md)
- [AuroraOval](src/model/pyaurora/README_zh.md)
- [IGRF](src/model/pyigrf/README_zh.md)
- [CIRA86](src/model/pycira86/README_zh.md)
- [MSIS86](src/model/pymsis86/README_zh.md)
- [MSISE90](src/model/pymsise90/README_zh.md)
- [Jacchia77](src/model/pyjacchia77/README_zh.md)
- [MET](src/model/pymet/README_zh.md)
- [Chiu](src/model/pychiu/README_zh.md)
- [Tsyganenko](src/model/pytsyganenko/README_zh.md)
- [SOLPRO](src/model/pysolpro/README_zh.md)

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

#### `utils.cache`

作用：给任意可调用对象加缓存，减少重复计算。

- `cached_call(func, cache_size=10000)`：返回带缓存的可调用对象。
- 封装后的对象提供 `cache_info()` 与 `cache_clear()`。

#### `utils.parallel`

作用：对大量独立参数的批量计算做线程并行。

- `parallel_map(func, items, max_workers=None, show_progress=False)`
- `parallel_batch_compute(compute_func, param_dicts, max_workers=None, show_progress=False)`

#### `utils.xarray_output`

作用：将模型输出字典转换为 `xarray.Dataset`，便于后续可视化和 NetCDF 导出。

- `msis_to_xarray(result, species_names=None, attrs=None)`
- `hwm_to_xarray(result, attrs=None)`

## 项目结构

```text
UpperAtmPy/
├── src/
│   ├── model/
│   │   ├── __init__.py      # 懒加载别名：MSIS2, MSIS00, HWM14, HWM93, AuroraOval, IGRF, CIRA86, MSIS86, MSISE90, Jacchia77, MET, Chiu, Tsyganenko, SOLPRO
│   │   ├── pymsis2/         # NRLMSIS-2.0 封装和 Fortran 源码
│   │   ├── pymsis00/        # NRLMSISE-00 封装和 Fortran 源码
│   │   ├── pyhwm14/         # HWM14 封装和 Fortran 源码
│   │   ├── pyhwm93/         # HWM93 封装和 Fortran 源码
│   │   ├── pyaurora/        # Feldstein 极光卵（Holzworth & Meng）
│   │   ├── pyigrf/          # IGRF-13/14 地磁场封装
│   │   ├── pycira86/        # CIRA-86 表格封装
│   │   ├── pymsis86/        # MSIS-86 热层模型封装
│   │   ├── pymsise90/       # MSISE-90 中性大气封装
│   │   ├── pyjacchia77/     # Jacchia 1977 参考大气封装
│   │   ├── pymet/           # 马歇尔工程热层模型封装
│   │   ├── pychiu/          # Chiu 电离层电子密度模型封装
│   │   ├── pytsyganenko/    # Tsyganenko 磁层磁场模型封装（T89/T96/T01/TS04）
│   │   └── pysolpro/        # SOLPRO 太阳质子通量模型封装
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
│   ├── igrf13data/
│   ├── igrf14data/
│   ├── cira86data/
│   ├── msis2data/
│   └── msis86data/
└── ROADMAP.md
```

`src/model/` 下每个模型目录都包含模型专属的英文和中文 README。见
[模型文档](#模型文档)。

## 测试

```bash
python -m pytest
```
