# PVIonosphere

`PVIonosphere` 实现金星先驱号经验电子密度和电子温度拟合。

## 接口

```python
from model import PVIonosphere

result = PVIonosphere().calculate(alt_km=200.0, sza_deg=30.0)
```

构造函数接受 `dll_path`、`data_dir` 和 `auto_download`。输入支持标量和可广播数组，高度范围为 150–3000 km。输出包含广播后的坐标，以及 `log10_electron_density_cm3`/`electron_density_cm3` 和 `log10_electron_temperature_K`/`electron_temperature_K`。

## 文件与资料

Python 解析 `fsmod.dat` 与 `fsmodt.dat` 并将系数传给 `pvionosphere_cshim.F90`；原生例程不打开文件，也不依赖当前工作目录。拟合来源于金星先驱号电离层观测。
