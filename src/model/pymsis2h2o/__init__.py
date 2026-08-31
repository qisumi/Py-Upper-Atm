"""NRLMSIS-2.0 with an offline Aura MLS H2O climatology."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence, Union

import numpy as np

from utils.model_data import ensure_model_data

__all__ = ["Model"]


_BOLTZMANN_J_K = 1.380649e-23
_DEFAULT_DATA_FILE = "mls_ml3mbh2o_v005_2005-2024_climatology.npz"
_SEASONAL_PERIOD_DAYS = 365.2425


class Model:
    """MSIS2 dry atmosphere plus monthly Aura MLS H2O climatology.

    The MLS component is a fixed 2005--2024 climatology. Values above the
    MLS pressure ceiling are constrained extrapolations and are explicitly
    marked in every result.
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        precision: str = "single",
        add_mingw_bin: bool = False,
        extra_dll_dirs: Optional[Sequence[Union[str, Path]]] = None,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
        h2o_data_path: Optional[Union[str, Path]] = None,
    ) -> None:
        # Importing this module remains lightweight; the native model is only
        # imported and instantiated when the concrete public class is created.
        from model.pymsis2 import Model as MSIS2Model

        self._msis2 = MSIS2Model(
            dll_path,
            precision=precision,
            add_mingw_bin=add_mingw_bin,
            extra_dll_dirs=extra_dll_dirs,
            data_dir=data_dir,
            auto_download=auto_download,
        )
        self._h2o_data_path = _resolve_h2o_data_path(
            h2o_data_path,
            data_dir=data_dir,
            auto_download=auto_download,
        )
        self._climatology = _Climatology.load(self._h2o_data_path)

    def calculate(
        self,
        *,
        day,
        utsec,
        alt_km,
        lat_deg,
        lon_deg,
        f107a,
        f107,
        ap7=None,
    ) -> dict:
        """计算 20--120 km 的 MSIS2 状态和 H2O 数密度。

        标量输入返回 Python 标量；数组输入按 NumPy 广播并返回数组。
        ``H2O_extrapolated`` 为真表示结果位于 MLS 顶部压力范围之外。
        """

        arrays = np.broadcast_arrays(
            np.asarray(day, dtype=float),
            np.asarray(utsec, dtype=float),
            np.asarray(alt_km, dtype=float),
            np.asarray(lat_deg, dtype=float),
            np.asarray(lon_deg, dtype=float),
            np.asarray(f107a, dtype=float),
            np.asarray(f107, dtype=float),
        )
        day_arr, utsec_arr, alt_arr, lat_arr, lon_arr, f107a_arr, f107_arr = arrays
        _validate_inputs(day_arr, utsec_arr, alt_arr, lat_arr, lon_arr)

        raw = self._msis2.calculate(
            day=day_arr,
            utsec=utsec_arr,
            alt_km=alt_arr,
            lat_deg=lat_arr,
            lon_deg=lon_arr,
            f107a=f107a_arr,
            f107=f107_arr,
            ap7=ap7,
        )
        densities = np.asarray(raw["densities"], dtype=float)
        if densities.shape[-1] != 10:
            raise RuntimeError("MSIS2 densities 最后一维必须为 10")

        # N2, O2, O, He, H, Ar, N and anomalous O occupy indexes 1..8.
        total_number_density = np.sum(densities[..., 1:9], axis=-1)
        temperature = np.asarray(raw["T_local_K"], dtype=float)
        pressure_pa = total_number_density * _BOLTZMANN_J_K * temperature
        if np.any(~np.isfinite(pressure_pa)) or np.any(pressure_pa <= 0.0):
            raise RuntimeError("MSIS2 推导压力必须为有限正值")

        vmr_ppmv, extrapolated, latitude_clamped, fallback = self._climatology.evaluate(
            day_arr,
            utsec_arr,
            lat_arr,
            lon_arr,
            pressure_pa / 100.0,
        )
        h2o_m3 = total_number_density * vmr_ppmv * 1.0e-6
        h2o_cm3 = h2o_m3 * 1.0e-6

        result = dict(raw)
        if day_arr.shape == ():
            result.update(
                total_number_density_m3=float(total_number_density),
                pressure_Pa=float(pressure_pa),
                H2O_vmr_ppmv=float(vmr_ppmv),
                H2O_number_density_m3=float(h2o_m3),
                H2O_number_density_cm3=float(h2o_cm3),
                H2O_extrapolated=bool(extrapolated),
                H2O_latitude_clamped=bool(latitude_clamped),
                H2O_climatology_fallback=bool(fallback),
            )
        else:
            result.update(
                total_number_density_m3=np.asarray(total_number_density, dtype=float),
                pressure_Pa=np.asarray(pressure_pa, dtype=float),
                H2O_vmr_ppmv=np.asarray(vmr_ppmv, dtype=float),
                H2O_number_density_m3=np.asarray(h2o_m3, dtype=float),
                H2O_number_density_cm3=np.asarray(h2o_cm3, dtype=float),
                H2O_extrapolated=np.asarray(extrapolated, dtype=bool),
                H2O_latitude_clamped=np.asarray(latitude_clamped, dtype=bool),
                H2O_climatology_fallback=np.asarray(fallback, dtype=bool),
            )
        return result


