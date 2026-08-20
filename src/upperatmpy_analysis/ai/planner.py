"""Bilingual natural-language planning with strict deterministic validation."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from ..catalog import GROUP_DEFAULT_QUANTITIES, MODELS
from ..compare import _validate_inputs, expand_inputs
from ..schema import AnalysisPlan, analysis_plan_json_schema
from .providers import AIProvider


_QUANTITY_TERMS = {
    "T_local_K": ("局地温度", "大气温度", "local temperature", "temperature"),
    "T_exo_K": ("外逸层温度", "外层温度", "exospheric temperature", "exo temperature"),
    "total_mass_density_kg_m3": ("总质量密度", "质量密度", "mass density"),
    "O_cm3": ("氧原子密度", "原子氧", "atomic oxygen", "o density"),
    "N2_cm3": ("氮气密度", "分子氮", "molecular nitrogen", "n2 density"),
    "O2_cm3": ("氧气密度", "分子氧", "molecular oxygen", "o2 density"),
    "B_abs_nT": ("总磁场", "磁场强度", "total magnetic field", "field intensity"),
    "B_north_nT": ("北向磁场", "northward field", "north field"),
    "B_east_nT": ("东向磁场", "eastward field", "east field"),
    "B_down_nT": ("向下磁场", "downward field", "down field"),
    "inclination_deg": ("磁倾角", "inclination"),
    "declination_deg": ("磁偏角", "declination"),
}


def plan_from_text(
    query: str,
    *,
    language: str = "auto",
    provider: Optional[AIProvider] = None,
) -> AnalysisPlan:
    """Create a strict plan; a provider is optional and never executes models."""

    if not query.strip():
        raise ValueError("query 不得为空")
    resolved_language = detect_language(query) if language == "auto" else language
    if resolved_language not in ("zh", "en"):
        raise ValueError("language 必须为 auto、zh 或 en")
    if provider is None:
        plan = _rule_based_plan(query, resolved_language)
    else:
        payload = provider.generate_json(
            system_prompt=_planner_system_prompt(resolved_language),
            user_prompt=query,
            schema=analysis_plan_json_schema(),
            schema_name="upperatmpy_analysis_plan",
        )
        plan = AnalysisPlan.from_dict(payload)
        plan.language = resolved_language
    _validate_catalog_plan(plan)
    return plan


def detect_language(text: str) -> str:
    return "zh" if re.search(r"[\u3400-\u9fff]", text) else "en"


def _rule_based_plan(query: str, language: str) -> AnalysisPlan:
    lower = query.lower()
    models = [name for name in MODELS if name.lower() in lower]
    if len(models) < 2:
        raise ValueError(
            "请明确写出至少两个目录模型名，例如 MSIS2 和 MSIS00。"
            if language == "zh"
            else "Name at least two catalog models, for example MSIS2 and MSIS00."
        )
    groups = {MODELS[name].group for name in models}
    if len(groups) != 1:
        raise ValueError("所选模型不属于同一科学分组" if language == "zh" else "Selected models are not in one scientific group")
    group = next(iter(groups))

    inputs: Dict[str, Any] = {}
    if group == "neutral_atmosphere":
        _capture(inputs, "year", query, (r"(?:年份|year)\s*[:=]?\s*(\d{4})", r"(\d{4})\s*年"), int)
        _capture(inputs, "day_of_year", query, (r"(?:doy|day[_ ]?of[_ ]?year|年积日|第)\s*[:=]?\s*(\d{1,3})(?:\s*天)?",), int)
        _capture(inputs, "utsec", query, (r"(?:utsec|ut秒|世界时秒)\s*[:=]?\s*(\d+(?:\.\d+)?)",), float)
        time_match = re.search(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(?:ut|utc|世界时)", lower)
        if time_match and "utsec" not in inputs:
            inputs["utsec"] = int(time_match.group(1)) * 3600 + int(time_match.group(2)) * 60 + int(time_match.group(3) or 0)
        _capture(inputs, "f107a", query, (r"f10[.]?7a\s*[:=]?\s*(\d+(?:\.\d+)?)",), float)
        _capture(inputs, "f107", query, (r"f10[.]?7(?!a)\s*[:=]?\s*(\d+(?:\.\d+)?)",), float)
    else:
        _capture(inputs, "year", query, (r"(?:年份|year)\s*[:=]?\s*(\d{4}(?:\.\d+)?)", r"(\d{4}(?:\.\d+)?)\s*年"), float)

    _capture(inputs, "lat_deg", query, (r"(?:纬度|lat(?:itude)?)\s*[:=]?\s*(-?\d+(?:\.\d+)?)",), float)
    _capture(inputs, "lon_deg", query, (r"(?:经度|lon(?:gitude)?)\s*[:=]?\s*(-?\d+(?:\.\d+)?)",), float)
    altitude = _altitude_value(query)
    if altitude is not None:
        inputs["alt_km"] = altitude

    quantities = [
        name for name, terms in _QUANTITY_TERMS.items()
        if any(term in lower for term in terms)
        and all(name in MODELS[model].quantities for model in models)
    ]
    if not quantities:
        quantities = list(GROUP_DEFAULT_QUANTITIES[group])
    title = "UpperAtmPy 模型对比" if language == "zh" else "UpperAtmPy model comparison"
    plan = AnalysisPlan(
        models=models,
        inputs=inputs,
        quantities=quantities,
        baseline=models[0],
        language=language,
        title=title,
    )
    return plan


def _altitude_value(query: str) -> Optional[Any]:
    normalized = query.lower().replace("–", "-").replace("—", "-").replace("~", "-")
    range_patterns = (
        r"(?:高度|海拔|alt(?:itude)?)\D{0,15}(-?\d+(?:\.\d+)?)\s*(?:-|到|至|to)\s*(-?\d+(?:\.\d+)?)\s*(?:km|千米|公里)",
        r"(-?\d+(?:\.\d+)?)\s*(?:-|到|至|to)\s*(-?\d+(?:\.\d+)?)\s*(?:km|千米|公里)(?:\s*(?:高度|altitude))?",
    )
    for pattern in range_patterns:
        match = re.search(pattern, normalized)
        if match:
            step_match = re.search(r"(?:步长|step)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:km|千米|公里)?", normalized)
            step = float(step_match.group(1)) if step_match else 10.0
            return {"start": float(match.group(1)), "stop": float(match.group(2)), "step": step, "num": None}
    match = re.search(r"(?:高度|海拔|alt(?:itude)?)\s*[:=]?\s*(-?\d+(?:\.\d+)?)\s*(?:km|千米|公里)", normalized)
    return float(match.group(1)) if match else None


def _capture(target: Dict[str, Any], name: str, text: str, patterns: Any, cast: Any) -> None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            target[name] = cast(match.group(1))
            return


def _validate_catalog_plan(plan: AnalysisPlan) -> None:
    specs = []
    for name in plan.models:
        if name not in MODELS:
            raise ValueError("AI 计划包含目录外模型 / plan contains unknown model: " + name)
        specs.append(MODELS[name])
    groups = {item.group for item in specs}
    if len(groups) != 1:
        raise ValueError("AI 计划混合了不兼容模型组 / incompatible model groups")
    expanded = expand_inputs(plan.inputs)
    _validate_inputs(specs, expanded)
    for quantity in plan.quantities or GROUP_DEFAULT_QUANTITIES[specs[0].group]:
        if any(quantity not in spec.quantities for spec in specs):
            raise ValueError("AI 计划请求了不可共同比较的量: " + quantity)


def _planner_system_prompt(language: str) -> str:
    catalog = {
        name: {
            "group": spec.group,
            "required_inputs": list(spec.required_inputs),
            "optional_inputs": list(spec.optional_inputs),
            "quantities": list(spec.quantities),
            "validity": {key: list(value) for key, value in spec.validity.items()},
        }
        for name, spec in MODELS.items()
    }
    return (
        "You convert a bilingual user request into one strict UpperAtmPy AnalysisPlan. "
        "Never calculate atmospheric values. Never invent missing scientific inputs, model names, or quantities. "
        "Select only models in one catalog group and preserve explicit user values. "
        "Include every canonical input key required by the schema and set unspecified inputs to null. "
        "Use a grid object with start, stop, and exactly one of step or num; set the unused field to null. "
        "The response language field must be %s. Catalog: %s"
    ) % (language, json.dumps(catalog, ensure_ascii=False, separators=(",", ":")))
