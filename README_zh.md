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

## 特性

- 每个模型只有一个公开接口：`Model.calculate(...)`。
- `model` 顶层只懒加载导出：`MSIS2`、`MSIS00`、`HWM14`、`HWM93`、`AuroraOval`、`IGRF`、`CIRA86`、`MSIS86`、`MSISE90`、`Jacchia77`、`MET`、`Chiu`。
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
   - `upperatmpy-0.1.0-py3-none-win_amd64.whl`
   - `upperatmpy-0.1.0-py3-none-manylinux_x86_64.whl`
2. 安装本地 wheel 文件

```bash
python -m pip install /path/to/upperatmpy-0.1.0-py3-none-win_amd64.whl
```

快速判断规则：

- `py3-none-win_amd64`：可安装到 Windows x86_64 下任意支持的 Python 3.x（如 3.8~3.12）。
- `py3-none-manylinux_x86_64`：可安装到 Linux x86_64 下任意支持的 Python 3.x（如 3.8~3.12）。
- `py3-none-any`（若有）：可安装到任意平台且同 major Python 3 的解释器。

或者直接从 release 直链安装：

```bash
python -m pip install https://github.com/<OWNER>/<REPO>/releases/download/<TAG>/<WHEEL_FILENAME>.whl
```

安装完成后可按平时方式直接使用：

```python
from model import MSIS2
from utils.time import doy, seconds_of_day

msis = MSIS2(precision="single")
_ = msis.calculate(day=doy(2023, 1, 1), utsec=seconds_of_day(12,0,0),
                  alt_km=100.0, lat_deg=35.0, lon_deg=116.0, f107a=100.0, f107=100.0)
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

MSIS2、HWM14、IGRF、CIRA86 和 MSIS86 需要外部模型数据。默认情况下，UpperAtmPy 会解析当前项目目录下的
`.upperatmpy`，并在存在下载清单时于首次实例化模型时按当前包版本的 release tag（如 `v0.1.1`）下载缺失文件。
CIRA86 当前使用本地 `cira86data/` ASCII 表，因此源码示例会显式传入 `data_dir=data/`。离线使用时，
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

代码中也可直接传入：

```python
from model import CIRA86, HWM14, IGRF, MSIS2

msis = MSIS2(precision="single", data_dir="C:/path/to/UPPERATMPY_DATA_DIR")
hwm = HWM14(data_dir="C:/path/to/UPPERATMPY_DATA_DIR")
igrf = IGRF(data_dir="C:/path/to/UPPERATMPY_DATA_DIR")
cira = CIRA86(data_dir="C:/path/to/UPPERATMPY_DATA_DIR")
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

### AuroraOval.calculate

签名：

```python
AuroraOval.calculate(*, mlt_hours, activity_level)
```

输入字段：

- `mlt_hours`：磁地方时（小时），标量或数组。
- `activity_level`：地磁活动等级，0（宁静）至 6（活跃）。

返回字段：

- `mlt_hours`：输入的 MLT 值。
- `activity_level`：输入的活动等级值。
- `poleward_boundary_deg`：极向边界修正地磁纬度（°）。
- `equatorward_boundary_deg`：赤道向边界修正地磁纬度（°）。

### IGRF.calculate

签名：

```python
IGRF.calculate(*, year, lat_deg, lon_deg, alt_km)
```

构造参数：

- `igrf_version`：`13` 或 `14`，默认 `14`。
- `data_dir`：可选数据根目录，包含 `igrf13data/` 和/或 `igrf14data/`。
- `auto_download`：缺失系数文件时是否自动下载。

输入字段：

- `year`：十进制年份，如 `2024.5`。
- `lat_deg`：地理纬度（度），北纬为正。
- `lon_deg`：地理经度（度），东经为正。
- `alt_km`：海拔高度（km）。

返回字段：

