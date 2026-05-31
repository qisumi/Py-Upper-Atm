"""
CIRA-86 (COSPAR International Reference Atmosphere 1986) table wrapper.

Public API:
    Model
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Optional, Union

import numpy as np
from utils.model_data import ModelDataError, ensure_model_data

__all__ = ["Model"]

_HEIGHT_LATS = np.arange(-80.0, 81.0, 10.0)
_PRESSURE_LATS = np.arange(-80.0, 81.0, 5.0)
_MONTH_NAMES = {
    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12,
}
_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?")


class Model:
    """CIRA-86 月平均大气表格封装。"""

    def __init__(
        self,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        """
        初始化 CIRA-86。

        参数：
            data_dir: 包含 ``cira86data`` 子目录的数据根目录。
            auto_download: 保留与其他模型一致的参数；当前本地数据表需已存在。
        """
        data_root = ensure_model_data(
            "cira86",
            data_dir=data_dir,
            auto_download=auto_download,
        )
        self._data_dir = data_root / "cira86data"
        if not self._data_dir.is_dir():
            raise ModelDataError(
                "CIRA-86 缺少数据目录：{0}\n"
                "请通过 data_dir 指定包含 cira86data 的数据根目录。".format(
                    self._data_dir
                )
            )
        self._height_table = _parse_height_table(self._data_dir / "twp.lsn")
        self._pressure_table = None

    def calculate(
        self,
        *,
        month,
        lat_deg,
        alt_km=None,
        pressure_mb=None,
    ) -> dict:
        """
        计算 CIRA-86 月平均纬向平均大气参数。

        参数：
            month: 月份，1 至 12，标量或数组。
            lat_deg: 地理纬度（度，北正），范围 -80 至 80，标量或数组。
            alt_km: 高度坐标（km），范围 0 至 120。与 pressure_mb 二选一。
            pressure_mb: 气压坐标（mb）。与 alt_km 二选一。

        返回：
            高度模式返回 T_K、zonal_wind_ms、pressure_mb。
            气压模式返回 T_K、zonal_wind_ms、geopotential_height_m。
        """
        if (alt_km is None) == (pressure_mb is None):
            raise ValueError("必须且只能指定 alt_km 或 pressure_mb 之一")
        if alt_km is not None:
            if self._pressure_table is None:
                self._pressure_table = _parse_pressure_tables(self._data_dir)
            return _calculate_height(
                self._height_table,
                self._pressure_table,
                month=month,
                lat_deg=lat_deg,
                alt_km=alt_km,
            )

        if self._pressure_table is None:
            self._pressure_table = _parse_pressure_tables(self._data_dir)
        return _calculate_pressure(
            self._pressure_table,
            month=month,
            lat_deg=lat_deg,
            pressure_mb=pressure_mb,
        )


def _calculate_height(table, pressure_table, *, month, lat_deg, alt_km) -> dict:
    month_arr, lat_arr, alt_arr = np.broadcast_arrays(
        np.asarray(month),
        np.asarray(lat_deg, dtype=float),
        np.asarray(alt_km, dtype=float),
    )
    month_int = _validate_month(month_arr)
    _validate_range(lat_arr, -80.0, 80.0, "lat_deg")
    _validate_range(alt_arr, 0.0, 120.0, "alt_km")

    shape = month_arr.shape
    flat_count = int(month_arr.size)
    temp = np.empty(flat_count, dtype=float)
    wind = np.empty(flat_count, dtype=float)
    pressure = np.empty(flat_count, dtype=float)

    for i, (mon, lat, alt) in enumerate(
        zip(month_int.reshape(-1), lat_arr.reshape(-1), alt_arr.reshape(-1))
    ):
        idx = int(mon) - 1
        temp[i] = _interp2(
            table["alt_km"],
            table["lat_deg"],
            table["temperature"][idx],
            float(alt),
            float(lat),
        )
        wind[i] = _interp2(
            table["alt_km"],
            table["lat_deg"],
            table["wind"][idx],
            float(alt),
            float(lat),
        )
        pressure[i] = _pressure_from_geopotential_height(
            pressure_table,
            idx,
            float(lat),
            float(alt),
        )

    if shape == ():
        return {
            "month": int(month_int),
            "alt_km": float(alt_arr),
            "lat_deg": float(lat_arr),
            "T_K": float(temp[0]),
            "zonal_wind_ms": float(wind[0]),
            "pressure_mb": float(pressure[0]),
        }

    return {
        "month": month_int.astype(int),
        "alt_km": alt_arr.astype(float),
        "lat_deg": lat_arr.astype(float),
        "T_K": temp.reshape(shape),
        "zonal_wind_ms": wind.reshape(shape),
        "pressure_mb": pressure.reshape(shape),
    }


def _calculate_pressure(table, *, month, lat_deg, pressure_mb) -> dict:
    month_arr, lat_arr, pressure_arr = np.broadcast_arrays(
        np.asarray(month),
        np.asarray(lat_deg, dtype=float),
        np.asarray(pressure_mb, dtype=float),
    )
    month_int = _validate_month(month_arr)
    _validate_range(lat_arr, -80.0, 80.0, "lat_deg")
    _validate_range(
        pressure_arr,
        float(table["pressure_mb"].min()),
        float(table["pressure_mb"].max()),
        "pressure_mb",
    )

    shape = month_arr.shape
    flat_count = int(month_arr.size)
    temp = np.empty(flat_count, dtype=float)
    wind = np.empty(flat_count, dtype=float)
    geop_height = np.empty(flat_count, dtype=float)
    log_pressure_grid = np.log(table["pressure_mb"])

    for i, (mon, lat, pressure) in enumerate(
        zip(
            month_int.reshape(-1),
            lat_arr.reshape(-1),
            pressure_arr.reshape(-1),
        )
    ):
        idx = int(mon) - 1
        log_pressure = math.log(float(pressure))
        temp[i] = _interp2(
            log_pressure_grid,
            table["lat_deg"],
            table["temperature"][idx],
            log_pressure,
            float(lat),
        )
        wind[i] = _interp2(
            log_pressure_grid,
            table["lat_deg"],
            table["wind"][idx],
            log_pressure,
            float(lat),
        )
        geop_height[i] = _interp2(
            log_pressure_grid,
            table["lat_deg"],
            table["geopotential_height"][idx],
            log_pressure,
            float(lat),
        )

    if shape == ():
        return {
            "month": int(month_int),
            "pressure_mb": float(pressure_arr),
            "lat_deg": float(lat_arr),
            "T_K": float(temp[0]),
            "zonal_wind_ms": float(wind[0]),
            "geopotential_height_m": float(geop_height[0]),
        }

    return {
        "month": month_int.astype(int),
        "pressure_mb": pressure_arr.astype(float),
        "lat_deg": lat_arr.astype(float),
        "T_K": temp.reshape(shape),
        "zonal_wind_ms": wind.reshape(shape),
        "geopotential_height_m": geop_height.reshape(shape),
    }


def _validate_month(month_arr) -> np.ndarray:
    values = np.asarray(month_arr, dtype=float)
    if np.any(~np.isfinite(values)) or np.any(values != np.floor(values)):
        raise ValueError("month 必须为 1 至 12 的整数")
    month_int = values.astype(int)
    if np.any((month_int < 1) | (month_int > 12)):
        raise ValueError("month 必须在 1 至 12 之间")
    return month_int


def _validate_range(values, minimum: float, maximum: float, name: str) -> None:
    if np.any(~np.isfinite(values)) or np.any(values < minimum) or np.any(values > maximum):
        raise ValueError(
            "{name} 必须在 {minimum:g} 至 {maximum:g} 之间".format(
                name=name,
                minimum=minimum,
                maximum=maximum,
            )
        )


def _interp2(x_grid, y_grid, values, x_value: float, y_value: float) -> float:
    row_values = np.empty(len(x_grid), dtype=float)
    for i in range(len(x_grid)):
        row = np.asarray(values[i], dtype=float)
        valid = np.isfinite(row)
        if not np.any(valid):
            row_values[i] = np.nan
            continue
        row_values[i] = np.interp(y_value, y_grid[valid], row[valid])

    valid_rows = np.isfinite(row_values)
    if not np.any(valid_rows):
        return float("nan")
    return float(np.interp(x_value, x_grid[valid_rows], row_values[valid_rows]))


def _pressure_from_geopotential_height(table, month_idx: int, lat: float, alt_km: float) -> float:
    heights_m = np.empty(len(table["pressure_mb"]), dtype=float)
    for i in range(len(table["pressure_mb"])):
        heights_m[i] = _interp1_ignore_nan(
            table["lat_deg"],
            table["geopotential_height"][month_idx, i],
            lat,
        )
    valid = np.isfinite(heights_m)
    order = np.argsort(heights_m[valid])
    sorted_heights = heights_m[valid][order]
    sorted_log_pressure = np.log(table["pressure_mb"][valid])[order]
    return float(math.exp(np.interp(alt_km * 1000.0, sorted_heights, sorted_log_pressure)))


def _interp1_ignore_nan(x_grid, values, x_value: float) -> float:
    row = np.asarray(values, dtype=float)
    valid = np.isfinite(row)
    if not np.any(valid):
        return float("nan")
    return float(np.interp(x_value, x_grid[valid], row[valid]))


def _parse_height_table(path: Path) -> dict:
    if not path.is_file():
        raise ModelDataError("CIRA-86 缺少高度坐标数据文件：{0}".format(path))

    data = {
        "temperature": {},
        "wind": {},
        "log_pressure": {},
    }
    current_month = None
    current_param = None

    with path.open("r", encoding="ascii", errors="ignore") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            header = line.strip().upper()
            month = _header_month(header)
            if month is not None and "ZONAL MEAN" in header:
                current_month = month
                if "TEMPERATURE" in header:
                    current_param = "temperature"
                elif "ZONAL WIND" in header:
                    current_param = "wind"
                elif "PRESSURE" in header:
                    current_param = "log_pressure"
                else:
                    current_param = None
                if current_param is not None:
                    data[current_param][current_month] = []
                continue

            if current_month is None or current_param is None:
                continue
            if not _starts_with_number(line):
                continue

            if current_param == "log_pressure":
                parsed = _parse_height_pressure_row(line)
            else:
                parsed = _parse_height_value_row(line)
            if parsed is not None:
                data[current_param][current_month].append(parsed)

    return _finalize_height_table(data)


def _parse_pressure_tables(data_dir: Path) -> dict:
    specs = {
        "temperature": ("sht.lsn", "nht.lsn"),
        "wind": ("shw.lsn", "nhw.lsn"),
        "geopotential_height": ("shz.lsn", "nhz.lsn"),
    }
    combined = {}
    pressure_grid = None

    for param, (south_name, north_name) in specs.items():
        south = _parse_pressure_file(data_dir / south_name)
        north = _parse_pressure_file(data_dir / north_name)
        if pressure_grid is None:
            pressure_grid = north["pressure_mb"]
        values = np.empty((12, len(pressure_grid), len(_PRESSURE_LATS)), dtype=float)
        for month in range(1, 13):
            month_values = np.concatenate(
                [
                    south["values"][month][:, :-1],
                    north["values"][month],
                ],
                axis=1,
            )
            values[month - 1] = month_values
        combined[param] = values

    return {
        "pressure_mb": pressure_grid,
        "lat_deg": _PRESSURE_LATS,
        **combined,
    }


def _parse_pressure_file(path: Path) -> dict:
    if not path.is_file():
        raise ModelDataError("CIRA-86 缺少气压坐标数据文件：{0}".format(path))

    values = {}
    pressure_by_month = {}
    current_month = None

    with path.open("r", encoding="ascii", errors="ignore") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            header = line.strip().upper()
            month = _header_month(header)
            if month is not None and "ZONAL MEAN" in header:
                current_month = month
                values[current_month] = []
                pressure_by_month[current_month] = []
                continue
            if current_month is None or not _starts_with_number(line):
                continue
            numbers = [float(item) for item in _NUMBER_RE.findall(line)]
            if len(numbers) < 19:
                continue
            pressure_by_month[current_month].append(numbers[1])
            if len(numbers) == 19:
                values[current_month].append(numbers[2:19])
            else:
                values[current_month].append(numbers[3:20])

    pressure_grid = np.asarray(pressure_by_month[1], dtype=float)
    parsed_values = {}
    for month in range(1, 13):
        parsed_values[month] = np.asarray(values[month], dtype=float)
    return {
        "pressure_mb": pressure_grid,
        "values": parsed_values,
    }


def _finalize_height_table(data: dict) -> dict:
    heights = None
    result = {}
    for param in ("temperature", "wind"):
        month_rows = data[param]
        month_arrays = []
        for month in range(1, 13):
            rows = month_rows.get(month, [])
            if len(rows) != 25:
                raise ModelDataError(
                    "CIRA-86 数据文件 twp.lsn 中 {param} 第 {month} 月行数异常".format(
                        param=param,
                        month=month,
                    )
                )
            row_heights = np.asarray([row[0] for row in rows], dtype=float)
            row_values = np.asarray([row[1] for row in rows], dtype=float)
            order = np.argsort(row_heights)
            if heights is None:
                heights = row_heights[order]
            month_arrays.append(row_values[order])
        result[param] = np.asarray(month_arrays, dtype=float)

    return {
        "alt_km": heights,
        "lat_deg": _HEIGHT_LATS,
        **result,
    }


def _parse_height_value_row(line: str):
    numbers = [float(item) for item in _NUMBER_RE.findall(line)]
    if len(numbers) < 2:
        return None
    height = numbers[0]
    values = numbers[1:]
    if len(values) == 16:
        values = [float("nan")] + values
    if len(values) != 17:
        return None
    return height, values


def _parse_height_pressure_row(line: str):
    tokens = line.split()
    if len(tokens) < 3:
        return None
    exponent_token = tokens[-1].upper()
    if not exponent_token.startswith("E"):
        return None
    height = float(tokens[0])
    exponent = int(exponent_token[1:])
    values = [float(token) * (10.0 ** exponent) for token in tokens[1:-1]]
    if len(values) == 16:
        values = [float("nan")] + values
    if len(values) != 17:
        return None
    return height, [math.log(value) if value > 0 else float("nan") for value in values]


def _header_month(header: str) -> Optional[int]:
    for name, month in _MONTH_NAMES.items():
        if header.startswith(name):
            return month
    return None


def _starts_with_number(line: str) -> bool:
    stripped = line.lstrip()
    return bool(stripped) and (stripped[0].isdigit() or stripped[0] in "+-.")
