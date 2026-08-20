# AEEUV

`AEEUV` 读取原始资料中的 4 套 Atmosphere Explorer 极紫外参考谱。该模型仅使用 NumPy 和数据表，不加载原生库。

## 接口

```python
from model import AEEUV

result = AEEUV().calculate(spectrum="f74113")
```

构造函数接受 `data_dir` 和 `auto_download`。`spectrum` 可取 `r74113`、`f74113`、`f76ref` 或 `sc21refw`。输出包含 `wavelength_angstrom`、`photon_flux_m2_s`、`line_or_range`、`group_type` 和 `adjustment_factor`，顺序与源文件一致。数据通过 UpperAtmPy 的统一数据机制解析，因此可在仓库外工作目录使用。

## 文件与资料

`__init__.py` 解析 `data/aeeuvdata/*.dat`；数据文件保留原始 AE-EUV 光谱的谱线标签和调整信息。
