
#show raw.where(block: true): it => block(
  width: 100%,                 // 占满行宽
  inset:  0.65em,              // 内边距
  radius: 4pt,                 // 圆角
  fill:   rgb("#f6f8fa"),      // 浅灰背景（GitHub 风格）
  stroke: 0.9pt + rgb("#d0d7de"), // 1 px 浅灰边框
  it                        // 原始代码内容保持不动
)

= UpperAtmPy 模型使用说明

本文档提供了如何使用 UpperAtmPy 中的温度密度模型和风场模型进行大气参数计算的简明指导。

== 快速开始

=== 基本导入

```python
from model import TempDensityModel, WindModel, convert_date_to_day, calculate_seconds_of_day
```

=== 运行示例脚本

项目根目录下提供了完整的示例脚本，可直接运行查看效果：

```bash
python quick_run.py
```

== 温度密度模型

=== 模型初始化

```python
# 创建默认配置的模型实例
model = TempDensityModel()

# 自定义DLL路径和精度
model = TempDensityModel(
    dll_path="path/to/nrlmsis2.dll",  = 可选：指定DLL路径
    precision="double",              = 可选：计算精度，"single"或"double"
    add_mingw_bin=True               = 可选：添加MinGW路径到DLL搜索
)
```

=== 单点计算

```python
# 准备时间参数
day_of_year = convert_date_to_day(2023, 1, 1)  = 2023年1月1日 -> 年内日数1.0
seconds_of_day = calculate_seconds_of_day(12, 0, 0)  = 12:00:00 -> 43200秒

# 执行单点计算
result = model.calculate_point(
    day=day_of_year,              = 年内日数
    utsec=seconds_of_day,         = UTC时间（秒）
    alt_km=100.0,                 = 高度（公里）
    lat_deg=35.0,                 = 纬度（度）
    lon_deg=116.0,                = 经度（度）
    f107a=100.0,                  = 81天平均F10.7太阳通量
    f107=100.0,                   = 当天F10.7太阳通量
    ap7=None                      = 地磁活动指数（None表示使用默认值）
)

# 获取结果
print(f"局部温度: {result.T_local_K:.2f} K")
print(f"外温度: {result.T_exo_K:.2f} K")
print(f"N2密度: {result.densities[0]:.2e} cm^-3")
print(f"O2密度: {result.densities[1]:.2e} cm^-3")
print(f"O密度: {result.densities[2]:.2e} cm^-3")
```

=== 批量计算

```python
# 准备多个高度点
altitudes = [80.0, 100.0, 120.0, 150.0]

#= 批量计算结果（返回结果对象列表）
batch_results = model.calculate_batch(
    day=day_of_year,
    utsec=seconds_of_day,
    alt_km=altitudes,     = 可以是列表
    lat_deg=35.0,         = 标量会自动广播
    lon_deg=116.0,
    f107a=100.0,
    f107=100.0,
    output_as_dict=False  = 返回结果对象列表
)

# 遍历结果
for res in batch_results:
    print(f"高度: {res.alt_km} km, 温度: {res.T_local_K} K")

# 或返回字典形式结果（适合处理大量数据）
dict_results = model.calculate_batch(
    # ... 同上的参数 ...
    output_as_dict=True  = 返回字典形式结果
)
print(dict_results.keys())  = ['alt_km', 'T_local_K', 'T_exo_K', 'densities']
```

== 风场模型

=== 模型初始化

```python
# 创建风场模型实例
model = WindModel()
```

=== 单点计算

```python
# 执行单点计算
meridional_wind, zonal_wind = model.calculate_point(
    iyd=2023001,          = 日历年+儒略日（YYYYDDD）
    sec=43200.0,          = UTC秒（0-86400）
    alt_km=100.0,         = 高度（公里）
    glat_deg=35.0,        = 纬度（度）
    glon_deg=116.0,       = 经度（度）
    stl_hours=12.0,       = 本地太阳时（小时）
    f107a=100.0,          = 81天平均F10.7太阳通量
    f107=100.0,           = 当天F10.7太阳通量
    ap2=(0.0, 20.0)       = 地磁活动指数
)

print(f"经向风（南北向）: {meridional_wind:.2f} m/s")
print(f"纬向风（东西向）: {zonal_wind:.2f} m/s")
```

