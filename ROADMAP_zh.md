# UpperAtmPy 开发路线图

[English Version](ROADMAP.md)

## 当前状态

以下模型已完成移植，可在 `src/model/` 包中使用：

| 模型 | 类名 | 说明 | 状态 |
|------|------|------|------|
| NRLMSIS-2.0 | `MSIS2` | 中性大气温度与密度 | 已完成 |
| NRLMSISE-00 | `MSIS00` | 中性大气温度与密度 | 已完成 |
| HWM14 | `HWM14` | 水平中性风场 | 已完成 |
| HWM93 | `HWM93` | 水平中性风场 | 已完成 |

## 计划移植模型

以下所有模型均来自 `TODO/` 目录（CCMC ModelWeb 存档）。每个模型将遵循已有模式进行移植：Fortran/C 源码通过 CMake 编译为 DLL，使用 `ctypes` 封装，对外暴露单一的 `Model.calculate(...)` 类接口。

### 第一阶段 — 大气与电离层扩展

这些模型扩展现有中性大气和电离层能力，FFI 特征与已移植模型类似。

| 模型 | 目录 | 说明 | 原始语言 | 外部数据 |
|------|------|------|----------|----------|
| IGRF-13 | `TODO/IGRF` | 国际地磁参考场 — 计算地磁场分量（X, Y, Z, F）、L 值、磁倾角、磁偏角（1945 年起） | Fortran 77 | DGRF/IGRF 系数 `.dat` 文件（1945–2025） |
| CIRA-86 | `TODO/CIRA` | COSPAR 国际参考大气 1986 — 0–120 km 温度、气压、纬向风、位势高度 | Fortran 77 | 24 个二进制 + 12 个 ASCII 月均表格 |
| Jacchia 1977 | `TODO/Jacchi-Reference-Atmosphere` | Jacchia 参考大气 — 90–2500+ km 温度与数密度剖面（N2, O2, O, Ar, He, H） | Fortran 77 | 无（硬编码系数） |
| MET | `TODO/MET-Model` | 马歇尔工程热层模型 — 改进的 Jacchia 1970/71 热层模型，面向工程应用 | Fortran 77 | 无（硬编码系数） |
| MSIS-86 | `TODO/MSIS/MSIS86` | MSIS-86 / CIRA-86 热层模型 — MSIS 历史版本 | Fortran 77 | `msis86.dat`（二进制系数） |
| MSISE-90 | `TODO/MSIS/MSIS90` | MSISE-90 — 将 MSIS-86 向下延伸至地面 | Fortran 77 | 无（硬编码系数） |
| Chiu 电离层模型 | `TODO/Chiu-Ionospheric-Model` | 经验电离层电子密度模型 — E、F1、F2 层电子密度（90–500 km） | Fortran 77 | 无（硬编码系数） |

### 第二阶段 — 磁层与辐射带模型

这些模型涉及磁层物理和辐射环境，是空间天气和航天任务规划的关键。

| 模型 | 目录 | 说明 | 原始语言 | 外部数据 |
|------|------|------|----------|----------|
| Tsyganenko（T89/T96/T01/TS04） | `TODO/Tsyganenko-Models` | 数据驱动的磁层磁场模型 — 外源磁场贡献、磁力线追踪 | Fortran 77 | 无（硬编码系数）；含 Geopack-2005 |
| RADBELT（AP8/AE8） | `TODO/RADBELT` | 捕获辐射环境模型 — 全向质子/电子通量（AP8MAX/MIN, AE8MAX/MIN） | Fortran 77 / C | 8 个二进制/ASCII 通量地图（各约 80K） |
| SHIELDOSE | `TODO/SHIELDOSE` | 铝屏蔽后的辐射剂量 — 捕获带、太阳质子、电子环境 | Fortran 77 | `shieldose.dat`（二进制剂量-深度数据） |
| SOLPRO | `TODO/SOLPRO` | 1 AU 行星际太阳质子积分通量 — 基于任务时长和置信水平 | Fortran IV | 无（硬编码系数） |
| SOFIP | `TODO/SOFIP` | 短轨道通量积分程序 — 沿航天器轨道计算任务平均通量，使用 AP8/AE8 | Fortran 77 | 二进制辐射带地图 |
| 地磁截止刚度 | `TODO/Geomagnetic-Cutoff-Rigidity` | 宇宙线截止刚度阈值 — 带电粒子轨迹预测 | Fortran 77 | 无（内部使用 IGRF） |

### 第三阶段 — 地磁与电场模型

球谐地磁场模型和高纬电离层电场模型。

