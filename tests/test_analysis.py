import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from upperatmpy_analysis import (
    AnalysisPlan,
    align_results,
    analyze_sensitivity,
    convert_values,
    execute_plan,
    expand_inputs,
    normalize_output,
)
from upperatmpy_analysis.cli import main
from upperatmpy_analysis.normalize import NormalizedResult


class FakeMSIS2:
    def __init__(self):
        self.kwargs = None

    def calculate(self, **kwargs):
        self.kwargs = kwargs
        alt = np.asarray(kwargs["alt_km"], dtype=float)
        shape = alt.shape
        densities = np.zeros(shape + (10,), dtype=float)
        densities[..., 0] = 2.0e10  # N2
        densities[..., 2] = 3.0e9   # O
        return {
            "alt_km": alt,
            "T_local_K": alt + 500.0,
            "T_exo_K": np.broadcast_to(900.0, shape),
            "densities": densities,
        }


class FakeMSIS00:
    def __init__(self):
        self.kwargs = None

    def calculate(self, **kwargs):
        self.kwargs = kwargs
        alt = np.asarray(kwargs["alt_km"], dtype=float)
        shape = alt.shape
        densities = np.zeros(shape + (9,), dtype=float)
        densities[..., 1] = 3.3e9  # O
        densities[..., 2] = 2.2e10  # N2
        densities[..., 5] = 1.2e-12  # g/cm3
        return {
            "alt_km": alt,
            "T_local_K": alt + 510.0,
            "T_exo_K": np.broadcast_to(930.0, shape),
            "densities": densities,
        }


class FakeMSIS86(FakeMSIS00):
    def calculate(self, **kwargs):
        result = super().calculate(**kwargs)
        result["densities"] = result["densities"][..., :8]
        return result


class FakeIGRF:
    def calculate(self, **kwargs):
        alt = np.asarray(kwargs["alt_km"], dtype=float)
        return {
            **kwargs,
            "B_north_nT": alt + 20000.0,
            "B_east_nT": alt * 0.0 + 100.0,
            "B_down_nT": alt + 30000.0,
            "B_abs_nT": alt + 40000.0,
            "H_nT": alt + 20010.0,
            "inclination_deg": alt * 0.0 + 50.0,
            "declination_deg": alt * 0.0 + 2.0,
        }


class FakeGSFC:
    def calculate(self, **kwargs):
        alt = np.asarray(kwargs["alt_km"], dtype=float)
        return {
            **kwargs,
            "X_nT": alt + 20100.0,
            "Y_nT": alt * 0.0 + 110.0,
            "Z_nT": alt + 30100.0,
            "F_nT": alt + 40100.0,
            "H_nT": alt + 20110.0,
            "inclination_deg": alt * 0.0 + 51.0,
            "declination_deg": alt * 0.0 + 3.0,
        }


def neutral_plan(**changes):
    value = {
        "models": ["MSIS2", "MSIS00"],
        "inputs": {
            "year": 2020,
            "day_of_year": 172,
            "utsec": 43200.0,
            "alt_km": {"start": 100.0, "stop": 120.0, "step": 10.0, "num": None},
            "lat_deg": 0.0,
            "lon_deg": 0.0,
            "f107a": 150.0,
            "f107": 150.0,
        },
        "quantities": ["T_local_K", "O_cm3"],
        "baseline": "MSIS2",
        "language": "zh",
    }
    value.update(changes)
    return AnalysisPlan.from_dict(value)


def test_expand_inputs_inclusive_step_and_num():
    step = expand_inputs({"alt_km": {"start": 100, "stop": 125, "step": 10, "num": None}})
    num = expand_inputs({"alt_km": {"start": 100, "stop": 120, "step": None, "num": 3}})
    assert step["alt_km"].tolist() == [100.0, 110.0, 120.0, 125.0]
    assert num["alt_km"].tolist() == [100.0, 110.0, 120.0]


def test_canonical_unit_conversion_is_explicit_and_finite():
    assert convert_values(1.0e-12, "g/cm^3", "kg/m^3") == pytest.approx(1.0e-9)
    assert convert_values([1.0e6, 2.0e6], "m^-3", "cm^-3").tolist() == [1.0, 2.0]
    with pytest.raises(ValueError, match="unsupported conversion"):
        convert_values(1.0, "K", "nT")


def test_analysis_plan_rejects_unknown_fields_and_models():
    with pytest.raises(ValueError, match="未知字段"):
        AnalysisPlan.from_dict({"models": ["MSIS2", "MSIS00"], "inputs": {"x": 1}, "extra": True})
    with pytest.raises(ValueError, match="目录"):
        execute_plan(
            AnalysisPlan(models=["MSIS2", "NoSuch"], inputs={"x": 1}),
            model_instances={},
        )


