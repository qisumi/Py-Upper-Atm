# Heppner-Maynard-Rich 电场模型

基于 OGO 6 和 DE 2 卫星电场测量数据的高纬度电离层电势模型。

## 支持的模型

| 模型 | IMF 条件 | 说明 |
|------|----------|------|
| `A` | Bz < 0, By < 0 | 北半球 |
| `BC` | Bz < 0, By > 0 | 北半球 |
| `DE` | Bz < 0, By < 0 | 南半球 |
| `heelis` | Bz > 0 | Heelis 对流模型 |

## 使用方法

### 电势计算

```python
from model import HMR

m = HMR()

# Heppner-Maynard 电势
r = m.calculate(lat_deg=70.0, lon_deg=180.0, model="A")
print(r["electric_potential_kV"])

# Heelis 对流模型
r = m.calculate_heelis(lat_deg=70.0, lon_hrs=12.0)
```

### 电导率计算

```python
r = m.calculate_conductivity(lat_deg=70.0, mlt_hrs=12.0, kp=3.0)
print(r["hall_conductivity_Mho"])
print(r["pedersen_conductivity_Mho"])
```

### 完整计算

```python
r = m.calculate_full(kp=3.5, sublat_deg=0.0, f107=80.0, model="A")
# 返回 41x25 网格（纬度 50-90°，地方时 0-24h）
print(r["electric_potential_kV"].shape)  # (41, 25)
print(r["joule_heating_mW_m2"])          # mW/m²
print(r["fac_uA_m2"])                    # μA/m²
```

## 返回字典

### `calculate()` — 电势

| 键名 | 单位 | 说明 |
|------|------|------|
| `electric_potential_kV` | kV | 电势 |

### `calculate_heelis()` — Heelis 模型

| 键名 | 单位 | 说明 |
|------|------|------|
| `electric_potential_kV` | kV | 电势 |
| `dlat_kV_per_rad` | kV/rad | 纬度梯度 |
| `dlon_kV_per_rad` | kV/rad | 地方时梯度 |

### `calculate_full()` — 完整网格

| 键名 | 单位 | 说明 |
|------|------|------|
| `electric_potential_kV` | kV | 电势 (41×25) |
| `e_field_lat_mV_m` | mV/m | 纬向电场 |
| `e_field_lon_mV_m` | mV/m | 经向电场 |
| `hall_conductivity_Mho` | Mho | Hall 电导率 |
| `pedersen_conductivity_Mho` | Mho | Pedersen 电导率 |
| `joule_heating_mW_m2` | mW/m² | Joule 加热率 |
| `fac_uA_m2` | μA/m² | 场向电流 |
| `lat_grid_deg` | 度 | 纬度网格 (50-90°) |
| `mlt_grid_hrs` | 小时 | 地方时网格 (0-24h) |

## 参考文献

- J. P. Heppner and N. C. Maynard, Empirical high-latitude electric field models, J. Geophys. Res., 92, 4467, 1987.
- P. A. Heelis 等, An analytical model of high-latitude ionospheric convection, J. Geophys. Res., 87, 6339, 1982.
