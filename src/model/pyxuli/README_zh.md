# Xu-Li 中性片模型

磁尾赤道中性片位置模型（Xu & Li，中国科学院，北京）。

## 背景

Xu-Li 模型计算 GSM（地心太阳磁层）坐标系下地磁尾中性片的 Z 位置。
提供三种变体，均将倾斜赤道面与中性片平滑连接，可用于整个磁层（包括近尾区域）：

- **AEN**（解析赤道中性片）— 单一闭合解析表达式
  （Zhu & Xu, 1994; Wang & Xu, 1994）
- **SEN**（标准赤道中性片）— 三区域分段模型
  （Xu, 1992）
- **DEN**（位移赤道中性片）— 中性片上下截面积近似相等的位移模型
  （Xu, 1991）

磁层顶边界使用 Sibeck et al. (1991) 模型。

## Fortran 接口

合并后的源文件 `xuli.for` 包含 7 个子程序：

| 子程序 | 说明 |
|---|---|
| `STIL(DOY, HR, TMI, TILA)` | 计算偶极倾角 |
| `SMPF(XSM, RMP, IM)` | 磁层顶截面半径 |
| `SAEN(TILA, XSM, YSM, ZAEN, RMP, IE)` | AEN 中性片 |
| `SSEN(TILA, XSM, YSM, ZSEN, RMP, IE)` | SEN 中性片 |
| `SDEN(TILA, XSM, YSM, ZDEN, RMP, IE)` | DEN 中性片 |
| `SD1(TIL, H, H1, XSM, D)` | 位移参数（DEN） |
| `SFA4(AA, BB, CC, DD, X)` | 四次方程求根（DEN） |

### 核心子程序签名

```
SAEN(TILA, XSM, YSM, ZAEN, RMP, IE)
SSEN(TILA, XSM, YSM, ZSEN, RMP, IE)
SDEN(TILA, XSM, YSM, ZDEN, RMP, IE)
```

| 参数 | 类型 | 方向 | 说明 |
|---|---|---|---|
| TILA | REAL | 输入 | 偶极倾角（度） |
| XSM | REAL | 输入 | GSM X 坐标（地球半径，负值指向磁尾） |
| YSM | REAL | 输入 | GSM Y 坐标（地球半径） |
| ZAEN/ZSEN/ZDEN | REAL | 输出 | 中性片 Z 位置（地球半径） |
| RMP | REAL | 输出 | 磁层顶半径（地球半径） |
| IE | INTEGER | 输出 | 1 = 磁层顶内, 2 = 磁层顶外 |

注意：`IE` 遵循 Fortran 77 隐式类型规则（I–N → INTEGER）。

## C ABI

C shim（`xuli_cshim.F90`）暴露两个函数：

### `xuli_eval`

```c
void xuli_eval(
    float tila, float xsm, float ysm,
    float *zaen, float *zsen, float *zden, float *rmp,
    int *ie_aen, int *ie_sen, int *ie_den
);
```

同时计算三种中性片变体。

### `xuli_tilt`

```c
void xuli_tilt(float doy, float ut_hours, float *tilt_deg);
```

从年积日和世界时计算偶极倾角。

## Python API

### 构造函数

```python
Model(dll_path=None)
```

- `dll_path`：编译后的 DLL/SO 路径，默认自动检测。

### `calculate()`

```python
result = model.calculate(
    *,
    x_re: float | np.ndarray,
    y_re: float | np.ndarray,
    doy: float | np.ndarray = None,
    ut_hours: float | np.ndarray = None,
    tilt_angle_deg: float | np.ndarray = None,
) -> dict
```

提供 `tilt_angle_deg` **或** 同时提供 `doy` + `ut_hours`：

- 若提供 `tilt_angle_deg`，直接用作偶极倾角。
- 否则需同时提供 `doy` 和 `ut_hours`，模型内部计算倾角。

### 输入参数

