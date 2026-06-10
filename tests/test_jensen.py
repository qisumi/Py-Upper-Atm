"""Tests for Jensen & Cain (1962) geomagnetic field model."""

from __future__ import annotations

import math

import numpy as np
import pytest


class TestJensenModule:
    """Module structure tests (no DLL required)."""

    def test_all_exports(self):
        from model.pyjensen import __all__

        assert __all__ == ["Model"]

    def test_lazy_import(self):
        import model

        assert "JensenCain" in model.__all__


@pytest.mark.requires_dll
class TestJensenCalculation:
    """Single-point and batch calculation tests."""

    def test_single_point_returns_dict(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        assert isinstance(result, dict)

    def test_single_point_keys(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        expected_keys = {
            "year",
            "lat_deg",
            "lon_deg",
            "alt_km",
            "X_nT",
            "Y_nT",
            "Z_nT",
            "F_nT",
            "H_nT",
            "inclination_deg",
            "declination_deg",
        }
        assert set(result.keys()) == expected_keys

    def test_single_point_values_finite(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        for key, val in result.items():
            assert math.isfinite(val), f"{key} is not finite: {val}"

    def test_single_point_values_reasonable(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        # Total field should be in reasonable range (20000-70000 nT)
        assert 20000 < result["F_nT"] < 70000
        # Inclination should be between -90 and 90 degrees
        assert -90 <= result["inclination_deg"] <= 90
        # Declination should be between -180 and 180 degrees
        assert -180 <= result["declination_deg"] <= 180

    def test_single_point_not_nan(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        for key, val in result.items():
            assert not math.isnan(val), f"{key} is NaN: {val}"

    def test_batch_calculation_shape(self, jensen_model):
        # Avoid poles where FIELDG has singularity
        lats = np.array([10.0, 30.0, 60.0])
        lons = np.array([0.0, 120.0, 240.0])
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=lats,
            lon_deg=lons,
            alt_km=0.0,
        )
        assert result["X_nT"].shape == (3,)
        assert result["Y_nT"].shape == (3,)
        assert result["Z_nT"].shape == (3,)
        assert result["F_nT"].shape == (3,)

    def test_broadcast_shape(self, jensen_model):
        # Avoid poles where FIELDG has singularity
        lats = np.array([[10.0, 30.0], [60.0, 80.0]])
        lons = 0.0
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=lats,
            lon_deg=lons,
            alt_km=0.0,
        )
        assert result["F_nT"].shape == (2, 2)

    def test_scalar_input_returns_scalar(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        assert isinstance(result["X_nT"], float)
        assert isinstance(result["Y_nT"], float)
        assert isinstance(result["Z_nT"], float)
        assert isinstance(result["F_nT"], float)

    def test_array_input_returns_array(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=np.array([45.0, 60.0]),
            lon_deg=np.array([0.0, 120.0]),
            alt_km=0.0,
        )
        assert isinstance(result["X_nT"], np.ndarray)
        assert isinstance(result["F_nT"], np.ndarray)

    def test_nmx_parameter(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
            nmx=3,
        )
        assert isinstance(result, dict)
        assert math.isfinite(result["F_nT"])

    def test_invalid_nmx_raises(self, jensen_model):
        with pytest.raises(ValueError, match="nmx"):
            jensen_model.calculate(
                year=1960.0,
                lat_deg=45.0,
                lon_deg=0.0,
                alt_km=0.0,
                nmx=0,
            )
        with pytest.raises(ValueError, match="nmx"):
            jensen_model.calculate(
                year=1960.0,
                lat_deg=45.0,
                lon_deg=0.0,
                alt_km=0.0,
                nmx=7,
            )

    def test_different_altitudes(self, jensen_model):
        result0 = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        result100 = jensen_model.calculate(
            year=1960.0,
            lat_deg=45.0,
            lon_deg=0.0,
            alt_km=100.0,
        )
        # Field should decrease with altitude
        assert result100["F_nT"] < result0["F_nT"]

    def test_non_repo_working_directory(self, jensen_model, tmp_path):
        """Test that model works from a non-repo working directory."""
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = jensen_model.calculate(
                year=1960.0,
                lat_deg=45.0,
                lon_deg=0.0,
                alt_km=0.0,
            )
            assert math.isfinite(result["F_nT"])
        finally:
            os.chdir(old_cwd)


@pytest.mark.requires_dll
class TestJensenConstructor:
    """Constructor and error handling tests."""

    def test_lazy_export(self):
        import model

        assert hasattr(model, "JensenCain")

    def test_invalid_dll_path_raises(self):
        from model.pyjensen import Model

        with pytest.raises(Exception):
            Model(dll_path="/nonexistent/path.dll")

    def test_default_epoch(self, jensen_model):
        result = jensen_model.calculate(
            year=1960.0,
            lat_deg=0.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        assert result["year"] == 1960.0
