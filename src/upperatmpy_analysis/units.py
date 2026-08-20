"""Small dependency-free unit conversions used by canonical normalization."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np


_LINEAR_CONVERSIONS: Dict[Tuple[str, str], float] = {
    ("g/cm^3", "kg/m^3"): 1000.0,
    ("kg/m^3", "g/cm^3"): 0.001,
    ("m^-3", "cm^-3"): 1.0e-6,
    ("cm^-3", "m^-3"): 1.0e6,
    ("G", "nT"): 1.0e5,
    ("nT", "G"): 1.0e-5,
    ("m", "km"): 1.0e-3,
    ("km", "m"): 1.0e3,
}


def convert_values(values: Any, from_unit: str, to_unit: str) -> Any:
    """Convert known linear units while preserving scalar/array behavior."""

    if from_unit == to_unit:
        factor = 1.0
    else:
        try:
            factor = _LINEAR_CONVERSIONS[(from_unit, to_unit)]
        except KeyError:
            raise ValueError("不支持单位转换 / unsupported conversion: %s -> %s" % (from_unit, to_unit))
    array = np.asarray(values, dtype=float) * factor
    return float(array) if array.shape == () else array
