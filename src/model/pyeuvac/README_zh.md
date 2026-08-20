# EUVAC

`EUVAC` 使用逐日和 81 日平均 F10.7 指数计算 Torr 37 波段太阳极紫外光子通量。

## 接口

```python
from model import EUVAC

result = EUVAC().calculate(f107=80.0, f107a=80.0)
```

构造函数可指定 `dll_path`。`f107` 和 `f107a` 必须为有限正数，支持标量和可广播数组。输出返回广播后的输入、1–37 的 `bin_index`，以及末维为 37 的 `photon_flux_cm2_s`。

## 文件与资料

`euvac_cshim.F90` 提供 C ABI，`CMakeLists.txt` 构建 `euvac.dll` 或 `libeuvac.so`。37 波段系数来自随原始资料提供的 EUVAC/Torr 参考实现。
