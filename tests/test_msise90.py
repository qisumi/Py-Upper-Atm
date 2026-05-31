"""MSISE-90 模型测试。"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODEL_DATA = ROOT / "data"


class TestMSISE90Module:
    def test_msise90_exported_in_model_all(self):
        import model

        assert "MSISE90" in model.__all__

    def test_msise90_module_only_exports_model(self):
        from model.pymsise90 import __all__ as msise90_exports

        assert msise90_exports == ["Model"]

    def test_msise90_lazy_import(self):
        sys.modules.pop("model", None)
        sys.modules.pop("model.pymsise90", None)
        for module_name in list(sys.modules):
            if module_name.startswith("model.py"):
                sys.modules.pop(module_name, None)

        import model

        assert "model.pymsise90" not in sys.modules
        _ = model.MSISE90
        assert "model.pymsise90" in sys.modules


class TestMSISE90:
    @pytest.mark.requires_dll
    def test_calculate_single_point(self, msise90_model):
        result = msise90_model.calculate(
            iyd=1990172,
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
        assert result["T_local_K"] > 0
        assert result["T_exo_K"] > 0

    @pytest.mark.requires_dll
    def test_calculate_surface(self, msise90_model):
        """MSISE-90 可计算地面高度。"""
        result = msise90_model.calculate(
            iyd=1990172,
            sec=29000.0,
            alt_km=0.0,
            lat_deg=60.0,
            lon_deg=-70.0,
            stl_hours=16.0,
            f107a=150.0,
            f107=150.0,
        )

        assert set(result) == {"alt_km", "T_local_K", "T_exo_K", "densities"}
        assert result["alt_km"] == 0.0
        assert result["densities"].shape == (8,)
        assert result["T_local_K"] > 0

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import MSISE90

        monkeypatch.chdir(tmp_path)
        model = MSISE90()
        result = model.calculate(
            iyd=1990172,
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
    def test_calculate_batch(self, msise90_model):
        result = msise90_model.calculate(
            iyd=1990172,
            sec=29000.0,
            alt_km=[0.0, 100.0, 200.0, 300.0],
            lat_deg=60.0,
            lon_deg=-70.0,
            stl_hours=16.0,
            f107a=150.0,
            f107=150.0,
        )

        np.testing.assert_allclose(result["alt_km"], [0.0, 100.0, 200.0, 300.0])
        assert result["T_local_K"].shape == (4,)
        assert result["T_exo_K"].shape == (4,)
        assert result["densities"].shape == (4, 8)

    @pytest.mark.requires_dll
    def test_invalid_ap7_raises_error(self, msise90_model):
        with pytest.raises(ValueError, match="ap7"):
            msise90_model.calculate(
                iyd=1990172,
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
    def test_scalar_input_returns_scalar(self, msise90_model):
        result = msise90_model.calculate(
            iyd=1990172,
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
    def test_mass_parameter(self, msise90_model):
        result = msise90_model.calculate(
            iyd=1990172,
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
