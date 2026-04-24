from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence

if TYPE_CHECKING:
    import xarray as xr

try:
    import xarray as xr

    _HAS_XARRAY = True
except ImportError:
    xr = None
    _HAS_XARRAY = False

import numpy as np


MSIS2_SPECIES_NAMES = [
    "N2",
    "O2",
    "O",
    "He",
    "H",
    "Ar",
    "N",
    "AnomalousO",
    "NO",
    "NPlus",
]
MSIS00_SPECIES_NAMES = [
    "He",
    "O",
    "N2",
    "O2",
    "Ar",
    "H",
    "N",
    "AnomalousO",
    "TotalMass",
]


def _require_xarray() -> None:
    if not _HAS_XARRAY:
        raise ImportError(
            "xarray 未安装。请运行 'pip install xarray' 或 'pip install upperatmpy[full]'"
        )


def msis_to_xarray(
    result: Dict[str, Any],
    *,
    species_names: Optional[Sequence[str]] = None,
    attrs: Optional[Dict[str, Any]] = None,
) -> "xr.Dataset":
    """将 MSIS 模型 `calculate()` 返回的字典转换为 xarray Dataset。"""
    _require_xarray()

    densities = np.asarray(result["densities"])
    if densities.ndim == 1:
        densities = densities.reshape(1, -1)

    alt = np.asarray(result["alt_km"]).reshape(-1)
    t_local = np.asarray(result["T_local_K"]).reshape(-1)
    t_exo = np.asarray(result["T_exo_K"]).reshape(-1)

    if species_names is None:
        species_names = (
            MSIS2_SPECIES_NAMES
            if densities.shape[1] == len(MSIS2_SPECIES_NAMES)
            else MSIS00_SPECIES_NAMES
        )

    data_vars = {
        "T_local_K": (["point"], t_local),
        "T_exo_K": (["point"], t_exo),
    }
    for index, species in enumerate(species_names[: densities.shape[1]]):
        data_vars[f"density_{species}"] = (["point"], densities[:, index])

    dataset_attrs = {"description": "MSIS temperature and density data"}
    if attrs:
        dataset_attrs.update(attrs)

    return xr.Dataset(
        data_vars,
        coords={"point": np.arange(len(t_local)), "alt_km": (["point"], alt)},
        attrs=dataset_attrs,
    )


def hwm_to_xarray(
    result: Dict[str, Any],
    *,
    attrs: Optional[Dict[str, Any]] = None,
) -> "xr.Dataset":
    """将 HWM 模型 `calculate()` 返回的字典转换为 xarray Dataset。"""
    _require_xarray()

    alt = np.asarray(result["alt_km"]).reshape(-1)
    meridional = np.asarray(result["meridional_wind_ms"]).reshape(-1)
    zonal = np.asarray(result["zonal_wind_ms"]).reshape(-1)

    dataset_attrs = {"description": "HWM horizontal wind data"}
    if attrs:
        dataset_attrs.update(attrs)

    return xr.Dataset(
        {
            "meridional_wind_ms": (["point"], meridional),
            "zonal_wind_ms": (["point"], zonal),
        },
        coords={"point": np.arange(len(meridional)), "alt_km": (["point"], alt)},
        attrs=dataset_attrs,
    )


__all__ = [
    "msis_to_xarray",
    "hwm_to_xarray",
    "MSIS2_SPECIES_NAMES",
    "MSIS00_SPECIES_NAMES",
]
