from __future__ import annotations

import numpy as np
import pytest


class TestCIRA86:
    def test_module_only_exports_model(self):
        from model.pycira86 import __all__

        assert __all__ == ["Model"]

    def test_calculate_height_single_point(self, cira86_model):
        result = cira86_model.calculate(month=1, lat_deg=0.0, alt_km=100.0)

        assert set(result) == {
            "month",
            "alt_km",
            "lat_deg",
            "T_K",
            "zonal_wind_ms",
            "pressure_mb",
        }
        assert isinstance(result["T_K"], float)
        assert isinstance(result["zonal_wind_ms"], float)
        assert isinstance(result["pressure_mb"], float)
        assert 100.0 < result["T_K"] < 500.0
        assert -150.0 < result["zonal_wind_ms"] < 150.0
        assert result["pressure_mb"] > 0.0

    def test_calculate_pressure_single_point(self, cira86_model):
        result = cira86_model.calculate(
            month=1,
            lat_deg=0.0,
            pressure_mb=3.10e-4,
        )

        assert set(result) == {
            "month",
            "pressure_mb",
            "lat_deg",
            "T_K",
            "zonal_wind_ms",
            "geopotential_height_m",
        }
        assert isinstance(result["geopotential_height_m"], float)
        assert 90000.0 < result["geopotential_height_m"] < 110000.0

    def test_calculate_batch(self, cira86_model):
        result = cira86_model.calculate(
            month=[1, 4, 7, 10],
            lat_deg=[-40.0, 0.0, 40.0, 80.0],
            alt_km=[20.0, 50.0, 80.0, 110.0],
        )

        assert result["T_K"].shape == (4,)
        assert result["zonal_wind_ms"].shape == (4,)
        assert result["pressure_mb"].shape == (4,)
        assert np.all(np.isfinite(result["T_K"]))
        assert np.all(result["pressure_mb"] > 0.0)

    def test_calculate_from_non_repo_working_directory(self, monkeypatch, tmp_path):
        from tests.conftest import MODEL_DATA
        from model import CIRA86

        monkeypatch.chdir(tmp_path)
        model = CIRA86(data_dir=MODEL_DATA, auto_download=False)
        result = model.calculate(month=1, lat_deg=0.0, alt_km=100.0)
        assert isinstance(result["T_K"], float)

    def test_invalid_parameter_raises_error(self, cira86_model):
        with pytest.raises(ValueError, match="month"):
            cira86_model.calculate(month=13, lat_deg=0.0, alt_km=100.0)
        with pytest.raises(ValueError, match="lat_deg"):
            cira86_model.calculate(month=1, lat_deg=90.0, alt_km=100.0)
        with pytest.raises(ValueError, match="alt_km"):
            cira86_model.calculate(month=1, lat_deg=0.0, alt_km=130.0)
        with pytest.raises(ValueError, match="alt_km"):
            cira86_model.calculate(
                month=1,
                lat_deg=0.0,
                alt_km=100.0,
                pressure_mb=1.0,
            )