class _Climatology:
    def __init__(
        self,
        month_midpoint_day: np.ndarray,
        latitude_deg: np.ndarray,
        longitude_deg: np.ndarray,
        pressure_hpa: np.ndarray,
        log_vmr_ppmv: np.ndarray,
        fallback_mask: np.ndarray,
    ) -> None:
        self.month_midpoint_day = np.asarray(month_midpoint_day, dtype=float)
        self.latitude_deg = np.asarray(latitude_deg, dtype=float)
        self.longitude_deg = np.asarray(longitude_deg, dtype=float)
        self.pressure_hpa = np.asarray(pressure_hpa, dtype=float)
        self.log_vmr_ppmv = np.asarray(log_vmr_ppmv, dtype=float)
        self.fallback_mask = np.asarray(fallback_mask, dtype=bool)
        self._validate()

    @classmethod
    def load(cls, path: Path) -> "_Climatology":
        try:
            with np.load(path, allow_pickle=False) as data:
                required = {
                    "month_midpoint_day",
                    "latitude_deg",
                    "longitude_deg",
                    "pressure_hpa",
                    "log_vmr_ppmv",
                    "fallback_mask",
                }
                missing = sorted(required - set(data.files))
                if missing:
                    raise ValueError("缺少数组: " + ", ".join(missing))
                return cls(*(data[name] for name in (
                    "month_midpoint_day",
                    "latitude_deg",
                    "longitude_deg",
                    "pressure_hpa",
                    "log_vmr_ppmv",
                    "fallback_mask",
                )))
        except (OSError, ValueError) as exc:
            raise RuntimeError("无法读取 MSIS2H2O 气候态 %s: %s" % (path, exc)) from exc

    def _validate(self) -> None:
        axes = (
            self.month_midpoint_day,
            self.latitude_deg,
            self.longitude_deg,
            self.pressure_hpa,
        )
        if any(axis.ndim != 1 or axis.size < 2 for axis in axes):
            raise ValueError("MSIS2H2O 气候态坐标必须是一维且至少含两个点")
        if self.month_midpoint_day.size != 12:
            raise ValueError("MSIS2H2O 气候态必须包含 12 个月")
        if any(np.any(np.diff(axis) <= 0.0) for axis in axes):
            raise ValueError("MSIS2H2O 气候态坐标必须严格递增")
        expected = tuple(axis.size for axis in axes)
        if self.log_vmr_ppmv.shape != expected or self.fallback_mask.shape != expected:
            raise ValueError("MSIS2H2O 气候态数组形状与坐标不一致")
        if np.any(~np.isfinite(self.log_vmr_ppmv)):
            raise ValueError("MSIS2H2O 气候态包含非有限 VMR")
        if self.latitude_deg[0] > -82.0 or self.latitude_deg[-1] < 82.0:
            raise ValueError("MSIS2H2O 气候态必须覆盖 MLS 的 ±82° 边界")

    def evaluate(
        self,
        day: np.ndarray,
        utsec: np.ndarray,
        latitude: np.ndarray,
        longitude: np.ndarray,
        pressure_hpa: np.ndarray,
    ):
        shape = day.shape
        day_f = day.reshape(-1)
        sec_f = utsec.reshape(-1)
        lat_f = latitude.reshape(-1)
        lon_f = longitude.reshape(-1)
        pressure_f = pressure_hpa.reshape(-1)

        phase = day_f - 1.0 + sec_f / 86400.0
        leap = day_f > 365.0
        phase = np.where(leap, phase * (_SEASONAL_PERIOD_DAYS / 366.0), phase)
        phase %= _SEASONAL_PERIOD_DAYS
        t0, t1, tw = _periodic_brackets(
            self.month_midpoint_day,
            phase,
            _SEASONAL_PERIOD_DAYS,
        )

        clamped_lat = np.clip(lat_f, self.latitude_deg[0], self.latitude_deg[-1])
        latitude_clamped = clamped_lat != lat_f
        y0, y1, yw = _linear_brackets(self.latitude_deg, clamped_lat)
        x0, x1, xw = _periodic_brackets(self.longitude_deg, lon_f, 360.0)

        extrapolated = pressure_f < self.pressure_hpa[0]
        vmr_log = np.empty(pressure_f.size, dtype=float)
        fallback = np.zeros(pressure_f.size, dtype=bool)

        observed = ~extrapolated
        if np.any(observed):
            if np.any(pressure_f[observed] > self.pressure_hpa[-1]):
                raise ValueError("MSIS2 压力高于 MLS 气候态覆盖范围")
            p0, p1, pw = _linear_brackets(
                np.log(self.pressure_hpa),
                np.log(pressure_f[observed]),
            )
            indices = np.flatnonzero(observed)
            vmr_log[indices], fallback[indices] = self._interpolate(
                t0[indices], t1[indices], tw[indices],
                y0[indices], y1[indices], yw[indices],
                x0[indices], x1[indices], xw[indices],
                p0, p1, pw,
            )

        if np.any(extrapolated):
            indices = np.flatnonzero(extrapolated)
            top_count = min(3, self.pressure_hpa.size)
            samples = np.empty((indices.size, top_count), dtype=float)
            sample_fallback = np.zeros((indices.size, top_count), dtype=bool)
            for level in range(top_count):
                level_index = np.full(indices.size, level, dtype=int)
                zeros = np.zeros(indices.size, dtype=float)
                samples[:, level], sample_fallback[:, level] = self._interpolate(
                    t0[indices], t1[indices], tw[indices],
                    y0[indices], y1[indices], yw[indices],
                    x0[indices], x1[indices], xw[indices],
                    level_index, level_index, zeros,
                )
            xp = np.log(self.pressure_hpa[:top_count])
            centered = xp - np.mean(xp)
            denominator = float(np.sum(centered * centered))
            slopes = np.sum((samples - np.mean(samples, axis=1, keepdims=True)) * centered, axis=1) / denominator
            slopes = np.maximum(slopes, 0.0)
            intercept = np.mean(samples, axis=1) - slopes * float(np.mean(xp))
            vmr_log[indices] = intercept + slopes * np.log(pressure_f[indices])
            fallback[indices] = np.any(sample_fallback, axis=1)

        vmr = np.exp(vmr_log)
        if np.any(~np.isfinite(vmr)) or np.any(vmr < 0.0):
            raise RuntimeError("H2O 插值产生非有限或负值")
        return (
            vmr.reshape(shape),
            extrapolated.reshape(shape),
            latitude_clamped.reshape(shape),
            fallback.reshape(shape),
        )

    def _interpolate(
        self,
        t0, t1, tw,
        y0, y1, yw,
        x0, x1, xw,
        p0, p1, pw,
    ):
        count = np.asarray(t0).size
        values = np.zeros(count, dtype=float)
        fallback = np.zeros(count, dtype=bool)
        for ti, wt in ((t0, 1.0 - tw), (t1, tw)):
            for yi, wy in ((y0, 1.0 - yw), (y1, yw)):
                for xi, wx in ((x0, 1.0 - xw), (x1, xw)):
                    for pi, wp in ((p0, 1.0 - pw), (p1, pw)):
                        weight = wt * wy * wx * wp
                        values += weight * self.log_vmr_ppmv[ti, yi, xi, pi]
                        active = weight > np.finfo(float).eps
                        fallback |= active & self.fallback_mask[ti, yi, xi, pi]
        return values, fallback


