"""Deterministic one-factor sensitivity analysis."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from .catalog import GROUP_DEFAULT_QUANTITIES, get_model_spec
from .compare import _model_kwargs, _provenance, _validate_inputs, expand_inputs
from .normalize import normalize_output
from .report import SensitivityReport


def analyze_sensitivity(
    model_name: str,
    *,
    base_inputs: Mapping[str, Any],
    parameter: str,
    values: Any,
    quantities: Optional[Sequence[str]] = None,
    language: str = "zh",
    model_instance: Any = None,
    model_options: Optional[Mapping[str, Any]] = None,
) -> SensitivityReport:
    """Vary one input while holding all other model inputs fixed."""

    if language not in ("zh", "en"):
        raise ValueError("language 必须为 zh 或 en")
    spec = get_model_spec(model_name)
    if parameter not in spec.required_inputs + spec.optional_inputs:
        raise ValueError("%s 不接受参数 %s" % (model_name, parameter))
    expanded_values = expand_inputs({parameter: values})[parameter]
    value_array = np.asarray(expanded_values, dtype=float)
    if value_array.ndim != 1 or value_array.size < 2:
        raise ValueError("敏感性 values 必须是一维且至少含两个值")
    if not np.all(np.isfinite(value_array)):
        raise ValueError("敏感性 values 包含非有限值")

    inputs = expand_inputs(base_inputs)
    inputs[parameter] = value_array
    for name, value in inputs.items():
        if name in (parameter, "ap7"):
            continue
        if np.asarray(value).size != 1:
            raise ValueError("除变化参数外，其余输入必须为标量 / non-varied inputs must be scalar")
    _validate_inputs([spec], inputs)

    selected = list(quantities or GROUP_DEFAULT_QUANTITIES[spec.group])
    unavailable = [item for item in selected if item not in spec.quantities]
    if unavailable:
        raise ValueError("模型不提供统一量 / unavailable quantities: " + ", ".join(unavailable))

    instance = model_instance
    if instance is None:
        model_package = import_module("model")
        instance = getattr(model_package, model_name)(**dict(model_options or {}))
    raw = instance.calculate(**_model_kwargs(model_name, inputs))
    normalized = normalize_output(model_name, raw, inputs)

    output: Dict[str, Any] = {}
    summary: Dict[str, Dict[str, float]] = {}
    warnings = [model_name + ": " + note for note in spec.notes(language)]
    for quantity in selected:
        array = np.asarray(normalized.quantities[quantity], dtype=float)
        if array.shape != value_array.shape:
            try:
                array = np.broadcast_to(array, value_array.shape)
            except ValueError:
                raise ValueError("%s 输出形状无法与敏感性参数对齐" % quantity)
        if not np.all(np.isfinite(array)):
            raise ValueError("%s 返回非有限值" % quantity)
        first = float(array[0])
        last = float(array[-1])
        if abs(first) > np.finfo(float).tiny:
            relative = (last - first) * 100.0 / abs(first)
        else:
            relative = 0.0
            warnings.append(
                ("%s 首个值为零，首末相对变化记为 0；请查看绝对变化。" if language == "zh" else
                 "%s starts at zero; endpoint percent change is recorded as 0. Inspect absolute change.")
                % quantity
            )
        output[quantity] = array
        summary[quantity] = {
            "min": float(np.min(array)),
            "max": float(np.max(array)),
            "range": float(np.max(array) - np.min(array)),
            "endpoint_absolute_change": last - first,
            "endpoint_change_percent": float(relative),
        }
    return SensitivityReport(
        model=model_name,
        parameter=parameter,
        values=value_array,
        quantities=output,
        summary=summary,
        inputs=dict(inputs),
        warnings=warnings,
        provenance=_provenance([model_name]),
        language=language,
    )
