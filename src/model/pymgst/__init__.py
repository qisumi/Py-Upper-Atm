"""
MGST (MAGSAT Geomagnetic Spherical Topology) field model wrappers.

Supports MGST(6/80) and MGST(4/81) spherical harmonic models of Earth's
main magnetic field from MAGSAT satellite data.

Public API:
    MGST80  — MGST(6/80) model, epoch 1979.85
    MGST81  — MGST(4/81) model, epoch 1980.0
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np
from utils.model_data import ensure_model_data

__all__ = ["MGST80", "MGST81"]


def _read_mgst_coefficients(filepath: Path) -> tuple:
    """Read MGST coefficient file and return (epoch, g, gt, gtt) dictionaries.

    Returns:
        epoch: reference epoch (decimal year)
        g: dict of (n, m) -> coefficient (constant terms)
        gt: dict of (n, m) -> coefficient (first derivative terms)
        gtt: dict of (n, m) -> coefficient (second derivative terms)
    """
    with open(filepath, "r") as f:
        lines = f.readlines()

    # Skip header line(s) — find first line starting with a digit (n value)
    coeff_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and stripped[0].isdigit():
            coeff_start = i
            break

    # Parse epoch from header if present
    epoch = 1980.0  # default
    for line in lines[:coeff_start]:
        upper = line.upper()
        for marker in ["EPOCH", "MGST"]:
            idx = upper.find(marker)
            if idx >= 0:
                # Try to extract a year-like number
                import re
                match = re.search(r'(\d{4}\.\d+)', line[idx:])
                if match:
                    epoch = float(match.group(1))
                    break

    g = {}
    gt = {}
    gtt = {}

    for line in lines[coeff_start:]:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) < 3:
            continue
        try:
            n = int(parts[0])
            m = int(parts[1])
        except ValueError:
            continue
        if n <= 0:
            break

        # FORMAT(2I3,6F11.4): N, M, GNM, HNM, GTNM, HTNM, GTTNM, HTTNM
        # Parse fixed-width columns
        if len(line) < 72:
            # Pad short lines
            line = line.ljust(72)

        try:
            gnm = float(line[6:17])
            hnm = float(line[17:28])
            gtnm = float(line[28:39])
            htnm = float(line[39:50])
            gttnm = float(line[50:61])
            httnm = float(line[61:72])
        except ValueError:
            continue

        if m == 0:
            # m=0: only G coefficient (no H)
            g[(n, 0)] = gnm
            gt[(n, 0)] = gtnm
            gtt[(n, 0)] = gttnm
        else:
            # m>0: G and H coefficients
            g[(n, m)] = gnm
            g[(m - 1, n)] = hnm  # Store H as g(m-1, n) following FIELDG convention
            gt[(n, m)] = gtnm
            gt[(m - 1, n)] = htnm
            gtt[(n, m)] = gttnm
            gtt[(m - 1, n)] = httnm

    return epoch, g, gt, gtt


def _schmidt_normalize(n: int, m: int) -> float:
    """Compute Schmidt normalization factor S_n^m."""
    if m == 0:
        return 1.0
    # S_n^m = sqrt(2 * (n-m)! / (n+m)!)
    # Using log to avoid overflow
    log_factor = 0.0
    for k in range(n - m + 1, n + m + 1):
        log_factor += math.log(k)
    return math.sqrt(2.0 / math.exp(log_factor))


def _associated_legendre(theta_rad: float, nmax: int) -> dict:
    """Compute associated Legendre polynomials P_n^m(cos(theta)) with Schmidt normalization.

    Uses the recursion relations from FIELDG.
    Returns dict of (n, m) -> P_n^m value.
    """
    ct = math.cos(theta_rad)
    st = math.sin(theta_rad)

    # Initialize
    p = {}
    p[(1, 1)] = 1.0
    sp = {1: 0.0}  # sin(m*phi) — not needed here
    cp = {1: 1.0}  # cos(m*phi) — not needed here

    # Build constants for recursion
    const = {}
    for n in range(2, nmax + 1):
        for m in range(1, n + 1):
            const[(n, m)] = float((n - 2) ** 2 - (m - 1) ** 2) / float((2 * n - 3) * (2 * n - 5))

    # Recursion
    for n in range(2, nmax + 1):
        for m in range(1, n + 1):
            if n == m:
                p[(n, n)] = st * p.get((n - 1, n - 1), 0.0)
            elif n == 2:
                p[(n, m)] = ct * p.get((n - 1, m), 0.0)
            else:
                p[(n, m)] = ct * p.get((n - 1, m), 0.0) - const.get((n, m), 0.0) * p.get((n - 2, m), 0.0)

    # Apply Schmidt normalization
    for n in range(1, nmax + 1):
        for m in range(1, n + 1):
            p[(n, m)] = p.get((n, m), 0.0) * _schmidt_normalize(n, m)

    return p


def _compute_field(
    lat_deg: float,
    lon_deg: float,
    alt_km: float,
    year: float,
    epoch: float,
    g: dict,
    gt: dict,
    gtt: dict,
    nmax: int,
) -> dict:
    """Compute geomagnetic field components at one point.

    Uses geocentric coordinates (matching FIELDG with J=1).
    """
    # Constants
    a = 6371.2  # Earth reference radius (km)

    # Convert to geocentric spherical coordinates
    theta = math.radians(90.0 - lat_deg)  # colatitude in radians
    phi = math.radians(lon_deg)            # longitude in radians
    r = alt_km + a                         # geocentric radius (km)

    ct = math.cos(theta)
    st = math.sin(theta)
    cph = math.cos(phi)
    sph = math.sin(phi)

    # Time offset from epoch
    t = year - epoch

    # Compute time-dependent coefficients: TG = G + T * (GT + GTT * T)
    tg = {}
    for key in g:
        tg[key] = g[key] + t * (gt.get(key, 0.0) + gtt.get(key, 0.0) * t)

    # Compute associated Legendre polynomials
    p = _associated_legendre(theta, nmax)

    # Compute field components using spherical harmonic expansion
    # V = a * Σ (a/r)^(n+1) * Σ [g_n^m cos(mφ) + h_n^m sin(mφ)] * P_n^m(cos θ)
    # B_r = -∂V/∂r, B_θ = -1/r ∂V/∂θ, B_φ = -1/(r sin θ) ∂V/∂φ

    br = 0.0
    bt = 0.0
    bp = 0.0

    for n in range(1, nmax + 1):
        fn = float(n)
        ratio = (a / r) ** (n + 2)  # (a/r)^(n+2) for radial derivative

        # m = 0 term
        g_n0 = tg.get((n, 0), 0.0)
        p_n0 = 1.0 if n == 1 else p.get((n, 1), 0.0) * 0.0  # P_n^0 = Legendre P_n
        # Actually, for m=0, P_n^0 is the ordinary Legendre polynomial
        # We need to compute it separately
        if n == 1:
            p_n0 = ct
        elif n == 2:
            p_n0 = (3.0 * ct * ct - 1.0) / 2.0
        else:
            # Use recursion: P_n^0 = ((2n-1) * ct * P_{n-1}^0 - (n-1) * P_{n-2}^0) / n
            p_n0_prev = ct  # P_1^0
            p_n0_prev2 = 1.0  # P_0^0
            for nn in range(2, n + 1):
                p_n0_curr = ((2 * nn - 1) * ct * p_n0_prev - (nn - 1) * p_n0_prev2) / nn
                p_n0_prev2 = p_n0_prev
                p_n0_prev = p_n0_curr
            p_n0 = p_n0_prev

        # dP_n^0/dθ = -sin θ * P_n^1 (Schmidt normalized)
        dp_n0 = -st * p.get((n, 1), 0.0) * _schmidt_normalize(n, 1) if n >= 1 else 0.0

        br += (fn + 1.0) * ratio * g_n0 * p_n0
        bt += ratio * g_n0 * dp_n0

        # m > 0 terms
        for m in range(1, n + 1):
            gnm = tg.get((n, m), 0.0)
            hnm = tg.get((m - 1, n), 0.0)  # H stored as g(m-1, n)

            cos_mphi = math.cos(m * phi)
            sin_mphi = math.sin(m * phi)

            pnm = p.get((n, m), 0.0)

            # dP_n^m/dθ using recursion
            # For Schmidt normalized: dP/dθ = (n * ct * P_n^m - (n+m) * P_{n-1}^m) / st
            if st != 0.0:
                if n == m:
                    dpnm = ct * pnm / st  # simplified for n=m
                else:
                    pnm_prev = p.get((n - 1, m), 0.0)
                    dpnm = (fn * ct * pnm - (fn + m) * pnm_prev) / st
            else:
                dpnm = 0.0

            factor = gnm * cos_mphi + hnm * sin_mphi

            br += (fn + 1.0) * ratio * factor * pnm
            bt += ratio * factor * dpnm
            if st != 0.0:
                bp += ratio * m * (-gnm * sin_mphi + hnm * cos_mphi) * pnm / st

    # Convert from spherical to local Cartesian (North, East, Down)
    # B_r is radial (positive outward), B_θ is southward, B_φ is eastward
    # North = -B_θ, East = B_φ, Down = -B_r (for geocentric)
    # But we need to convert to geodetic if needed
    # For geocentric: X = -B_θ, Y = B_φ, Z = -B_r

    # The field is in nT (coefficients are in nT)
    x = -bt   # North component
    y = bp    # East component
    z = -br   # Down component (positive downward)
    f = math.sqrt(x * x + y * y + z * z)

    return {
        "X_nT": x,
        "Y_nT": y,
        "Z_nT": z,
        "F_nT": f,
        "H_nT": math.sqrt(x * x + y * y) if x != 0.0 or y != 0.0 else 0.0,
        "inclination_deg": math.degrees(math.atan2(z, math.sqrt(x * x + y * y))) if (x != 0.0 or y != 0.0) else (90.0 if z > 0 else -90.0),
        "declination_deg": math.degrees(math.atan2(y, x)),
    }


class MGST80:
    """MGST(6/80) geomagnetic field model, epoch 1979.85.

    MAGSAT scalar + fine attitude data, November 5-6 1979.
    Spherical harmonics to degree and order 13, no secular variation.
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        data_root = ensure_model_data(
            "mgst",
            data_dir=data_dir,
            auto_download=auto_download,
        )
        self._data_root = data_root / "mgst"

        coeff_file = self._data_root / "mgst380.dat"
        self._epoch, self._g, self._gt, self._gtt = _read_mgst_coefficients(coeff_file)

        self._maxn = max(n for n, m in self._g.keys()) if self._g else 13

    def calculate(
        self,
        *,
        year,
        lat_deg,
        lon_deg,
        alt_km,
        nmx: int = 13,
    ) -> dict:
        """
        计算地磁场分量。

        参数：
            year: 十进制年份（如 1979.85），标量或数组。
            lat_deg: 地理纬度（度，北正），标量或数组。
            lon_deg: 地理经度（度，东正），标量或数组。
            alt_km: 海拔高度（km），标量或数组。
            nmx: 最大阶数（默认 13）。

        返回：
            包含地磁场分量（nT）的字典。
        """
        if not 1 <= nmx <= self._maxn:
            raise ValueError(f"nmx 必须在 1-{self._maxn} 之间，当前值: {nmx}")

        year_arr, lat_arr, lon_arr, alt_arr = np.broadcast_arrays(
            np.asarray(year, dtype=float),
            np.asarray(lat_deg, dtype=float),
            np.asarray(lon_deg, dtype=float),
            np.asarray(alt_km, dtype=float),
        )
        shape = year_arr.shape
        flat_count = int(year_arr.size)

        results = []
        for i in range(flat_count):
            y = float(year_arr.flat[i])
            la = float(lat_arr.flat[i])
            lo = float(lon_arr.flat[i])
            al = float(alt_arr.flat[i])
            r = _compute_field(la, lo, al, y, self._epoch, self._g, self._gt, self._gtt, nmx)
            results.append(r)

        scalar_input = shape == ()
        if scalar_input:
            r = results[0]
            return {
                "year": float(year_arr),
                "lat_deg": float(lat_arr),
                "lon_deg": float(lon_arr),
                "alt_km": float(alt_arr),
                **r,
            }

        keys = results[0].keys()
        out = {
            "year": year_arr.astype(float),
            "lat_deg": lat_arr.astype(float),
            "lon_deg": lon_arr.astype(float),
            "alt_km": alt_arr.astype(float),
        }
        for k in keys:
            out[k] = np.array([r[k] for r in results]).reshape(shape)
        return out


