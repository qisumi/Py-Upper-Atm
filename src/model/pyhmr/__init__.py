"""
Heppner-Maynard-Rich (HMR) high-latitude electric field model wrapper.

Supports Heppner-Maynard electric potential models (A, BC, DE) and
the Heelis convection model, with conductivity and field-aligned
current computations.

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
from utils.model_data import ensure_model_data

__all__ = ["Model"]

_C_INT = C.c_int
_C_FLOAT = C.c_float

_HMR_EPOT_ARGTYPES = [
    _C_FLOAT,              # lat
    _C_FLOAT,              # lon
    _C_INT,                # model
    _C_INT,                # nmax
    C.POINTER(_C_FLOAT),   # potential
]

_HMR_PMODEL_ARGTYPES = [
    _C_FLOAT,              # lat
    _C_FLOAT,              # lon_hrs
    _C_FLOAT,              # pole2m
    _C_FLOAT,              # pole2d
    C.POINTER(_C_FLOAT),   # potential
    C.POINTER(_C_FLOAT),   # dpdlat
    C.POINTER(_C_FLOAT),   # dpdlt
]

_HMR_CONDUCT_ARGTYPES = [
    _C_FLOAT,              # lat_deg
    _C_FLOAT,              # mlt_hrs
    _C_FLOAT,              # kp
    _C_INT,                # model_type
    _C_FLOAT,              # sublat_deg
    _C_FLOAT,              # f107
    _C_INT,                # sun_model_type
    C.POINTER(_C_FLOAT),   # cond_total
]

# hmr_full(kp, sublat_deg, f107, model, nmax, pole2m, pole2d,
#          ephi[41*25], ey[41*25], ez[41*25],
#          sigma_h[41*25], sigma_p[41*25], joule[41*25], fac[41*25])
_HMR_FULL_ARGTYPES = [
    _C_FLOAT,              # kp
    _C_FLOAT,              # sublat_deg
    _C_FLOAT,              # f107
    _C_INT,                # model
    _C_INT,                # nmax
    _C_FLOAT,              # pole2m
    _C_FLOAT,              # pole2d
    C.POINTER(_C_FLOAT),   # ephi
    C.POINTER(_C_FLOAT),   # ey
    C.POINTER(_C_FLOAT),   # ez
    C.POINTER(_C_FLOAT),   # sigma_h
    C.POINTER(_C_FLOAT),   # sigma_p
    C.POINTER(_C_FLOAT),   # joule
    C.POINTER(_C_FLOAT),   # fac
]

_MODEL_MAP = {"A": 1, "BC": 2, "DE": 3, "heelis": 8}


class Model:
    """Heppner-Maynard-Rich electric field model ctypes wrapper.

    Supports Heppner-Maynard models A, BC, DE and the Heelis convection model.
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        data_root = ensure_model_data(
            "hmr",
            data_dir=data_dir,
            auto_download=auto_download,
        )
        self._data_root = data_root / "hmr"

        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "hmr.dll" if os.name == "nt" else "libhmr.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._set_data_root(self._data_root)

        self._hmr_epot = self._dll.hmr_epot
        self._hmr_epot.restype = None
        self._hmr_epot.argtypes = _HMR_EPOT_ARGTYPES

        self._hmr_pmodel = self._dll.hmr_pmodel
        self._hmr_pmodel.restype = None
        self._hmr_pmodel.argtypes = _HMR_PMODEL_ARGTYPES

        self._hmr_conduct = self._dll.hmr_conduct
        self._hmr_conduct.restype = None
        self._hmr_conduct.argtypes = _HMR_CONDUCT_ARGTYPES

        self._hmr_full = self._dll.hmr_full
        self._hmr_full.restype = None
        self._hmr_full.argtypes = _HMR_FULL_ARGTYPES

    def _set_data_root(self, data_dir: Path) -> None:
        set_data_root = self._dll.hmr_set_data_root
        set_data_root.argtypes = [C.c_char_p]
        set_data_root.restype = None
        set_data_root(os.fsencode(str(data_dir)) + b"\x00")

    def _resolve_model(self, model) -> int:
        if isinstance(model, str):
            if model not in _MODEL_MAP:
                raise ValueError(
                    f"未知模型: {model!r}，可选: {list(_MODEL_MAP.keys())}"
                )
            return _MODEL_MAP[model]
        if isinstance(model, int):
            return model
        raise TypeError(f"model 必须是字符串或整数，当前类型: {type(model).__name__}")

    def calculate(
        self,
        *,
        lat_deg,
        lon_deg,
        model: str = "A",
        nmax: int = 12,
    ) -> dict:
        """
        计算 Heppner-Maynard 电势。

        参数：
            lat_deg: 地磁纬度（度，极点=90），标量或数组。
            lon_deg: 地磁地方时（度，午夜=0，正午=180），标量或数组。
            model: 子模型名称 ("A", "BC", "DE") 或 "heelis"。
            nmax: 最大多项式阶数（默认 12）。

        返回：
            包含电势（kV）的字典。
        """
        model_idx = self._resolve_model(model)
        self._set_data_root(self._data_root)

        lat_arr, lon_arr = np.broadcast_arrays(
            np.asarray(lat_deg, dtype=float),
            np.asarray(lon_deg, dtype=float),
        )
        shape = lat_arr.shape
        lat_flat = lat_arr.reshape(-1)
        lon_flat = lon_arr.reshape(-1)
        count = lat_flat.size

        pot_arr = np.empty(count, dtype=float)

        for i in range(count):
            pot = _C_FLOAT()
            self._hmr_epot(
                _C_FLOAT(float(lat_flat[i])),
                _C_FLOAT(float(lon_flat[i])),
                _C_INT(model_idx),
                _C_INT(nmax),
                C.byref(pot),
            )
            pot_arr[i] = float(pot.value)

        scalar_input = shape == ()
        if scalar_input:
            return {
                "lat_deg": float(lat_arr),
                "lon_deg": float(lon_arr),
                "electric_potential_kV": float(pot_arr[0]),
            }
        return {
            "lat_deg": lat_arr,
            "lon_deg": lon_arr,
            "electric_potential_kV": pot_arr.reshape(lat_arr.shape),
        }

    def calculate_heelis(
        self,
        *,
        lat_deg,
        lon_hrs,
        pole2m: float = 5.0,
        pole2d: float = 0.0,
    ) -> dict:
        """
        计算 Heelis 对流模型电势。

        参数：
            lat_deg: 地磁纬度（度），标量或数组。
            lon_hrs: 地磁地方时（小时，午夜=0），标量或数组。
            pole2m: 从极点向午夜方向的旋转角度（度，默认 5.0）。
            pole2d: 绕极点向黄昏方向的旋转角度（小时，默认 0.0）。

        返回：
            包含电势（kV）和梯度的字典。
        """
        self._set_data_root(self._data_root)

        lat_arr, lon_arr = np.broadcast_arrays(
            np.asarray(lat_deg, dtype=float),
            np.asarray(lon_hrs, dtype=float),
        )
        shape = lat_arr.shape
        lat_flat = lat_arr.reshape(-1)
        lon_flat = lon_arr.reshape(-1)
        count = lat_flat.size

        pot_arr = np.empty(count, dtype=float)
        dlat_arr = np.empty(count, dtype=float)
        dlon_arr = np.empty(count, dtype=float)

        for i in range(count):
            pot = _C_FLOAT()
            dpdlat = _C_FLOAT()
            dpdlt = _C_FLOAT()
            self._hmr_pmodel(
                _C_FLOAT(float(lat_flat[i])),
                _C_FLOAT(float(lon_flat[i])),
                _C_FLOAT(pole2m),
                _C_FLOAT(pole2d),
                C.byref(pot),
                C.byref(dpdlat),
                C.byref(dpdlt),
            )
            pot_arr[i] = float(pot.value)
            dlat_arr[i] = float(dpdlat.value)
            dlon_arr[i] = float(dpdlt.value)

        scalar_input = lat_arr.shape == ()
        if scalar_input:
            return {
                "lat_deg": float(lat_arr),
                "lon_hrs": float(lon_arr),
                "electric_potential_kV": float(pot_arr[0]),
                "dlat_kV_per_rad": float(dlat_arr[0]),
                "dlon_kV_per_rad": float(dlon_arr[0]),
            }
        return {
            "lat_deg": lat_arr,
            "lon_hrs": lon_arr,
            "electric_potential_kV": pot_arr.reshape(lat_arr.shape),
            "dlat_kV_per_rad": dlat_arr.reshape(lat_arr.shape),
            "dlon_kV_per_rad": dlon_arr.reshape(lat_arr.shape),
        }

    def calculate_conductivity(
        self,
        *,
        lat_deg,
        mlt_hrs,
        kp: float = 3.0,
        sublat_deg: float = 0.0,
        f107: float = 80.0,
    ) -> dict:
        """
        计算电导率（Hall + Pedersen）。

        参数：
            lat_deg: 地磁纬度（度，50-90），标量或数组。
            mlt_hrs: 地磁地方时（小时，午夜=0），标量或数组。
            kp: Kp 指数（0-9，默认 3.0）。
            sublat_deg: 太阳直射点地磁纬度（度，默认 0.0）。
            f107: 10.7 cm 太阳射电流量（默认 80.0）。

        返回：
            包含 Hall 和 Pedersen 电导率的字典。
        """
        self._set_data_root(self._data_root)

        lat_arr, lon_arr = np.broadcast_arrays(
            np.asarray(lat_deg, dtype=float),
            np.asarray(mlt_hrs, dtype=float),
        )
        shape = lat_arr.shape
        lat_flat = lat_arr.reshape(-1)
        lon_flat = lon_arr.reshape(-1)
        count = lat_flat.size

        hall_arr = np.empty(count, dtype=float)
        ped_arr = np.empty(count, dtype=float)

        for i in range(count):
            cond = _C_FLOAT()
            # Hall conductivity
            self._hmr_conduct(
                _C_FLOAT(float(lat_flat[i])),
                _C_FLOAT(float(lon_flat[i])),
                _C_FLOAT(kp),
                _C_INT(1),
                _C_FLOAT(sublat_deg),
                _C_FLOAT(f107),
                _C_INT(1),
                C.byref(cond),
            )
            hall_arr[i] = float(cond.value)
            # Pedersen conductivity
            self._hmr_conduct(
                _C_FLOAT(float(lat_flat[i])),
                _C_FLOAT(float(lon_flat[i])),
                _C_FLOAT(kp),
                _C_INT(2),
                _C_FLOAT(sublat_deg),
                _C_FLOAT(f107),
                _C_INT(2),
                C.byref(cond),
            )
            ped_arr[i] = float(cond.value)

        scalar_input = lat_arr.shape == ()
        if scalar_input:
            return {
                "lat_deg": float(lat_arr),
                "mlt_hrs": float(lon_arr),
                "hall_conductivity_Mho": float(hall_arr[0]),
                "pedersen_conductivity_Mho": float(ped_arr[0]),
            }
        return {
            "lat_deg": lat_arr,
            "mlt_hrs": lon_arr,
            "hall_conductivity_Mho": hall_arr.reshape(lat_arr.shape),
            "pedersen_conductivity_Mho": ped_arr.reshape(lat_arr.shape),
        }

    def calculate_full(
        self,
        *,
        kp: float = 3.5,
        sublat_deg: float = 0.0,
        f107: float = 80.0,
        model: str = "A",
        nmax: int = 12,
        pole2m: float = 5.0,
        pole2d: float = 0.0,
    ) -> dict:
        """
        完整计算：电势 + 电场 + Joule加热 + 场向电流。

        在 41x25 网格上计算（纬度 50-90°，地方时 0-24h）。

        参数：
            kp: Kp 指数（0-9，默认 3.5）。
            sublat_deg: 太阳直射点地磁纬度（度，默认 0.0）。
            f107: 10.7 cm 太阳射电流量（默认 80.0）。
            model: 子模型 ("A", "BC", "DE", "heelis")。
            nmax: 最大多项式阶数（默认 12）。
            pole2m: Heelis 旋转角度（度，默认 5.0）。
            pole2d: Heelis 旋转角度（小时，默认 0.0）。

        返回：
            包含 41x25 网格结果的字典：
            - electric_potential_kV: 电势 (kV)
            - e_field_lat_mV_m: 纬向电场 (mV/m)
            - e_field_lon_mV_m: 经向电场 (mV/m)
            - hall_conductivity_Mho: Hall 电导率
            - pedersen_conductivity_Mho: Pedersen 电导率
            - joule_heating_mW_m2: Joule 加热率 (mW/m²)
            - fac_uA_m2: 场向电流 (μA/m²)
            - lat_grid_deg: 纬度网格 (50-90°)
            - mlt_grid_hrs: 地方时网格 (0-24h)
        """
        model_idx = self._resolve_model(model)
        self._set_data_root(self._data_root)

        # Allocate output arrays (41 x 25, column-major for Fortran)
        ephi = np.zeros(41 * 25, dtype=np.float32)
        ey = np.zeros(41 * 25, dtype=np.float32)
        ez = np.zeros(41 * 25, dtype=np.float32)
        sigma_h = np.zeros(41 * 25, dtype=np.float32)
        sigma_p = np.zeros(41 * 25, dtype=np.float32)
        joule = np.zeros(41 * 25, dtype=np.float32)
        fac = np.zeros(41 * 25, dtype=np.float32)

        self._hmr_full(
            _C_FLOAT(kp),
            _C_FLOAT(sublat_deg),
            _C_FLOAT(f107),
            _C_INT(model_idx),
            _C_INT(nmax),
            _C_FLOAT(pole2m),
            _C_FLOAT(pole2d),
            ephi.ctypes.data_as(C.POINTER(_C_FLOAT)),
            ey.ctypes.data_as(C.POINTER(_C_FLOAT)),
            ez.ctypes.data_as(C.POINTER(_C_FLOAT)),
            sigma_h.ctypes.data_as(C.POINTER(_C_FLOAT)),
            sigma_p.ctypes.data_as(C.POINTER(_C_FLOAT)),
            joule.ctypes.data_as(C.POINTER(_C_FLOAT)),
            fac.ctypes.data_as(C.POINTER(_C_FLOAT)),
        )

        # Reshape: Fortran is column-major, but numpy default is row-major.
        # The arrays are (41, 25) in Fortran order.
        shape = (41, 25)
        lat_grid = np.linspace(50.0, 90.0, 41)
        mlt_grid = np.linspace(0.0, 24.0, 25)

        return {
            "electric_potential_kV": ephi.reshape(shape, order='F'),
            "e_field_lat_mV_m": ez.reshape(shape, order='F'),
            "e_field_lon_mV_m": ey.reshape(shape, order='F'),
            "hall_conductivity_Mho": sigma_h.reshape(shape, order='F'),
            "pedersen_conductivity_Mho": sigma_p.reshape(shape, order='F'),
            "joule_heating_mW_m2": joule.reshape(shape, order='F'),
            "fac_uA_m2": fac.reshape(shape, order='F'),
            "lat_grid_deg": lat_grid,
            "mlt_grid_hrs": mlt_grid,
        }
