from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class TestISRDriftModule:
    """Test module structure and lazy imports."""

    def test_module_only_exports_model(self):
        from model.pyisrdrift import __all__

        assert __all__ == ["Model"]

    def test_all_exports(self):
        import model

        assert "ISRDrift" in model.__all__


class TestISRDriftCalculation:
    """Test single-point and batch calculations."""

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, isrdrift_model):
        result = isrdrift_model.calculate(
            mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
        )

        assert set(result) == {
            "mlat_deg", "mlon_deg", "doy", "ut_hours",
            "potential_V", "poleward_drift_ms", "eastward_drift_ms",
        }
        assert isinstance(result["potential_V"], float)
        assert isinstance(result["poleward_drift_ms"], float)
        assert isinstance(result["eastward_drift_ms"], float)

    @pytest.mark.requires_dll
    def test_finite_values(self, isrdrift_model):
        result = isrdrift_model.calculate(
            mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
        )
        assert math.isfinite(result["potential_V"])
        assert math.isfinite(result["poleward_drift_ms"])
        assert math.isfinite(result["eastward_drift_ms"])

    @pytest.mark.requires_dll
    def test_batch_shape(self, isrdrift_model):
        result = isrdrift_model.calculate(
            mlat_deg=[40.0, 50.0, 60.0],
            mlon_deg=[0.0, 90.0, 180.0],
            doy=[80.0, 172.0, 264.0],
            ut_hours=[0.0, 6.0, 12.0],
        )
        assert result["potential_V"].shape == (3,)
        assert result["poleward_drift_ms"].shape == (3,)
        assert result["eastward_drift_ms"].shape == (3,)
        assert np.all(np.isfinite(result["potential_V"]))
        assert np.all(np.isfinite(result["poleward_drift_ms"]))
        assert np.all(np.isfinite(result["eastward_drift_ms"]))

    @pytest.mark.requires_dll
    def test_scalar_returns_scalar(self, isrdrift_model):
        result = isrdrift_model.calculate(
            mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
        )
        assert isinstance(result["potential_V"], float)
        assert isinstance(result["poleward_drift_ms"], float)
        assert isinstance(result["eastward_drift_ms"], float)

    @pytest.mark.requires_dll
    def test_array_returns_array(self, isrdrift_model):
        result = isrdrift_model.calculate(
            mlat_deg=[45.0, 50.0],
            mlon_deg=[0.0, 90.0],
            doy=[172.0, 172.0],
            ut_hours=[12.0, 12.0],
        )
        assert isinstance(result["potential_V"], np.ndarray)
        assert isinstance(result["poleward_drift_ms"], np.ndarray)
        assert isinstance(result["eastward_drift_ms"], np.ndarray)

    @pytest.mark.requires_dll
    def test_all_seasonal_avg_modes(self, isrdrift_model):
        for mode in range(5):
            result = isrdrift_model.calculate(
                mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
                seasonal_avg=mode,
            )
            assert math.isfinite(result["potential_V"])

    @pytest.mark.requires_dll
    def test_ut_avg_mode(self, isrdrift_model):
        result = isrdrift_model.calculate(
            mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
            ut_avg=1,
        )
        assert math.isfinite(result["potential_V"])

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import ISRDrift

        monkeypatch.chdir(tmp_path)
        model = ISRDrift()
        result = model.calculate(
            mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
        )
        assert isinstance(result["potential_V"], float)


class TestISRDriftValidation:
    """Test input validation."""

    def test_invalid_seasonal_avg(self, isrdrift_model):
        with pytest.raises(ValueError, match="seasonal_avg"):
            isrdrift_model.calculate(
                mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
                seasonal_avg=5,
            )

    def test_invalid_seasonal_avg_negative(self, isrdrift_model):
        with pytest.raises(ValueError, match="seasonal_avg"):
            isrdrift_model.calculate(
                mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
                seasonal_avg=-1,
            )

    def test_invalid_ut_avg(self, isrdrift_model):
        with pytest.raises(ValueError, match="ut_avg"):
            isrdrift_model.calculate(
                mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
                ut_avg=2,
            )


class TestISRDriftConstructor:
    """Test constructor edge cases."""

    def test_invalid_dll_path(self):
        from model.pyisrdrift import Model

        with pytest.raises((FileNotFoundError, OSError)):
            Model(dll_path="/nonexistent/path.dll")
