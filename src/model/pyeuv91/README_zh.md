# EUV91

`EUV91` 封装修订版 SERF2 太阳辐照度模型。确定性的 `bind(C)` 接口利用 Python 解析的系数和逐日代理指数计算 39 个波段。

## 接口

```python
from model import EUV91

result = EUV91().calculate(year=1980, day_of_year=183)
```

构造函数接受 `dll_path`、`data_dir` 和 `auto_download`。输入支持标量和可广播数组。模型仅接受 `euv91ix2.dat` 中实际存在的日期；缺失日期直接抛出 `ValueError`，不做日期插值。输出包含日期、波段起止波长、`photon_flux_cm2_s` 和 `energy_flux_erg_cm2_s`。

## 文件与资料

`euv91_cshim.F90` 提供原生接口，`euv91coe.txt` 与 `euv91ix2.dat` 提供系数和历史指数。每次调用都会重置工作数组，批量顺序和重复调用不会改变结果。
