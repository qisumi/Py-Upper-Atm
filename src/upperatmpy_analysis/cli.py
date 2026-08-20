"""Command-line interface for reproducible atmospheric analyses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from .ai import OpenAIProvider, explain_report, plan_from_text
from .catalog import GROUP_DEFAULT_QUANTITIES, catalog_dict, list_models
from .compare import execute_plan
from .schema import AnalysisPlan
from .sensitivity import analyze_sensitivity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="upperatmpy-analysis",
        description="UpperAtmPy bilingual deterministic analysis / 双语确定性大气分析",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    catalog = subparsers.add_parser("catalog", help="List safe comparison groups / 列出可比较模型")
    catalog.add_argument("--language", choices=("zh", "en"), default="zh")
    catalog.add_argument("--format", choices=("markdown", "json"), default="markdown")

    compare = subparsers.add_parser("compare", help="Execute a strict JSON plan / 执行严格计划")
    compare.add_argument("--plan", required=True, help="Plan JSON path, JSON text, or - for stdin")
    compare.add_argument("--model-options", help="Optional constructor options JSON path or text")
    _add_output_options(compare)

    sensitivity = subparsers.add_parser("sensitivity", help="One-factor sensitivity / 单因素敏感性")
    sensitivity.add_argument("--model", required=True)
    sensitivity.add_argument("--base-inputs", required=True, help="JSON path or JSON object")
    sensitivity.add_argument("--parameter", required=True)
    sensitivity.add_argument("--values", required=True, help="JSON list/grid object or comma-separated values")
    sensitivity.add_argument("--quantities", help="Comma-separated canonical quantities")
    sensitivity.add_argument("--model-options", help="Optional constructor options JSON path or text")
    sensitivity.add_argument("--language", choices=("zh", "en"), default="zh")
    _add_output_options(sensitivity)

    plan_parser = subparsers.add_parser("plan", help="Natural language to AnalysisPlan / 自然语言生成计划")
    plan_parser.add_argument("--query", required=True)
    _add_ai_options(plan_parser)
    plan_parser.add_argument("--output-file")

    ask = subparsers.add_parser("ask", help="Plan, calculate, and explain / 规划、计算并解释")
    ask.add_argument("--query", required=True)
    ask.add_argument("--model-options", help="Optional constructor options JSON path or text")
    _add_ai_options(ask)
    _add_output_options(ask, formats=("markdown", "json"))
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "catalog":
            output = _catalog_output(args.language, args.format)
        elif args.command == "compare":
            plan = AnalysisPlan.from_dict(_read_json(args.plan))
            report = execute_plan(
                plan,
                model_options=_optional_json(args.model_options),
            )
            output = report.to_json() if args.format == "json" else report.to_markdown()
        elif args.command == "sensitivity":
            report = analyze_sensitivity(
                args.model,
                base_inputs=_read_json(args.base_inputs),
                parameter=args.parameter,
                values=_parse_values(args.values),
                quantities=args.quantities.split(",") if args.quantities else None,
                language=args.language,
                model_options=_optional_json(args.model_options),
            )
            output = report.to_json() if args.format == "json" else report.to_markdown()
        elif args.command == "plan":
            provider = _provider(args)
            plan = plan_from_text(args.query, language=args.language, provider=provider)
            output = json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)
        elif args.command == "ask":
            provider = _provider(args)
            plan = plan_from_text(args.query, language=args.language, provider=provider)
            report = execute_plan(plan, model_options=_optional_json(args.model_options))
            if args.format == "json":
                value = report.to_dict()
                value["explanation"] = explain_report(report, provider=provider)
                output = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
            else:
                output = report.to_markdown() + "\n" + (
                    "## 智能解读\n\n" if plan.language == "zh" else "## Intelligent interpretation\n\n"
                ) + explain_report(report, provider=provider) + "\n"
        else:
            parser.error("unknown command")
            return 2
    except (ValueError, ImportError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        parser.exit(2, "upperatmpy-analysis: error: %s\n" % exc)
        return 2

    output_file = getattr(args, "output_file", None)
    if output_file:
        Path(output_file).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


def _add_output_options(parser: argparse.ArgumentParser, formats: Any = ("markdown", "json")) -> None:
    parser.add_argument("--format", choices=formats, default=formats[0])
    parser.add_argument("--output-file")


def _add_ai_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", choices=("rule", "openai"), default="rule")
    parser.add_argument("--ai-model", help="Required only for --provider openai")
    parser.add_argument("--language", choices=("auto", "zh", "en"), default="auto")


def _provider(args: argparse.Namespace) -> Any:
    if args.provider == "rule":
        return None
    if not args.ai_model:
        raise ValueError("--provider openai 需要 --ai-model")
    return OpenAIProvider(model=args.ai_model)


def _read_json(value: str) -> Dict[str, Any]:
    if value == "-":
        parsed = json.load(sys.stdin)
    else:
        path = Path(value)
        if path.is_file():
            parsed = json.loads(path.read_text(encoding="utf-8"))
        else:
            parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("JSON 顶层必须为对象 / top-level JSON must be an object")
    return parsed


def _optional_json(value: Optional[str]) -> Optional[Dict[str, Any]]:
    return _read_json(value) if value else None


def _parse_values(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        try:
            return [float(item.strip()) for item in value.split(",")]
        except ValueError:
            raise ValueError("--values 必须是 JSON 或逗号分隔数字")


def _catalog_output(language: str, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(catalog_dict(language), ensure_ascii=False, indent=2)
    zh = language == "zh"
    lines = ["# UpperAtmPy " + ("可比较模型目录" if zh else "comparison catalog"), ""]
    groups = sorted({item.group for item in list_models()})
    for group in groups:
        lines.extend(["## `%s`" % group, ""])
        for spec in list_models(group):
            lines.append("- `%s` — %s" % (spec.name, spec.description(language)))
        lines.append("")
        lines.append(
            ("默认比较量：" if zh else "Default quantities: ")
            + ", ".join("`%s`" % item for item in GROUP_DEFAULT_QUANTITIES[group])
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
