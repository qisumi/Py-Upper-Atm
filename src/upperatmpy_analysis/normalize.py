"""Normalize heterogeneous model outputs to canonical quantities and units."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np

from .catalog import QUANTITIES, get_model_spec
from .units import convert_values


_MSIS_SPECIES = {
    "MSIS2": ("TotalMass", "N2", "O2", "O", "He", "H", "Ar", "N", "AnomalousO", "NO"),
    "MSIS2H2O": ("TotalMass", "N2", "O2", "O", "He", "H", "Ar", "N", "AnomalousO", "NO"),
    "MSIS00": ("He", "O", "N2", "O2", "Ar", "TotalMass", "H", "N", "AnomalousO"),
    "MSIS86": ("He", "O", "N2", "O2", "Ar", "TotalMass", "H", "N"),
    "MSISE90": ("He", "O", "N2", "O2", "Ar", "TotalMass", "H", "N"),
}


@dataclass
class NormalizedResult:
    model: str
    group: str
    coordinates: Dict[str, np.ndarray]
    quantities: Dict[str, np.ndarray]
    units: Dict[str, str]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "group": self.group,
            "coordinates": {key: _json_value(value) for key, value in self.coordinates.items()},
            "quantities": {key: _json_value(value) for key, value in self.quantities.items()},
            "units": dict(self.units),
            "warnings": list(self.warnings),
        }


def normalize_output(
    model_name: str,
    raw: Mapping[str, Any],
    canonical_inputs: Mapping[str, Any],
) -> NormalizedResult:
    """Normalize one supported model output without changing scientific values."""

    spec = get_model_spec(model_name)
    quantities: Dict[str, np.ndarray] = {}

    if model_name in _MSIS_SPECIES:
        quantities["T_local_K"] = np.asarray(raw["T_local_K"], dtype=float)
        quantities["T_exo_K"] = np.asarray(raw["T_exo_K"], dtype=float)
        densities = np.asarray(raw["densities"], dtype=float)
        species = _MSIS_SPECIES[model_name]
        if densities.shape == () or densities.shape[-1] != len(species):
            raise ValueError(
                "%s densities 最后一维应为 %d / last dimension must be %d"
                % (model_name, len(species), len(species))
            )
        for index, name in enumerate(species):
            values = densities[..., index]
            if name == "TotalMass":
                if model_name in ("MSIS2", "MSIS2H2O"):
                    # NRLMSIS 2.0 is already SI.
                    quantities["total_mass_density_kg_m3"] = np.asarray(values, dtype=float)
                else:
                    # Legacy MSIS interfaces return total mass in g/cm^3.
                    quantities["total_mass_density_kg_m3"] = np.asarray(
                        convert_values(values, "g/cm^3", "kg/m^3"), dtype=float
                    )
            elif name in ("NO", "NPlus"):
                # Kept out of the initial cross-version catalog because older
                # MSIS versions do not expose these species.
                continue
            else:
                if model_name in ("MSIS2", "MSIS2H2O"):
                    quantities[name + "_cm3"] = np.asarray(
                        convert_values(values, "m^-3", "cm^-3"), dtype=float
                    )
                else:
                    quantities[name + "_cm3"] = values
        if model_name == "MSIS2H2O":
            quantities["H2O_cm3"] = np.asarray(raw["H2O_number_density_cm3"], dtype=float)
            quantities["H2O_vmr_ppmv"] = np.asarray(raw["H2O_vmr_ppmv"], dtype=float)
    elif spec.group == "geomagnetic_internal":
        key_map = {
            "B_north_nT": "B_north_nT" if "B_north_nT" in raw else "X_nT",
            "B_east_nT": "B_east_nT" if "B_east_nT" in raw else "Y_nT",
            "B_down_nT": "B_down_nT" if "B_down_nT" in raw else "Z_nT",
            "B_abs_nT": "B_abs_nT" if "B_abs_nT" in raw else "F_nT",
            "H_nT": "H_nT",
            "inclination_deg": "inclination_deg",
            "declination_deg": "declination_deg",
        }
        for canonical, source in key_map.items():
            quantities[canonical] = np.asarray(raw[source], dtype=float)
    else:
        raise ValueError("尚未实现该模型的统一输出 / no normalizer for model: " + model_name)

    units = {key: QUANTITIES[key].unit for key in quantities if key in QUANTITIES}
    coordinates = _coordinates(raw, canonical_inputs, quantities)
    return NormalizedResult(
        model=model_name,
        group=spec.group,
        coordinates=coordinates,
        quantities=quantities,
        units=units,
    )


def align_results(
    results: Sequence[NormalizedResult],
    coordinate: str = "alt_km",
) -> List[NormalizedResult]:
    """Align 1-D results on the exact coordinate intersection.

    No scientific interpolation is performed. Multi-dimensional coordinates
    must already be identical, which is the normal path for ``execute_plan``.
    """

    if not results:
        return []
    arrays = [np.asarray(item.coordinates[coordinate], dtype=float) for item in results]
    if all(np.array_equal(arrays[0], item) for item in arrays[1:]):
        return list(results)
    if any(item.ndim != 1 for item in arrays):
        raise ValueError("多维坐标必须完全一致 / multidimensional coordinates must match exactly")

    common = arrays[0]
    for item in arrays[1:]:
        common = np.intersect1d(common, item)
    if common.size == 0:
        raise ValueError("模型结果没有共同坐标 / model results have no shared coordinates")

    aligned: List[NormalizedResult] = []
    for result, values in zip(results, arrays):
        lookup = {float(value): index for index, value in enumerate(values)}
        indices = np.asarray([lookup[float(value)] for value in common], dtype=int)
        coordinates = dict(result.coordinates)
        coordinates[coordinate] = common.copy()
        quantities = {
            key: np.asarray(value)[indices]
            for key, value in result.quantities.items()
        }
        aligned.append(
            NormalizedResult(
                result.model,
                result.group,
                coordinates,
                quantities,
                dict(result.units),
                list(result.warnings),
            )
        )
    return aligned


def _coordinates(
    raw: Mapping[str, Any],
    inputs: Mapping[str, Any],
    quantities: Mapping[str, np.ndarray],
) -> Dict[str, np.ndarray]:
    coordinate_names = ("year", "day_of_year", "utsec", "alt_km", "lat_deg", "lon_deg")
    reference = next(iter(quantities.values()))
    shape = np.asarray(reference).shape
    result: Dict[str, np.ndarray] = {}
    for name in coordinate_names:
        if name in raw:
            value = raw[name]
        elif name in inputs:
            value = inputs[name]
        else:
            continue
        array = np.asarray(value, dtype=float)
        try:
            result[name] = np.broadcast_to(array, shape).copy()
        except ValueError:
            # A coordinate can be provenance-only (for example year with a
            # non-broadcast density axis); preserve it rather than guessing.
            result[name] = array.copy()
    return result


def _json_value(value: Any) -> Any:
    array = np.asarray(value)
    if array.shape == ():
        scalar = array.item()
        if isinstance(scalar, float) and not np.isfinite(scalar):
            return None
        return scalar
    output = array.astype(object)
    if np.issubdtype(array.dtype, np.floating):
        output[~np.isfinite(array)] = None
    return output.tolist()
