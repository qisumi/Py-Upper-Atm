# Photoelectron

`Photoelectron` 封装 Richards 简化电离层光电子通量模型，在 0.5–99.5 eV 范围计算 100 个 1 eV 能箱。

## 接口

```python
from model import Photoelectron

result = Photoelectron().calculate(
    alt_km=148.0, sza_deg=0.0,
    electron_temperature_K=1000.0, neutral_temperature_K=800.0,
    O_cm3=1e10, O2_cm3=1e9, N2_cm3=1e9,
    electron_density_cm3=1e6, f107=71.0,
)
```

各点输入支持 NumPy 广播。只能提供 `f107` 或恰好 9 个 `euv_factors`，二者互斥。输出包含 `energy_eV`、总微分通量、每球面度通量和 `attenuation_factor`。高度超过 350 km 或衰减因子低于 0.14 时会发出科学适用性警告。

## 文件与资料

`photoelectron.for` 包含 Richards（1992）数值模型，`photoelectron_cshim.F90` 提供无外部状态的 C ABI；构造函数可指定 `dll_path`。
