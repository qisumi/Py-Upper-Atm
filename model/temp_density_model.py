"""
温度和密度模型接口
基于NRLMSIS-2.0模型，提供温度和密度计算功能。
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Union

# 导入原始MSIS2模型，但不暴露其名称
try:
    from .pymsis2 import NRLMSIS2, MSISResult, doy, seconds_of_day
    _has_msis = True
except ImportError:
    _has_msis = False
    raise ImportError("温度密度模型组件加载失败")


@dataclass
class TempDensityResult:
    """
    温度和密度计算结果

    Attributes:
        alt_km: 高度（公里）
        T_local_K: 局部温度（开尔文）
        T_exo_K: 外温度（开尔文）
        densities: 各成分数密度（10^6 cm^-3），按顺序：N2, O2, O, He, H, Ar, N, AnomalousO, NO, NPlus
    """
    alt_km: float
    T_local_K: float
    T_exo_K: float
    densities: Tuple[float, float, float, float,
                     float, float, float, float, float, float]


class TempDensityModel:
    """
    温度和密度模型
    提供大气温度和密度的计算功能。
    """

    def __init__(self,
                 dll_path: Optional[Union[str, str]] = None,
                 *,
                 precision: str = "single",
                 add_mingw_bin: bool = False,
                 extra_dll_dirs: Optional[Sequence[Union[str, str]]] = None):
        """
        初始化温度密度模型

        Args:
            dll_path: 模型DLL文件路径，若为None则使用默认路径
            precision: 计算精度，可选"single"(单精度)或"double"(双精度)
            add_mingw_bin: 是否添加MinGW二进制目录到DLL搜索路径
            extra_dll_dirs: 额外的DLL搜索目录列表
        """
        if not _has_msis:
            raise RuntimeError("温度密度模型组件未正确加载")

        self._model = NRLMSIS2(
            dll_path=dll_path,
            precision=precision,
            add_mingw_bin=add_mingw_bin,
            extra_dll_dirs=extra_dll_dirs
        )

    def calculate_point(self,
                        *,
                        day: float,
                        utsec: float,
                        alt_km: float,
                        lat_deg: float,
                        lon_deg: float,
                        f107a: float,
                        f107: float,
                        ap7: Optional[Sequence[float]] = None) -> TempDensityResult:
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

        Returns:
            TempDensityResult: 包含温度和密度结果的对象
        """
        msis_result = self._model.calc(
            day=day,
            utsec=utsec,
            alt_km=alt_km,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            f107a=f107a,
            f107=f107,
            ap7=ap7
        )

        # 转换为我们的结果格式，保持数据不变
        return TempDensityResult(
            alt_km=msis_result.alt_km,
            T_local_K=msis_result.T_local_K,
            T_exo_K=msis_result.T_exo_K,
            densities=msis_result.dn10
        )

    def calculate_batch(self,
                        *,
                        day: Union[float, Sequence[float]],
                        utsec: Union[float, Sequence[float]],
                        alt_km: Union[float, Sequence[float]],
                        lat_deg: Union[float, Sequence[float]],
                        lon_deg: Union[float, Sequence[float]],
                        f107a: Union[float, Sequence[float]],
                        f107: Union[float, Sequence[float]],
                        ap7: Optional[Union[Sequence[float],
                                            Sequence[Sequence[float]]]] = None,
                        output_as_dict: bool = False) -> Union[List[TempDensityResult], dict]:
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

        Returns:
            结果对象列表或字典形式的结果数据
        """
        msis_results = self._model.calc_many(
            day=day,
            utsec=utsec,
            alt_km=alt_km,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            f107a=f107a,
            f107=f107,
            ap7=ap7,
            out_numpy=output_as_dict
        )

        if output_as_dict:
            # 直接返回字典结果，但修改键名
            msis_results['densities'] = msis_results.pop('dn10')
            return msis_results

        # 转换为我们的结果格式列表
        return [
            TempDensityResult(
                alt_km=res.alt_km,
                T_local_K=res.T_local_K,
                T_exo_K=res.T_exo_K,
                densities=res.dn10
            )
            for res in msis_results
        ]


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
    "calculate_seconds_of_day"
]
