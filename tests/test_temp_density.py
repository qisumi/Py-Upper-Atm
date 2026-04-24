from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODEL_DATA = ROOT / "data"


class TestModelPackage:
    def test_import_model_is_lazy(self):
        sys.modules.pop("model", None)
        sys.modules.pop("utils.model_data", None)
        for module_name in list(sys.modules):
            if module_name.startswith("model.py"):
                sys.modules.pop(module_name, None)

        model = importlib.import_module("model")

        assert model.__all__ == ["MSIS2", "MSIS00", "HWM14", "HWM93"]
        assert "model.pymsis2" not in sys.modules
        assert "model.pymsis00" not in sys.modules
        assert "model.pyhwm14" not in sys.modules
        assert "model.pyhwm93" not in sys.modules
        assert "utils.model_data" not in sys.modules

    def test_old_top_level_exports_are_removed(self):
        with pytest.raises(ImportError):
            exec("from model import NRLMSIS2", {})
        with pytest.raises(ImportError):
            exec("from model import gtd7", {})
        with pytest.raises(ImportError):
            exec("from model import hwm14_eval", {})
        with pytest.raises(ImportError):
            exec("from model import cached_call", {})

    def test_model_modules_only_export_model(self):
        from model.pymsis2 import __all__ as msis2_exports
        from model.pymsis00 import __all__ as msis00_exports

        assert msis2_exports == ["Model"]
        assert msis00_exports == ["Model"]


class TestMSIS2:
    @pytest.mark.requires_dll
    def test_calculate_single_point(
        self, msis2_model, default_geo_params, default_solar_params
    ):
        result = msis2_model.calculate(
            day=196.0,
            utsec=45000.0,
            **default_geo_params,
            **default_solar_params,
        )

        assert set(result) == {"alt_km", "T_local_K", "T_exo_K", "densities"}
        assert result["alt_km"] == default_geo_params["alt_km"]
        assert result["densities"].shape == (10,)
        assert 100 < result["T_local_K"] < 500
        assert 500 < result["T_exo_K"] < 2000

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path, default_geo_params, default_solar_params
    ):
        from model import MSIS2

        monkeypatch.chdir(tmp_path)
        model = MSIS2(precision="single", data_dir=MODEL_DATA, auto_download=False)
        result = model.calculate(
            day=196.0,
            utsec=45000.0,
            **default_geo_params,
            **default_solar_params,
        )

        assert result["densities"].shape == (10,)

    @pytest.mark.requires_dll
    def test_calculate_batch(self, msis2_model, default_solar_params):
        result = msis2_model.calculate(
            day=196.0,
            utsec=45000.0,
            alt_km=[100.0, 200.0, 300.0],
            lat_deg=35.0,
            lon_deg=116.0,
            **default_solar_params,
        )

        np.testing.assert_allclose(result["alt_km"], [100.0, 200.0, 300.0])
        assert result["T_local_K"].shape == (3,)
        assert result["densities"].shape == (3, 10)

    @pytest.mark.requires_dll
    def test_invalid_ap7_raises_error(
        self, msis2_model, default_geo_params, default_solar_params
    ):
        with pytest.raises(ValueError, match="ap7"):
            msis2_model.calculate(
                day=196.0,
                utsec=45000.0,
                ap7=[4.0, 4.0],
                **default_geo_params,
                **default_solar_params,
            )


class TestMSIS00:
    @pytest.mark.requires_dll
    def test_calculate_single_point(self, msis00_model):
        result = msis00_model.calculate(
            iyd=2023196,
            sec=45000.0,
            alt_km=100.0,
            lat_deg=35.0,
            lon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
        )

        assert set(result) == {"alt_km", "T_local_K", "T_exo_K", "densities"}
        assert result["densities"].shape == (9,)
        assert 100 < result["T_local_K"] < 500

    @pytest.mark.requires_dll
    def test_calculate_batch(self, msis00_model):
        result = msis00_model.calculate(
            iyd=2023196,
            sec=45000.0,
            alt_km=[100.0, 200.0, 300.0],
            lat_deg=35.0,
            lon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
        )

        np.testing.assert_allclose(result["alt_km"], [100.0, 200.0, 300.0])
        assert result["T_local_K"].shape == (3,)
        assert result["densities"].shape == (3, 9)

    @pytest.mark.requires_dll
    def test_invalid_ap7_raises_error(self, msis00_model):
        with pytest.raises(ValueError, match="ap7"):
            msis00_model.calculate(
                iyd=2023196,
                sec=45000.0,
                alt_km=100.0,
                lat_deg=35.0,
                lon_deg=116.0,
                stl_hours=12.0,
                f107a=100.0,
                f107=100.0,
                ap7=[4.0, 4.0],
            )
