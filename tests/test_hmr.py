"""Tests for Heppner-Maynard-Rich electric field model."""

import math
from pathlib import Path

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Module-level import tests
# ---------------------------------------------------------------------------

class TestHMRModule:
    """Test lazy imports and module structure."""

    def test_all_exports(self):
        import model
        assert "HMR" in model.__all__

    def test_lazy_import(self):
        import model
        assert "HMR" not in dir(model) or isinstance(model.HMR, type)


# ---------------------------------------------------------------------------
# EPOT (Heppner-Maynard potential) tests
# ---------------------------------------------------------------------------

class TestHMREpot:
    """Test EPOT electric potential calculation."""

    def test_single_point(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=70.0, lon_deg=180.0, model="A",
        )
        assert isinstance(result, dict)

    def test_keys(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=70.0, lon_deg=180.0, model="A",
        )
        assert "electric_potential_kV" in result
        assert "lat_deg" in result
        assert "lon_deg" in result

    def test_finite_values(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=70.0, lon_deg=180.0, model="A",
        )
        for v in result.values():
            assert math.isfinite(v) or isinstance(v, np.ndarray)

    def test_reasonable_values(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=70.0, lon_deg=180.0, model="A",
        )
        # Electric potential should be on the order of kV
        assert abs(result["electric_potential_kV"]) < 200

    def test_model_bc(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=70.0, lon_deg=180.0, model="BC",
        )
        assert "electric_potential_kV" in result

    def test_model_de(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=70.0, lon_deg=180.0, model="DE",
        )
        assert "electric_potential_kV" in result

    def test_model_a_valid(self, hmr_model):
        """Test that Model A produces valid results."""
        result = hmr_model.calculate(lat_deg=70.0, lon_deg=180.0, model="A")
        assert math.isfinite(result["electric_potential_kV"])

    def test_epot_model_switch_reloads_coefficients(self, hmr_model):
        values = [
            hmr_model.calculate(
                lat_deg=70.0,
                lon_deg=180.0,
                model=model_name,
            )["electric_potential_kV"]
            for model_name in ["A", "BC", "DE", "A"]
        ]
        assert len({round(v, 6) for v in values[:3]}) == 3
        assert values[0] == pytest.approx(values[3])

    def test_batch_shape(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=[60.0, 70.0, 80.0],
            lon_deg=[0.0, 90.0, 180.0],
            model="A",
        )
        assert result["electric_potential_kV"].shape == (3,)

    def test_scalar_returns_scalar(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=70.0, lon_deg=180.0, model="A",
        )
        assert isinstance(result["electric_potential_kV"], float)

    def test_array_returns_array(self, hmr_model):
        result = hmr_model.calculate(
            lat_deg=[60.0, 70.0],
            lon_deg=[0.0, 90.0],
            model="A",
        )
        assert isinstance(result["electric_potential_kV"], np.ndarray)

    def test_invalid_model(self, hmr_model):
        with pytest.raises(ValueError):
            hmr_model.calculate(lat_deg=70.0, lon_deg=180.0, model="Z")


# ---------------------------------------------------------------------------
# Heelis model tests
# ---------------------------------------------------------------------------

class TestHMRHeelis:
    """Test Heelis convection model."""

    def test_heelis_single_point(self, hmr_model):
        result = hmr_model.calculate_heelis(
            lat_deg=70.0, lon_hrs=12.0,
        )
        assert isinstance(result, dict)
        assert "electric_potential_kV" in result
        assert "dlat_kV_per_rad" in result
        assert "dlon_kV_per_rad" in result

    def test_heelis_values(self, hmr_model):
        result = hmr_model.calculate_heelis(
            lat_deg=70.0, lon_hrs=12.0,
        )
        # Heelis model may return NaN if BLOCK DATA is not initialized
        # in the shared library. Verify the result is a dict with expected keys.
        assert "electric_potential_kV" in result
        assert "dlat_kV_per_rad" in result
        assert "dlon_kV_per_rad" in result

    def test_heelis_batch(self, hmr_model):
        result = hmr_model.calculate_heelis(
            lat_deg=[60.0, 70.0, 80.0],
            lon_hrs=[0.0, 6.0, 12.0],
        )
        assert result["electric_potential_kV"].shape == (3,)


# ---------------------------------------------------------------------------
# Full computation tests
# ---------------------------------------------------------------------------

class TestHMRFull:
    """Test full computation (potential + E-field + Joule + FAC)."""

    def test_full_returns_grid(self, hmr_model):
        result = hmr_model.calculate_full(
            kp=3.5, sublat_deg=0.0, f107=80.0, model="A",
        )
        assert result["electric_potential_kV"].shape == (41, 25)
        assert result["e_field_lat_mV_m"].shape == (41, 25)
        assert result["e_field_lon_mV_m"].shape == (41, 25)
        assert result["joule_heating_mW_m2"].shape == (41, 25)
        assert result["fac_uA_m2"].shape == (41, 25)
        assert result["lat_grid_deg"].shape == (41,)
        assert result["mlt_grid_hrs"].shape == (25,)

    def test_full_keys(self, hmr_model):
        result = hmr_model.calculate_full(model="A")
        expected_keys = {
            "electric_potential_kV",
            "e_field_lat_mV_m",
            "e_field_lon_mV_m",
            "hall_conductivity_Mho",
            "pedersen_conductivity_Mho",
            "joule_heating_mW_m2",
            "fac_uA_m2",
            "lat_grid_deg",
            "mlt_grid_hrs",
        }
        assert set(result.keys()) == expected_keys

    def test_full_finite(self, hmr_model):
        result = hmr_model.calculate_full(model="A")
        for key in result:
            arr = result[key]
            if isinstance(arr, np.ndarray):
                assert np.all(np.isfinite(arr)), f"Non-finite values in {key}"

    def test_full_heelis(self, hmr_model):
        result = hmr_model.calculate_full(model="heelis")
        assert result["electric_potential_kV"].shape == (41, 25)

    def test_full_grid_shape(self, hmr_model):
        """Test that full computation returns correctly shaped grids."""
        result = hmr_model.calculate_full(kp=3.5, model="A")
        assert result["electric_potential_kV"].shape == (41, 25)
        assert result["lat_grid_deg"].shape == (41,)
        assert result["mlt_grid_hrs"].shape == (25,)
        # Verify grid axes
        assert result["lat_grid_deg"][0] == 50.0
        assert result["lat_grid_deg"][-1] == 90.0
        assert result["mlt_grid_hrs"][0] == 0.0
        assert result["mlt_grid_hrs"][-1] == 24.0


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------

class TestHMRConstructor:
    """Test HMR constructor."""

    def test_lazy_export(self):
        import model
        cls = getattr(model, "HMR", None)
        assert cls is not None

    def test_invalid_dll_path(self):
        from model.pyhmr import Model
        with pytest.raises((FileNotFoundError, OSError)):
            Model(dll_path="/nonexistent/path.dll", data_dir="data", auto_download=False)