=== 批量计算

```python
# 准备多个高度点
altitudes = [80.0, 100.0, 120.0, 150.0]

# 批量计算
meridional_winds, zonal_winds = model.calculate_batch(
    iyd=2023001,
    sec=43200.0,
    alt_km=altitudes,
    glat_deg=35.0,
    glon_deg=116.0,
    stl_hours=12.0,
    f107a=100.0,
    f107=100.0,
    ap2=(0.0, 20.0)
)

# 遍历结果
for i, alt in enumerate(altitudes):
    print(f"高度: {alt} km, 经向风: {meridional_winds[i]} m/s, 纬向风: {zonal_winds[i]} m/s")
```

=== 便捷函数

除了使用类方法，还可以直接使用便捷函数：

```python
from model import calculate_wind_at_point, calculate_wind_batch

# 单点计算
wind_ns, wind_ew = calculate_wind_at_point(
    iyd=2023001,
    sec=43200.0,
    alt_km=100.0,
    glat_deg=35.0,
    glon_deg=116.0,
    stl_hours=12.0,
    f107a=100.0,
    f107=100.0,
    ap2=(0.0, 20.0)
)

# 批量计算
winds_ns, winds_ew = calculate_wind_batch(
    # ... 同上的参数 ...
)
```

== 参数说明

=== 时间参数

- **温度密度模型**：
  - `day`：年内日数（1-366），可通过 `convert_date_to_day(year, month, day)` 计算
  - `utsec`：UTC时间（秒，0-86400），可通过 `calculate_seconds_of_day(hour, minute, second)` 计算

- **风场模型**：
  - `iyd`：日历年+儒略日（格式为YYYYDDD）
  - `sec`：UTC时间（秒，0-86400）
  - `stl_hours`：本地太阳时（小时，0-24）

=== 位置参数

- `alt_km`：高度（公里）
- `lat_deg`/`glat_deg`：纬度（度，北纬为正）
- `lon_deg`/`glon_deg`：经度（度，东经为正）

=== 太阳活动和地磁参数

- `f107a`：81天平均F10.7太阳通量
- `f107`：当天F10.7太阳通量
- `ap7`（温度密度模型）：长度为7的地磁活动指数数组
- `ap2`（风场模型）：长度为2的地磁活动指数数组

== 结果解析

=== 温度密度模型结果

`TempDensityResult` 对象包含以下属性：

- `alt_km`：高度（公里）
- `T_local_K`：局部温度（开尔文）
- `T_exo_K`：外温度（开尔文）
- `densities`：各成分数密度（10^6 cm^-3），顺序为：
  1. N2（氮气）
  2. O2（氧气）
  3. O（原子氧）
  4. He（氦气）
  5. H（氢气）
  6. Ar（氩气）
  7. N（原子氮）
  8. AnomalousO（异常氧）
  9. NO（一氧化氮）
  10. NPlus（氮离子）

=== 风场模型结果

- 返回值为元组 `(经向风, 纬向风)`，单位均为 m/s：
  - **经向风**（南北向）：正值表示向北，负值表示向南
  - **纬向风**（东西向）：正值表示向东，负值表示向西

== 注意事项

1. 确保模型DLL文件在正确的位置或通过参数指定
2. 对于批量计算，所有数组参数需要能够广播到共同形状
3. 输入参数单位必须正确：高度为公里，角度为度，时间为秒
4. 太阳活动和地磁指数应使用实际观测值以获得准确结果

== 示例文件

完整的示例代码可在 `quick_run.py` 中找到，包含了单点和批量计算的详细演示。