"""Reproducible comparison and intelligent analysis for UpperAtmPy."""

from .catalog import MODELS, QUANTITIES, catalog_dict, get_model_spec, get_quantity_spec, list_models
from .compare import execute_plan, expand_inputs
from .normalize import NormalizedResult, align_results, normalize_output
from .report import AnalysisReport, SensitivityReport
from .schema import AnalysisPlan, ModelSpec, QuantitySpec, analysis_plan_json_schema
from .sensitivity import analyze_sensitivity
from .units import convert_values

__all__ = [
    "AnalysisPlan",
    "AnalysisReport",
    "SensitivityReport",
    "ModelSpec",
    "QuantitySpec",
    "NormalizedResult",
    "MODELS",
    "QUANTITIES",
    "get_model_spec",
    "get_quantity_spec",
    "list_models",
    "catalog_dict",
    "expand_inputs",
    "normalize_output",
    "align_results",
    "execute_plan",
    "analyze_sensitivity",
    "analysis_plan_json_schema",
    "convert_values",
]
