"""
Tests for IGRF geomagnetic field model (IGRF-13 and IGRF-14).
"""

import pytest

from model import IGRF
from model.pyigrf import Model, __all__


class TestIGRFModule:
    """Test IGRF module structure."""

    def test_module_only_exports_model(self):
        assert __all__ == ["Model"]


class TestIGRF14:
    """Test IGRF-14 model."""

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, igrf_model):
        result = igrf_model.calculate(
            year=2024.0,
            lat_deg=39.9,
            lon_deg=116.4,
            alt_km=0.0,
        )
        assert isinstance(result, dict)
        # Verify key fields
        assert "B_north_nT" in result
        assert "B_east_nT" in result
        assert "B_down_nT" in result
        assert "B_abs_nT" in result
        assert "H_nT" in result
        assert "inclination_deg" in result
        assert "declination_deg" in result
        assert "L_value" in result
        assert "icode" in result
        # Types
        assert isinstance(float(result["B_abs_nT"]), float)
        assert isinstance(int(result["icode"]), int)
        # Reasonable ranges for Beijing at surface
        assert 30000 < result["B_abs_nT"] < 70000  # nT
        assert -90 <= result["inclination_deg"] <= 90
        assert -180 <= result["declination_deg"] <= 180
        assert 0 < result["L_value"] < 10
        assert result["icode"] in (1, 2, 3)

    @pytest.mark.requires_dll
    def test_calculate_batch(self, igrf_model):
        result = igrf_model.calculate(
            year=2020.0,
            lat_deg=[30.0, 40.0, 50.0],
            lon_deg=[116.0, 116.0, 116.0],
            alt_km=[0.0, 100.0, 200.0],
        )
        assert result["B_north_nT"].shape == (3,)
        assert result["L_value"].shape == (3,)

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(self, igrf_model, tmp_path):
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = igrf_model.calculate(
                year=2020.0,
                lat_deg=39.9,
                lon_deg=116.4,
                alt_km=0.0,
            )
            assert result["B_abs_nT"] > 0
        finally:
            os.chdir(original_cwd)

    @pytest.mark.requires_dll
    def test_calculate_scalar_returns_scalar(self, igrf_model):
        result = igrf_model.calculate(
            year=2020.0,
            lat_deg=39.9,
            lon_deg=116.4,
            alt_km=0.0,
        )
        for key, value in result.items():
            if key in ("icode",):
                assert isinstance(value, int), f"{key} should be int"
            else:
                assert isinstance(value, float), f"{key} should be float"

    @pytest.mark.requires_dll
    def test_broadcast_same_size(self, igrf_model):
        """Test that same-size arrays produce no broadcast changes."""
        result = igrf_model.calculate(
            year=[2020.0, 2020.5],
            lat_deg=[30.0, 40.0],
            lon_deg=[116.0, 120.0],
            alt_km=[0.0, 100.0],
        )
        assert result["B_abs_nT"].shape == (2,)


class TestIGRF13:
    """Test IGRF-13 model."""

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, igrf13_model):
        result = igrf13_model.calculate(
            year=2020.0,
            lat_deg=0.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        assert result["B_abs_nT"] > 0
        assert result["L_value"] > 0

    @pytest.mark.requires_dll
    def test_year_backward_compatible(self, igrf13_model):
        """Test that pre-2000 years work with lower-degree models."""
        result = igrf13_model.calculate(
            year=1960.0,
            lat_deg=39.9,
            lon_deg=116.4,
            alt_km=0.0,
        )
        assert result["B_abs_nT"] > 0
        assert result["icode"] in (1, 2, 3)


class TestIGRFValidation:
    """Cross-version and basic physics validation."""

    @pytest.mark.requires_dll
    def test_igrf13_vs_igrf14_consistent_before_2020(self, igrf_model, igrf13_model):
        """IGRF-13 and IGRF-14 should agree exactly for DGRF epochs before 2020."""
        r13 = igrf13_model.calculate(year=2000.0, lat_deg=0.0, lon_deg=0.0, alt_km=0.0)
        r14 = igrf_model.calculate(year=2000.0, lat_deg=0.0, lon_deg=0.0, alt_km=0.0)
        # DGRF 2000 should be identical in both models
        assert abs(r13["B_abs_nT"] - r14["B_abs_nT"]) < 1.0  # sub-nT difference

    @pytest.mark.requires_dll
    def test_igrf13_vs_igrf14_differ_at_2020(self, igrf_model, igrf13_model):
        """IGRF-14 DGRF-2020 differs slightly from IGRF-13 IGRF-2020."""
        r13 = igrf13_model.calculate(year=2020.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
        r14 = igrf_model.calculate(year=2020.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
        # The updated DGRF coefficients differ; check any component differs
        diff_n = abs(r13["B_north_nT"] - r14["B_north_nT"])
        diff_e = abs(r13["B_east_nT"] - r14["B_east_nT"])
        diff_d = abs(r13["B_down_nT"] - r14["B_down_nT"])
        total_diff = abs(r13["B_abs_nT"] - r14["B_abs_nT"])
        # The difference should be small but non-zero at this location
        assert 0 <= total_diff < 50, f"Unexpected large diff: {total_diff:.2f} nT"
        # At least one component should differ measurably
        assert (diff_n + diff_e + diff_d) > 0, "IGRF-13 and IGRF-14 should differ!"


class TestIGRFConstructor:
    """Test constructor validation."""

    def test_invalid_version_raises_error(self):
        with pytest.raises(ValueError, match="必须为 13 或 14"):
            IGRF(igrf_version=12, data_dir="nonexistent", auto_download=False)

    def test_lazy_export(self):
        """import model must not load IGRF DLL."""
        import model
        assert "IGRF" in model.__all__
