# ExosphericH

`ExosphericH` 实现 Hodges（1994）地球外逸层氢三阶球谐模型。

## 接口

```python
from model import ExosphericH

result = ExosphericH().calculate(
    radius_km=10000.0, colatitude_deg=45.0, longitude_deg=0.0,
    season="equinox", f107=80,
)
```

构造函数接受 `data_dir` 和 `auto_download`，输入支持 NumPy 广播。地心半径限定为 6640–62126 km；`season` 只能为 `equinox` 或 `solstice`；F10.7 只能为 80、130、180、230。系数按对数半径插值，密度基值采用对数插值且不外推，输出为 `H_cm3`。

## 文件与资料

`__init__.py` 不依赖 SciPy，直接计算固定三阶归一化球谐。`h_exos.dat` 包含 Hodges 的 8 张系数表，并按文献要求采用 `1e-4` 缩放。参考：Hodges，*JGR*，1994，doi:10.1029/94JA02183。