class MGST81:
    """MGST(4/81) geomagnetic field model, epoch 1980.0.

    MAGSAT 15-day data set. Spherical harmonics to degree and order 13
    in constant terms, degree 7 in first derivative terms.
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        data_root = ensure_model_data(
            "mgst",
            data_dir=data_dir,
            auto_download=auto_download,
        )
        self._data_root = data_root / "mgst"

        coeff_file = self._data_root / "mgst481.dat"
        self._epoch, self._g, self._gt, self._gtt = _read_mgst_coefficients(coeff_file)

        self._maxn = max(n for n, m in self._g.keys()) if self._g else 13

    def calculate(
        self,
        *,
        year,
        lat_deg,
        lon_deg,
        alt_km,
        nmx: int = 13,
    ) -> dict:
        """
        计算地磁场分量。

        参数：
            year: 十进制年份（如 1980.0），标量或数组。
            lat_deg: 地理纬度（度，北正），标量或数组。
            lon_deg: 地理经度（度，东正），标量或数组。
            alt_km: 海拔高度（km），标量或数组。
            nmx: 最大阶数（默认 13）。

        返回：
            包含地磁场分量（nT）的字典。
        """
        if not 1 <= nmx <= self._maxn:
            raise ValueError(f"nmx 必须在 1-{self._maxn} 之间，当前值: {nmx}")

        year_arr, lat_arr, lon_arr, alt_arr = np.broadcast_arrays(
            np.asarray(year, dtype=float),
            np.asarray(lat_deg, dtype=float),
            np.asarray(lon_deg, dtype=float),
            np.asarray(alt_km, dtype=float),
        )
        shape = year_arr.shape
        flat_count = int(year_arr.size)

        results = []
        for i in range(flat_count):
            y = float(year_arr.flat[i])
            la = float(lat_arr.flat[i])
            lo = float(lon_arr.flat[i])
            al = float(alt_arr.flat[i])
            r = _compute_field(la, lo, al, y, self._epoch, self._g, self._gt, self._gtt, nmx)
            results.append(r)

        scalar_input = shape == ()
        if scalar_input:
            r = results[0]
            return {
                "year": float(year_arr),
                "lat_deg": float(lat_arr),
                "lon_deg": float(lon_arr),
                "alt_km": float(alt_arr),
                **r,
            }

        keys = results[0].keys()
        out = {
            "year": year_arr.astype(float),
            "lat_deg": lat_arr.astype(float),
            "lon_deg": lon_arr.astype(float),
            "alt_km": alt_arr.astype(float),
        }
        for k in keys:
            out[k] = np.array([r[k] for r in results]).reshape(shape)
        return out