def _resolve_h2o_data_path(
    value: Optional[Union[str, Path]],
    *,
    data_dir: Optional[Union[str, Path]],
    auto_download: bool,
) -> Path:
    if value is None:
        root = ensure_model_data("msis2h2o", data_dir=data_dir, auto_download=auto_download)
        path = root / "msis2h2odata" / _DEFAULT_DATA_FILE
    else:
        path = Path(value).expanduser().resolve()
        if path.is_dir():
            direct = path / _DEFAULT_DATA_FILE
            nested = path / "msis2h2odata" / _DEFAULT_DATA_FILE
            path = direct if direct.is_file() else nested
    if not path.is_file():
        raise FileNotFoundError("找不到 MSIS2H2O 气候态文件: %s" % path)
    return path


def _validate_inputs(day, utsec, altitude, latitude, longitude) -> None:
    for name, values in (
        ("day", day),
        ("utsec", utsec),
        ("alt_km", altitude),
        ("lat_deg", latitude),
        ("lon_deg", longitude),
    ):
        if np.any(~np.isfinite(values)):
            raise ValueError("%s 包含非有限值" % name)
    if np.any(day < 1.0) or np.any(day > 366.0):
        raise ValueError("day 必须在 [1, 366] 内")
    if np.any(utsec < 0.0) or np.any(utsec >= 86400.0):
        raise ValueError("utsec 必须在 [0, 86400) 内")
    if np.any(altitude < 20.0) or np.any(altitude > 120.0):
        raise ValueError("MSIS2H2O 仅支持 20--120 km")
    if np.any(latitude < -90.0) or np.any(latitude > 90.0):
        raise ValueError("lat_deg 必须在 [-90, 90] 内")


