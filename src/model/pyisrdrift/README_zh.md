# ISRDrift — ISR 离子漂移模型（Richmond et al., 1980）

[English](README.md)

## 模型背景

非相干散射雷达（ISR）离子漂移模型计算太阳活动低年静日条件下 300 km 高度的电离层电伪势和 E x B 漂移速度。该模型基于非相干散射雷达观测的球谐分析结果。

本模块将该 Fortran 模型编译为共享库，通过 `ctypes` 封装为 `ISRDrift` 类，遵循项目统一的 `Model.calculate(...)` 接口。

**无需外部数据文件**，所有 128 个系数均硬编码在 Fortran 源码中。

**参考文献**：

> Richmond, A. D., et al., *An empirical model of quiet-day ionospheric electric fields at middle and low latitudes*, J. Geophys. Res. **85**, 4658, 1980.

## 目录结构

```
pyisrdrift/
├── isr_drift.for          # Fortran 77 EFIELD 子例程
├── isr_drift_cshim.F90    # C ABI shim，导出 isr_drift_eval()
├── CMakeLists.txt         # CMake 构建目标 isr_drift
├── __init__.py            # Python Model 类
└── README.md              # 本文件
```

## Fortran 接口

### `isr_drift.for` — `EFIELD` 子例程

```fortran
SUBROUTINE EFIELD(XMLAT, XMLON, DAYNO, UT, ISEASAV, IUTAV, POT, VU, VE)
```

| 参数      | 方向 | 类型      | 说明                                                               |
|-----------|------|-----------|--------------------------------------------------------------------|
| `XMLAT`   | 入参 | `real`    | 磁纬度（°）                                                        |
| `XMLON`   | 入参 | `real`    | 磁东经（°）                                                        |
| `DAYNO`   | 入参 | `real`    | 年积日（1.0 = 1月1日，最大 365.24）                                 |
| `UT`      | 入参 | `real`    | 世界时（小时）                                                      |
| `ISEASAV` | 入参 | `integer` | 季节平均模式（0–4，见下表）                                         |
| `IUTAV`   | 入参 | `integer` | UT 平均模式（0 或 1，见下表）                                       |
| `POT`     | 出参 | `real`    | 电伪势（伏特）                                                      |
| `VU`      | 出参 | `real`    | 极向/向上漂移速度（垂直于 B，在磁子午面内）（m/s）                    |
| `VE`      | 出参 | `real`    | 东向漂移速度（m/s）                                                  |

**季节平均模式（`ISEASAV`）**：

| 值 | 含义                                           |
|----|------------------------------------------------|
| 0  | 不做季节平均，直接使用 `DAYNO`                   |
| 1  | 11月–2月平均                                     |
| 2  | 5月–8月平均                                      |
| 3  | 3月、4月、9月、10月平均                            |
| 4  | 全年平均（`DAYNO` 被忽略）                         |

**UT 平均模式（`IUTAV`）**：

| 值 | 含义                                              |
|----|---------------------------------------------------|
| 0  | 不做 UT 平均                                       |
| 1  | 在固定磁地方时上对所有 UT 取平均                     |

### `isr_drift_cshim.F90` — C ABI

```c
void isr_drift_eval(float xmlat, float xmlon, float dayno, float ut,
                    int isea, int iutav, float *pot, float *vu, float *ve);
```

## 输入参数

| 参数            | 类型          | 说明                                                               |
|-----------------|---------------|--------------------------------------------------------------------|
| `mlat_deg`      | float / array | 磁纬度（°）                                                        |
| `mlon_deg`      | float / array | 磁东经（°）                                                        |
| `doy`           | float / array | 年积日（1.0–365.24），1.0 = 1月1日                                  |
| `ut_hours`      | float / array | 世界时（小时）                                                      |
| `seasonal_avg`  | int           | 季节平均模式（0–4，默认 0）                                         |
| `ut_avg`        | int           | UT 平均模式（0 或 1，默认 0）                                       |

## 输出

`calculate()` 返回一个字典，包含以下字段：

| 字段                  | 类型            | 说明                          |
|-----------------------|-----------------|-------------------------------|
| `mlat_deg`            | float / ndarray | 输入磁纬度（°）                |
| `mlon_deg`            | float / ndarray | 输入磁东经（°）                |
| `doy`                 | float / ndarray | 输入年积日                     |
| `ut_hours`            | float / ndarray | 输入世界时（小时）              |
| `potential_V`         | float / ndarray | 电伪势（伏特）                  |
| `poleward_drift_ms`   | float / ndarray | 极向 E x B 漂移速度（m/s）     |
| `eastward_drift_ms`   | float / ndarray | 东向 E x B 漂移速度（m/s）     |

## 用法示例

### 单点计算

```python
from model import ISRDrift

model = ISRDrift()
result = model.calculate(
    mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
)

print(f"电伪势: {result['potential_V']:.2f} V")
print(f"极向漂移: {result['poleward_drift_ms']:.2f} m/s")
print(f"东向漂移: {result['eastward_drift_ms']:.2f} m/s")
```

### 批量计算

```python
import numpy as np

mlat = np.linspace(30, 60, 7)
mlon = np.zeros_like(mlat)
doy = np.full_like(mlat, 172.0)
ut = np.full_like(mlat, 12.0)

result = model.calculate(mlat_deg=mlat, mlon_deg=mlon, doy=doy, ut_hours=ut)
print(result["potential_V"].shape)           # (7,)
print(result["poleward_drift_ms"].shape)     # (7,)
print(result["eastward_drift_ms"].shape)     # (7,)
```

### 季节平均模式

```python
for mode in range(5):
    r = model.calculate(
        mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
        seasonal_avg=mode,
    )
    print(f"seasonal_avg={mode}: 电伪势={r['potential_V']:.2f} V")
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |

## 坐标说明

- 输入坐标使用 Richmond et al. (1980) 定义的**磁坐标系**。
- 输出漂移分量垂直于 300 km 高度的地磁场。
- 结果仅在磁纬度约 **-65° 至 +65°** 之间具有地球物理意义。

## 致谢

在基于此软件发表的论文或包含此模型代码的应用程序中，请注明软件提供方（NSSDC/CCMC）和模型作者（A. D. Richmond）。
