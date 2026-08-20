"""Hodges (1994) terrestrial exospheric hydrogen model."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

from utils.model_data import ensure_model_data

__all__ = ["Model"]

_F107_LEVELS = {80, 130, 180, 230}
_TABLE_RE = re.compile(r"Table\s+\d+\.\s+(Equinox|Solstice),\s+F10\.7\s*=\s*(\d+)", re.I)


class Model:
    """Hodges 三阶球谐外逸层氢密度模型。"""

    def __init__(
        self,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        root = ensure_model_data(
            "exospherich", data_dir=data_dir, auto_download=auto_download
        )
        self._tables = _parse_tables(root / "exospherichdata" / "h_exos.dat")

    def calculate(
        self,
        *,
        radius_km: Any,
        colatitude_deg: Any,
        longitude_deg: Any,
        season: Any = "equinox",
        f107: Any = 80,
    ) -> dict:
        """计算地心球坐标处的氢数密度（cm⁻³）。"""
        radius, colat, lon, season_arr, f107_arr = np.broadcast_arrays(
            np.asarray(radius_km, dtype=float),
            np.asarray(colatitude_deg, dtype=float),
            np.asarray(longitude_deg, dtype=float),
            np.asarray(season, dtype=object),
            np.asarray(f107),
        )
        _finite_range(radius, 6640.0, 62126.0, "radius_km")
        _finite_range(colat, 0.0, 180.0, "colatitude_deg")
        if np.any(~np.isfinite(lon)):
            raise ValueError("longitude_deg 必须为有限数值")
        f107_float = np.asarray(f107_arr, dtype=float)
        if np.any(~np.isfinite(f107_float)) or np.any(f107_float != np.floor(f107_float)):
            raise ValueError("f107 必须是 80、130、180 或 230")
        f107_int = f107_float.astype(int)
        if any(int(value) not in _F107_LEVELS for value in f107_int.reshape(-1)):
            raise ValueError("f107 必须是 80、130、180 或 230")

        normalized_seasons = np.empty(season_arr.shape, dtype=object)
        for idx, value in np.ndenumerate(season_arr):
            normalized = str(value).strip().lower()
            if normalized not in {"equinox", "solstice"}:
                raise ValueError("season 必须是 equinox 或 solstice")
            normalized_seasons[idx] = normalized

        density = np.empty(radius.size, dtype=float)
        for i, values in enumerate(
            zip(
                radius.reshape(-1),
                colat.reshape(-1),
                lon.reshape(-1),
                normalized_seasons.reshape(-1),
                f107_int.reshape(-1),
            )
        ):
            density[i] = _calculate_one(self._tables, *values)

        density = density.reshape(radius.shape)
        if radius.shape == ():
            return {
                "radius_km": float(radius),
                "colatitude_deg": float(colat),
                "longitude_deg": float(lon),
                "season": str(normalized_seasons.item()),
                "f107": int(f107_int),
                "H_cm3": float(density),
            }
        return {
            "radius_km": radius.astype(float),
            "colatitude_deg": colat.astype(float),
            "longitude_deg": lon.astype(float),
            "season": normalized_seasons.copy(),
            "f107": f107_int,
            "H_cm3": density,
        }


def _calculate_one(tables, radius, colatitude, longitude, season, f107):
    table = tables[(str(season), int(f107))]
    log_radius = np.log(table[:, 0])
    x = math.log(float(radius))
    base_density = math.exp(float(np.interp(x, log_radius, np.log(table[:, 1]))))
    coeff = np.asarray(
        [np.interp(x, log_radius, table[:, column]) for column in range(2, 17)],
        dtype=float,
    ) * 1.0e-4

    theta = math.radians(float(colatitude))
    phi = math.radians(float(longitude))
    # File ordering: A10, A11, B11, A20, A21, B21, ... A33, B33.
    angular = _normalized_legendre(0, 0, theta)
    pos = 0
    for degree in (1, 2, 3):
        for order in range(degree + 1):
            ylm = _normalized_legendre(degree, order, theta)
            a = coeff[pos]
            pos += 1
            angular += a * math.cos(order * phi) * ylm
            if order > 0:
                b = coeff[pos]
                pos += 1
                angular += b * math.sin(order * phi) * ylm
    return base_density * math.sqrt(4.0 * math.pi) * angular


def _normalized_legendre(degree: int, order: int, theta: float) -> float:
    x = math.cos(theta)
    s = math.sin(theta)
    values = {
        (0, 0): 1.0,
        (1, 0): x,
        (1, 1): -s,
        (2, 0): 0.5 * (3.0 * x * x - 1.0),
        (2, 1): -3.0 * x * s,
        (2, 2): 3.0 * s * s,
        (3, 0): 0.5 * (5.0 * x**3 - 3.0 * x),
        (3, 1): -1.5 * (5.0 * x * x - 1.0) * s,
        (3, 2): 15.0 * x * s * s,
        (3, 3): -15.0 * s**3,
    }
    norm = math.sqrt(
        (2 * degree + 1)
        / (4.0 * math.pi)
        * math.factorial(degree - order)
        / math.factorial(degree + order)
    )
    return norm * values[(degree, order)]


def _parse_tables(path: Path):
    tables = {}
    current = None
    rows = []
    with path.open("r", encoding="ascii", errors="ignore") as fh:
        for raw in fh:
            match = _TABLE_RE.search(raw)
            if match:
                if current is not None:
                    tables[current] = np.asarray(rows, dtype=float)
                current = (match.group(1).lower(), int(match.group(2)))
                rows = []
                continue
            if current is None:
                continue
            fields = raw.split()
            if len(fields) == 17:
                try:
                    rows.append([float(value) for value in fields])
                except ValueError:
                    pass
    if current is not None:
        tables[current] = np.asarray(rows, dtype=float)
    expected = {(season, f107) for season in ("equinox", "solstice") for f107 in _F107_LEVELS}
    if set(tables) != expected or any(value.shape != (40, 17) for value in tables.values()):
        raise ValueError(f"无法解析完整的 H_EXOS 系数表：{path}")
    return tables


def _finite_range(values, minimum, maximum, name):
    if np.any(~np.isfinite(values)) or np.any(values < minimum) or np.any(values > maximum):
        raise ValueError(f"{name} 必须在 {minimum:g} 至 {maximum:g} 之间")
