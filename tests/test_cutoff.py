from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class TestCutoffModule:
    def test_module_only_exports_model(self):
        from model.pycutoff import __all__

        assert __all__ == ["Model"]

    def test_model_only_exposes_calculate(self):
        from model.pycutoff import Model

        public_methods = sorted(
            name for name, value in vars(Model).items()
            if callable(value) and not name.startswith("_")
        )
        assert public_methods == ["calculate"]

    def test_lazy_export(self):
        import model

        assert "CutoffRigidity" in model.__all__


class TestCutoffSingleTrajectory:
    @pytest.mark.requires_dll
    def test_allowed_trajectory_midlatitude(self, cutoff_model):
        """Mid-latitude, moderate rigidity should be allowed."""
        result = cutoff_model.calculate(
            lat_deg=40.0,
            lon_deg=0.0,
            rigidity_gv=10.0,
            zenith_deg=0.0,
            azimuth_deg=0.0,
        )
        assert result["rigidity_gv"] == 10.0
        assert result["result_code"] == 1
        assert result["fate"] == "allowed"
        assert isinstance(result["asymptotic_latitude_deg"], float)
        assert isinstance(result["asymptotic_longitude_deg"], float)
        assert isinstance(result["path_length_re"], float)

    @pytest.mark.requires_dll
    def test_single_point_returns_scalar(self, cutoff_model):
        result = cutoff_model.calculate(
            lat_deg=0.0,
            lon_deg=0.0,
            rigidity_gv=15.0,
        )
        assert isinstance(result["rigidity_gv"], float)
        assert isinstance(result["result_code"], int)
        assert isinstance(result["asymptotic_latitude_deg"], float)
        assert isinstance(result["path_length_re"], float)

    @pytest.mark.requires_dll
    def test_batch_single_trajectory_shapes(self, cutoff_model):
        result = cutoff_model.calculate(
            lat_deg=np.array([0.0, 40.0]),
            lon_deg=0.0,
            rigidity_gv=np.array([15.0, 10.0]),
        )
        assert result["rigidity_gv"].shape == (2,)
        assert result["result_code"].shape == (2,)
        assert result["fate"].shape == (2,)
        assert result["asymptotic_latitude_deg"].shape == (2,)
        assert result["asymptotic_longitude_deg"].shape == (2,)
        assert result["path_length_re"].shape == (2,)

    @pytest.mark.requires_dll
    def test_reentrant_trajectory_low_rigidity(self, cutoff_model):
        """Very low rigidity at high latitude should be re-entrant."""
        result = cutoff_model.calculate(
            lat_deg=60.0,
            lon_deg=0.0,
            rigidity_gv=0.1,
        )
        assert result["result_code"] in (-1, 0, 1)
        assert result["fate"] in ("allowed", "failed", "reentrant")


class TestCutoffScan:
    @pytest.mark.requires_dll
    def test_scan_finds_cutoff(self, cutoff_model):
        result = cutoff_model.calculate(
            lat_deg=40.0,
            lon_deg=0.0,
            zenith_deg=0.0,
            azimuth_deg=0.0,
            start_rigidity_gv=20.0,
            delta_rigidity_mv=100.0,
            max_trajectories=300,
        )
        assert "cutoff_rigidity_gv" in result
        assert "n_trajectories_computed" in result
        assert result["n_trajectories_computed"] > 0
        assert isinstance(result["rigidity_gv"], np.ndarray)
        assert isinstance(result["trajectory_results"], np.ndarray)

    @pytest.mark.requires_dll
    def test_scan_arrays_shape(self, cutoff_model):
        result = cutoff_model.calculate(
            lat_deg=0.0,
            lon_deg=0.0,
            start_rigidity_gv=15.0,
            delta_rigidity_mv=100.0,
            max_trajectories=200,
        )
        n = result["n_trajectories_computed"]
        assert result["rigidity_gv"].shape == (n,)
        assert result["trajectory_results"].shape == (n,)

    @pytest.mark.requires_dll
    def test_scan_cutoff_reasonable_range(self, cutoff_model):
        """Equatorial cutoff should be around 15-17 GV."""
        result = cutoff_model.calculate(
            lat_deg=0.0,
            lon_deg=0.0,
            start_rigidity_gv=20.0,
            delta_rigidity_mv=50.0,
            max_trajectories=500,
        )
        if result["cutoff_rigidity_gv"] > 0:
            assert 5.0 < result["cutoff_rigidity_gv"] < 20.0


class TestCutoffConstructor:
    @pytest.mark.requires_dll
    def test_invalid_lat_raises_error(self, cutoff_model):
        with pytest.raises(ValueError, match="lat_deg"):
            cutoff_model.calculate(lat_deg=91.0, lon_deg=0.0, rigidity_gv=5.0)

    @pytest.mark.requires_dll
    def test_invalid_lon_raises_error(self, cutoff_model):
        with pytest.raises(ValueError, match="lon_deg"):
            cutoff_model.calculate(lat_deg=0.0, lon_deg=400.0, rigidity_gv=5.0)

    @pytest.mark.requires_dll
    def test_invalid_zenith_raises_error(self, cutoff_model):
        with pytest.raises(ValueError, match="zenith_deg"):
            cutoff_model.calculate(
                lat_deg=0.0, lon_deg=0.0, rigidity_gv=5.0, zenith_deg=200.0,
            )

    @pytest.mark.requires_dll
    def test_invalid_rigidity_raises_error(self, cutoff_model):
        with pytest.raises(ValueError, match="rigidity_gv"):
            cutoff_model.calculate(lat_deg=0.0, lon_deg=0.0, rigidity_gv=-1.0)

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import CutoffRigidity

        monkeypatch.chdir(tmp_path)
        model = CutoffRigidity()
        result = model.calculate(
            lat_deg=0.0,
            lon_deg=0.0,
            rigidity_gv=10.0,
        )
        assert isinstance(result["result_code"], int)
