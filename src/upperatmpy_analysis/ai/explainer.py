"""Evidence-bounded bilingual explanations."""

from __future__ import annotations

import json
from typing import Optional

from ..report import AnalysisReport
from .providers import AIProvider


def explain_report(
    report: AnalysisReport,
    *,
    language: str = "",
    provider: Optional[AIProvider] = None,
) -> str:
    """Explain only evidence present in a deterministic report."""

    lang = language or report.plan.language
    if lang not in ("zh", "en"):
        raise ValueError("language 必须为 zh 或 en")
    evidence = report.evidence_summary()
    if provider is not None:
        return provider.generate_text(
            system_prompt=(
                "Explain an UpperAtmPy deterministic comparison in %s. "
                "Use only the supplied JSON evidence. Do not invent causes, values, validity ranges, or citations. "
                "Attach an evidence key such as [MSIS00:T_local_K] to every numerical claim. "
                "Clearly separate observed differences from possible physical interpretations, and retain warnings."
            ) % ("Chinese" if lang == "zh" else "English"),
            user_prompt=json.dumps(evidence, ensure_ascii=False, allow_nan=False),
        )
    return _deterministic_explanation(report, lang)


def _deterministic_explanation(report: AnalysisReport, language: str) -> str:
    zh = language == "zh"
    lines = [
        ("以 `%s` 为基准，确定性计算得到：" if zh else "Using `%s` as the baseline, deterministic calculations show:")
        % report.plan.baseline
    ]
    for model_name, quantities in report.comparisons.items():
        for quantity, entry in quantities.items():
            summary = entry["summary"]
            evidence_key = "[%s:%s]" % (model_name, quantity)
            labels = {
                "zh": {
                    "bias": "平均偏差",
                    "mae": "MAE",
                    "rmse": "RMSE",
                    "max_abs_difference": "最大绝对差",
                    "mean_relative_difference_percent": "平均相对差(%)",
                    "mean_ratio": "平均比值",
                },
                "en": {
                    "bias": "bias",
                    "mae": "MAE",
                    "rmse": "RMSE",
                    "max_abs_difference": "maximum absolute difference",
                    "mean_relative_difference_percent": "mean relative difference (%)",
                    "mean_ratio": "mean ratio",
                },
            }[language]
            dimensionless = {"mean_relative_difference_percent", "mean_ratio"}
            metrics = ", ".join(
                "%s=%g%s" % (
                    labels[key],
                    value,
                    "" if key in dimensionless else " " + entry["unit"],
                )
                for key, value in summary.items()
            )
            if zh:
                lines.append("- `%s` 的 `%s`：%s。%s" % (model_name, quantity, metrics, evidence_key))
            else:
                lines.append("- `%s` `%s`: %s. %s" % (model_name, quantity, metrics, evidence_key))
    if report.warnings:
        lines.append("科学适用性提示：" if zh else "Scientific applicability notes:")
        lines.extend("- " + item for item in report.warnings)
    lines.append(
        "这些数值描述模型差异，不自动证明差异的物理成因。"
        if zh else
        "These values describe model differences; they do not by themselves establish physical causes."
    )
    return "\n".join(lines)
