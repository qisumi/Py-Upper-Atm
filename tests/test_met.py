from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class TestMET:
    def test_module_only_exports_model(self):
        from model.pymet import __all__

        assert __all__ == ["Model"]

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, met_model):
        result = met_model.calculate(
            alt_km=200.0,
            lat_deg=35.0,
            lon_deg=116.0,
            year=23,
            month=7,
            day=15,
            hour=12,
            minute=0,
            geo_index_type=2,
            f107=100.0,
            f107a=100.0,
            ap=15.0,
        )

        assert set(result) == {
            "alt_km",
            "lat_deg",
            "lon_deg",
            "T_exo_K",
            "T_local_K",
            "N2_m3",
            "O2_m3",
            "O_m3",
            "Ar_m3",
            "He_m3",
            "H_m3",
            "mean_molecular_weight",
            "total_density_kg_m3",
            "log10_density",
            "pressure_Pa",
            "gravity_m_s2",
            "gamma",
            "scale_height_m",
            "cp",
            "cv",
        }
        assert isinstance(result["T_exo_K"], float)
        assert isinstance(result["T_local_K"], float)
        assert result["T_exo_K"] > 0
        assert result["T_local_K"] > 0

    @pytest.mark.requires_dll
    def test_calculate_batch(self, met_model):
        alts = [100.0, 200.0, 300.0, 400.0, 500.0]
        result = met_model.calculate(
            alt_km=alts,
            lat_deg=35.0,
            lon_deg=116.0,
            year=23,
            month=7,
            day=15,
            hour=12,
            minute=0,
            geo_index_type=2,
            f107=100.0,
            f107a=100.0,
            ap=15.0,
        )

        assert result["T_local_K"].shape == (5,)
        assert np.all(result["T_local_K"] > 0)

    @pytest.mark.requires_dll
    def test_calculate_array(self, met_model):
        alts = np.arange(100, 301, 50)
        result = met_model.calculate(
            alt_km=alts,
            lat_deg=35.0,
            lon_deg=116.0,
            year=23,
            month=7,
            day=15,
            hour=12,
            minute=0,
            geo_index_type=2,
            f107=100.0,
            f107a=100.0,
            ap=15.0,
        )

        assert result["T_local_K"].shape == alts.shape
        assert np.all(np.isfinite(result["T_local_K"]))

    @pytest.mark.requires_dll
    def test_different_solar_activity(self, met_model):
        alt = 300.0
        for f107 in [70.0, 100.0, 150.0, 200.0]:
            result = met_model.calculate(
                alt_km=alt,
                lat_deg=35.0,
                lon_deg=116.0,
                year=23,
                month=7,
                day=15,
                hour=12,
                minute=0,
                geo_index_type=2,
                f107=f107,
                f107a=f107,
                ap=15.0,
            )
            assert np.isfinite(result["T_exo_K"])
            assert result["T_exo_K"] > 0

    @pytest.mark.requires_dll
    def test_species_densities(self, met_model):
        result = met_model.calculate(
            alt_km=200.0,
            lat_deg=35.0,
            lon_deg=116.0,
            year=23,
            month=7,
            day=15,
            hour=12,
            minute=0,
            geo_index_type=2,
            f107=100.0,
            f107a=100.0,
            ap=15.0,
        )
        for species in ["N2_m3", "O2_m3", "O_m3", "Ar_m3", "He_m3", "H_m3"]:
            assert result[species] >= 0

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import MET

        monkeypatch.chdir(tmp_path)
        model = MET()
        result = model.calculate(
            alt_km=200.0,
            lat_deg=35.0,
            lon_deg=116.0,
            year=23,
            month=7,
            day=15,
            hour=12,
            minute=0,
            geo_index_type=2,
            f107=100.0,
            f107a=100.0,
            ap=15.0,
        )
        assert isinstance(result["T_local_K"], float)
        assert result["T_local_K"] > 0
