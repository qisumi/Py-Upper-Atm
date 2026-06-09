# GSFC — 戈达德太空飞行中心地磁场模型

[English](README.md)

## 模型背景

GSFC 地磁场模型是美国宇航局戈达德太空飞行中心（Goddard Space Flight Center）开发的一系列球谐展开地磁场模型。本模块将 Fortran 77 实现（FIDD、FID、MAGF 子程序）编译为共享库，并通过 `ctypes` 以 `GSFC` 类的形式暴露，遵循项目统一的 `Model.calculate(...)` 接口。

支持三个模型版本：

| 版本 | 模型 | 历元 | 最大阶数 |
|------|------|------|----------|
| 80 | GSFC 9/80 | 1980.0 | 9 |
| 83 | GSFC 12/83 | 1980.0 | 14 |
| 87 | GSFC 11/87 | 1982.0 | 14 |

模型支持含三阶长期变化项的时间相关系数，同时支持大地坐标系和地心坐标系。

需要外部系数数据文件，通过 `utils.model_data.ensure_model_data()` 解析路径，支持 `UPPERATMPY_DATA_DIR` 环境变量、构造函数 `data_dir` 参数，以及在发布资源匹配时自动下载。

## 目录结构

```text
pygsfc/
├── gsfcsub.for        # Fortran 77 源码（FIDD、FID、MAGF）
├── gsfc_cshim.F90     # C ABI shim，供 ctypes 调用
├── CMakeLists.txt     # CMake 目标 gsfc
├── __init__.py        # Python Model 类
├── README.md          # 英文文档
└── README_zh.md       # 中文文档
```

## Fortran 接口

`gsfcsub.for` 中的核心子程序：

| 子程序 | 说明 |
|--------|------|
| `FIDD(MODEL, JJ, DLAT, DLONG, ALT1, TM, X, Y, Z, F)` | 驱动程序，打开系数文件并调用 FID。 |
| `FID(IU, J, MM, NEXT, IDST, DLAT, DLONG, Q1, TM, DST, NMX, L, X, Y, Z, F)` | 核心计算程序，读取系数并计算时间相关的磁场。 |
| `MAGF` | 通过球谐综合计算磁场。 |

C ABI shim 导出函数：

```c
void gsfc_set_data_root(const char *path);
void gsfc_eval(int model, float lat, float lon, float alt, float year,
               int jj, float *x, float *y, float *z, float *f);
```

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `year` | 浮点数 / 数组 | 十进制年份，如 `1985.5`。 |
| `lat_deg` | 浮点数 / 数组 | 大地纬度（度，北正）。 |
| `lon_deg` | 浮点数 / 数组 | 大地经度（度，东正）。 |
| `alt_km` | 浮点数 / 数组 | 海拔高度（km）。 |

标量输入返回标量值。数组输入通过 NumPy 广播，返回具有广播形状的数组。

## 输出

`calculate()` 返回包含以下字段的字典：

| 字段 | 单位 / 类型 | 说明 |
|------|-------------|------|
| `year` | 浮点数 / 数组 | 广播后的输入年份。 |
| `lat_deg` | 浮点数 / 数组 | 广播后的输入纬度。 |
| `lon_deg` | 浮点数 / 数组 | 广播后的输入经度。 |
| `alt_km` | 浮点数 / 数组 | 广播后的输入高度。 |
| `X_nT` | nT | 北向地磁场分量。 |
| `Y_nT` | nT | 东向地磁场分量。 |
| `Z_nT` | nT | 垂直向下地磁场分量（正向下）。 |
| `F_nT` | nT | 总场强度。 |
| `H_nT` | nT | 水平场强度。 |
| `inclination_deg` | 度 | 磁倾角（正向下）。 |
| `declination_deg` | 度 | 磁偏角（正向东）。 |

## 使用示例

### 单点计算

```python
from model import GSFC

model = GSFC(gsfc_version=87)
result = model.calculate(
    year=1985.0,
    lat_deg=39.9,
    lon_deg=116.4,
    alt_km=0.0,
)

print(f"总场强度: {result['F_nT']:.1f} nT")
print(f"磁偏角: {result['declination_deg']:.2f} 度")
```

### 批量计算

```python
from model import GSFC

model = GSFC(gsfc_version=87)
result = model.calculate(
    year=1985.0,
    lat_deg=[30.0, 40.0, 50.0],
    lon_deg=[116.0, 116.0, 116.0],
    alt_km=[0.0, 100.0, 200.0],
)

print(result["F_nT"].shape)  # (3,)
```

### 模型版本比较

```python
from model import GSFC

m80 = GSFC(gsfc_version=80)
m83 = GSFC(gsfc_version=83)
m87 = GSFC(gsfc_version=87)

r80 = m80.calculate(year=1980.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
r83 = m83.calculate(year=1980.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
r87 = m87.calculate(year=1980.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
```

## 构造函数参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 `gsfc.dll` 或 `libgsfc.so` 路径。 |
| `gsfc_version` | `87` | 模型版本：`80`、`83` 或 `87`。 |
| `data_dir` | 自动解析 | 包含 `gsfcdata/` 目录的数据根目录。 |
| `auto_download` | `True` | 发布资源匹配时自动下载缺失的系数文件。 |

## 数据文件

数据根目录包含三个 ASCII 系数文件：

```text
UPPERATMPY_DATA_DIR/
└── gsfcdata/
    ├── GSFC80.DAT    # GSFC 9/80 系数
    ├── GSFC83.DAT    # GSFC 12/83 系数
    └── GSFC87.DAT    # GSFC 11/87 系数
```

## 参考文献

- Cain, J. C., Davis, W. M., and Jensen, D. C. (1965). A proposed model for the
  international geomagnetic reference field—1965. *Journal of Geophysical Research*,
  70(15), 3647–3652.
- GSFC 地磁场模型系数：`TODO/GSFC-Model-Coefficients/`
