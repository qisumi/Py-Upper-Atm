"""Tests for SOFIP (Short Orbital Flux Integration Program) model wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ---------------------------------------------------------------------------
# Helper: generate a simple circular-orbit trajectory
# ---------------------------------------------------------------------------
def _make_orbit(altitude_km=500.0, inclination_deg=51.6, n_points=100, n_orbits=3.0):
    """生成简单圆轨道的 (times, b_field, l_shell) 数组。"""
    R_E = 6371.0
    r = R_E + altitude_km
    L = r / R_E

    mu = 398600.4418  # km³/s²
    period_s = 2 * np.pi * np.sqrt(r**3 / mu)
    period_h = period_s / 3600.0

    total_time = n_orbits * period_h
    times = np.linspace(0, total_time, n_points, dtype=np.float32)

    lat = inclination_deg * np.sin(2 * np.pi * times / period_h)
    lat_rad = np.radians(lat)

    l_shell = np.full(n_points, L, dtype=np.float32)
    B0 = 0.311653
    b_field = ((B0 / L**3) * np.sqrt(1 + 3 * np.sin(lat_rad)**2)).astype(np.float32)

    return times, b_field, l_shell, period_h


# ---------------------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------------------
class TestModuleExports:
    """Verify __all__ and lazy-loading."""

    def test_all_contains_only_model(self):
        from model import pysofip

        assert pysofip.__all__ == ["Model"]

    def test_lazy_export_sofip(self):
        import model

        assert "SOFIP" in model.__all__

    def test_import_from_model(self):
        from model import SOFIP

        assert SOFIP is not None


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------
class TestConstructor:
    """Test Model construction and parameter validation."""

    def test_invalid_model_type(self):
        from model import SOFIP

        with pytest.raises(ValueError, match="model_type"):
            SOFIP("INVALID", data_dir=ROOT / "data", auto_download=False)

    def test_valid_model_types(self):
        """All four standard model types should be accepted at init level."""
        from model import SOFIP

        for mt in ("AP8MAX", "AP8MIN", "AE8MAX", "AE8MIN"):
            # This will raise FileNotFoundError since we don't check DLL,
            # but the ValueError for model_type should NOT be raised.
            try:
                SOFIP(mt, data_dir=ROOT / "data", auto_download=False)
            except (FileNotFoundError, OSError):
                pass  # Expected if DLL or data missing
            except ValueError:
                pytest.fail(f"model_type={mt!r} should be valid")


# ---------------------------------------------------------------------------
# Calculation tests (require DLL)
# ---------------------------------------------------------------------------
@pytest.mark.requires_dll
class TestSOFIPAP8MAX:
    """Test SOFIP with AP8MAX (protons, solar maximum)."""

    def test_single_orbit_result_keys(self, sofip_ap8max_model):
        times, b, l, _ = _make_orbit(altitude_km=500.0, n_points=50, n_orbits=1.0)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        expected_keys = {
            "energy_levels", "integral_flux", "differential_flux",
            "difference_flux", "solar_proton_energy", "solar_proton_fluence",
            "n_al_events", "exposure_factor", "lzone_counts",
            "total_time_hours", "time_step_minutes",
        }
        assert set(result.keys()) == expected_keys

    def test_output_shapes(self, sofip_ap8max_model):
        times, b, l, _ = _make_orbit(altitude_km=500.0, n_points=50)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        assert result["energy_levels"].shape == (30,)
        assert result["integral_flux"].shape == (30,)
        assert result["differential_flux"].shape == (30,)
        assert result["difference_flux"].shape == (30,)
        assert result["solar_proton_energy"].shape == (20,)
        assert result["solar_proton_fluence"].shape == (20,)
        assert result["lzone_counts"].shape == (4,)

    def test_output_types(self, sofip_ap8max_model):
        times, b, l, _ = _make_orbit(altitude_km=500.0, n_points=50)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        assert isinstance(result["total_time_hours"], float)
        assert isinstance(result["time_step_minutes"], float)
        assert isinstance(result["n_al_events"], int)
        assert isinstance(result["exposure_factor"], float)

    def test_total_time_positive(self, sofip_ap8max_model):
        times, b, l, period = _make_orbit(altitude_km=500.0, n_points=100)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        assert result["total_time_hours"] > 0
        assert result["time_step_minutes"] > 0

    def test_energy_levels_are_proton(self, sofip_ap8max_model):
        """AP8MAX should use proton energy levels (2–500 MeV)."""
        times, b, l, _ = _make_orbit(altitude_km=500.0, n_points=50)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        energies = result["energy_levels"]
        assert energies[0] == pytest.approx(2.0)
        assert energies[-1] == pytest.approx(500.0)
        assert np.all(np.diff(energies) > 0)  # monotonically increasing

    def test_flux_non_negative(self, sofip_ap8max_model):
        times, b, l, _ = _make_orbit(altitude_km=500.0, n_points=50)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        assert np.all(result["integral_flux"] >= 0)

    def test_lzone_counts_sum_to_npoints(self, sofip_ap8max_model):
        """L-zone counts should sum to the number of trajectory points."""
        n = 100
        times, b, l, _ = _make_orbit(altitude_km=500.0, n_points=n)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        assert result["lzone_counts"].sum() == n

    def test_low_orbit_no_proton_flux(self, sofip_ap8max_model):
        """500 km orbit at L≈1.08 is below the inner proton belt — zero flux."""
        times, b, l, _ = _make_orbit(altitude_km=500.0, n_points=100)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        # Below the proton belt, integral flux should be zero everywhere
        assert np.all(result["integral_flux"] == 0.0)

    def test_high_orbit_has_proton_flux(self, sofip_ap8max_model):
        """1000 km orbit at L≈1.16 penetrates the inner proton belt."""
        times, b, l, _ = _make_orbit(altitude_km=1000.0, n_points=100)
        result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)

        # At least some energy levels should have nonzero flux
        assert np.any(result["integral_flux"] > 0)


@pytest.mark.requires_dll
class TestSOFIPAE8MIN:
    """Test SOFIP with AE8MIN (electrons, solar minimum)."""

    def test_electron_energy_levels(self, sofip_ae8min_model):
        """AE8MIN should use electron energy levels (0.1–7.0 MeV)."""
        times, b, l, _ = _make_orbit(altitude_km=2000.0, n_points=50)
        result = sofip_ae8min_model.calculate(times=times, b_field=b, l_shell=l)

        energies = result["energy_levels"]
        assert energies[0] == pytest.approx(0.1)
        assert energies[-1] == pytest.approx(7.0)
        assert np.all(np.diff(energies) > 0)

    def test_high_orbit_flux(self, sofip_ae8min_model):
        """2000 km orbit at L≈1.31 should have electron flux."""
        times, b, l, _ = _make_orbit(altitude_km=2000.0, n_points=100)
        result = sofip_ae8min_model.calculate(times=times, b_field=b, l_shell=l)

        assert np.any(result["integral_flux"] > 0)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
@pytest.mark.requires_dll
class TestValidation:
    """Test parameter validation."""

    def test_confidence_too_low(self, sofip_ap8max_model):
        times, b, l, _ = _make_orbit(n_points=10)
        with pytest.raises(ValueError, match="confidence_pct"):
            sofip_ap8max_model.calculate(
                times=times, b_field=b, l_shell=l, confidence_pct=50,
            )

    def test_confidence_too_high(self, sofip_ap8max_model):
        times, b, l, _ = _make_orbit(n_points=10)
        with pytest.raises(ValueError, match="confidence_pct"):
            sofip_ap8max_model.calculate(
                times=times, b_field=b, l_shell=l, confidence_pct=100,
            )

    def test_duration_zero(self, sofip_ap8max_model):
        times, b, l, _ = _make_orbit(n_points=10)
        with pytest.raises(ValueError, match="duration_months"):
            sofip_ap8max_model.calculate(
                times=times, b_field=b, l_shell=l, duration_months=0,
            )

    def test_empty_trajectory(self, sofip_ap8max_model):
        with pytest.raises(ValueError, match="不能为空"):
            sofip_ap8max_model.calculate(
                times=np.array([], dtype=np.float32),
                b_field=np.array([], dtype=np.float32),
                l_shell=np.array([], dtype=np.float32),
            )

    def test_mismatched_shapes(self, sofip_ap8max_model):
        with pytest.raises(ValueError, match="相同的形状"):
            sofip_ap8max_model.calculate(
                times=np.array([0.0, 1.0], dtype=np.float32),
                b_field=np.array([0.3], dtype=np.float32),
                l_shell=np.array([1.1, 1.1], dtype=np.float32),
            )


# ---------------------------------------------------------------------------
# Non-repo working directory
# ---------------------------------------------------------------------------
@pytest.mark.requires_dll
class TestNonRepoDirectory:
    """Ensure model works when CWD is not the repo root."""

    def test_calculate_from_tmp(self, sofip_ap8max_model, tmp_path):
        times, b, l, _ = _make_orbit(n_points=20)
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = sofip_ap8max_model.calculate(times=times, b_field=b, l_shell=l)
            assert result["total_time_hours"] > 0
        finally:
            os.chdir(old_cwd)
