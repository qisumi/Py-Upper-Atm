# PVThermosphere

`PVThermosphere` 封装金星先驱号中性热层模型 VTS3。

## 接口

```python
from model import PVThermosphere

result = PVThermosphere().calculate(
    alt_km=250.0, lat_deg=0.0, local_time_hours=12.0,
    f107a=200.0, f107=200.0,
)
```

构造函数可指定 `dll_path`。输入支持 NumPy 广播；可调用高度为 100–250 km，地方时为 `[0, 24)`。低于文献科学适用范围 140 km 时发出 `RuntimeWarning`，以便复现原始参考驱动中的样例。输出包含总质量密度、CO2/O/CO/He/N/N2 数密度，以及局地温度和外逸层温度。

## 文件与资料

`pvatmos.for` 包含清理后的 VTS3 例程，`pvthermosphere_cshim.F90` 提供 C ABI。Fortran 持久工作数组均显式声明，保证不同平台及调用顺序下结果可重复。模型依据金星先驱号热层观测建立。
