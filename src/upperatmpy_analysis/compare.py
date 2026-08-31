"""Deterministic execution and comparison engine."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .catalog import GROUP_DEFAULT_QUANTITIES, get_model_spec
from .normalize import NormalizedResult, align_results, normalize_output
from .report import AnalysisReport
from .schema import AnalysisPlan


def execute_plan(
    plan: AnalysisPlan,
    *,
    model_instances: Optional[Mapping[str, Any]] = None,
    model_options: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> AnalysisReport:
    """Validate and execute a comparison plan.

    ``model_instances`` is primarily useful for controlled deployments and
    tests. Ordinary callers should let this function lazily instantiate the
    public classes from :mod:`model`.
    """

    plan.validate_basic()
    specs = [get_model_spec(name) for name in plan.models]
    groups = {item.group for item in specs}
    if len(groups) != 1:
        raise ValueError("只能比较同一科学分组的模型 / models must share one scientific group")
    group = specs[0].group
    inputs = expand_inputs(plan.inputs)
    validity = _validate_inputs(specs, inputs)

    quantities = list(plan.quantities or GROUP_DEFAULT_QUANTITIES[group])
    if not quantities:
        raise ValueError("quantities 不得为空")
    for quantity in quantities:
        missing = [spec.name for spec in specs if quantity not in spec.quantities]
        if missing:
            raise ValueError(
                "统一量 %s 并非所有模型都提供 / quantity unavailable in: %s"
                % (quantity, ", ".join(missing))
            )
    # Store resolved defaults so reports and reproduced runs are identical.
    plan.quantities = quantities

    options = model_options or {}
    supplied = model_instances or {}
    outputs: List[NormalizedResult] = []
    for spec in specs:
        instance = supplied.get(spec.name)
        if instance is None:
            model_package = import_module("model")
            model_class = getattr(model_package, spec.name)
            instance = model_class(**dict(options.get(spec.name, {})))
        kwargs = _model_kwargs(spec.name, inputs)
        raw = instance.calculate(**kwargs)
        normalized = normalize_output(spec.name, raw, inputs)
        for quantity in quantities:
            values = np.asarray(normalized.quantities[quantity], dtype=float)
            if not np.all(np.isfinite(values)):
                raise ValueError("%s.%s 返回非有限值 / returned non-finite values" % (spec.name, quantity))
        outputs.append(normalized)

    outputs = align_results(outputs)
    output_map = {item.model: item for item in outputs}
    comparisons = _compare_outputs(plan, output_map)
    warnings = _collect_warnings(specs, plan.language)
    warnings.extend(_metric_warnings(comparisons, plan.language))
    citations = sorted({citation for spec in specs for citation in spec.citations})
    return AnalysisReport(
        plan=plan,
        outputs=output_map,
        comparisons=comparisons,
        warnings=warnings,
        validity_intersection={key: [value[0], value[1]] for key, value in validity.items()},
        provenance=_provenance(plan.models),
        citations=citations,
    )


def expand_inputs(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    """Expand ``{start, stop, step|num}`` grid objects to NumPy arrays."""

    result: Dict[str, Any] = {}
    for name, value in inputs.items():
        if not isinstance(value, Mapping):
            result[name] = value
            continue
        unknown = sorted(set(value) - {"start", "stop", "step", "num"})
        if unknown or "start" not in value or "stop" not in value:
            raise ValueError("输入网格格式错误 / invalid grid for %s" % name)
        start = float(value["start"])
        stop = float(value["stop"])
        step = value.get("step")
        num = value.get("num")
        if (step is None) == (num is None):
            raise ValueError("%s 网格必须且只能指定 step 或 num" % name)
        if num is not None:
            count = int(num)
            if count < 2 or count > 1000000:
                raise ValueError("%s.num 必须在 2 到 1000000 之间" % name)
            result[name] = np.linspace(start, stop, count)
        else:
            increment = float(step)
            if increment == 0.0 or (stop - start) * increment < 0.0:
                raise ValueError("%s.step 的方向必须指向 stop" % name)
            count = int(np.floor((stop - start) / increment + 1e-12)) + 1
            if count < 1 or count > 1000000:
                raise ValueError("%s 网格点数超出范围" % name)
            values = start + np.arange(count, dtype=float) * increment
            if not np.isclose(values[-1], stop) and (stop - values[-1]) * increment > 0:
                values = np.append(values, stop)
            result[name] = values
    return result


def _validate_inputs(specs: Sequence[Any], inputs: Mapping[str, Any]) -> Dict[str, Tuple[float, float]]:
    allowed = set()
    for spec in specs:
        allowed.update(spec.required_inputs)
        allowed.update(spec.optional_inputs)
        missing = [name for name in spec.required_inputs if name not in inputs]
        if missing:
            raise ValueError("%s 缺少输入 / missing inputs: %s" % (spec.name, ", ".join(missing)))
    unknown = sorted(set(inputs) - allowed)
    if unknown:
        raise ValueError("当前模型组不接受输入 / unsupported inputs: " + ", ".join(unknown))

    validity: Dict[str, Tuple[float, float]] = {}
    keys = {key for spec in specs for key in spec.validity}
    for key in keys:
        ranges = [spec.validity[key] for spec in specs if key in spec.validity]
        low = max(item[0] for item in ranges)
        high = min(item[1] for item in ranges)
        if low > high:
            raise ValueError("模型的 %s 有效域没有交集" % key)
        validity[key] = (float(low), float(high))
        if key in inputs:
            values = np.asarray(inputs[key], dtype=float)
            if not np.all(np.isfinite(values)):
                raise ValueError("%s 包含非有限值 / contains non-finite values" % key)
            if np.any(values < low) or np.any(values > high):
                raise ValueError(
                    "%s 超出模型共同有效域 [%g, %g] / outside shared validity domain"
                    % (key, low, high)
                )
    if specs[0].group == "neutral_atmosphere":
        years = np.asarray(inputs["year"], dtype=float)
        days = np.asarray(inputs["day_of_year"], dtype=float)
        if np.any(years != np.floor(years)) or np.any(days != np.floor(days)):
            raise ValueError("year 和 day_of_year 必须为整数")
        if "local_time_hours" in inputs:
            local_time = np.asarray(inputs["local_time_hours"], dtype=float)
            if not np.all(np.isfinite(local_time)) or np.any(local_time < 0.0) or np.any(local_time > 24.0):
                raise ValueError("local_time_hours 必须在 [0, 24] 内")
        if "ap7" in inputs:
            ap7 = np.asarray(inputs["ap7"], dtype=float)
            if not np.all(np.isfinite(ap7)) or ap7.ndim not in (1, 2) or ap7.shape[-1] != 7:
                raise ValueError("ap7 必须为有限的长度 7 向量或 (N, 7) 数组")
    return validity


def _model_kwargs(model_name: str, inputs: Mapping[str, Any]) -> Dict[str, Any]:
    if model_name in ("MSIS2", "MSIS2H2O"):
        result = {
            "day": inputs["day_of_year"],
            "utsec": inputs["utsec"],
            "alt_km": inputs["alt_km"],
            "lat_deg": inputs["lat_deg"],
            "lon_deg": inputs["lon_deg"],
            "f107a": inputs["f107a"],
            "f107": inputs["f107"],
        }
    elif model_name in ("MSIS00", "MSIS86", "MSISE90"):
        year = np.asarray(inputs["year"], dtype=int)
        day = np.asarray(inputs["day_of_year"], dtype=int)
        local_time = inputs.get("local_time_hours")
        if local_time is None:
            local_time = (
                np.asarray(inputs["utsec"], dtype=float) / 3600.0
                + np.asarray(inputs["lon_deg"], dtype=float) / 15.0
            ) % 24.0
        result = {
            "iyd": year * 1000 + day,
            "sec": inputs["utsec"],
            "alt_km": inputs["alt_km"],
            "lat_deg": inputs["lat_deg"],
            "lon_deg": inputs["lon_deg"],
            "stl_hours": local_time,
            "f107a": inputs["f107a"],
            "f107": inputs["f107"],
        }
    elif get_model_spec(model_name).group == "geomagnetic_internal":
        result = {key: inputs[key] for key in ("year", "lat_deg", "lon_deg", "alt_km")}
    else:
        raise ValueError("没有模型输入适配器 / no input adapter for " + model_name)
    if "ap7" in inputs and model_name in ("MSIS2", "MSIS2H2O", "MSIS00", "MSIS86", "MSISE90"):
        result["ap7"] = inputs["ap7"]
    return result


def _compare_outputs(
    plan: AnalysisPlan,
    outputs: Mapping[str, NormalizedResult],
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    baseline = outputs[str(plan.baseline)]
    result: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for model_name in plan.models:
        if model_name == plan.baseline:
            continue
        result[model_name] = {}
        for quantity in plan.quantities:
            reference, candidate = np.broadcast_arrays(
                np.asarray(baseline.quantities[quantity], dtype=float),
                np.asarray(outputs[model_name].quantities[quantity], dtype=float),
            )
            difference = candidate - reference
            absolute = np.abs(difference)
            relative = np.divide(
                difference * 100.0,
                np.abs(reference),
                out=np.full(reference.shape, np.nan, dtype=float),
                where=np.abs(reference) > np.finfo(float).tiny,
            )
            ratio = np.divide(
                candidate,
                reference,
                out=np.full(reference.shape, np.nan, dtype=float),
                where=np.abs(reference) > np.finfo(float).tiny,
            )
            all_metrics = {
                "bias": float(np.mean(difference)),
                "mae": float(np.mean(absolute)),
                "rmse": float(np.sqrt(np.mean(difference * difference))),
                "max_abs_difference": float(np.max(absolute)),
                "mean_relative_difference_percent": _finite_mean(relative),
                "mean_ratio": _finite_mean(ratio),
            }
            result[model_name][quantity] = {
                "baseline": plan.baseline,
                "unit": baseline.units[quantity],
                "difference": difference,
                "absolute_difference": absolute,
                "relative_difference_percent": relative,
                "ratio": ratio,
                "zero_baseline_count": int(np.count_nonzero(np.abs(reference) <= np.finfo(float).tiny)),
                "summary": {key: all_metrics[key] for key in plan.metrics},
            }
    return result


def _finite_mean(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if finite.size else 0.0


def _collect_warnings(specs: Sequence[Any], language: str) -> List[str]:
    result: List[str] = []
    for spec in specs:
        for note in spec.notes(language):
            value = "%s: %s" % (spec.name, note)
            if value not in result:
                result.append(value)
    return result


def _metric_warnings(
    comparisons: Mapping[str, Mapping[str, Mapping[str, Any]]],
    language: str,
) -> List[str]:
    warnings: List[str] = []
    for model_name, quantities in comparisons.items():
        for quantity, entry in quantities.items():
            count = int(entry.get("zero_baseline_count", 0))
            if count:
                if language == "zh":
                    warnings.append(
                        "%s.%s 有 %d 个基准值为零；这些点的比值和相对差在 JSON 中记为 null。"
                        % (model_name, quantity, count)
                    )
                else:
                    warnings.append(
                        "%s.%s has %d zero baseline value(s); point ratios and relative differences are null in JSON."
                        % (model_name, quantity, count)
                    )
    return warnings


def _provenance(models: Sequence[str]) -> Dict[str, Any]:
    try:
        package_version = version("upperatmpy")
    except PackageNotFoundError:
        package_version = "source-tree"
    return {
        "engine": "upperatmpy-analysis-deterministic",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "upperatmpy_version": package_version,
        "models": list(models),
        "ai_used_for_calculation": False,
    }
