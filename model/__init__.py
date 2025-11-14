"""
UpperAtmPy 模型接口包
提供大气温度、密度和风场计算的统一接口。
"""

from .temp_density_model import (
    TempDensityModel,
    TempDensityResult,
    convert_date_to_day,
    calculate_seconds_of_day
)

from .wind_model import (
    WindModel,
    calculate_wind_at_point,
    calculate_wind_batch
)

__all__ = [
    # 温度密度模型相关
    "TempDensityModel",
    "TempDensityResult",
    "convert_date_to_day",
    "calculate_seconds_of_day",
    # 风场模型相关
    "WindModel",
    "calculate_wind_at_point",
    "calculate_wind_batch"
]
