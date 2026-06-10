# MGST 地磁场模型

MGST（MAGSAT 地磁场球谐模型）基于 MAGSAT 卫星数据的地球主磁场模型。

## 支持的模型

| 类名 | 模型 | 历元 | 阶数 | 长期变化 |
|------|------|------|------|----------|
| `MGST80` | MGST(6/80) | 1979.85 | 13 | 无 |
| `MGST81` | MGST(4/81) | 1980.0 | 13（常数项）+ 7（一阶导数） | 一阶导数 |

## 使用方法

```python
from model import MGST80, MGST81

# MGST(6/80) — 标量 + 精细姿态数据，1979年11月5-6日
m80 = MGST80()
r = m80.calculate(year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0)
print(r["F_nT"])  # 总场强度，单位 nT

# MGST(4/81) — 15天数据集，含长期变化
m81 = MGST81()
r = m81.calculate(year=1985.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0)
```

## 返回字典

| 键名 | 单位 | 说明 |
|------|------|------|
| `X_nT` | nT | 北向分量 |
| `Y_nT` | nT | 东向分量 |
| `Z_nT` | nT | 垂直向下分量（正值向下） |
| `F_nT` | nT | 总场强度 |
| `H_nT` | nT | 水平分量 |
| `inclination_deg` | 度 | 磁倾角 |
| `declination_deg` | 度 | 磁偏角 |

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `year` | float | — | 十进制年份 |
| `lat_deg` | float/数组 | — | 地理纬度（°N） |
| `lon_deg` | float/数组 | — | 地理经度（°E） |
| `alt_km` | float/数组 | — | 海拔高度（km） |
| `nmx` | int | 13 | 最大阶数（1-13） |

## 参考文献

- R. A. Langel, Initial Geomagnetic Field Model from MAGSAT, NASA TM-80679, 1980.
- R. A. Langel 等, Initial Geomagnetic Field Model from MAGSAT Vector Data, Geophys. Res. Lett. 7, 793, 1980.
