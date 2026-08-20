"""Bilingual JSON and Markdown reports for deterministic analyses."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from .catalog import get_quantity_spec
from .normalize import NormalizedResult
from .schema import AnalysisPlan


_METRIC_NAMES = {
    "zh": {
        "bias": "平均偏差",
        "mae": "平均绝对差",
        "rmse": "均方根差",
        "max_abs_difference": "最大绝对差",
        "mean_relative_difference_percent": "平均相对差(%)",
        "mean_ratio": "平均比值",
    },
    "en": {
        "bias": "Bias",
        "mae": "MAE",
        "rmse": "RMSE",
        "max_abs_difference": "Max absolute difference",
        "mean_relative_difference_percent": "Mean relative difference (%)",
        "mean_ratio": "Mean ratio",
    },
}


@dataclass
class AnalysisReport:
    plan: AnalysisPlan
    outputs: Dict[str, NormalizedResult]
    comparisons: Dict[str, Dict[str, Dict[str, Any]]]
    warnings: List[str]
    validity_intersection: Dict[str, List[float]]
    provenance: Dict[str, Any]
    citations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0",
            "plan": self.plan.to_dict(),
            "outputs": {key: value.to_dict() for key, value in self.outputs.items()},
            "comparisons": _clean_json(self.comparisons),
            "warnings": list(self.warnings),
            "validity_intersection": dict(self.validity_intersection),
            "provenance": _clean_json(self.provenance),
            "citations": list(self.citations),
            "reproducible_code": self.reproducible_code(),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, allow_nan=False)

    def to_markdown(self, language: str = "") -> str:
        lang = language or self.plan.language
        zh = lang == "zh"
        title = self.plan.title or ("大气模型对比分析" if zh else "Atmospheric Model Comparison")
        lines = ["# " + title, ""]
        lines.append("基准模型：`%s`" % self.plan.baseline if zh else "Baseline model: `%s`" % self.plan.baseline)
        lines.append("")
        lines.append("## 指标摘要" if zh else "## Metric summary")
        lines.append("")
        lines.append("| %s | %s | %s | %s |" % (
            "模型" if zh else "Model",
            "物理量" if zh else "Quantity",
            "单位" if zh else "Unit",
            "结果" if zh else "Results",
        ))
        lines.append("|---|---|---|---|")
        for model_name, quantities in self.comparisons.items():
            for quantity, entry in quantities.items():
                spec = get_quantity_spec(quantity)
                summary = entry["summary"]
                rendered = "; ".join(
                    "%s=%.6g" % (_METRIC_NAMES[lang][key], value)
                    for key, value in summary.items()
                )
                lines.append(
                    "| `%s` | %s (`%s`) | %s | %s |"
                    % (model_name, spec.title(lang), quantity, spec.unit, rendered)
                )
        if self.warnings:
            lines.extend(["", "## 科学适用性提示" if zh else "## Scientific applicability notes", ""])
            lines.extend("- " + item for item in self.warnings)
        if self.validity_intersection:
            lines.extend(["", "## 有效域交集" if zh else "## Validity intersection", ""])
            for name, bounds in self.validity_intersection.items():
                lines.append("- `%s`: [%g, %g]" % (name, bounds[0], bounds[1]))
        if self.citations:
            lines.extend(["", "## 参考资料" if zh else "## References", ""])
            lines.extend("- " + item for item in self.citations)
        lines.extend(["", "## 可复现代码" if zh else "## Reproducible code", "", "```python", self.reproducible_code(), "```"])
        return "\n".join(lines) + "\n"

    def evidence_summary(self) -> Dict[str, Any]:
        """Compact evidence allowed to be passed to an AI explainer."""

        evidence: Dict[str, Any] = {}
        for model_name, quantities in self.comparisons.items():
            for quantity, entry in quantities.items():
                evidence[model_name + ":" + quantity] = {
                    "unit": entry["unit"],
                    "summary": dict(entry["summary"]),
                }
        return {
            "baseline": self.plan.baseline,
            "evidence": evidence,
            "warnings": list(self.warnings),
            "validity_intersection": dict(self.validity_intersection),
            "citations": list(self.citations),
        }

    def reproducible_code(self) -> str:
        plan_json = json.dumps(self.plan.to_dict(), ensure_ascii=False, indent=4)
        return (
            "import json\n"
            "from upperatmpy_analysis import AnalysisPlan, execute_plan\n\n"
            "plan = AnalysisPlan.from_dict(json.loads(%r))\n"
            "report = execute_plan(plan)\n"
            "print(report.to_markdown())"
        ) % plan_json


@dataclass
class SensitivityReport:
    model: str
    parameter: str
    values: Any
    quantities: Dict[str, Any]
    summary: Dict[str, Dict[str, float]]
    inputs: Dict[str, Any]
    warnings: List[str]
    provenance: Dict[str, Any]
    language: str = "zh"

    def to_dict(self) -> Dict[str, Any]:
        return _clean_json({
            "schema_version": "1.0",
            "model": self.model,
            "parameter": self.parameter,
            "values": self.values,
            "quantities": self.quantities,
            "summary": self.summary,
            "inputs": self.inputs,
            "warnings": self.warnings,
            "provenance": self.provenance,
        })

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, allow_nan=False)

    def to_markdown(self, language: str = "") -> str:
        lang = language or self.language
        zh = lang == "zh"
        lines = ["# " + ("大气模型敏感性分析" if zh else "Atmospheric Model Sensitivity Analysis"), ""]
        lines.append(("模型" if zh else "Model") + ": `%s`  " % self.model)
        lines.append(("变化参数" if zh else "Varied parameter") + ": `%s`" % self.parameter)
        lines.extend(["", "| %s | %s | %s | %s |" % (
            "物理量" if zh else "Quantity",
            "最小值" if zh else "Minimum",
            "最大值" if zh else "Maximum",
            "首末相对变化(%)" if zh else "Endpoint change (%)",
        ), "|---|---:|---:|---:|"])
        for quantity, item in self.summary.items():
            lines.append("| `%s` | %.6g | %.6g | %.6g |" % (
                quantity, item["min"], item["max"], item["endpoint_change_percent"]
            ))
        if self.warnings:
            lines.extend(["", "## 提示" if zh else "## Notes", ""])
            lines.extend("- " + item for item in self.warnings)
        return "\n".join(lines) + "\n"


def _clean_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_json(item) for item in value]
    if hasattr(value, "tolist"):
        return _clean_json(value.tolist())
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        import math
        return value if math.isfinite(value) else None
    return value
