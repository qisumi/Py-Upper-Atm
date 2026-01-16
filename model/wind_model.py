"""
风场模型接口
支持 HWM14 和 HWM93 模型，提供统一的大气风场计算功能。
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Iterable, List, Literal, Optional, Tuple, Union

if TYPE_CHECKING:
    import xarray as xr

try:
    from .pyhwm14 import hwm14_eval, hwm14_eval_many

    _has_hwm14 = True
except ImportError:
    _has_hwm14 = False
    hwm14_eval = None
    hwm14_eval_many = None

try:
    from .pyhwm93 import hwm93_eval, hwm93_eval_many

    _has_hwm93 = True
except ImportError:
    _has_hwm93 = False
    hwm93_eval = None
    hwm93_eval_many = None

if not _has_hwm14 and not _has_hwm93:
    raise ImportError("风场模型组件加载失败：HWM14 和 HWM93 均不可用")

ModelVersion = Literal["hwm14", "hwm93"]


def _validate_wind_inputs(
    alt_km: float,
    glat_deg: float,
    glon_deg: float,
    sec: Optional[float] = None,
    stl_hours: Optional[float] = None,
    f107a: Optional[float] = None,
    f107: Optional[float] = None,
) -> None:
    if alt_km < 0 or alt_km > 1000:
        raise ValueError(f"alt_km 必须在 0-1000 km 范围内，当前值: {alt_km}")
    if glat_deg < -90 or glat_deg > 90:
        raise ValueError(f"glat_deg 必须在 -90 到 90 度范围内，当前值: {glat_deg}")
    if glon_deg < -180 or glon_deg > 360:
        raise ValueError(f"glon_deg 必须在 -180 到 360 度范围内，当前值: {glon_deg}")
    if sec is not None and (sec < 0 or sec > 86400):
        raise ValueError(f"sec 必须在 0-86400 秒范围内，当前值: {sec}")
    if stl_hours is not None and (stl_hours < 0 or stl_hours > 24):
        raise ValueError(f"stl_hours 必须在 0-24 小时范围内，当前值: {stl_hours}")
    if f107a is not None and f107a < 0:
        raise ValueError(f"f107a 必须为非负数，当前值: {f107a}")
    if f107 is not None and f107 < 0:
        raise ValueError(f"f107 必须为非负数，当前值: {f107}")


@dataclass
class WindResult:
    """
    风场计算结果

    Attributes:
        alt_km: 高度（公里）
        meridional_wind_ms: 经向风速度 (m/s)，正值表示向北
        zonal_wind_ms: 纬向风速度 (m/s)，正值表示向东
    """

    alt_km: float
    meridional_wind_ms: float
    zonal_wind_ms: float


class WindModel:
    """
    风场模型
    提供大气风场的计算功能，支持 HWM14 和 HWM93 两种模型。
    """

    def __init__(self, model_version: ModelVersion = "hwm14"):
        """
        初始化风场模型

        Args:
            model_version: 模型版本，可选 "hwm14"（默认）或 "hwm93"
        """
        self._model_version = model_version.lower().strip()

        if self._model_version == "hwm14":
            if not _has_hwm14:
                raise RuntimeError("HWM14 模型组件未正确加载")
            self._eval_func = hwm14_eval
            self._eval_many_func = hwm14_eval_many
        elif self._model_version == "hwm93":
            if not _has_hwm93:
                raise RuntimeError("HWM93 模型组件未正确加载")
            self._eval_func = hwm93_eval
            self._eval_many_func = hwm93_eval_many
        else:
            raise ValueError(
                f"不支持的模型版本: {model_version}，可选: 'hwm14', 'hwm93'"
            )

    @property
    def model_version(self) -> str:
        """返回当前使用的模型版本"""
        return self._model_version

    def calculate_point(
        self,
        iyd: int,
        sec: float,
        alt_km: float,
        glat_deg: float,
        glon_deg: float,
        stl_hours: float,
        f107a: float,
        f107: float,
        ap2: Iterable[float] = (0.0, 20.0),
        validate: bool = True,
    ) -> WindResult:
        """
        计算单点的风场

        Args:
            iyd: 日历年+儒略日（YYYYDDD），如 2025290
            sec: UTC 秒（0..86400）
            alt_km: 高度 km
            glat_deg: 纬度 deg
            glon_deg: 经度 deg（东经为正）
            stl_hours: 本地太阳时（小时）
            f107a: 81日滑动平均 F10.7
            f107: 日 F10.7
            ap2: 地磁活动指数，长度为 2 的数组；ap2[0] 常未用，ap2[1]=当前 3h ap
            validate: 是否验证输入参数范围（默认True）

        Returns:
            WindResult: 包含经向风和纬向风的结果对象
        """
        if validate:
            _validate_wind_inputs(
                alt_km=alt_km,
                glat_deg=glat_deg,
                glon_deg=glon_deg,
                sec=sec,
                stl_hours=stl_hours,
                f107a=f107a,
                f107=f107,
            )
        meridional, zonal = self._eval_func(
            iyd=iyd,
            sec=sec,
            alt_km=alt_km,
            glat_deg=glat_deg,
            glon_deg=glon_deg,
            stl_hours=stl_hours,
            f107a=f107a,
            f107=f107,
            ap2=ap2,
        )
        return WindResult(
            alt_km=float(alt_km),
            meridional_wind_ms=float(meridional),
            zonal_wind_ms=float(zonal),
        )

    def calculate_point_at_datetime(
        self,
        *,
        dt: datetime,
        alt_km: float,
        glat_deg: float,
        glon_deg: float,
        f107a: float,
        f107: float,
        ap2: Iterable[float] = (0.0, 20.0),
        validate: bool = True,
    ) -> WindResult:
        """
        使用 datetime 对象计算单点的风场

        Args:
            dt: Python datetime 对象（UTC时间）
            alt_km: 高度 km
            glat_deg: 纬度 deg
            glon_deg: 经度 deg（东经为正）
            f107a: 81日滑动平均 F10.7
            f107: 日 F10.7
            ap2: 地磁活动指数，长度为 2 的数组
            validate: 是否验证输入参数范围（默认True）

        Returns:
            WindResult: 包含经向风和纬向风的结果对象
        """
        day_of_year = dt.timetuple().tm_yday
        iyd = dt.year * 1000 + day_of_year
        sec = dt.hour * 3600.0 + dt.minute * 60.0 + dt.second + dt.microsecond / 1e6
        stl_hours = (sec / 3600.0 + glon_deg / 15.0) % 24.0
        return self.calculate_point(
            iyd=iyd,
            sec=sec,
            alt_km=alt_km,
            glat_deg=glat_deg,
            glon_deg=glon_deg,
            stl_hours=stl_hours,
            f107a=f107a,
            f107=f107,
            ap2=ap2,
            validate=validate,
        )

    def calculate_batch(
        self,
        iyd: Union[int, Iterable[int]],
        sec: Union[float, Iterable[float]],
        alt_km: Union[float, Iterable[float]],
        glat_deg: Union[float, Iterable[float]],
        glon_deg: Union[float, Iterable[float]],
        stl_hours: Union[float, Iterable[float]],
        f107a: Union[float, Iterable[float]],
        f107: Union[float, Iterable[float]],
        ap2: Iterable[float] = (0.0, 20.0),
        output_as_tuple: bool = False,
        output_as_xarray: bool = False,
        parallel: bool = False,
        max_workers: Optional[int] = None,
    ) -> Union[List[WindResult], Tuple[object, object], "xr.Dataset"]:
        """
        批量计算风场
        接受任意能广播到共同形状的数组/标量

        Args:
            iyd: 日历年+儒略日（YYYYDDD），可接受标量或数组
            sec: UTC 秒（0..86400），可接受标量或数组
            alt_km: 高度 km，可接受标量或数组
            glat_deg: 纬度 deg，可接受标量或数组
            glon_deg: 经度 deg（东经为正），可接受标量或数组
            stl_hours: 本地太阳时（小时），可接受标量或数组
            f107a: 81日滑动平均 F10.7，可接受标量或数组
            f107: 日 F10.7，可接受标量或数组
            ap2: 地磁活动指数，长度为 2 的数组；ap2[0] 常未用，ap2[1]=当前 3h ap
            output_as_tuple: 若为 True，返回原始 (wm, wz) 数组元组；否则返回 WindResult 列表
            output_as_xarray: 是否以 xarray.Dataset 形式返回结果（需要安装 xarray）
            parallel: 是否使用多线程并行计算（GIL在ctypes调用时释放）
            max_workers: 并行时最大线程数（默认为CPU核心数，最多8）

        Returns:
            WindResult 列表、(经向风数组, 纬向风数组) 元组或 xarray.Dataset
        """
        if parallel:
            results = self._calculate_batch_parallel(
                iyd=iyd,
                sec=sec,
                alt_km=alt_km,
                glat_deg=glat_deg,
                glon_deg=glon_deg,
                stl_hours=stl_hours,
                f107a=f107a,
                f107=f107,
                ap2=ap2,
                max_workers=max_workers,
            )
            if output_as_xarray:
                from .xarray_output import wind_results_to_xarray

                return wind_results_to_xarray(
                    results,
                    alt_km=alt_km,
                    lat_deg=glat_deg,
                    lon_deg=glon_deg,
                    model_version=self._model_version,
                )
            if output_as_tuple:
                import numpy as np

                wm = np.array([r.meridional_wind_ms for r in results])
                wz = np.array([r.zonal_wind_ms for r in results])
                return wm, wz
            return results

        if output_as_xarray:
            from .xarray_output import wind_results_to_xarray

            results = self._calculate_batch_internal(
                iyd=iyd,
                sec=sec,
                alt_km=alt_km,
                glat_deg=glat_deg,
                glon_deg=glon_deg,
                stl_hours=stl_hours,
                f107a=f107a,
                f107=f107,
                ap2=ap2,
            )
            return wind_results_to_xarray(
                results,
                alt_km=alt_km,
                lat_deg=glat_deg,
                lon_deg=glon_deg,
                model_version=self._model_version,
            )

        if output_as_tuple:
            wm, wz = self._eval_many_func(
                iyd=iyd,
                sec=sec,
                alt_km=alt_km,
                glat_deg=glat_deg,
                glon_deg=glon_deg,
                stl_hours=stl_hours,
                f107a=f107a,
                f107=f107,
                ap2=ap2,
            )
            return wm, wz

        return self._calculate_batch_internal(
            iyd=iyd,
            sec=sec,
            alt_km=alt_km,
            glat_deg=glat_deg,
            glon_deg=glon_deg,
            stl_hours=stl_hours,
            f107a=f107a,
            f107=f107,
            ap2=ap2,
        )

    def _calculate_batch_parallel(
        self,
        *,
        iyd,
        sec,
        alt_km,
        glat_deg,
        glon_deg,
        stl_hours,
        f107a,
        f107,
        ap2,
        max_workers,
    ) -> List[WindResult]:
        from .parallel import parallel_batch_compute
        import numpy as np

        def _to_array(x):
            if isinstance(x, (int, float)):
                return [x]
            return list(x)

        iyd_arr = _to_array(iyd)
        sec_arr = _to_array(sec)
        alt_arr = _to_array(alt_km)
        lat_arr = _to_array(glat_deg)
        lon_arr = _to_array(glon_deg)
        stl_arr = _to_array(stl_hours)
        f107a_arr = _to_array(f107a)
        f107_arr = _to_array(f107)

        N = max(
            len(iyd_arr),
            len(sec_arr),
            len(alt_arr),
            len(lat_arr),
            len(lon_arr),
            len(stl_arr),
            len(f107a_arr),
            len(f107_arr),
        )

        def _get(arr, i):
            return arr[i % len(arr)]

        param_dicts = [
            {
                "iyd": _get(iyd_arr, i),
                "sec": _get(sec_arr, i),
                "alt_km": _get(alt_arr, i),
                "glat_deg": _get(lat_arr, i),
                "glon_deg": _get(lon_arr, i),
                "stl_hours": _get(stl_arr, i),
                "f107a": _get(f107a_arr, i),
                "f107": _get(f107_arr, i),
                "ap2": ap2,
                "validate": False,
            }
            for i in range(N)
        ]

        return parallel_batch_compute(
            self.calculate_point, param_dicts, max_workers=max_workers
        )

    def _calculate_batch_internal(
        self, *, iyd, sec, alt_km, glat_deg, glon_deg, stl_hours, f107a, f107, ap2
    ) -> List[WindResult]:
        wm, wz = self._eval_many_func(
            iyd=iyd,
            sec=sec,
            alt_km=alt_km,
            glat_deg=glat_deg,
            glon_deg=glon_deg,
            stl_hours=stl_hours,
            f107a=f107a,
            f107=f107,
            ap2=ap2,
        )

        import numpy as np

        alt_arr = np.atleast_1d(np.asarray(alt_km, dtype=np.float32))
        wm_flat = np.asarray(wm).flatten()
        wz_flat = np.asarray(wz).flatten()

        if len(alt_arr) == 1:
            alt_arr = np.full(len(wm_flat), alt_arr[0])
        else:
            alt_arr = alt_arr.flatten()

        return [
            WindResult(
                alt_km=float(alt_arr[i % len(alt_arr)]),
                meridional_wind_ms=float(wm_flat[i]),
                zonal_wind_ms=float(wz_flat[i]),
            )
            for i in range(len(wm_flat))
        ]


def calculate_wind_at_point(
    iyd: int,
    sec: float,
    alt_km: float,
    glat_deg: float,
    glon_deg: float,
    stl_hours: float,
    f107a: float,
    f107: float,
    ap2: Iterable[float] = (0.0, 20.0),
    model_version: ModelVersion = "hwm14",
) -> WindResult:
    """
    便捷函数：计算单点的风场

    Args:
        iyd: 日历年+儒略日（YYYYDDD），如 2025290
        sec: UTC 秒（0..86400）
        alt_km: 高度 km
        glat_deg: 纬度 deg
        glon_deg: 经度 deg（东经为正）
        stl_hours: 本地太阳时（小时）
        f107a: 81日滑动平均 F10.7
        f107: 日 F10.7
        ap2: 地磁活动指数，长度为 2 的数组
        model_version: 模型版本，可选 "hwm14"（默认）或 "hwm93"

    Returns:
        WindResult: 包含经向风和纬向风的结果对象
    """
    model = WindModel(model_version=model_version)
    return model.calculate_point(
        iyd=iyd,
        sec=sec,
        alt_km=alt_km,
        glat_deg=glat_deg,
        glon_deg=glon_deg,
        stl_hours=stl_hours,
        f107a=f107a,
        f107=f107,
        ap2=ap2,
    )


def calculate_wind_batch(
    iyd,
    sec,
    alt_km,
    glat_deg,
    glon_deg,
    stl_hours,
    f107a,
    f107,
    ap2=(0.0, 20.0),
    model_version: ModelVersion = "hwm14",
    output_as_tuple: bool = False,
) -> Union[List[WindResult], Tuple[object, object]]:
    """
    便捷函数：批量计算风场
    接受任意能广播到共同形状的数组/标量

    Args:
        iyd: 日历年+儒略日（YYYYDDD），可接受标量或数组
        sec: UTC 秒（0..86400），可接受标量或数组
        alt_km: 高度 km，可接受标量或数组
        glat_deg: 纬度 deg，可接受标量或数组
        glon_deg: 经度 deg（东经为正），可接受标量或数组
        stl_hours: 本地太阳时（小时），可接受标量或数组
        f107a: 81日滑动平均 F10.7，可接受标量或数组
        f107: 日 F10.7，可接受标量或数组
        ap2: 地磁活动指数，长度为 2 的数组
        model_version: 模型版本，可选 "hwm14"（默认）或 "hwm93"
        output_as_tuple: 若为 True，返回原始数组元组

    Returns:
        WindResult 列表或 (经向风数组, 纬向风数组) 元组，单位 m/s
    """
    model = WindModel(model_version=model_version)
    return model.calculate_batch(
        iyd=iyd,
        sec=sec,
        alt_km=alt_km,
        glat_deg=glat_deg,
        glon_deg=glon_deg,
        stl_hours=stl_hours,
        f107a=f107a,
        f107=f107,
        ap2=ap2,
        output_as_tuple=output_as_tuple,
    )


__all__ = ["WindModel", "WindResult", "calculate_wind_at_point", "calculate_wind_batch"]
