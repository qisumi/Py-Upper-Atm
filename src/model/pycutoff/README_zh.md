# CutoffRigidity — 地磁截止刚度（Smart & Shea，IGRF-95）

[English](README.md)

## 模型背景

地磁截止刚度模型预测宇宙线带电粒子从行星际空间穿透地球地磁磁场的磁刚度（动量/电荷）截止阈值。该概念由 Carl Störmer 于 1930 年提出。

本实现基于 Don F. Smart 和 Margaret A. Shea（阿拉巴马大学亨茨维尔分校）维护的标准宇宙线轨迹程序，从 NSSDC/CCMC ModelWeb 存档获取。使用 IGRF-1995 地磁场模型（10 阶，Schmidt 归一化系数）和 Runge-Kutta 积分追踪带电粒子轨迹。

**无需外部数据文件** — IGRF-95 系数硬编码在 Fortran 源码中。

**参考文献**：

> Smart, D. F. & Shea, M. A., *Geomagnetic Cutoff Rigidity Computer Program*, NSSDC, 2001.

> Störmer, C., *On the Trajectories of Electric Particles in the Field of a Magnetic Dipole*, Astrophysica Norvegica, 1930.

## 目录结构

```
pycutoff/
├── cutoff_legacy.for    # Fortran 77 子例程（GDGC, SINGLTJ, FGRAD, MAGNEW95, azrgeg）
├── cutoff_cshim.F90     # C ABI shim，导出 cutoff_trajectory()
├── CMakeLists.txt       # CMake 构建目标 cutoff
├── __init__.py          # Python Model 类
└── README.md            # 本文件
```

## Fortran 接口

### `cutoff_legacy.for` — 核心子例程

| 子例程 | 说明 |
|--------|------|
| `GDGC(TCD, TSD)` | 地理坐标到地心坐标转换 |
| `SINGLTJ(PC, IRSLT, INDXPC, Y1GC, Y2GC, Y3GC)` | 单条轨迹计算（Runge-Kutta） |
| `FGRAD` | 力梯度计算 |
| `MAGNEW95` | IGRF-95 磁场计算 |
| `azrgeg(na, nz, pamu, rigin, epn, beta)` | 能量-刚度转换 |

### `cutoff_cshim.F90` — C ABI

```c
void cutoff_trajectory(double lat_deg, double lon_deg, double rigidity_gv,
                       double zenith_deg, double azimuth_deg,
                       int *result_code, double *faslat, double *faslon,
                       double *path_length);

void cutoff_rigidity_to_energy(int atomic_number, int charge,
                               double mass_amu, double rigidity_mv,
                               double *energy_mev);
```

## 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `lat_deg` | float 或 ndarray | 地理纬度（度），-90 到 90 |
| `lon_deg` | float 或 ndarray | 地理经度（度），-180 到 360 |
| `rigidity_gv` | float、ndarray 或 None | 磁刚度（GV）。若为 None，使用扫描模式 |
| `zenith_deg` | float 或 ndarray | 天顶角（度），0 到 180。默认 0（垂直向上） |
| `azimuth_deg` | float 或 ndarray | 方位角（度）。默认 0（北） |
| `start_rigidity_gv` | float | 扫描起始刚度（GV）。默认 20.0。仅扫描模式 |
| `delta_rigidity_mv` | float | 刚度步长（MV）。默认 10.0。仅扫描模式 |
| `max_trajectories` | int | 最大轨迹数。默认 1000。仅扫描模式 |

单轨迹模式支持数组输入，并按 NumPy 规则广播。扫描模式接受标量位置和方向输入。

## 输出

### 单轨迹模式（指定 `rigidity_gv`）

| 字段 | 类型 | 说明 |
|------|------|------|
| `rigidity_gv` | float | 输入刚度 |
| `result_code` | int | +1（允许），0（失败），-1（再入） |
| `fate` | str | "allowed"、"failed" 或 "reentrant" |
| `asymptotic_latitude_deg` | float | 渐近纬度（度） |
| `asymptotic_longitude_deg` | float | 渐近经度（度） |
| `path_length_re` | float | 轨迹路径长度（地球半径） |

### 扫描模式（`rigidity_gv` 为 None）

| 字段 | 类型 | 说明 |
|------|------|------|
| `cutoff_rigidity_gv` | float | 地磁截止刚度（GV） |
| `fate` | str | "allowed" 或 "forbidden" |
| `asymptotic_latitude_deg` | float | 截止轨迹的渐近纬度 |
| `asymptotic_longitude_deg` | float | 截止轨迹的渐近经度 |
| `path_length_re` | float | 截止轨迹的路径长度 |
| `n_trajectories_computed` | int | 计算的轨迹数 |
| `rigidity_gv` | ndarray | 所有测试刚度（GV） |
| `trajectory_results` | ndarray | 各轨迹的结果代码 |

## 用法示例

### 单条轨迹

```python
from model import CutoffRigidity

model = CutoffRigidity()
result = model.calculate(
    lat_deg=40.0, lon_deg=0.0, rigidity_gv=10.0,
    zenith_deg=0.0, azimuth_deg=0.0,
)
print(f"命运: {result['fate']}")
print(f"渐近方向: ({result['asymptotic_latitude_deg']:.1f}°, "
      f"{result['asymptotic_longitude_deg']:.1f}°)")
```

### 批量单轨迹

```python
import numpy as np
from model import CutoffRigidity

model = CutoffRigidity()
result = model.calculate(
    lat_deg=np.array([0.0, 40.0]),
    lon_deg=0.0,
    rigidity_gv=np.array([15.0, 10.0]),
)
print(result["fate"])
```

### 截止刚度扫描

```python
result = model.calculate(
    lat_deg=0.0, lon_deg=0.0,
    start_rigidity_gv=20.0,
    delta_rigidity_mv=50.0,
    max_trajectories=500,
)
print(f"截止刚度: {result['cutoff_rigidity_gv']:.2f} GV")
print(f"计算轨迹数: {result['n_trajectories_computed']}")
```

## 构造参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dll_path` | 自动检测 | 自定义 DLL 路径 |

## 坐标说明

- 输入坐标为**地理**（大地）经纬度。
- 内部使用 WGS 椭球体转换为地心坐标。
- 渐近坐标表示宇宙线到达大气层顶部的方向。
- 模型无法处理极点上方的轨迹（会产生 BETA 溢出）。

## 致谢

在基于此软件发表的论文中，请注明软件提供方（NSSDC）和模型作者（Smart & Shea）。
