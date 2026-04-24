from __future__ import annotations

import datetime as _dt


def doy(year: int, month: int, day: int) -> float:
    """将 (year, month, day) 转换为年内日（1-366）。"""
    d0 = _dt.date(year, 1, 1)
    d = _dt.date(year, month, day)
    return float((d - d0).days + 1)


def seconds_of_day(hour: int, minute: int = 0, second: float = 0.0) -> float:
    """一天内秒数（0-86400），可带小数秒。"""
    return float(hour) * 3600.0 + float(minute) * 60.0 + float(second)


__all__ = ["doy", "seconds_of_day"]
