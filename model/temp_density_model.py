"""
温度和密度模型接口
支持 NRLMSIS-2.0 和 NRLMSISE-00 模型，提供统一的温度和密度计算功能。
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Sequence, Tuple, Union

if TYPE_CHECKING:
    import xarray as xr

# 尝试导入 MSIS-2.0 模型
try:
    from .pymsis2 import NRLMSIS2, MSISResult, doy, seconds_of_day

    _has_msis2 = True
except ImportError:
    _has_msis2 = False
    NRLMSIS2 = None
    MSISResult = None

# 尝试导入 MSIS-00 模型
try:
    from .pymsis00 import gtd7, gtd7_batch, MSIS00

    _has_msis00 = True
except ImportError:
    _has_msis00 = False
    gtd7 = None
    gtd7_batch = None
    MSIS00 = None

# 至少需要一个模型可用
if not _has_msis2 and not _has_msis00:
    raise ImportError("温度密度模型组件加载失败：MSIS-2.0 和 MSIS-00 均不可用")

# 如果 pymsis2 可用，导入工具函数
if _has_msis2:
    from .pymsis2 import doy, seconds_of_day
else:
    # 如果只有 MSIS-00 可用，提供基本的工具函数
    import datetime as _dt

    def doy(year: int, month: int, day: int) -> float:
        """将 (year, month, day) 转换为年内日（浮点），不含闰秒。"""
        d0 = _dt.date(year, 1, 1)
        d = _dt.date(year, month, day)
        return float((d - d0).days + 1)

    def seconds_of_day(hour: int, minute: int = 0, second: float = 0.0) -> float:
        """一天内秒数（0~86400），可带小数秒。"""
        return float(hour) * 3600.0 + float(minute) * 60.0 + float(second)


# 支持的模型版本
ModelVersion = Literal["msis2", "msis00"]


@dataclass
class TempDensityResult:
    """
    温度和密度计算结果

    Attributes:
        alt_km: 高度（公里）
        T_local_K: 局部温度（开尔文）
        T_exo_K: 外温度（开尔文）
        densities: 各成分数密度，格式取决于模型版本：
            - MSIS-2.0: (N2, O2, O, He, H, Ar, N, AnomalousO, NO, NPlus) [10^6 cm^-3]
            - MSIS-00: (He, O, N2, O2, Ar, H, N, AnomalousO, TotalMass) [cm^-3 或 g/cm^3]
    """

    alt_km: float
    T_local_K: float
    T_exo_K: float
    densities: Tuple[float, ...]


class TempDensityModel:
    """
    温度和密度模型
    提供大气温度和密度的计算功能，支持 MSIS-2.0 和 MSIS-00 两种模型。
    """

    def __init__(
        self,
        model_version: ModelVersion = "msis2",
        dll_path: Optional[Union[str, str]] = None,
        *,
        precision: str = "single",
        add_mingw_bin: bool = False,
        extra_dll_dirs: Optional[Sequence[Union[str, str]]] = None,
    ):
        """
        初始化温度密度模型

        Args:
            model_version: 模型版本，可选 "msis2"（NRLMSIS-2.0，默认）或 "msis00"（NRLMSISE-00）
            dll_path: 模型DLL文件路径，若为None则使用默认路径
            precision: 计算精度，可选"single"(单精度)或"double"(双精度)，仅对 MSIS-2.0 有效
            add_mingw_bin: 是否添加MinGW二进制目录到DLL搜索路径，仅对 MSIS-2.0 有效
            extra_dll_dirs: 额外的DLL搜索目录列表，仅对 MSIS-2.0 有效
        """
        self._model_version = model_version.lower().strip()

        if self._model_version == "msis2":
            if not _has_msis2:
                raise RuntimeError("NRLMSIS-2.0 模型组件未正确加载")
            self._model = NRLMSIS2(
                dll_path=dll_path,
                precision=precision,
                add_mingw_bin=add_mingw_bin,
                extra_dll_dirs=extra_dll_dirs,
            )
            self._backend = "msis2"
        elif self._model_version == "msis00":
            if not _has_msis00:
                raise RuntimeError("NRLMSISE-00 模型组件未正确加载")
            self._model = MSIS00()
            self._backend = "msis00"
        else:
            raise ValueError(
                f"不支持的模型版本: {model_version}，可选: 'msis2', 'msis00'"
            )

    @property
    def model_version(self) -> str:
        """返回当前使用的模型版本"""
        return self._model_version

    def calculate_point(
        self,
        *,
        day: float,
        utsec: float,
        alt_km: float,
        lat_deg: float,
        lon_deg: float,
        f107a: float,
        f107: float,
        ap7: Optional[Sequence[float]] = None,
        validate: bool = True,
    ) -> TempDensityResult:
        """
        计算单点的温度和密度

        Args:
            day: 年内日数（1-366）
            utsec: UTC时间（秒，0-86400）
            alt_km: 高度（公里）
            lat_deg: 纬度（度）
            lon_deg: 经度（度）
            f107a: 81天平均F10.7太阳通量
            f107: 当天F10.7太阳通量
            ap7: 地磁活动指数，长度为7的序列，若为None则使用默认值
            validate: 是否验证输入参数范围（默认True）

        Returns:
            TempDensityResult: 包含温度和密度结果的对象
        """
        if validate:
            _validate_temp_density_inputs(
                alt_km=alt_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                day=day,
                utsec=utsec,
                f107a=f107a,
                f107=f107,
            )
        if self._backend == "msis2":
            return self._calculate_point_msis2(
                day=day,
                utsec=utsec,
                alt_km=alt_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                f107a=f107a,
                f107=f107,
                ap7=ap7,
            )
        else:
            return self._calculate_point_msis00(
                day=day,
                utsec=utsec,
                alt_km=alt_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                f107a=f107a,
                f107=f107,
                ap7=ap7,
            )

    def calculate_point_at_datetime(
        self,
        *,
        dt: datetime,
        alt_km: float,
        lat_deg: float,
        lon_deg: float,
        f107a: float,
        f107: float,
        ap7: Optional[Sequence[float]] = None,
        validate: bool = True,
    ) -> TempDensityResult:
        """
        使用 datetime 对象计算单点的温度和密度

        Args:
            dt: Python datetime 对象（UTC时间）
            alt_km: 高度（公里）
            lat_deg: 纬度（度）
            lon_deg: 经度（度）
            f107a: 81天平均F10.7太阳通量
            f107: 当天F10.7太阳通量
            ap7: 地磁活动指数，长度为7的序列，若为None则使用默认值
            validate: 是否验证输入参数范围（默认True）

        Returns:
            TempDensityResult: 包含温度和密度结果的对象
        """
        day_of_year = float(dt.timetuple().tm_yday)
        utsec = dt.hour * 3600.0 + dt.minute * 60.0 + dt.second + dt.microsecond / 1e6
        return self.calculate_point(
            day=day_of_year,
            utsec=utsec,
            alt_km=alt_km,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            f107a=f107a,
            f107=f107,
            ap7=ap7,
            validate=validate,
        )

    def _calculate_point_msis2(
        self, *, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, ap7
    ) -> TempDensityResult:
        """MSIS-2.0 单点计算"""
        msis_result = self._model.calc(
            day=day,
            utsec=utsec,
            alt_km=alt_km,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            f107a=f107a,
            f107=f107,
            ap7=ap7,
        )

        return TempDensityResult(
            alt_km=msis_result.alt_km,
            T_local_K=msis_result.T_local_K,
            T_exo_K=msis_result.T_exo_K,
            densities=msis_result.dn10,
        )

    def _calculate_point_msis00(
        self, *, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, ap7
    ) -> TempDensityResult:
        """MSIS-00 单点计算"""
        import numpy as np

        # 转换参数格式
        # MSIS-00 使用 iyd (YYYYDDD) 格式
        # day 是年内日数，需要转换为 iyd 格式
        # 假设当前年份为 2023（实际应该从输入获取）
        # 为了兼容，我们使用一个简化的 iyd 格式
        year = 2023  # 默认年份，MSIS-00 对年份不敏感
        iyd = int(year * 1000 + day)

        # 计算本地太阳时 (近似)
        stl = (utsec / 3600.0 + lon_deg / 15.0) % 24.0

        # 准备 ap 数组
        if ap7 is None:
            ap_arr = np.array([4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], dtype=np.float32)
        else:
            ap_arr = np.array(list(ap7), dtype=np.float32)

        # 调用 MSIS-00
        d_out, t_out = gtd7(
            iyd=iyd,
            sec=float(utsec),
            alt=float(alt_km),
            glat=float(lat_deg),
            glong=float(lon_deg),
            stl=float(stl),
            f107a=float(f107a),
            f107=float(f107),
            ap=ap_arr,
            mass=48,
        )

        # 转换为统一格式
        # MSIS-00 输出: d[0-8] = He, O, N2, O2, Ar, H, N, AnomalousO, TotalMass
        # t[0] = Exospheric temp, t[1] = Local temp
        return TempDensityResult(
            alt_km=float(alt_km),
            T_local_K=float(t_out[1]),
            T_exo_K=float(t_out[0]),
            densities=tuple(float(d_out[i]) for i in range(9)),
        )

    def calculate_batch(
        self,
        *,
        day: Union[float, Sequence[float]],
        utsec: Union[float, Sequence[float]],
        alt_km: Union[float, Sequence[float]],
        lat_deg: Union[float, Sequence[float]],
        lon_deg: Union[float, Sequence[float]],
        f107a: Union[float, Sequence[float]],
        f107: Union[float, Sequence[float]],
        ap7: Optional[Union[Sequence[float], Sequence[Sequence[float]]]] = None,
        output_as_dict: bool = False,
        output_as_xarray: bool = False,
        parallel: bool = False,
        max_workers: Optional[int] = None,
    ) -> Union[List[TempDensityResult], dict, "xr.Dataset"]:
        """
        批量计算温度和密度

        Args:
            day: 年内日数（1-366），可接受标量或序列
            utsec: UTC时间（秒，0-86400），可接受标量或序列
            alt_km: 高度（公里），可接受标量或序列
            lat_deg: 纬度（度），可接受标量或序列
            lon_deg: 经度（度），可接受标量或序列
            f107a: 81天平均F10.7太阳通量，可接受标量或序列
            f107: 当天F10.7太阳通量，可接受标量或序列
            ap7: 地磁活动指数，可为长度7的序列（所有点共用）或(N,7)的二维序列
            output_as_dict: 是否以字典形式返回结果，False则返回结果对象列表
            output_as_xarray: 是否以 xarray.Dataset 形式返回结果（需要安装 xarray）
            parallel: 是否使用多线程并行计算（GIL在ctypes调用时释放）
            max_workers: 并行时最大线程数（默认为CPU核心数，最多8）

        Returns:
            结果对象列表、字典形式的结果数据或 xarray.Dataset
        """
        if parallel:
            results = self._calculate_batch_parallel(
                day=day,
                utsec=utsec,
                alt_km=alt_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                f107a=f107a,
                f107=f107,
                ap7=ap7,
                max_workers=max_workers,
            )
            if output_as_xarray:
                from .xarray_output import temp_density_results_to_xarray

                return temp_density_results_to_xarray(
                    results,
                    alt_km=alt_km,
                    lat_deg=lat_deg,
                    lon_deg=lon_deg,
                    model_version=self._model_version,
                )
            if output_as_dict:
                return {
                    "alt_km": [r.alt_km for r in results],
                    "T_local_K": [r.T_local_K for r in results],
                    "T_exo_K": [r.T_exo_K for r in results],
                    "densities": [r.densities for r in results],
                }
            return results

        if output_as_xarray:
            from .xarray_output import temp_density_results_to_xarray

            results = self._calculate_batch_internal(
                day=day,
                utsec=utsec,
                alt_km=alt_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                f107a=f107a,
                f107=f107,
                ap7=ap7,
                output_as_dict=False,
            )
            return temp_density_results_to_xarray(
                results,
                alt_km=alt_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                model_version=self._model_version,
            )

        return self._calculate_batch_internal(
            day=day,
            utsec=utsec,
            alt_km=alt_km,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            f107a=f107a,
            f107=f107,
            ap7=ap7,
            output_as_dict=output_as_dict,
        )

    def _calculate_batch_parallel(
        self, *, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, ap7, max_workers
    ) -> List[TempDensityResult]:
        from .parallel import parallel_batch_compute
        import numpy as np

        def _to_array(x):
            if isinstance(x, (int, float)):
                return [x]
            return list(x)

        day_arr = _to_array(day)
        utsec_arr = _to_array(utsec)
        alt_arr = _to_array(alt_km)
        lat_arr = _to_array(lat_deg)
        lon_arr = _to_array(lon_deg)
        f107a_arr = _to_array(f107a)
        f107_arr = _to_array(f107)

        N = max(
            len(day_arr),
            len(utsec_arr),
            len(alt_arr),
            len(lat_arr),
            len(lon_arr),
            len(f107a_arr),
            len(f107_arr),
        )

        def _get(arr, i):
            return arr[i % len(arr)]

        if ap7 is None:
            ap7_list = [None] * N
        elif hasattr(ap7[0], "__iter__") and not isinstance(ap7[0], str):
            ap7_list = list(ap7)
        else:
            ap7_list = [ap7] * N

        param_dicts = [
            {
                "day": _get(day_arr, i),
                "utsec": _get(utsec_arr, i),
                "alt_km": _get(alt_arr, i),
                "lat_deg": _get(lat_arr, i),
                "lon_deg": _get(lon_arr, i),
                "f107a": _get(f107a_arr, i),
                "f107": _get(f107_arr, i),
                "ap7": ap7_list[i % len(ap7_list)],
                "validate": False,
            }
            for i in range(N)
        ]

        return parallel_batch_compute(
            self.calculate_point, param_dicts, max_workers=max_workers
        )

    def _calculate_batch_internal(
        self, *, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, ap7, output_as_dict
    ) -> Union[List[TempDensityResult], dict]:
        if self._backend == "msis2":
            return self._calculate_batch_msis2(
                day=day,
                utsec=utsec,
                alt_km=alt_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                f107a=f107a,
                f107=f107,
                ap7=ap7,
                output_as_dict=output_as_dict,
            )
        else:
            return self._calculate_batch_msis00(
                day=day,
                utsec=utsec,
                alt_km=alt_km,
                lat_deg=lat_deg,
                lon_deg=lon_deg,
                f107a=f107a,
                f107=f107,
                ap7=ap7,
                output_as_dict=output_as_dict,
            )

    def _calculate_batch_msis2(
        self, *, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, ap7, output_as_dict
    ) -> Union[List[TempDensityResult], dict]:
        """MSIS-2.0 批量计算"""
        msis_results = self._model.calc_many(
            day=day,
            utsec=utsec,
            alt_km=alt_km,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            f107a=f107a,
            f107=f107,
            ap7=ap7,
            out_numpy=output_as_dict,
        )

        if output_as_dict:
            msis_results["densities"] = msis_results.pop("dn10")
            return msis_results

        return [
            TempDensityResult(
                alt_km=res.alt_km,
                T_local_K=res.T_local_K,
                T_exo_K=res.T_exo_K,
                densities=res.dn10,
            )
            for res in msis_results
        ]

    def _calculate_batch_msis00(
        self, *, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, ap7, output_as_dict
    ) -> Union[List[TempDensityResult], dict]:
        """MSIS-00 批量计算"""
        import numpy as np

        # 转换为数组
        def _to_array(x):
            if isinstance(x, (int, float)):
                return [x]
            return list(x)

        day_arr = _to_array(day)
        utsec_arr = _to_array(utsec)
        alt_arr = _to_array(alt_km)
        lat_arr = _to_array(lat_deg)
        lon_arr = _to_array(lon_deg)
        f107a_arr = _to_array(f107a)
        f107_arr = _to_array(f107)

        # 确定数组长度
        N = max(
            len(day_arr),
            len(utsec_arr),
            len(alt_arr),
            len(lat_arr),
            len(lon_arr),
            len(f107a_arr),
            len(f107_arr),
        )

        # 广播函数
        def _get(arr, i):
            return arr[i % len(arr)]

        # 处理 ap7
        if ap7 is None:
            ap_arr = np.array([4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0], dtype=np.float32)
            ap_is_2d = False
        elif hasattr(ap7[0], "__iter__") and not isinstance(ap7[0], str):
            ap_arr = np.array(ap7, dtype=np.float32)
            ap_is_2d = True
        else:
            ap_arr = np.array(ap7, dtype=np.float32)
            ap_is_2d = False

        results = []
        for i in range(N):
            d = _get(day_arr, i)
            ut = _get(utsec_arr, i)
            alt = _get(alt_arr, i)
            lat = _get(lat_arr, i)
            lon = _get(lon_arr, i)
            f107a_v = _get(f107a_arr, i)
            f107_v = _get(f107_arr, i)

            if ap_is_2d:
                ap_i = ap_arr[i % len(ap_arr)]
            else:
                ap_i = ap_arr

            result = self._calculate_point_msis00(
                day=d,
                utsec=ut,
                alt_km=alt,
                lat_deg=lat,
                lon_deg=lon,
                f107a=f107a_v,
                f107=f107_v,
                ap7=ap_i,
            )
            results.append(result)

        if output_as_dict:
            return {
                "alt_km": [r.alt_km for r in results],
                "T_local_K": [r.T_local_K for r in results],
                "T_exo_K": [r.T_exo_K for r in results],
                "densities": [r.densities for r in results],
            }

        return results


def _validate_temp_density_inputs(
    alt_km: float,
    lat_deg: float,
    lon_deg: float,
    day: Optional[float] = None,
    utsec: Optional[float] = None,
    f107a: Optional[float] = None,
    f107: Optional[float] = None,
) -> None:
    """验证温度密度模型输入参数"""
    if alt_km < 0 or alt_km > 1000:
        raise ValueError(f"alt_km 必须在 0-1000 km 范围内，当前值: {alt_km}")
    if lat_deg < -90 or lat_deg > 90:
        raise ValueError(f"lat_deg 必须在 -90 到 90 度范围内，当前值: {lat_deg}")
    if lon_deg < -180 or lon_deg > 360:
        raise ValueError(f"lon_deg 必须在 -180 到 360 度范围内，当前值: {lon_deg}")
    if day is not None and (day < 1 or day > 366):
        raise ValueError(f"day 必须在 1-366 范围内，当前值: {day}")
    if utsec is not None and (utsec < 0 or utsec > 86400):
        raise ValueError(f"utsec 必须在 0-86400 秒范围内，当前值: {utsec}")
    if f107a is not None and f107a < 0:
        raise ValueError(f"f107a 必须为非负数，当前值: {f107a}")
    if f107 is not None and f107 < 0:
        raise ValueError(f"f107 必须为非负数，当前值: {f107}")


def convert_date_to_day(year: int, month: int, day: int) -> float:
    """
    将日期转换为年内日数

    Args:
        year: 年份
        month: 月份（1-12）
        day: 日期（1-31）

    Returns:
        float: 年内日数
    """
    return doy(year, month, day)


def calculate_seconds_of_day(hour: int, minute: int = 0, second: float = 0.0) -> float:
    """
    计算一天中的秒数

    Args:
        hour: 小时（0-23）
        minute: 分钟（0-59）
        second: 秒（0-60）

    Returns:
        float: 一天中的秒数
    """
    return seconds_of_day(hour, minute, second)


__all__ = [
    "TempDensityModel",
    "TempDensityResult",
    "convert_date_to_day",
    "calculate_seconds_of_day",
]
