from __future__ import annotations

import pytest
from datetime import datetime

from model import WindModel, WindResult


class TestWindModelInstantiation:
    def test_default_model_is_hwm14(self):
        try:
            model = WindModel()
            assert model.model_version == "hwm14"
        except RuntimeError:
            pytest.skip("HWM14 DLL not available")

    def test_explicit_hwm14_version(self):
        try:
            model = WindModel(model_version="hwm14")
            assert model.model_version == "hwm14"
        except RuntimeError:
            pytest.skip("HWM14 DLL not available")

    def test_hwm93_version(self):
        try:
            model = WindModel(model_version="hwm93")
            assert model.model_version == "hwm93"
        except RuntimeError:
            pytest.skip("HWM93 DLL not available")

    def test_invalid_version_raises_error(self):
        with pytest.raises(ValueError, match="不支持的模型版本"):
            WindModel(model_version="invalid")


class TestWindHWM14:
    @pytest.mark.requires_dll
    def test_calculate_point_returns_wind_result(
        self, wind_model_hwm14, sample_iyd, default_geo_params, default_solar_params
    ):
        result = wind_model_hwm14.calculate_point(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=default_geo_params["alt_km"],
            glat_deg=default_geo_params["lat_deg"],
            glon_deg=default_geo_params["lon_deg"],
            stl_hours=12.0,
            **default_solar_params,
        )
        assert isinstance(result, WindResult)
        assert result.alt_km == default_geo_params["alt_km"]

    @pytest.mark.requires_dll
    def test_wind_values_are_finite(
        self, wind_model_hwm14, sample_iyd, default_geo_params, default_solar_params
    ):
        result = wind_model_hwm14.calculate_point(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=default_geo_params["alt_km"],
            glat_deg=default_geo_params["lat_deg"],
            glon_deg=default_geo_params["lon_deg"],
            stl_hours=12.0,
            **default_solar_params,
        )
        assert -500 < result.meridional_wind_ms < 500
        assert -500 < result.zonal_wind_ms < 500

    @pytest.mark.requires_dll
    def test_calculate_point_at_datetime(
        self,
        wind_model_hwm14,
        sample_datetime,
        default_geo_params,
        default_solar_params,
    ):
        result = wind_model_hwm14.calculate_point_at_datetime(
            dt=sample_datetime,
            alt_km=default_geo_params["alt_km"],
            glat_deg=default_geo_params["lat_deg"],
            glon_deg=default_geo_params["lon_deg"],
            **default_solar_params,
        )
        assert isinstance(result, WindResult)

    @pytest.mark.requires_dll
    def test_batch_calculation_returns_list(
        self, wind_model_hwm14, sample_iyd, default_solar_params
    ):
        results = wind_model_hwm14.calculate_batch(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=[100.0, 200.0, 300.0],
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            **default_solar_params,
        )
        assert len(results) == 3
        assert all(isinstance(r, WindResult) for r in results)

    @pytest.mark.requires_dll
    def test_batch_output_as_tuple(
        self, wind_model_hwm14, sample_iyd, default_solar_params
    ):
        wm, wz = wind_model_hwm14.calculate_batch(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=[100.0, 200.0],
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            output_as_tuple=True,
            **default_solar_params,
        )
        assert len(wm) == 2
        assert len(wz) == 2


class TestWindHWM93:
    @pytest.mark.requires_dll
    def test_calculate_point_returns_wind_result(
        self, wind_model_hwm93, sample_iyd, default_geo_params, default_solar_params
    ):
        result = wind_model_hwm93.calculate_point(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=default_geo_params["alt_km"],
            glat_deg=default_geo_params["lat_deg"],
            glon_deg=default_geo_params["lon_deg"],
            stl_hours=12.0,
            **default_solar_params,
        )
        assert isinstance(result, WindResult)

    @pytest.mark.requires_dll
    def test_wind_values_are_finite(
        self, wind_model_hwm93, sample_iyd, default_geo_params, default_solar_params
    ):
        result = wind_model_hwm93.calculate_point(
            iyd=sample_iyd,
            sec=45000.0,
            alt_km=default_geo_params["alt_km"],
            glat_deg=default_geo_params["lat_deg"],
            glon_deg=default_geo_params["lon_deg"],
            stl_hours=12.0,
            **default_solar_params,
        )
        assert -500 < result.meridional_wind_ms < 500
        assert -500 < result.zonal_wind_ms < 500


class TestWindValidation:
    @pytest.mark.requires_dll
    def test_invalid_altitude_raises_error(
        self, wind_model_hwm14, sample_iyd, default_solar_params
    ):
        with pytest.raises(ValueError, match="alt_km"):
            wind_model_hwm14.calculate_point(
                iyd=sample_iyd,
                sec=45000.0,
                alt_km=-10.0,
                glat_deg=35.0,
                glon_deg=116.0,
                stl_hours=12.0,
                **default_solar_params,
            )

    @pytest.mark.requires_dll
    def test_invalid_latitude_raises_error(
        self, wind_model_hwm14, sample_iyd, default_solar_params
    ):
        with pytest.raises(ValueError, match="glat_deg"):
            wind_model_hwm14.calculate_point(
                iyd=sample_iyd,
                sec=45000.0,
                alt_km=100.0,
                glat_deg=100.0,
                glon_deg=116.0,
                stl_hours=12.0,
                **default_solar_params,
            )

    @pytest.mark.requires_dll
    def test_validation_can_be_disabled(
        self, wind_model_hwm14, sample_iyd, default_solar_params
    ):
        try:
            wind_model_hwm14.calculate_point(
                iyd=sample_iyd,
                sec=45000.0,
                alt_km=-10.0,
                glat_deg=35.0,
                glon_deg=116.0,
                stl_hours=12.0,
                validate=False,
                **default_solar_params,
            )
        except ValueError:
            pytest.fail("Should not validate when validate=False")
        except Exception:
            pass
