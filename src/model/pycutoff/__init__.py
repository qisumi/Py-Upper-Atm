"""
地磁截止刚度模型（Geomagnetic Cutoff Rigidity）wrapper。

基于 Smart & Shea 宇宙线轨迹追踪程序（IGRF-95 磁场模型），
计算给定位置和方向的带电粒子轨迹，确定地磁截止刚度。

Public API:
    Model
"""

from __future__ import annotations

import ctypes as C
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np
from utils.dll_loader import configure_dll_directories, resolve_dll_path

__all__ = ["Model"]

_C_INT = C.c_int
_C_DOUBLE = C.c_double
_NumberOrArray = Union[float, np.ndarray]

_TRAJECTORY_ARGTYPES = [
    _C_DOUBLE,            # lat_deg (value)
    _C_DOUBLE,            # lon_deg (value)
    _C_DOUBLE,            # rigidity_gv (value)
    _C_DOUBLE,            # zenith_deg (value)
    _C_DOUBLE,            # azimuth_deg (value)
    C.POINTER(_C_INT),    # result_code (out)
    C.POINTER(_C_DOUBLE), # faslat (out)
    C.POINTER(_C_DOUBLE), # faslon (out)
    C.POINTER(_C_DOUBLE), # path_length (out)
]

_FATE_MAP = {
    1: "allowed",
    0: "failed",
    -1: "reentrant",
}


