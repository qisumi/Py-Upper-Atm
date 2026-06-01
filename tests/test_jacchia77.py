from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class TestJacchia77:
    def test_module_only_exports_model(self):
        from model.pyjacchia77 import __all__

        assert __all__ == ["Model"]

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, jacchia77_model):
        result = jacchia77_model.calculate(alt_km=100.0, Tinf_K=1000.0)

        assert set(result) == {
            "alt_km",
            "Tinf_K",
            "T_local_K",
            "N2_cm3",
            "O2_cm3",
            "O_cm3",
            "Ar_cm3",
            "He_cm3",
            "H_cm3",
            "total_density_cm3",
            "mean_molecular_weight",
        }
        assert isinstance(result["alt_km"], float)
        assert isinstance(result["Tinf_K"], float)
        assert isinstance(result["T_local_K"], float)
        assert isinstance(result["N2_cm3"], float)
        assert result["T_local_K"] > 0
        assert result["N2_cm3"] > 0

    @pytest.mark.requires_dll
    def test_calculate_batch(self, jacchia77_model):
        alts = [90.0, 100.0, 200.0, 300.0, 500.0]
        result = jacchia77_model.calculate(alt_km=alts, Tinf_K=1000.0)

        assert result["T_local_K"].shape == (5,)
        assert result["N2_cm3"].shape == (5,)
        assert np.all(result["T_local_K"] > 0)
        assert np.all(result["N2_cm3"] > 0)

    @pytest.mark.requires_dll
    def test_calculate_array(self, jacchia77_model):
        alts = np.arange(90, 201, 10)
        result = jacchia77_model.calculate(alt_km=alts, Tinf_K=1000.0)

        assert result["T_local_K"].shape == alts.shape
        assert result["N2_cm3"].shape == alts.shape
        assert np.all(np.isfinite(result["T_local_K"]))
        assert np.all(np.isfinite(result["N2_cm3"]))

    @pytest.mark.requires_dll
    def test_different_Tinf(self, jacchia77_model):
        alt = 200.0
        for Tinf in [600.0, 800.0, 1000.0, 1200.0, 1500.0]:
            result = jacchia77_model.calculate(alt_km=alt, Tinf_K=Tinf)
            assert np.isfinite(result["T_local_K"])
            assert result["T_local_K"] > 0

    @pytest.mark.requires_dll
    def test_species_densities_sum(self, jacchia77_model):
        result = jacchia77_model.calculate(alt_km=200.0, Tinf_K=1000.0)
        species = ["N2_cm3", "O2_cm3", "O_cm3", "Ar_cm3", "He_cm3", "H_cm3"]
        total = sum(result[s] for s in species)
        # 允许小的数值误差
        assert abs(result["total_density_cm3"] - total) / result["total_density_cm3"] < 0.01

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import Jacchia77

        monkeypatch.chdir(tmp_path)
        model = Jacchia77()
        result = model.calculate(alt_km=100.0, Tinf_K=1000.0)
        assert isinstance(result["T_local_K"], float)
        assert result["T_local_K"] > 0