- `year`、`lat_deg`、`lon_deg`、`alt_km`：广播后的输入坐标。
- `B_north_nT`、`B_east_nT`、`B_down_nT`：磁场分量（nT）。
- `B_abs_nT`：总磁场强度（nT）。
- `H_nT`：水平磁场强度（nT）。
- `inclination_deg`：磁倾角，向下为正。
- `declination_deg`：磁偏角，东偏为正。
- `L_value`：L-shell 参数。
- `icode`：`SHELLG` 返回的 L 值状态码。

### CIRA86.calculate

签名：

```python
CIRA86.calculate(*, month, lat_deg, alt_km=None, pressure_mb=None)
```

构造参数：

- `data_dir`：可选数据根目录，包含 `cira86data/`。
- `auto_download`：与其他数据模型保持一致的参数。

输入字段：

- `month`：月份，1~12。
- `lat_deg`：地理纬度（度），北纬为正，范围 -80~80。
- `alt_km`：高度坐标输入（km），范围 0~120；与 `pressure_mb` 二选一。
- `pressure_mb`：气压坐标输入（mb）；与 `alt_km` 二选一。

返回字段：

- 高度模式：`month`、`alt_km`、`lat_deg`、`T_K`、`zonal_wind_ms`、`pressure_mb`。
- 气压模式：`month`、`pressure_mb`、`lat_deg`、`T_K`、`zonal_wind_ms`、`geopotential_height_m`。

### MSIS86.calculate

签名：

```python
MSIS86.calculate(*, iyd, sec, alt_km, lat_deg, lon_deg, stl_hours, f107a, f107, ap7=None, mass=48)
```

输入字段：

- `iyd`：日期，整数格式 `YYYYDDD`（如 `1987172`）。
- `sec`：UTC 秒，0~86400。
- `alt_km`：高度（公里），必须大于 85 km。
- `lat_deg`：纬度（度）。
- `lon_deg`：经度（度）。
- `stl_hours`：地方太阳时（小时）。
- `f107a`：81 天平均 F10.7 太阳通量。
- `f107`：前一天的 F10.7 太阳通量。
- `ap7`：可选，长度为 7 的地磁活动指数序列。
- `mass`：可选，目标质量数选择器，默认 `48`（所有物种）。

返回字段：

- `alt_km`：输出高度（同广播后的形状）。
- `T_local_K`：局地温度（K）。
- `T_exo_K`：外逸层温度（K）。
- `densities`：形状为 `(..., 8)` 的密度数组，物种顺序为：
  `He, O, N2, O2, Ar, TotalMass, H, N`。

### MSISE90.calculate

签名：

```python
MSISE90.calculate(*, iyd, sec, alt_km, lat_deg, lon_deg, stl_hours, f107a, f107, ap7=None, mass=48)
```

输入字段：

- `iyd`：日期，整数格式 `YYYYDDD`（如 `1990172`）。
- `sec`：UTC 秒，0~86400。
- `alt_km`：高度（公里），可从地面向上计算。
- `lat_deg`：纬度（度）。
- `lon_deg`：经度（度）。
- `stl_hours`：地方太阳时（小时）。
- `f107a`：81 天平均 F10.7 太阳通量。
- `f107`：前一天的 F10.7 太阳通量。
- `ap7`：可选，长度为 7 的地磁活动指数序列。
- `mass`：可选，目标质量数选择器，默认 `48`（所有物种）。

返回字段：

- `alt_km`：输出高度（同广播后的形状）。
- `T_local_K`：局地温度（K）。
- `T_exo_K`：外逸层温度（K）。
- `densities`：形状为 `(..., 8)` 的密度数组，物种顺序为：
  `He, O, N2, O2, Ar, TotalMass, H, N`。

### Jacchia77.calculate

签名：

```python
Jacchia77.calculate(*, alt_km, Tinf_K)
```

输入字段：

- `alt_km`：高度（公里），标量或数组，范围 0–2500。
- `Tinf_K`：外逸层温度（K），标量。

返回字段：

