# Jensen & Cain (1962) 地磁场模型

## 概述

Jensen & Cain (1962) 模型是一个早期的地球主磁场球谐模型。它在早期卫星任务中被广泛用于计算地磁坐标。

**参考文献**: D. C. Jensen and J. C. Cain, "An Interim Geomagnetic Field," *J. Geophys. Res.* 67, 3568, 1962.

## 模型特征

- **历元**: 1960.0
- **最大阶数**: 6（48 个非零系数）
- **数据来源**: 1940 年以来约 74,000 个地面 H 和 F 观测值
- **坐标系**: 地理坐标（系数确定未考虑地球扁率）
- **时间变化**: 无（无长期变化系数）

## 目录结构

```
pyjensen/
├── fieldg.for           # Fortran 77 源码（FIELDG 和 FIELD 子程序）
├── jensen_cshim.F90     # Fortran 90 C ABI shim
├── CMakeLists.txt        # CMake 构建配置
├── __init__.py           # Python Model 类
├── README.md             # 英文文档
└── README_zh.md          # 本文件
```

## Fortran 接口

### FIELDG 子程序

```fortran
SUBROUTINE FIELDG(DLAT, DLONG, ALT, TM, NMX, L, X, Y, Z, F)
```

**输入参数:**
- `DLAT` — 地理纬度（度，北正）
- `DLONG` — 地理经度（度，东正）
- `ALT` — 海拔高度（km）
- `TM` — 十进制年份（如 1960.0）
- `NMX` — 最大阶数（1–6）
- `L` — 控制标志（0 = 使用内嵌系数，>0 = 从文件读取）

**输出参数:**
- `X` — 磁场北向分量（nT）
- `Y` — 磁场东向分量（nT）
- `Z` — 磁场下向分量（nT，向下为正）
- `F` — 总场强度 |B|（nT）

## Python API

### 构造函数

```python
from model import JensenCain

model = JensenCain(
    dll_path=None,      # DLL 路径（None 时自动检测）
    data_dir=None,      # 数据目录路径
    auto_download=True,  # 未找到数据时自动下载
)
```

### calculate() 方法

```python
result = model.calculate(
    year=1960.0,      # 十进制年份（标量或数组）
    lat_deg=45.0,     # 地理纬度（度，北正）
    lon_deg=0.0,      # 地理经度（度，东正）
    alt_km=0.0,       # 海拔高度（km）
    nmx=6,            # 最大阶数（1–6，默认 6）
)
```

### 返回字典

| 键名 | 说明 | 单位 |
|------|------|------|
| `year` | 输入年份 | - |
| `lat_deg` | 输入纬度 | 度 |
| `lon_deg` | 输入经度 | 度 |
| `alt_km` | 输入高度 | km |
| `X_nT` | 北向分量 | nT |
| `Y_nT` | 东向分量 | nT |
| `Z_nT` | 下向分量 | nT |
| `F_nT` | 总场强度 | nT |
| `H_nT` | 水平分量 | nT |
| `inclination_deg` | 磁倾角 | 度 |
| `declination_deg` | 磁偏角 | 度 |

## 使用示例

```python
from model import JensenCain

# 单点计算
model = JensenCain()
result = model.calculate(
    year=1960.0,
    lat_deg=45.0,
    lon_deg=0.0,
    alt_km=0.0,
)
print(f"总场强度: {result['F_nT']:.1f} nT")

# 批量计算
import numpy as np
lats = np.linspace(-90, 90, 19)
result = model.calculate(
    year=1960.0,
    lat_deg=lats,
    lon_deg=0.0,
    alt_km=0.0,
)
print(f"场强范围: {result['F_nT'].min():.1f} 到 {result['F_nT'].max():.1f} nT")
```

## 局限性

- 无时间变化（长期变化）— 系数仅适用于 1960.0 历元
- 与现代模型（如 IGRF）相比精度较低
- 系数确定未考虑地球扁率
- 最大阶数限制为 6

## 参考文献

1. Jensen, D. C. and Cain, J. C. (1962). An Interim Geomagnetic Field. *Journal of Geophysical Research*, 67(9), 3568–3569.
