# AuroraOval — Feldstein 极光卵边界模型（Holzworth & Meng 参数化）

[English](README.md)

## 模型背景

Feldstein (1963) 通过观测总结出极光卵随地磁活动水平变化的经验形态。Holzworth 和 Meng (1975) 为七个 Feldstein 极光卵（对应地磁活动等级 0–6）拟合了七参数傅里叶级数系数，实现了极光卵边界的数学参数化表示。

本模块将该 Fortran 模型编译为共享库，通过 `ctypes` 封装为 `AuroraOval` 类，遵循项目统一的 `Model.calculate(...)` 接口。

**无需外部数据文件**，所有傅里叶系数均硬编码在 Fortran 源码中。

**参考文献**：

> Feldstein, Y. I., *On Morphology and Auroral and Magnetic Disturbances at High Latitudes*, Geomagn. Aeron. **3**, 138, 1963.

> Holzworth, R. H., & Meng, C.-I., *Mathematical Representation of the Auroral Oval*, Geophys. Res. Lett. **2**, 377, 1975.

## 目录结构

```
pyaurora/
├── oval.for           # Fortran 77 原始 oval 子例程
├── oval_cshim.F90     # C ABI shim，导出 oval_eval()
├── CMakeLists.txt     # CMake 构建目标 aurora_oval
├── __init__.py        # Python Model 类
└── README.md          # 本文件
```

## Fortran 接口

### `oval.for` — `oval` 子例程

```fortran
subroutine oval(xmlt, iql, pcgl, ecgl)
```

| 参数   | 方向 | 类型     | 说明                                      |
|--------|------|----------|-------------------------------------------|
| `xmlt` | 入参 | `real`   | 磁地方时（小时）                           |
| `iql`  | 入参 | `integer`| 地磁活动等级，0（宁静）至 6（活跃）         |
| `pcgl` | 出参 | `real`   | 极向边界修正地磁纬度（°）                   |
| `ecgl` | 出参 | `real`   | 赤道向边界修正地磁纬度（°）                  |

### `oval_cshim.F90` — C ABI

```c
void oval_eval(float xmlt, int iql, float *pcgl, float *ecgl);
```

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `mlt_hours` | float / array | 磁地方时（小时），使用修正地磁坐标系（CGML） |
| `activity_level` | int / array | 地磁活动等级，0（宁静）至 6（活跃） |

## 输出

`calculate()` 返回一个字典，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `mlt_hours` | float / ndarray | 输入磁地方时 |
| `activity_level` | int / ndarray | 输入地磁活动等级 |
| `poleward_boundary_deg` | float / ndarray | 极向边界修正地磁纬度（°） |
| `equatorward_boundary_deg` | float / ndarray | 赤道向边界修正地磁纬度（°） |

## 用法示例

### 单点计算

```python
from model import AuroraOval

model = AuroraOval()
result = model.calculate(mlt_hours=12.0, activity_level=3)

print(f"极向边界: {result['poleward_boundary_deg']:.2f}°")
print(f"赤道向边界: {result['equatorward_boundary_deg']:.2f}°")
```

### 批量计算

```python
import numpy as np

mlt = np.linspace(0, 24, 25)
levels = np.full_like(mlt, 3, dtype=int)

result = model.calculate(mlt_hours=mlt, activity_level=levels)
print(result["poleward_boundary_deg"].shape)       # (25,)
print(result["equatorward_boundary_deg"].shape)     # (25,)
```

### 遍历所有活动等级

```python
for level in range(7):
    r = model.calculate(mlt_hours=0.0, activity_level=level)
    print(f"level={level}: poleward={r['poleward_boundary_deg']:.2f}°, "
          f"equatorward={r['equatorward_boundary_deg']:.2f}°")
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |

## 坐标说明

- 输入 MLT 使用**修正地磁坐标系**（Corrected Geomagnetic Coordinate System）。
- 输出纬度为**修正地磁纬度**（Corrected Geomagnetic Latitude, CGL）。
- 地理坐标与修正地磁坐标之间的转换可参考：
  - 在线工具：https://nssdc.gsfc.nasa.gov/space/cgm/cgm.html
  - 离线程序：https://nssdc.gsfc.nasa.gov/pub/models/geomagnetic/geo_cgm/geo-cgm.for

## 致谢

在基于此软件发表的论文或包含此模型代码的应用程序中，请注明软件提供方（NSSDC）和模型作者（Holzworth & Meng）。
