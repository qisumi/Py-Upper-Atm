"""Tests for the Chiu ionospheric electron density model."""
from __future__ import annotations

import math

import numpy as np
import pytest


class TestChiuModule:
    def test_all_exports_model(self):
        from model.pychiu import __all__

        assert __all__ == ["Model"]


class TestChiu:
    @pytest.mark.requires_dll
    def test_single_point(self, chiu_model):
        result = chiu_model.calculate(
            alt_km=300.0,
            sunspot_number=100.0,
            local_time_rad=math.pi,
            month_from_dec15=6.0,
            geo_lat_rad=math.radians(35.0),
            geo_mag_lat_rad=math.radians(25.0),
            geo_mag_lon_rad=math.radians(120.0),
            dip_angle_rad=math.radians(45.0),
        )

        expected_keys = {
            "alt_km",
            "sunspot_number",
            "Ne_total_cm3",
            "Ne_E_cm3",
            "Ne_F1_cm3",
            "Ne_F2_cm3",
        }
        assert set(result) == expected_keys
        assert result["alt_km"] == 300.0
        assert result["Ne_total_cm3"] > 0
        assert result["Ne_F2_cm3"] > result["Ne_E_cm3"]

    @pytest.mark.requires_dll
    def test_batch_altitude(self, chiu_model):
        result = chiu_model.calculate(
            alt_km=[100.0, 200.0, 300.0, 400.0, 500.0],
            sunspot_number=100.0,
            local_time_rad=math.pi,
            month_from_dec15=6.0,
            geo_lat_rad=math.radians(35.0),
            geo_mag_lat_rad=math.radians(25.0),
            geo_mag_lon_rad=math.radians(120.0),
            dip_angle_rad=math.radians(45.0),
        )

        np.testing.assert_allclose(
            result["alt_km"], [100.0, 200.0, 300.0, 400.0, 500.0]
        )
        assert result["Ne_total_cm3"].shape == (5,)
        assert result["Ne_E_cm3"].shape == (5,)
        assert result["Ne_F1_cm3"].shape == (5,)
        assert result["Ne_F2_cm3"].shape == (5,)
        # All densities should be positive
        assert np.all(result["Ne_total_cm3"] > 0)

    @pytest.mark.requires_dll
    def test_peak_density_mode(self, chiu_model):
        """alt_km=0 returns layer peak densities with Ne_total=0."""
        result = chiu_model.calculate(
            alt_km=0.0,
            sunspot_number=100.0,
            local_time_rad=math.pi,
            month_from_dec15=6.0,
            geo_lat_rad=math.radians(35.0),
            geo_mag_lat_rad=math.radians(25.0),
            geo_mag_lon_rad=math.radians(120.0),
            dip_angle_rad=math.radians(45.0),
        )

        assert result["Ne_total_cm3"] == 0.0
        assert result["Ne_E_cm3"] > 0
        assert result["Ne_F1_cm3"] > 0
        assert result["Ne_F2_cm3"] > 0

    @pytest.mark.requires_dll
    def test_solar_activity_variation(self, chiu_model):
        """Electron density changes with solar activity."""
        result = chiu_model.calculate(
            alt_km=300.0,
            sunspot_number=[10.0, 100.0, 200.0],
            local_time_rad=math.pi,
            month_from_dec15=6.0,
            geo_lat_rad=math.radians(35.0),
            geo_mag_lat_rad=math.radians(25.0),
            geo_mag_lon_rad=math.radians(120.0),
            dip_angle_rad=math.radians(45.0),
        )

        assert result["Ne_total_cm3"].shape == (3,)
        assert result["Ne_total_cm3"][2] > result["Ne_total_cm3"][0]

    @pytest.mark.requires_dll
    def test_day_night_contrast(self, chiu_model):
        """Daytime (noon) and nighttime (midnight) should produce different densities."""
        common = dict(
            alt_km=300.0,
            sunspot_number=100.0,
            month_from_dec15=6.0,
            geo_lat_rad=math.radians(45.0),
            geo_mag_lat_rad=math.radians(40.0),
            geo_mag_lon_rad=math.radians(120.0),
            dip_angle_rad=math.radians(60.0),
        )
        # PHI is local time angle measured from midnight: 0=midnight, pi=noon
        day = chiu_model.calculate(local_time_rad=math.pi, **common)
        night = chiu_model.calculate(local_time_rad=0.0, **common)

        # Daytime and nighttime should be meaningfully different
        assert day["Ne_total_cm3"] != night["Ne_total_cm3"]
        # Both should be positive
        assert day["Ne_total_cm3"] > 0
        assert night["Ne_total_cm3"] > 0

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import Chiu

        monkeypatch.chdir(tmp_path)
        model = Chiu()
        result = model.calculate(
            alt_km=300.0,
            sunspot_number=100.0,
            local_time_rad=math.pi,
            month_from_dec15=6.0,
            geo_lat_rad=math.radians(35.0),
            geo_mag_lat_rad=math.radians(25.0),
            geo_mag_lon_rad=math.radians(120.0),
            dip_angle_rad=math.radians(45.0),
        )
        assert isinstance(result["Ne_total_cm3"], float)
        assert result["Ne_total_cm3"] > 0
