import json
from pathlib import Path

import numpy as np
import pytest

from upperatmpy_analysis import AnalysisPlan, execute_plan
from upperatmpy_analysis.ai import OpenAIProvider, explain_report, plan_from_text
from upperatmpy_analysis.schema import analysis_plan_json_schema


class FakeMSIS2:
    def calculate(self, **kwargs):
        alt = np.asarray(kwargs["alt_km"], dtype=float)
        densities = np.ones(alt.shape + (10,), dtype=float)
        return {"alt_km": alt, "T_local_K": alt + 500, "T_exo_K": alt * 0 + 900, "densities": densities}


class FakeMSIS00:
    def calculate(self, **kwargs):
        alt = np.asarray(kwargs["alt_km"], dtype=float)
        densities = np.ones(alt.shape + (9,), dtype=float)
        return {"alt_km": alt, "T_local_K": alt + 510, "T_exo_K": alt * 0 + 930, "densities": densities}


def neutral_plan():
    return AnalysisPlan(
        models=["MSIS2", "MSIS00"],
        inputs={
            "year": 2020,
            "day_of_year": 172,
            "utsec": 43200,
            "alt_km": [100, 110],
            "lat_deg": 0,
            "lon_deg": 0,
            "f107a": 150,
            "f107": 150,
        },
        quantities=["T_local_K"],
        baseline="MSIS2",
    )


def test_rule_planner_parses_bilingual_scientific_inputs():
    plan = plan_from_text(
        "比较 MSIS2 和 MSIS00：年份 2020，第 172 天，12:00 UT，"
        "高度 100 到 120 km，步长 10 km，纬度 0，经度 0，"
        "F10.7a=150，F10.7=150，比较局地温度。"
    )
    assert plan.models == ["MSIS2", "MSIS00"]
    assert plan.language == "zh"
    assert plan.inputs["utsec"] == 43200
    assert plan.inputs["alt_km"]["step"] == 10.0
    assert plan.quantities == ["T_local_K"]


def test_cli_plan_emits_strict_json(capsys):
    from upperatmpy_analysis.cli import main

    query = (
        "Compare IGRF and GSFC in year 1987 at altitude 100 km, "
        "latitude 20, longitude 30, total magnetic field."
    )
    assert main(["plan", "--query", query, "--language", "en"]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["models"] == ["IGRF", "GSFC"]
    assert value["quantities"] == ["B_abs_nT"]


def test_rule_planner_refuses_missing_inputs_instead_of_guessing():
    with pytest.raises(ValueError, match="缺少输入"):
        plan_from_text("Compare MSIS2 and MSIS00 local temperature from 100 to 200 km.")


class _Response:
    def __init__(self, output_text):
        self.output_text = output_text


class _Responses:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _Response(self.payload)


class _Client:
    def __init__(self, payload):
        self.responses = _Responses(payload)


def test_openai_provider_uses_strict_responses_schema_without_sdk_import():
    payload = json.dumps(neutral_plan().to_dict(), ensure_ascii=False)
    client = _Client(payload)
    provider = OpenAIProvider(model="test-model", client=client)
    result = provider.generate_json(
        system_prompt="system",
        user_prompt="user",
        schema=analysis_plan_json_schema(),
        schema_name="plan",
    )
    assert result["models"] == ["MSIS2", "MSIS00"]
    call = client.responses.calls[0]
    assert call["text"]["format"]["type"] == "json_schema"
    assert call["text"]["format"]["strict"] is True
    assert call["store"] is False


def test_ai_json_schema_closes_every_object_and_null_inputs_are_removed():
    schema = analysis_plan_json_schema()
    assert schema["additionalProperties"] is False
    inputs = schema["properties"]["inputs"]
    assert inputs["additionalProperties"] is False
    grid = inputs["properties"]["alt_km"]["anyOf"][2]
    assert grid["additionalProperties"] is False
    payload = neutral_plan().to_dict()
    payload["inputs"]["local_time_hours"] = None
    payload["inputs"]["ap7"] = None
    assert "local_time_hours" not in AnalysisPlan.from_dict(payload).inputs


class _TextProvider:
    def __init__(self):
        self.prompt = ""

    def generate_text(self, *, system_prompt, user_prompt):
        self.prompt = user_prompt
        return "grounded"


def test_explainer_receives_compact_evidence_not_raw_model_execution():
    report = execute_plan(
        neutral_plan(),
        model_instances={"MSIS2": FakeMSIS2(), "MSIS00": FakeMSIS00()},
    )
    provider = _TextProvider()
    assert explain_report(report, provider=provider) == "grounded"
    evidence = json.loads(provider.prompt)
    assert "MSIS00:T_local_K" in evidence["evidence"]
    assert "outputs" not in evidence


def test_deterministic_explainer_has_evidence_keys_and_caveat():
    report = execute_plan(
        neutral_plan(),
        model_instances={"MSIS2": FakeMSIS2(), "MSIS00": FakeMSIS00()},
    )
    text = explain_report(report)
    assert "[MSIS00:T_local_K]" in text
    assert "不自动证明" in text


def test_publishable_skill_is_repo_contained_and_bilingual():
    root = Path(__file__).resolve().parents[1]
    skill = root / "skills" / "upperatmpy-atmospheric-analysis"
    content = (skill / "SKILL.md").read_text(encoding="utf-8")
    metadata = (skill / "agents" / "openai.yaml").read_text(encoding="utf-8")
    workflows = (skill / "references" / "analysis-workflows.md").read_text(encoding="utf-8")
    release = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "name: upperatmpy-atmospheric-analysis" in content
    assert "Chinese/English" in content
    assert "$upperatmpy-atmospheric-analysis" in metadata
    assert "分析工作流" in workflows and "Strict" in workflows
    assert "Package publishable atmospheric analysis Skill" in release
    assert 'f"{skill_name}-{tag}.zip"' in release
