from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence

if TYPE_CHECKING:
    import xarray as xr

try:
    import xarray as xr

    _HAS_XARRAY = True
except ImportError:
    xr = None
    _HAS_XARRAY = False

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:
    np = None
    _HAS_NUMPY = False


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


def _require_xarray():
    if not _HAS_XARRAY:
        raise ImportError(
            "xarray 未安装。请运行 'pip install xarray' 或 'pip install upperatmpy[full]'"
        )


def temp_density_results_to_xarray(
    results: List[Any],
    *,
    alt_km: Optional[Sequence[float]] = None,
    lat_deg: Optional[Sequence[float]] = None,
    lon_deg: Optional[Sequence[float]] = None,
    model_version: str = "msis2",
    attrs: Optional[Dict[str, Any]] = None,
) -> "xr.Dataset":
    _require_xarray()
    import numpy as np

    species_names = (
        MSIS2_SPECIES_NAMES if model_version == "msis2" else MSIS00_SPECIES_NAMES
    )

    n_results = len(results)
    alt_arr = np.array([r.alt_km for r in results])
    t_local = np.array([r.T_local_K for r in results])
    t_exo = np.array([r.T_exo_K for r in results])

    density_matrix = np.array([list(r.densities) for r in results])

    data_vars = {
        "T_local_K": (["point"], t_local),
        "T_exo_K": (["point"], t_exo),
    }

    for i, species in enumerate(species_names):
        if i < density_matrix.shape[1]:
            data_vars[f"density_{species}"] = (["point"], density_matrix[:, i])

    coords = {"alt_km": (["point"], alt_arr)}

    if lat_deg is not None:
        lat_arr = np.atleast_1d(lat_deg)
        if len(lat_arr) == 1:
            lat_arr = np.full(n_results, lat_arr[0])
        coords["lat_deg"] = (["point"], lat_arr[:n_results])

    if lon_deg is not None:
        lon_arr = np.atleast_1d(lon_deg)
        if len(lon_arr) == 1:
            lon_arr = np.full(n_results, lon_arr[0])
        coords["lon_deg"] = (["point"], lon_arr[:n_results])

    default_attrs = {
        "model_version": model_version,
        "description": "Upper atmosphere temperature and density data",
    }
    if attrs:
        default_attrs.update(attrs)

    return xr.Dataset(data_vars, coords=coords, attrs=default_attrs)


def wind_results_to_xarray(
    results: List[Any],
    *,
    alt_km: Optional[Sequence[float]] = None,
    lat_deg: Optional[Sequence[float]] = None,
    lon_deg: Optional[Sequence[float]] = None,
    model_version: str = "hwm14",
    attrs: Optional[Dict[str, Any]] = None,
) -> "xr.Dataset":
    _require_xarray()
    import numpy as np

    n_results = len(results)
    alt_arr = np.array([r.alt_km for r in results])
    meridional = np.array([r.meridional_wind_ms for r in results])
    zonal = np.array([r.zonal_wind_ms for r in results])

    data_vars = {
        "meridional_wind_ms": (["point"], meridional),
        "zonal_wind_ms": (["point"], zonal),
    }

    coords = {"alt_km": (["point"], alt_arr)}

    if lat_deg is not None:
        lat_arr = np.atleast_1d(lat_deg)
        if len(lat_arr) == 1:
            lat_arr = np.full(n_results, lat_arr[0])
        coords["lat_deg"] = (["point"], lat_arr[:n_results])

    if lon_deg is not None:
        lon_arr = np.atleast_1d(lon_deg)
        if len(lon_arr) == 1:
            lon_arr = np.full(n_results, lon_arr[0])
        coords["lon_deg"] = (["point"], lon_arr[:n_results])

    default_attrs = {
        "model_version": model_version,
        "description": "Upper atmosphere wind data",
    }
    if attrs:
        default_attrs.update(attrs)

    return xr.Dataset(data_vars, coords=coords, attrs=default_attrs)


__all__ = [
    "temp_density_results_to_xarray",
    "wind_results_to_xarray",
    "MSIS2_SPECIES_NAMES",
    "MSIS00_SPECIES_NAMES",
]
