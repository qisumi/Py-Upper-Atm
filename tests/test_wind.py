from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODEL_DATA = ROOT / "data"


class TestHWM14:
    def test_module_only_exports_model(self):
        from model.pyhwm14 import __all__

        assert __all__ == ["Model"]

    @pytest.mark.requires_dll
    def test_calculate_single_point(
        self, hwm14_model, sample_iyd, default_geo_params, default_solar_params
    ):
        result = hwm14_model.calculate(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=default_geo_params["alt_km"],
            glat_deg=default_geo_params["lat_deg"],
            glon_deg=default_geo_params["lon_deg"],
            stl_hours=12.0,
            **default_solar_params,
        )

        assert set(result) == {"alt_km", "meridional_wind_ms", "zonal_wind_ms"}
        assert isinstance(result["meridional_wind_ms"], float)
        assert -500 < result["meridional_wind_ms"] < 500
        assert -500 < result["zonal_wind_ms"] < 500

    @pytest.mark.requires_dll
    def test_calculate_batch(self, hwm14_model, sample_iyd, default_solar_params):
        result = hwm14_model.calculate(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=[100.0, 200.0, 300.0],
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            **default_solar_params,
        )

        assert result["meridional_wind_ms"].shape == (3,)
        assert result["zonal_wind_ms"].shape == (3,)

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path, sample_iyd, default_geo_params, default_solar_params
    ):
        from model import HWM14

        monkeypatch.chdir(tmp_path)
        model = HWM14(data_dir=MODEL_DATA, auto_download=False)
        result = model.calculate(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=default_geo_params["alt_km"],
            glat_deg=default_geo_params["lat_deg"],
            glon_deg=default_geo_params["lon_deg"],
            stl_hours=12.0,
            **default_solar_params,
        )

        assert isinstance(result["meridional_wind_ms"], float)

    @pytest.mark.requires_dll
    def test_invalid_ap2_raises_error(self, hwm14_model, sample_iyd):
        with pytest.raises(ValueError, match="ap2"):
            hwm14_model.calculate(
                iyd=sample_iyd,
                sec=45000.0,
                alt_km=100.0,
                glat_deg=35.0,
                glon_deg=116.0,
                stl_hours=12.0,
                f107a=100.0,
                f107=100.0,
                ap2=(1.0,),
            )


class TestHWM93:
    def test_module_only_exports_model(self):
        from model.pyhwm93 import __all__

        assert __all__ == ["Model"]

    @pytest.mark.requires_dll
    def test_calculate_single_point(
        self, hwm93_model, sample_iyd, default_geo_params, default_solar_params
    ):
        result = hwm93_model.calculate(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=default_geo_params["alt_km"],
            glat_deg=default_geo_params["lat_deg"],
            glon_deg=default_geo_params["lon_deg"],
            stl_hours=12.0,
            **default_solar_params,
        )

        assert set(result) == {"alt_km", "meridional_wind_ms", "zonal_wind_ms"}
        assert isinstance(result["meridional_wind_ms"], float)
        assert -500 < result["meridional_wind_ms"] < 500
        assert -500 < result["zonal_wind_ms"] < 500

    @pytest.mark.requires_dll
    def test_calculate_batch(self, hwm93_model, sample_iyd, default_solar_params):
        result = hwm93_model.calculate(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=np.array([100.0, 200.0]),
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            **default_solar_params,
        )

        assert result["meridional_wind_ms"].shape == (2,)
        assert result["zonal_wind_ms"].shape == (2,)

    @pytest.mark.requires_dll
    def test_invalid_ap2_raises_error(self, hwm93_model, sample_iyd):
        with pytest.raises(ValueError, match="ap2"):
            hwm93_model.calculate(
                iyd=sample_iyd,
                sec=45000.0,
                alt_km=100.0,
                glat_deg=35.0,
                glon_deg=116.0,
                stl_hours=12.0,
                f107a=100.0,
                f107=100.0,
                ap2=(1.0,),
            )
