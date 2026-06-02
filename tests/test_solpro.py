"""Tests for the SOLPRO solar proton fluence model."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestModuleExports:
    def test_submodule_all(self):
        from model.pysolpro import __all__ as exports

        assert exports == ["Model"]

    def test_submodule_exports_model_class(self):
        from model.pysolpro import Model

        assert callable(Model)

    @pytest.mark.requires_dll
    def test_lazy_export(self):
        from model import SOLPRO

        assert callable(SOLPRO)


class TestConstructor:
    @pytest.mark.requires_dll
    def test_default_construction(self):
        from model import SOLPRO

        m = SOLPRO()
        assert m is not None

    @pytest.mark.requires_dll
    def test_non_repo_working_directory(self, monkeypatch, tmp_path):
        from model import SOLPRO

        monkeypatch.chdir(tmp_path)
        m = SOLPRO()
        assert m is not None


class TestCalculate:
    @pytest.mark.requires_dll
    def test_single_point_al_event(self, solpro_model):
        """AL-event conditions: 12 months at 90% confidence."""
        result = solpro_model.calculate(duration_months=12, confidence_pct=90)

        assert isinstance(result["duration_months"], float)
        assert result["duration_months"] == 12.0
        assert isinstance(result["confidence_pct"], int)
        assert result["confidence_pct"] == 90
        assert isinstance(result["fluence_cm2"], np.ndarray)
        assert result["fluence_cm2"].shape == (10,)
        assert all(result["fluence_cm2"] > 0)
        assert isinstance(result["n_al_events"], int)
        assert result["n_al_events"] > 0

    @pytest.mark.requires_dll
    def test_single_point_or_event(self, solpro_model):
        """OR-event conditions: short mission with high confidence."""
        # Use parameters that produce no AL events
        result = solpro_model.calculate(duration_months=3, confidence_pct=90)

        assert isinstance(result["fluence_cm2"], np.ndarray)
        assert result["fluence_cm2"].shape == (10,)
        # Fluence should be non-negative (could be zero for edge cases)
        assert all(result["fluence_cm2"] >= 0)

    @pytest.mark.requires_dll
    def test_batch_calculation(self, solpro_model):
        """Batch: array duration, scalar confidence."""
        durs = np.array([3.0, 6.0, 12.0, 24.0])
        result = solpro_model.calculate(duration_months=durs, confidence_pct=90)

        assert result["fluence_cm2"].shape == (4, 10)
        assert result["n_al_events"].shape == (4,)
        np.testing.assert_array_equal(result["duration_months"], durs)

    @pytest.mark.requires_dll
    def test_batch_both_array(self, solpro_model):
        """Batch: both inputs as arrays."""
        durs = np.array([6.0, 12.0, 24.0])
        confs = np.array([80, 90, 95])
        result = solpro_model.calculate(duration_months=durs, confidence_pct=confs)

        assert result["fluence_cm2"].shape == (3, 10)
        assert result["n_al_events"].shape == (3,)

    @pytest.mark.requires_dll
    def test_fluence_monotone_decrease(self, solpro_model):
        """Fluence should decrease with increasing energy threshold."""
        result = solpro_model.calculate(duration_months=12, confidence_pct=90)
        fluence = result["fluence_cm2"]
        for i in range(9):
            assert fluence[i] >= fluence[i + 1], (
                f"Fluence not monotone at index {i}: {fluence[i]} < {fluence[i + 1]}"
            )

    @pytest.mark.requires_dll
    def test_longer_duration_higher_fluence(self, solpro_model):
        """Longer missions should have higher fluence."""
        r1 = solpro_model.calculate(duration_months=6, confidence_pct=90)
        r2 = solpro_model.calculate(duration_months=24, confidence_pct=90)
        assert r2["fluence_cm2"][0] > r1["fluence_cm2"][0]

    @pytest.mark.requires_dll
    def test_higher_confidence_higher_fluence(self, solpro_model):
        """Higher confidence level should have higher fluence (OR-event regime)."""
        # Use 3 months where both 80% and 90% produce OR-event (n_al_events=0)
        r1 = solpro_model.calculate(duration_months=3, confidence_pct=80)
        r2 = solpro_model.calculate(duration_months=3, confidence_pct=90)
        assert r2["fluence_cm2"][0] > r1["fluence_cm2"][0]


class TestValidation:
    def test_duration_too_large(self, solpro_model):
        with pytest.raises(ValueError, match="duration_months"):
            solpro_model.calculate(duration_months=100, confidence_pct=90)

    def test_duration_zero(self, solpro_model):
        with pytest.raises(ValueError, match="duration_months"):
            solpro_model.calculate(duration_months=0, confidence_pct=90)

    def test_confidence_too_low(self, solpro_model):
        with pytest.raises(ValueError, match="confidence_pct"):
            solpro_model.calculate(duration_months=12, confidence_pct=50)

    def test_confidence_too_high(self, solpro_model):
        with pytest.raises(ValueError, match="confidence_pct"):
            solpro_model.calculate(duration_months=12, confidence_pct=100)