| 参数 | 类型 | 单位 | 说明 |
|---|---|---|---|
| `x_re` | float 或数组 | 地球半径 | GSM X 坐标（负值指向磁尾） |
| `y_re` | float 或数组 | 地球半径 | GSM Y 坐标 |
| `doy` | float 或数组 | — | 年积日（1.0–366.0） |
| `ut_hours` | float 或数组 | 小时 | 世界时 |
| `tilt_angle_deg` | float 或数组 | 度 | 偶极倾角（直接指定） |

### 输出字典

| 键 | 类型 | 说明 |
|---|---|---|
| `x_re` | float 或 ndarray | 输入回显 |
| `y_re` | float 或 ndarray | 输入回显 |
| `tilt_angle_deg` | float 或 ndarray | 使用的偶极倾角 |
| `zaen_re` | float 或 ndarray | AEN 中性片 Z（地球半径） |
| `zsen_re` | float 或 ndarray | SEN 中性片 Z（地球半径） |
| `zden_re` | float 或 ndarray | DEN 中性片 Z（地球半径） |
| `rmp_re` | float 或 ndarray | 磁层顶截面半径（地球半径） |
| `ie_aen` | int 或 ndarray | AEN 磁层顶内/外标志（1=内, 2=外） |
| `ie_sen` | int 或 ndarray | SEN 磁层顶内/外标志（1=内, 2=外） |
| `ie_den` | int 或 ndarray | DEN 磁层顶内/外标志（1=内, 2=外） |

标量输入返回标量输出；数组输入返回对应广播形状的 numpy 数组。

## 使用示例

### 单点计算（日期/时间）

```python
from model import XuLi

model = XuLi()
result = model.calculate(x_re=-10.0, y_re=0.0, doy=172.0, ut_hours=12.0)
print(f"ZAEN = {result['zaen_re']:.3f} RE")
print(f"ZSEN = {result['zsen_re']:.3f} RE")
print(f"ZDEN = {result['zden_re']:.3f} RE")
```

### 直接指定倾角

```python
result = model.calculate(x_re=-15.0, y_re=5.0, tilt_angle_deg=20.0)
```

### 批量计算

```python
import numpy as np

xs = np.linspace(-5, -30, 6)
result = model.calculate(x_re=xs, y_re=0.0, tilt_angle_deg=15.0)
print(result["zaen_re"])  # ZAEN 数组
```

## 坐标系

所有位置均为 GSM（地心太阳磁层）坐标系，以地球半径（RE ≈ 6371.2 km）为单位：
- **X**：正值指向太阳方向，负值指向磁尾
- **Y**：正值指向黄昏方向
- **Z**：正值指向北方（在包含偶极轴的平面内垂直于 X）

偶极倾角是地磁偶极轴与 GSM Z 轴之间的夹角，随季节（±23.5° 年变化）和 UT（±11.7° 日变化）变化。

## 参考文献

1. Xu, R.-L., A Displaced Equatorial Neutral Sheet Surface Observed on
   ISEE-2 Satellite, J. Atmospheric and Terrestrial Phys., 58, 1085, 1991.
2. Xu, R.-L., Dynamics of the Neutral Sheet in the Magnetotail during
   Substorm, Advances in solar-terrestrial science of China, ed. by W.-R.
   Hu et al., China Science Press, 1992.
3. Zhu, M. and R.-L. Xu, A continuous neutral sheet model and a normal
   curved coordinate system in the magnetotail, Chinese J. Space Science,
   14(4), 269, 1994.
4. Wang, Z.-D. and R.-L. Xu, Neutral Sheet Observed on ISEE Satellite,
   Geophysical Research Letter, 21(19), 2087, 1994.
5. Sibeck, D. G., R. E. Lopez, and R. C. Roelof, Solar wind control of
   the magnetopause shape, location, and motion, J. Geophys. Res., 96,
   5489, 1991.