| 模型 | 目录 | 说明 | 原始语言 | 外部数据 |
|------|------|------|----------|----------|
| GSFC 模型 | `TODO/GSFC-Model-Coefficients` | GSFC 地磁场模型（9/65, 12/66, 10/68, 8/69, 80, 83, 87） — 任意位置磁场分量 | Fortran 77 | 5 个二进制 `.dat` 系数文件 |
| Jensen & Cain (1962) | `TODO/Jensen-Cain-Model-Coefficients` | 早期球谐地磁场模型（12 阶，约 1962 历元） | Fortran 77 | `jensen_cain_62.dat`（二进制） |
| MGST 系数 | `TODO/MGST-Model-Coefficients-All` | MGST 地磁场模型系数（1980、1981 历元） | 纯数据 | 2 个二进制 `.dat` 文件 |
| Heppner-Maynard-Rich | `TODO/Heppner-Maynard-Rich_Electric-Field-Model` | 高纬电离层电势模型 — 球谐拟合，焦耳加热 | Fortran 77 | `hmcoef.dat`（二进制） |
| ISR 离子漂移 | `TODO/ISR-Ion-Drift-Model` | 非相干散射雷达离子漂移模型 — 静日 E×B 漂移（300 km） | Fortran 77 | 无（硬编码系数） |
| 极光卵 | `TODO/Auroral-Oval-Representation` | Feldstein 极光卵边界模型 — 傅里叶级数参数化的极向/赤道向边界 | Fortran 77/90 | 无（硬编码系数） |
| Xu-Li 中性片 | `TODO/Xu-Li-Neutral-Sheet-Model` | 磁尾赤道中性片位置模型（SEN, DEN, AEN 三种变体） | Fortran 77 | 无（硬编码系数） |

### 第四阶段 — 太阳辐照度与行星模型

太阳极紫外通量模型和行星大气模型。

| 模型 | 目录 | 说明 | 原始语言 | 外部数据 |
|------|------|------|----------|----------|
| EUV（AE-EUV / EUV91 / EUVAC / SOLAR2000） | `TODO/EUV` | 太阳极紫外辐照度模型（18–1050 Å）— 热层/电离层输入 | Fortran 77 | 系数文件、代理指数、参考光谱 |
| 光电子模型 | `TODO/photoelectron_code` | 光电子通量模型 — 120–500 km，太阳天顶角驱动 | Fortran 77 | 无（硬编码系数） |
| 金星电离层 | `TODO/PV-Ionosphere-Mode` | 金星电离层电子密度与温度 — 太阳天顶角与高度 | Fortran 77 | `fsmod.dat`、`fsmodt.dat`（二进制） |
| 金星热层 | `TODO/PV-Thermosphere-Model` | 金星中性大气密度（CO2, O, CO, He, N, N2）— 类 MSIS 结构 | Fortran 77 | 无（硬编码系数） |
| 外逸层氢模型 | `TODO/Exospheric-H-Model` | 外逸层氢密度（40 个半径 × 4 种太阳条件）— 球谐展开 | 纯数据 | `h_exos.dat`（二进制） |

### 不计划移植

以下内容为纯文档、Java 工具或重复项，不纳入 Python 封装计划。

| 项目 | 目录 | 原因 |
|------|------|------|
| 归档模型信息页 | `TODO/Archived-Models-InfoPages` | 仅 HTML 文档目录 — 无源码 |
| Revised SERF2 太阳 EUV 通量 | `TODO/Revised-SERF2-Solar-EUV-Flux-Mode` | 与 `TODO/EUV` 内容重复 |
| LWS / MineTool | `TODO/LWS` | 基于 Java 的数据挖掘工具 — 非 Fortran/C 模型 |
| HWM93（TODO 目录内） | `TODO/HWM93` | 已移植为 `model.HWM93` |

## 移植规范

每个模型移植应遵循 `AGENTS.md` 中的既定约定：

1. **源码布局**：在 `src/model/` 下创建子目录（如 `src/model/pyigrf/`）。
2. **构建系统**：将 Fortran/C 源码加入 `CMakeLists.txt`，新增目标生成共享库（DLL/.so/.dylib）。
3. **Python 封装**：实现 `Model` 类，提供唯一的 `calculate(...)` 方法，仅接受关键字参数。
4. **懒加载**：在 `src/model/__init__.py` 中通过 `_LAZY_EXPORTS` 注册新类。
5. **模块 `__all__`**：每个模型模块只导出 `["Model"]`。
6. **返回值**：`calculate(...)` 返回普通 `dict`。
7. **测试**：在 `tests/` 中添加至少一个测试，在 `example/` 中添加示例脚本。
8. **工具函数**：共享辅助代码放在 `src/utils/`，不要放在 `src/model/`。
