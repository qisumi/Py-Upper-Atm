"""
风场模型接口
提供大气风场计算功能。
"""
from __future__ import annotations
from typing import Iterable, Tuple, Union

# 导入原始HWM14模型，但不暴露其名称
try:
    from .pyhwm14 import hwm14_eval, hwm14_eval_many
    _has_wind_model = True
except ImportError:
    _has_wind_model = False
    raise ImportError("风场模型组件加载失败")


class WindModel:
    """
    风场模型
    提供大气风场的计算功能。
    """
    
    def __init__(self):
        """
        初始化风场模型
        """
        if not _has_wind_model:
            raise RuntimeError("风场模型组件未正确加载")
    
    def calculate_point(self,
                      iyd: int,
                      sec: float,
                      alt_km: float,
                      glat_deg: float,
                      glon_deg: float,
                      stl_hours: float,
                      f107a: float,
                      f107: float,
                      ap2: Iterable[float] = (0.0, 20.0)) -> Tuple[float, float]:
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
            
        Returns:
            Tuple[float, float]: (经向风, 纬向风) 速度，单位 m/s
        """
        return hwm14_eval(
            iyd=iyd,
            sec=sec,
            alt_km=alt_km,
            glat_deg=glat_deg,
            glon_deg=glon_deg,
            stl_hours=stl_hours,
            f107a=f107a,
            f107=f107,
            ap2=ap2
        )
    
    def calculate_batch(self,
                      iyd: Union[int, Iterable[int]],
                      sec: Union[float, Iterable[float]],
                      alt_km: Union[float, Iterable[float]],
                      glat_deg: Union[float, Iterable[float]],
                      glon_deg: Union[float, Iterable[float]],
                      stl_hours: Union[float, Iterable[float]],
                      f107a: Union[float, Iterable[float]],
                      f107: Union[float, Iterable[float]],
                      ap2: Iterable[float] = (0.0, 20.0)) -> Tuple[object, object]:
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
            
        Returns:
            Tuple[ndarray, ndarray]: (经向风数组, 纬向风数组)，单位 m/s，形状与输入对齐
        """
        return hwm14_eval_many(
            iyd=iyd,
            sec=sec,
            alt_km=alt_km,
            glat_deg=glat_deg,
            glon_deg=glon_deg,
            stl_hours=stl_hours,
            f107a=f107a,
            f107=f107,
            ap2=ap2
        )


def calculate_wind_at_point(
    iyd: int,
    sec: float,
    alt_km: float,
    glat_deg: float,
    glon_deg: float,
    stl_hours: float,
    f107a: float,
    f107: float,
    ap2: Iterable[float] = (0.0, 20.0)
) -> Tuple[float, float]:
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
        ap2: 地磁活动指数，长度为 2 的数组；ap2[0] 常未用，ap2[1]=当前 3h ap
        
    Returns:
        Tuple[float, float]: (经向风, 纬向风) 速度，单位 m/s
    """
    return hwm14_eval(
        iyd=iyd,
        sec=sec,
        alt_km=alt_km,
        glat_deg=glat_deg,
        glon_deg=glon_deg,
        stl_hours=stl_hours,
        f107a=f107a,
        f107=f107,
        ap2=ap2
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
    ap2=(0.0, 20.0)
) -> Tuple[object, object]:
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
        ap2: 地磁活动指数，长度为 2 的数组；ap2[0] 常未用，ap2[1]=当前 3h ap
        
    Returns:
        Tuple[ndarray, ndarray]: (经向风数组, 纬向风数组)，单位 m/s，形状与输入对齐
    """
    return hwm14_eval_many(
        iyd=iyd,
        sec=sec,
        alt_km=alt_km,
        glat_deg=glat_deg,
        glon_deg=glon_deg,
        stl_hours=stl_hours,
        f107a=f107a,
        f107=f107,
        ap2=ap2
    )


__all__ = [
    "WindModel",
    "calculate_wind_at_point",
    "calculate_wind_batch"
]