"""Tests for MGST80 and MGST81 geomagnetic field models."""

import math

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Module-level import tests
# ---------------------------------------------------------------------------

class TestMGSTModule:
    """Test lazy imports and module structure."""

    def test_all_exports(self):
        import model
        assert "MGST80" in model.__all__
        assert "MGST81" in model.__all__

    def test_lazy_import(self):
        import model
        assert "MGST80" not in dir(model) or isinstance(
            model.MGST80, type
        )


# ---------------------------------------------------------------------------
# MGST80 calculation tests
# ---------------------------------------------------------------------------

class TestMGST80Calculation:
    """Test MGST80 model calculations."""

    def test_single_point(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        assert isinstance(result, dict)

    def test_keys(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        expected = {
            "year", "lat_deg", "lon_deg", "alt_km",
            "X_nT", "Y_nT", "Z_nT", "F_nT", "H_nT",
            "inclination_deg", "declination_deg",
        }
        assert set(result.keys()) == expected

    def test_finite_values(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        for v in result.values():
            assert math.isfinite(v), f"Non-finite value: {v}"

    def test_reasonable_values(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        # FIELDG stores degree 1 at internal index N=2; the public result
        # should include the dipole term and be a full main-field magnitude.
        assert 30000 < result["F_nT"] < 70000

    def test_not_nan(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        for v in result.values():
            assert not math.isnan(v)

    def test_batch_shape(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85,
            lat_deg=[40.0, 50.0, 60.0],
            lon_deg=[0.0, 90.0, 180.0],
            alt_km=0.0,
        )
        assert result["F_nT"].shape == (3,)

    def test_broadcast_shape(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85,
            lat_deg=np.array([[40.0], [50.0]]),
            lon_deg=np.array([0.0, 90.0, 180.0]),
            alt_km=0.0,
        )
        assert result["F_nT"].shape == (2, 3)

    def test_scalar_returns_scalar(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        assert isinstance(result["F_nT"], float)

    def test_array_returns_array(self, mgst80_model):
        result = mgst80_model.calculate(
            year=1979.85,
            lat_deg=[40.0, 50.0],
            lon_deg=[0.0, 90.0],
            alt_km=0.0,
        )
        assert isinstance(result["F_nT"], np.ndarray)

    def test_nmx_parameter(self, mgst80_model):
        r6 = mgst80_model.calculate(
            year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0, nmx=6,
        )
        r13 = mgst80_model.calculate(
            year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0, nmx=13,
        )
        # Different nmx should give different results
        assert r6["F_nT"] != r13["F_nT"]

    def test_invalid_nmx(self, mgst80_model):
        with pytest.raises(ValueError):
            mgst80_model.calculate(
                year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0, nmx=0,
            )
        with pytest.raises((ValueError, AssertionError)):
            mgst80_model.calculate(
                year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0, nmx=20,
            )


# ---------------------------------------------------------------------------
# MGST81 calculation tests
# ---------------------------------------------------------------------------

class TestMGST81Calculation:
    """Test MGST81 model calculations."""

    def test_single_point(self, mgst81_model):
        result = mgst81_model.calculate(
            year=1980.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        assert isinstance(result, dict)

    def test_keys(self, mgst81_model):
        result = mgst81_model.calculate(
            year=1980.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        expected = {
            "year", "lat_deg", "lon_deg", "alt_km",
            "X_nT", "Y_nT", "Z_nT", "F_nT", "H_nT",
            "inclination_deg", "declination_deg",
        }
        assert set(result.keys()) == expected

    def test_finite_values(self, mgst81_model):
        result = mgst81_model.calculate(
            year=1980.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        for v in result.values():
            assert math.isfinite(v)

    def test_reasonable_values(self, mgst81_model):
        result = mgst81_model.calculate(
            year=1980.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        assert 30000 < result["F_nT"] < 70000

    def test_secular_variation(self, mgst81_model):
        """MGST81 has secular variation terms; values should differ from epoch."""
        r1980 = mgst81_model.calculate(
            year=1980.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        r1985 = mgst81_model.calculate(
            year=1985.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0,
        )
        # MGST81 has first derivative terms, so values should change
        assert r1980["F_nT"] != r1985["F_nT"]

    def test_batch_shape(self, mgst81_model):
        result = mgst81_model.calculate(
            year=1980.0,
            lat_deg=[40.0, 50.0, 60.0],
            lon_deg=[0.0, 90.0, 180.0],
            alt_km=0.0,
        )
        assert result["F_nT"].shape == (3,)


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------

class TestMGSTConstructor:
    """Test MGST80 and MGST81 constructors."""

    def test_lazy_export(self):
        import model
        cls80 = getattr(model, "MGST80", None)
        assert cls80 is not None
        cls81 = getattr(model, "MGST81", None)
        assert cls81 is not None

    def test_invalid_dll_path(self):
        # MGST uses pure Python, no DLL needed — test data_dir validation
        from model.pymgst import MGST80
        with pytest.raises(Exception):
            MGST80(data_dir="/nonexistent/path", auto_download=False)
