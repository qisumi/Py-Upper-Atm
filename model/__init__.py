"""
UpperAtmPy 模型接口包
提供大气温度、密度和风场计算的统一接口。
"""

from .temp_density_model import (
    TempDensityModel,
    TempDensityResult,
    convert_date_to_day,
    calculate_seconds_of_day,
)

from .wind_model import (
    WindModel,
    WindResult,
    calculate_wind_at_point,
    calculate_wind_batch,
)

from .xarray_output import (
    temp_density_results_to_xarray,
    wind_results_to_xarray,
)

from .space_weather import (
    SpaceWeatherIndices,
    get_indices,
)

from .cache import (
    CachedModel,
    CachedWindModel,
)

from .parallel import (
    parallel_map,
    parallel_batch_compute,
)

__all__ = [
    "TempDensityModel",
    "TempDensityResult",
    "convert_date_to_day",
    "calculate_seconds_of_day",
    "WindModel",
    "WindResult",
    "calculate_wind_at_point",
    "calculate_wind_batch",
    "temp_density_results_to_xarray",
    "wind_results_to_xarray",
    "SpaceWeatherIndices",
    "get_indices",
    "CachedModel",
    "CachedWindModel",
    "parallel_map",
    "parallel_batch_compute",
]
