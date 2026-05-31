"""MSIS-86 模型测试。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODEL_DATA = ROOT / "data"


class TestMSIS86Module:
    def test_msis86_exported_in_model_all(self):
        import model

        assert "MSIS86" in model.__all__

    def test_msis86_module_only_exports_model(self):
        from model.pymsis86 import __all__ as msis86_exports

        assert msis86_exports == ["Model"]

    def test_msis86_lazy_import(self):
        sys.modules.pop("model", None)
        sys.modules.pop("model.pymsis86", None)
        for module_name in list(sys.modules):
            if module_name.startswith("model.py"):
                sys.modules.pop(module_name, None)

        import model

        assert "model.pymsis86" not in sys.modules
        _ = model.MSIS86
        assert "model.pymsis86" in sys.modules


class TestMSIS86:
    @pytest.mark.requires_dll
    def test_calculate_single_point(self, msis86_model):
        result = msis86_model.calculate(
            iyd=1987172,
            sec=29000.0,
            alt_km=400.0,
            lat_deg=60.0,
            lon_deg=-70.0,
            stl_hours=16.0,
            f107a=150.0,
            f107=150.0,
        )

        assert set(result) == {"alt_km", "T_local_K", "T_exo_K", "densities"}
        assert result["alt_km"] == 400.0
        assert result["densities"].shape == (8,)
        assert 1000.0 < result["T_local_K"] < 1500.0
        assert 1000.0 < result["T_exo_K"] < 1500.0
        np.testing.assert_allclose(result["T_exo_K"], 1277.3132, rtol=1e-5)
        np.testing.assert_allclose(result["T_local_K"], 1270.0803, rtol=1e-5)
        np.testing.assert_allclose(
            result["densities"],
            [
                6.67590625e05,
                1.08759880e08,
                1.86693160e07,
                6.72686625e05,
                4.22998145e03,
                3.88077335e-15,
                3.49830469e04,
                3.60827025e06,
            ],
            rtol=1e-5,
        )

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import MSIS86

        monkeypatch.chdir(tmp_path)
        model = MSIS86(data_dir=MODEL_DATA, auto_download=False)
        result = model.calculate(
            iyd=1987172,
            sec=29000.0,
            alt_km=400.0,
            lat_deg=60.0,
            lon_deg=-70.0,
            stl_hours=16.0,
            f107a=150.0,
            f107=150.0,
        )

        assert result["densities"].shape == (8,)

    @pytest.mark.requires_dll
    def test_calculate_batch(self, msis86_model):
        result = msis86_model.calculate(
            iyd=1987172,
            sec=29000.0,
            alt_km=[100.0, 200.0, 300.0],
            lat_deg=60.0,
            lon_deg=-70.0,
            stl_hours=16.0,
            f107a=150.0,
            f107=150.0,
        )

        np.testing.assert_allclose(result["alt_km"], [100.0, 200.0, 300.0])
        assert result["T_local_K"].shape == (3,)
        assert result["T_exo_K"].shape == (3,)
        assert result["densities"].shape == (3, 8)

    @pytest.mark.requires_dll
    def test_invalid_ap7_raises_error(self, msis86_model):
        with pytest.raises(ValueError, match="ap7"):
            msis86_model.calculate(
                iyd=1987172,
                sec=29000.0,
                alt_km=400.0,
                lat_deg=60.0,
                lon_deg=-70.0,
                stl_hours=16.0,
                f107a=150.0,
                f107=150.0,
                ap7=[4.0, 4.0],
            )

    @pytest.mark.requires_dll
    def test_scalar_input_returns_scalar(self, msis86_model):
        result = msis86_model.calculate(
            iyd=1987172,
            sec=29000.0,
            alt_km=200.0,
            lat_deg=60.0,
            lon_deg=-70.0,
            stl_hours=16.0,
            f107a=150.0,
            f107=150.0,
        )

        assert isinstance(result["alt_km"], float)
        assert isinstance(result["T_local_K"], float)
        assert isinstance(result["T_exo_K"], float)
        assert result["densities"].shape == (8,)

    @pytest.mark.requires_dll
    def test_mass_parameter(self, msis86_model):
        result = msis86_model.calculate(
            iyd=1987172,
            sec=29000.0,
            alt_km=200.0,
            lat_deg=60.0,
            lon_deg=-70.0,
            stl_hours=16.0,
            f107a=150.0,
            f107=150.0,
            mass=0,
        )

        # mass=0 only computes temperature, densities should be zero
        assert result["T_exo_K"] > 0