class Model:
    """地磁截止刚度模型 ctypes 封装。

    基于 Smart & Shea 宇宙线轨迹追踪程序（IGRF-95 磁场模型），
    使用 Runge-Kutta 积分计算带电粒子在地磁场中的轨迹。

    无需外部数据文件 — IGRF-95 系数硬编码在 Fortran 源码中。

    两种计算模式：
    - 单轨迹模式：指定刚度，计算单条轨迹的命运
    - 扫描模式：从高刚度向下扫描，找到截止刚度

    单轨迹模式支持 numpy 广播输入；扫描模式一次处理一个位置。
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "cutoff.dll" if os.name == "nt" else "libcutoff.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))

        self._trajectory = self._dll.cutoff_trajectory
        self._trajectory.restype = None
        self._trajectory.argtypes = _TRAJECTORY_ARGTYPES

    def calculate(
        self,
        *,
        lat_deg: _NumberOrArray,
        lon_deg: _NumberOrArray,
        rigidity_gv: Optional[_NumberOrArray] = None,
        zenith_deg: _NumberOrArray = 0.0,
        azimuth_deg: _NumberOrArray = 0.0,
        start_rigidity_gv: float = 20.0,
        delta_rigidity_mv: float = 10.0,
        max_trajectories: int = 1000,
    ) -> dict:
        """计算地磁截止刚度或单条轨迹。

        参数：
            lat_deg: 地理纬度（度），-90 到 90。
            lon_deg: 地理经度（度），-180 到 360。
            rigidity_gv: 磁刚度（GV）。若指定，计算单条轨迹；若为 None，执行扫描。
                单轨迹模式可传入标量或可广播数组。
            zenith_deg: 天顶角（度），0 到 180，默认 0（垂直向上）。
            azimuth_deg: 方位角（度），默认 0（北）。
            start_rigidity_gv: 扫描起始刚度（GV），默认 20.0。仅扫描模式使用。
            delta_rigidity_mv: 刚度步长（MV），默认 10.0。仅扫描模式使用。
            max_trajectories: 最大轨迹数，默认 1000。仅扫描模式使用。

        返回：
            包含计算结果的字典。详见模块文档。
        """
        if rigidity_gv is not None:
            return self._calculate_single_broadcast(
                lat_deg, lon_deg, rigidity_gv, zenith_deg, azimuth_deg,
            )

        lat = self._require_scan_scalar(lat_deg, "lat_deg")
        lon = self._require_scan_scalar(lon_deg, "lon_deg")
        zenith = self._require_scan_scalar(zenith_deg, "zenith_deg")
        azimuth = self._require_scan_scalar(azimuth_deg, "azimuth_deg")
        start = self._require_scan_scalar(start_rigidity_gv, "start_rigidity_gv")
        delta = self._require_scan_scalar(delta_rigidity_mv, "delta_rigidity_mv")
        max_traj = self._require_scan_integer(max_trajectories)

        self._validate_inputs(lat, lon, zenith)
        return self._calculate_scan(
            lat, lon, zenith, azimuth, start, delta, max_traj,
        )

    def _validate_inputs(
        self, lat_deg: float, lon_deg: float, zenith_deg: float,
    ) -> None:
        if not (-90.0 <= lat_deg <= 90.0):
            raise ValueError(
                f"lat_deg 必须在 -90 到 90 之间，当前值: {lat_deg}"
            )
        if not (-180.0 <= lon_deg <= 360.0):
            raise ValueError(
                f"lon_deg 必须在 -180 到 360 之间，当前值: {lon_deg}"
            )
        if not (0.0 <= zenith_deg <= 180.0):
            raise ValueError(
                f"zenith_deg 必须在 0 到 180 之间，当前值: {zenith_deg}"
            )

    def _validate_input_arrays(
        self,
        lat_deg: np.ndarray,
        lon_deg: np.ndarray,
        zenith_deg: np.ndarray,
        rigidity_gv: Optional[np.ndarray] = None,
    ) -> None:
        def first_bad(values: np.ndarray, mask: np.ndarray) -> float:
            return float(values.reshape(-1)[mask.reshape(-1)][0])

        lat_bad = (lat_deg < -90.0) | (lat_deg > 90.0)
        if np.any(lat_bad):
            raise ValueError(
                f"lat_deg 必须在 -90 到 90 之间，当前值: "
                f"{first_bad(lat_deg, lat_bad)}"
            )

        lon_bad = (lon_deg < -180.0) | (lon_deg > 360.0)
        if np.any(lon_bad):
            raise ValueError(
                f"lon_deg 必须在 -180 到 360 之间，当前值: "
                f"{first_bad(lon_deg, lon_bad)}"
            )

        zenith_bad = (zenith_deg < 0.0) | (zenith_deg > 180.0)
        if np.any(zenith_bad):
            raise ValueError(
                f"zenith_deg 必须在 0 到 180 之间，当前值: "
                f"{first_bad(zenith_deg, zenith_bad)}"
            )

        if rigidity_gv is not None:
            rigidity_bad = rigidity_gv <= 0.0
            if np.any(rigidity_bad):
                raise ValueError(
                    f"rigidity_gv 必须大于 0，当前值: "
                    f"{first_bad(rigidity_gv, rigidity_bad)}"
                )

    def _require_scan_scalar(self, value, name: str) -> float:
        arr = np.asarray(value)
        if arr.ndim != 0:
            raise ValueError(
                f"{name} 在扫描模式下必须是标量，当前形状: {arr.shape}"
            )
        return float(arr)

    def _require_scan_integer(self, value) -> int:
        numeric = self._require_scan_scalar(value, "max_trajectories")
        if not numeric.is_integer():
            raise ValueError(
                f"max_trajectories 必须是整数，当前值: {numeric}"
            )
        return int(numeric)

    def _calculate_single_broadcast(
        self,
        lat_deg: _NumberOrArray,
        lon_deg: _NumberOrArray,
        rigidity_gv: _NumberOrArray,
        zenith_deg: _NumberOrArray,
        azimuth_deg: _NumberOrArray,
    ) -> dict:
        lat_arr = np.asarray(lat_deg, dtype=float)
        lon_arr = np.asarray(lon_deg, dtype=float)
        rigidity_arr = np.asarray(rigidity_gv, dtype=float)
        zenith_arr = np.asarray(zenith_deg, dtype=float)
        azimuth_arr = np.asarray(azimuth_deg, dtype=float)

        lat_b, lon_b, rigidity_b, zenith_b, azimuth_b = np.broadcast_arrays(
            lat_arr, lon_arr, rigidity_arr, zenith_arr, azimuth_arr,
        )
        self._validate_input_arrays(lat_b, lon_b, zenith_b, rigidity_b)

        scalar_input = all(
            arr.ndim == 0
            for arr in [lat_arr, lon_arr, rigidity_arr, zenith_arr, azimuth_arr]
        )
        shape = lat_b.shape
        flat_count = lat_b.size

        result_codes = np.empty(flat_count, dtype=int)
        fates = np.empty(flat_count, dtype=object)
        faslats = np.empty(flat_count, dtype=float)
        faslons = np.empty(flat_count, dtype=float)
        paths = np.empty(flat_count, dtype=float)

        for i, (lat, lon, rigidity, zenith, azimuth) in enumerate(
            zip(
                lat_b.reshape(-1),
                lon_b.reshape(-1),
                rigidity_b.reshape(-1),
                zenith_b.reshape(-1),
                azimuth_b.reshape(-1),
            )
        ):
            result = self._calculate_single(
                float(lat),
                float(lon),
                float(rigidity),
                float(zenith),
                float(azimuth),
            )
            result_codes[i] = result["result_code"]
            fates[i] = result["fate"]
            faslats[i] = result["asymptotic_latitude_deg"]
            faslons[i] = result["asymptotic_longitude_deg"]
            paths[i] = result["path_length_re"]

        if scalar_input:
            return {
                "rigidity_gv": float(rigidity_b.reshape(-1)[0]),
                "result_code": int(result_codes[0]),
                "fate": str(fates[0]),
                "asymptotic_latitude_deg": float(faslats[0]),
                "asymptotic_longitude_deg": float(faslons[0]),
                "path_length_re": float(paths[0]),
            }

        return {
            "rigidity_gv": rigidity_b.reshape(shape).astype(float),
            "result_code": result_codes.reshape(shape),
            "fate": fates.reshape(shape),
            "asymptotic_latitude_deg": faslats.reshape(shape),
            "asymptotic_longitude_deg": faslons.reshape(shape),
            "path_length_re": paths.reshape(shape),
        }

    def _calculate_single(
        self,
        lat_deg: float,
        lon_deg: float,
        rigidity_gv: float,
        zenith_deg: float,
        azimuth_deg: float,
    ) -> dict:
        if rigidity_gv <= 0:
            raise ValueError(
                f"rigidity_gv 必须大于 0，当前值: {rigidity_gv}"
            )

        result_code = _C_INT()
        faslat = _C_DOUBLE()
        faslon = _C_DOUBLE()
        path_length = _C_DOUBLE()

        self._trajectory(
            _C_DOUBLE(float(lat_deg)),
            _C_DOUBLE(float(lon_deg)),
            _C_DOUBLE(float(rigidity_gv)),
            _C_DOUBLE(float(zenith_deg)),
            _C_DOUBLE(float(azimuth_deg)),
            C.byref(result_code),
            C.byref(faslat),
            C.byref(faslon),
            C.byref(path_length),
        )

        rc = int(result_code.value)
        return {
            "rigidity_gv": float(rigidity_gv),
            "result_code": rc,
            "fate": _FATE_MAP.get(rc, "unknown"),
            "asymptotic_latitude_deg": float(faslat.value),
            "asymptotic_longitude_deg": float(faslon.value),
            "path_length_re": float(path_length.value),
        }

    def _calculate_scan(
        self,
        lat_deg: float,
        lon_deg: float,
        zenith_deg: float,
        azimuth_deg: float,
        start_rigidity_gv: float,
        delta_rigidity_mv: float,
        max_trajectories: int,
    ) -> dict:
        if start_rigidity_gv <= 0:
            raise ValueError(
                f"start_rigidity_gv 必须大于 0，当前值: {start_rigidity_gv}"
            )
        if delta_rigidity_mv <= 0:
            raise ValueError(
                f"delta_rigidity_mv 必须大于 0，当前值: {delta_rigidity_mv}"
            )
        if max_trajectories < 1:
            raise ValueError(
                f"max_trajectories 必须大于 0，当前值: {max_trajectories}"
            )

        # Scan loop in Python (calls single trajectory for each rigidity)
        rigidities = []
        results = []
        faslats = []
        faslons = []
        paths = []

        pc = start_rigidity_gv
        for _ in range(max_trajectories):
            if pc <= 0:
                break
            r = self._calculate_single(
                lat_deg, lon_deg, pc, zenith_deg, azimuth_deg,
            )
            rigidities.append(pc)
            results.append(r["result_code"])
            faslats.append(r["asymptotic_latitude_deg"])
            faslons.append(r["asymptotic_longitude_deg"])
            paths.append(r["path_length_re"])
            pc -= delta_rigidity_mv / 1000.0

        n = len(rigidities)
        rigidities = np.array(rigidities)
        results = np.array(results, dtype=int)
        faslats = np.array(faslats)
        faslons = np.array(faslons)
        paths = np.array(paths)

        # Find cutoff: last allowed trajectory before a non-allowed one
        cutoff_gv = 0.0
        cutoff_fate = "forbidden"
        cutoff_faslat = 0.0
        cutoff_faslon = 0.0
        cutoff_path = 0.0

        for i in range(n):
            if results[i] == 1:  # allowed
                cutoff_gv = rigidities[i]
                cutoff_faslat = faslats[i]
                cutoff_faslon = faslons[i]
                cutoff_path = paths[i]
            else:
                if cutoff_gv > 0:
                    cutoff_fate = "allowed"
                break

        return {
            "cutoff_rigidity_gv": float(cutoff_gv),
            "fate": cutoff_fate,
            "asymptotic_latitude_deg": float(cutoff_faslat),
            "asymptotic_longitude_deg": float(cutoff_faslon),
            "path_length_re": float(cutoff_path),
            "n_trajectories_computed": n,
            "rigidity_gv": rigidities,
            "trajectory_results": results,
        }