def test_execute_plan_normalizes_and_compares_msis_family():
    msis2 = FakeMSIS2()
    msis00 = FakeMSIS00()
    report = execute_plan(
        neutral_plan(),
        model_instances={"MSIS2": msis2, "MSIS00": msis00},
    )

    assert msis2.kwargs["day"] == 172
    assert np.asarray(msis00.kwargs["iyd"]).item() == 2020172
    assert np.asarray(msis00.kwargs["stl_hours"]).item() == 12.0
    assert report.outputs["MSIS00"].quantities["total_mass_density_kg_m3"].tolist() == pytest.approx([1.2e-9] * 3)
    assert report.comparisons["MSIS00"]["T_local_K"]["summary"]["mae"] == pytest.approx(10.0)
    assert report.comparisons["MSIS00"]["O_cm3"]["summary"]["mean_ratio"] == pytest.approx(1.1)
    payload = json.loads(report.to_json())
    assert payload["provenance"]["ai_used_for_calculation"] is False
    assert "可复现代码" in report.to_markdown()
    compile(report.reproducible_code(), "<report>", "exec")


def test_execute_plan_normalizes_geomagnetic_axes():
    plan = AnalysisPlan(
        models=["IGRF", "GSFC"],
        inputs={"year": 1987.0, "lat_deg": 20.0, "lon_deg": 30.0, "alt_km": [0.0, 100.0]},
        quantities=["B_north_nT", "B_abs_nT"],
        baseline="IGRF",
        language="en",
    )
    report = execute_plan(plan, model_instances={"IGRF": FakeIGRF(), "GSFC": FakeGSFC()})
    assert report.outputs["GSFC"].quantities["B_north_nT"].tolist() == [20100.0, 20200.0]
    assert report.comparisons["GSFC"]["B_abs_nT"]["summary"]["bias"] == pytest.approx(100.0)


def test_validity_intersection_is_enforced():
    plan = neutral_plan(models=["MSIS2", "MSIS86"])
    plan.inputs["alt_km"] = 80.0
    with pytest.raises(ValueError, match="共同有效域"):
        execute_plan(plan, model_instances={"MSIS2": FakeMSIS2(), "MSIS86": FakeMSIS86()})


def test_align_results_uses_exact_intersection_only():
    first = NormalizedResult("a", "g", {"alt_km": np.array([1.0, 2.0, 3.0])}, {"q": np.array([10, 20, 30])}, {"q": "u"})
    second = NormalizedResult("b", "g", {"alt_km": np.array([2.0, 3.0, 4.0])}, {"q": np.array([200, 300, 400])}, {"q": "u"})
    aligned = align_results([first, second])
    assert aligned[0].coordinates["alt_km"].tolist() == [2.0, 3.0]
    assert aligned[0].quantities["q"].tolist() == [20, 30]
    assert aligned[1].quantities["q"].tolist() == [200, 300]


def test_sensitivity_analysis_uses_only_varied_parameter():
    report = analyze_sensitivity(
        "MSIS2",
        base_inputs={
            "year": 2020,
            "day_of_year": 172,
            "utsec": 43200,
            "alt_km": 100,
            "lat_deg": 0,
            "lon_deg": 0,
            "f107a": 150,
            "f107": 150,
        },
        parameter="alt_km",
        values=[100, 110, 120],
        quantities=["T_local_K"],
        model_instance=FakeMSIS2(),
    )
    assert report.quantities["T_local_K"].tolist() == [600.0, 610.0, 620.0]
    assert report.summary["T_local_K"]["endpoint_change_percent"] == pytest.approx(20 / 600 * 100)


def test_cli_catalog(capsys):
    assert main(["catalog", "--language", "en"]) == 0
    output = capsys.readouterr().out
    assert "MSIS2" in output
    assert "geomagnetic_internal" in output


def test_analysis_import_is_lazy_for_models_and_ai_sdk():
    source = Path(__file__).resolve().parents[1] / "src"
    code = (
        "import sys; sys.path.insert(0, %r); import upperatmpy_analysis; "
        "assert 'model' not in sys.modules; assert 'openai' not in sys.modules"
    ) % str(source)
    completed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr


@pytest.mark.requires_dll
def test_real_msis_comparison_smoke_is_finite():
    try:
        report = execute_plan(neutral_plan())
    except (OSError, RuntimeError, FileNotFoundError) as exc:
        pytest.skip("native MSIS libraries or data unavailable: %s" % exc)
    summary = report.comparisons["MSIS00"]["T_local_K"]["summary"]
    assert all(np.isfinite(value) for value in summary.values())
