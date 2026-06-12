"""Tests for the Xu-Li Neutral Sheet Model wrapper."""

from __future__ import annotations

import importlib
import math
import os
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import model as model_pkg


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------
class TestXuLiModule:
    """Verify module layout and lazy export registration."""

    def test_pyxuli_all_exports_model(self):
        pyxuli = importlib.import_module("model.pyxuli")
        assert pyxuli.__all__ == ["Model"]

    def test_xuli_in_model_all(self):
        assert "XuLi" in model_pkg.__all__


# ---------------------------------------------------------------------------
# Calculation tests (require compiled DLL)
# ---------------------------------------------------------------------------
@pytest.mark.requires_dll
class TestXuLiCalculation:
    """Functional tests using the compiled DLL."""

    def test_calculate_single_point_with_time(self, xuli_model):
        result = xuli_model.calculate(
            x_re=-10.0, y_re=0.0, doy=172.0, ut_hours=12.0
        )
        # All 10 keys present
        expected_keys = {
            "x_re", "y_re", "tilt_angle_deg",
            "zaen_re", "zsen_re", "zden_re",
            "rmp_re", "ie_aen", "ie_sen", "ie_den",
        }
        assert set(result.keys()) == expected_keys
        # Scalar input → scalar output
        for key in ("x_re", "y_re", "tilt_angle_deg",
                     "zaen_re", "zsen_re", "zden_re", "rmp_re"):
            assert isinstance(result[key], float), f"{key} should be float"
        for key in ("ie_aen", "ie_sen", "ie_den"):
            assert isinstance(result[key], int), f"{key} should be int"

    def test_finite_values_in_tail(self, xuli_model):
        result = xuli_model.calculate(
            x_re=-10.0, y_re=0.0, doy=172.0, ut_hours=12.0
        )
        for key in ("zaen_re", "zsen_re", "zden_re", "rmp_re", "tilt_angle_deg"):
            assert math.isfinite(result[key]), f"{key} is not finite: {result[key]}"

    def test_inside_magnetopause(self, xuli_model):
        result = xuli_model.calculate(
            x_re=-10.0, y_re=0.0, doy=172.0, ut_hours=12.0
        )
        assert result["ie_aen"] == 1
        assert result["ie_sen"] == 1

    def test_batch_shape(self, xuli_model):
        xs = [-5.0, -10.0, -20.0]
        ys = [0.0, 5.0, 10.0]
        result = xuli_model.calculate(
            x_re=xs, y_re=ys, doy=100.0, ut_hours=6.0
        )
        assert result["zaen_re"].shape == (3,)
        assert result["zsen_re"].shape == (3,)
        assert result["zden_re"].shape == (3,)
        assert result["rmp_re"].shape == (3,)
        assert result["tilt_angle_deg"].shape == (3,)

    def test_scalar_returns_scalar(self, xuli_model):
        result = xuli_model.calculate(
            x_re=-10.0, y_re=0.0, doy=172.0, ut_hours=12.0
        )
        assert isinstance(result["zaen_re"], float)
        assert isinstance(result["ie_aen"], int)

    def test_tilt_angle_direct(self, xuli_model):
        result = xuli_model.calculate(
            x_re=-10.0, y_re=0.0, tilt_angle_deg=15.0
        )
        assert result["tilt_angle_deg"] == 15.0
        assert math.isfinite(result["zaen_re"])

    def test_variants_differ(self, xuli_model):
        """At a typical tail position, the three variants give different Z."""
        result = xuli_model.calculate(
            x_re=-15.0, y_re=3.0, tilt_angle_deg=20.0
        )
        # At non-zero tilt and Y, the three models should differ
        assert result["zaen_re"] != result["zsen_re"]
        assert result["zsen_re"] != result["zden_re"]

    def test_broadcast_xy(self, xuli_model):
        """Broadcast x_re (3,) with y_re (1,) and tilt."""
        result = xuli_model.calculate(
            x_re=[-5.0, -10.0, -20.0],
            y_re=0.0,
            tilt_angle_deg=10.0,
        )
        assert result["zaen_re"].shape == (3,)
        assert result["x_re"][0] == -5.0
        assert result["x_re"][2] == -20.0

    def test_zero_tilt(self, xuli_model):
        """At zero tilt, all three Z positions should be zero."""
        result = xuli_model.calculate(
            x_re=-10.0, y_re=0.0, tilt_angle_deg=0.0
        )
        assert abs(result["zaen_re"]) < 1e-10
        assert abs(result["zsen_re"]) < 1e-10
        assert abs(result["zden_re"]) < 1e-10


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
class TestXuLiValidation:
    """Parameter validation tests (no DLL needed)."""

    def test_missing_tilt_and_time_with_dll(self, xuli_model):
        with pytest.raises(ValueError, match="tilt_angle_deg"):
            xuli_model.calculate(x_re=-10.0, y_re=0.0)


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------
class TestXuLiConstructor:
    """Constructor edge cases."""

    def test_bad_dll_path(self):
        from model.pyxuli import Model
        with pytest.raises((FileNotFoundError, OSError)):
            Model(dll_path="/nonexistent/path/libxuli.so")

    def test_calculate_from_non_repo_working_directory(
        self, xuli_model, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        result = xuli_model.calculate(
            x_re=-10.0, y_re=0.0, doy=100.0, ut_hours=6.0
        )
        assert "zaen_re" in result