- `alt_km`：输出高度（同广播后的形状）。
- `Tinf_K`：外逸层温度（K）。
- `T_local_K`：局地温度（K）。
- `N2_cm3`：N2 数密度（cm⁻³）。
- `O2_cm3`：O2 数密度（cm⁻³）。
- `O_cm3`：O 数密度（cm⁻³）。
- `Ar_cm3`：Ar 数密度（cm⁻³）。
- `He_cm3`：He 数密度（cm⁻³）。
- `H_cm3`：H 数密度（cm⁻³）。
- `total_density_cm3`：总数密度（cm⁻³）。
- `mean_molecular_weight`：平均分子量（g/mol）。

### MET.calculate

签名：

```python
MET.calculate(*, alt_km, lat_deg, lon_deg, year, month, day, hour, minute, geo_index_type, f107, f107a, ap)
```

输入字段：

- `alt_km`：高度（公里），标量或数组。
- `lat_deg`：地理纬度（度）。
- `lon_deg`：地理经度（度）。
- `year`：年份（2位数，如23表示2023年）。
- `month`：月份（1-12）。
- `day`：日。
- `hour`：时（0-23）。
- `minute`：分（0-59）。
- `geo_index_type`：地磁指数类型（1=Kp, 2=Ap）。
- `f107`：F10.7 太阳射电噪声通量。
- `f107a`：162天平均 F10.7。
- `ap`：地磁活动指数 Ap。

返回字段：

- `alt_km`：输出高度。
- `lat_deg`：纬度（度）。
- `lon_deg`：经度（度）。
- `T_exo_K`：外逸层温度（K）。
- `T_local_K`：高度 Z 处的局地温度（K）。
- `N2_m3`：N2 数密度（每立方米）。
- `O2_m3`：O2 数密度（每立方米）。
- `O_m3`：O 数密度（每立方米）。
- `Ar_m3`：Ar 数密度（每立方米）。
- `He_m3`：He 数密度（每立方米）。
- `H_m3`：H 数密度（每立方米）。
- `mean_molecular_weight`：平均分子量。
- `total_density_kg_m3`：总质量密度（kg/m³）。
- `log10_density`：总密度的对数。
- `pressure_Pa`：总压力（Pa）。
- `gravity_m_s2`：重力加速度（m/s²）。
- `gamma`：比热比。
- `scale_height_m`：气压标高（m）。
- `cp`：定压比热。
- `cv`：定容比热。

### Chiu.calculate

签名：

```python
Chiu.calculate(*, alt_km, sunspot_number, local_time_rad, month_from_dec15, geo_lat_rad, geo_mag_lat_rad, geo_mag_lon_rad, dip_angle_rad)
```

输入字段：

- `alt_km`：高度（km），范围 90–500。设为 0 可获取各层峰值密度。
- `sunspot_number`：苏黎世平滑太阳黑子数（Rz）。
- `local_time_rad`：地方时角（弧度），从午夜起算（0 = 午夜，π = 正午）。
- `month_from_dec15`：年度时间（月），从上年 12 月 15 日起算。
- `geo_lat_rad`：地理纬度（弧度）。
- `geo_mag_lat_rad`：地磁纬度（弧度）。
- `geo_mag_lon_rad`：地磁东经（弧度）。
- `dip_angle_rad`：地磁磁倾角（弧度）。

返回字段：

- `alt_km`：输出高度。
- `sunspot_number`：输入太阳黑子数。
- `Ne_total_cm3`：总电子密度（cm⁻³）。
- `Ne_E_cm3`：E 层电子密度（cm⁻³）。
- `Ne_F1_cm3`：F1 层电子密度（cm⁻³）。
- `Ne_F2_cm3`：F2 层电子密度（cm⁻³）。

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
│   │   ├── __init__.py      # 懒加载别名：MSIS2, MSIS00, HWM14, HWM93, AuroraOval, IGRF, CIRA86, MSIS86, MSISE90, Jacchia77, MET, Chiu
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
│   │   └── pychiu/          # Chiu 电离层电子密度模型封装
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

`src/model/` 下每个模型目录都包含各自的 `README.md`（英文）和 `README_zh.md`（中文），详细文档涵盖模型背景、Fortran 接口、输入输出参数和用法示例：

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

## 测试

```bash
python -m pytest
```