def _linear_brackets(axis: np.ndarray, values: np.ndarray):
    values = np.asarray(values, dtype=float)
    upper = np.searchsorted(axis, values, side="right")
    upper = np.clip(upper, 1, axis.size - 1)
    lower = upper - 1
    exact_last = values == axis[-1]
    lower = np.where(exact_last, axis.size - 1, lower)
    upper = np.where(exact_last, axis.size - 1, upper)
    denominator = axis[upper] - axis[lower]
    weight = np.divide(
        values - axis[lower],
        denominator,
        out=np.zeros_like(values, dtype=float),
        where=denominator != 0.0,
    )
    return lower.astype(int), upper.astype(int), weight


def _periodic_brackets(axis: np.ndarray, values: np.ndarray, period: float):
    origin = float(axis[0])
    normalized = (np.asarray(values, dtype=float) - origin) % period + origin
    extended = np.concatenate((axis, [axis[0] + period]))
    upper_ext = np.searchsorted(extended, normalized, side="right")
    upper_ext = np.clip(upper_ext, 1, axis.size)
    lower = upper_ext - 1
    upper = upper_ext % axis.size
    denominator = extended[upper_ext] - extended[lower]
    weight = (normalized - extended[lower]) / denominator
    return lower.astype(int), upper.astype(int), weight
