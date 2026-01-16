from __future__ import annotations

import pytest
from datetime import datetime

from model import (
    TempDensityModel,
    TempDensityResult,
    convert_date_to_day,
    calculate_seconds_of_day,
)


class TestTempDensityModelInstantiation:
    def test_default_model_is_msis2(self):
        try:
            model = TempDensityModel()
            assert model.model_version == "msis2"
        except RuntimeError:
            pytest.skip("MSIS-2.0 DLL not available")

    def test_explicit_msis2_version(self):
        try:
            model = TempDensityModel(model_version="msis2")
            assert model.model_version == "msis2"
        except RuntimeError:
            pytest.skip("MSIS-2.0 DLL not available")

    def test_msis00_version(self):
        try:
            model = TempDensityModel(model_version="msis00")
            assert model.model_version == "msis00"
        except RuntimeError:
            pytest.skip("MSIS-00 DLL not available")

    def test_invalid_version_raises_error(self):
        with pytest.raises(ValueError, match="不支持的模型版本"):
            TempDensityModel(model_version="invalid")


class TestTempDensityMSIS2:
    @pytest.mark.requires_dll
    def test_calculate_point_returns_result(
        self, temp_density_model_msis2, default_geo_params, default_solar_params
    ):
        result = temp_density_model_msis2.calculate_point(
            day=196.0,
            utsec=45000.0,
            **default_geo_params,
            **default_solar_params,
        )
        assert isinstance(result, TempDensityResult)
        assert result.alt_km == default_geo_params["alt_km"]

    @pytest.mark.requires_dll
    def test_temperature_values_are_reasonable(
        self, temp_density_model_msis2, default_geo_params, default_solar_params
    ):
        result = temp_density_model_msis2.calculate_point(
            day=196.0,
            utsec=45000.0,
            **default_geo_params,
            **default_solar_params,
        )
        assert 100 < result.T_local_K < 500
        assert 500 < result.T_exo_K < 2000

    @pytest.mark.requires_dll
    def test_densities_are_positive(
        self, temp_density_model_msis2, default_geo_params, default_solar_params
    ):
        result = temp_density_model_msis2.calculate_point(
            day=196.0,
            utsec=45000.0,
            **default_geo_params,
            **default_solar_params,
        )
        for density in result.densities:
            assert density >= 0

    @pytest.mark.requires_dll
    def test_calculate_point_at_datetime(
        self,
        temp_density_model_msis2,
        sample_datetime,
        default_geo_params,
        default_solar_params,
    ):
        result = temp_density_model_msis2.calculate_point_at_datetime(
            dt=sample_datetime,
            **default_geo_params,
            **default_solar_params,
        )
        assert isinstance(result, TempDensityResult)

    @pytest.mark.requires_dll
    def test_batch_calculation_returns_list(
        self, temp_density_model_msis2, default_solar_params
    ):
        results = temp_density_model_msis2.calculate_batch(
            day=196.0,
            utsec=45000.0,
            alt_km=[100.0, 200.0, 300.0],
            lat_deg=35.0,
            lon_deg=116.0,
            **default_solar_params,
        )
        assert len(results) == 3
        assert all(isinstance(r, TempDensityResult) for r in results)

    @pytest.mark.requires_dll
    def test_batch_output_as_dict(self, temp_density_model_msis2, default_solar_params):
        result = temp_density_model_msis2.calculate_batch(
            day=196.0,
            utsec=45000.0,
            alt_km=[100.0, 200.0],
            lat_deg=35.0,
            lon_deg=116.0,
            output_as_dict=True,
            **default_solar_params,
        )
        assert isinstance(result, dict)
        assert "alt_km" in result or "T_local_K" in result


class TestTempDensityMSIS00:
    @pytest.mark.requires_dll
    def test_calculate_point_returns_result(
        self, temp_density_model_msis00, default_geo_params, default_solar_params
    ):
        result = temp_density_model_msis00.calculate_point(
            day=196.0,
            utsec=45000.0,
            **default_geo_params,
            **default_solar_params,
        )
        assert isinstance(result, TempDensityResult)

    @pytest.mark.requires_dll
    def test_temperature_values_are_reasonable(
        self, temp_density_model_msis00, default_geo_params, default_solar_params
    ):
        result = temp_density_model_msis00.calculate_point(
            day=196.0,
            utsec=45000.0,
            **default_geo_params,
            **default_solar_params,
        )
        assert 100 < result.T_local_K < 500
        assert 500 < result.T_exo_K < 2000


class TestTempDensityValidation:
    @pytest.mark.requires_dll
    def test_invalid_altitude_raises_error(
        self, temp_density_model_msis2, default_solar_params
    ):
        with pytest.raises(ValueError, match="alt_km"):
            temp_density_model_msis2.calculate_point(
                day=196.0,
                utsec=45000.0,
                alt_km=-10.0,
                lat_deg=35.0,
                lon_deg=116.0,
                **default_solar_params,
            )

    @pytest.mark.requires_dll
    def test_invalid_latitude_raises_error(
        self, temp_density_model_msis2, default_solar_params
    ):
        with pytest.raises(ValueError, match="lat_deg"):
            temp_density_model_msis2.calculate_point(
                day=196.0,
                utsec=45000.0,
                alt_km=100.0,
                lat_deg=100.0,
                lon_deg=116.0,
                **default_solar_params,
            )

    @pytest.mark.requires_dll
    def test_validation_can_be_disabled(
        self, temp_density_model_msis2, default_solar_params
    ):
        try:
            temp_density_model_msis2.calculate_point(
                day=196.0,
                utsec=45000.0,
                alt_km=-10.0,
                lat_deg=35.0,
                lon_deg=116.0,
                validate=False,
                **default_solar_params,
            )
        except ValueError:
            pytest.fail("Should not validate when validate=False")
        except Exception:
            pass
