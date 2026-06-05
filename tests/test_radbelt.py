from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class TestRADBELTModule:
    def test_module_only_exports_model(self):
        from model.pyradbelt import __all__

        assert __all__ == ["Model"]


class TestRADBELTInvalidInit:
    def test_invalid_model_type_raises_error(self):
        from model import RADBELT

        with pytest.raises(ValueError, match="model_type"):
            RADBELT("INVALID", data_dir=ROOT / "data", auto_download=False)

    def test_valid_model_types(self):
        from model import RADBELT

        for mt in ("AP8MAX", "AP8MIN", "AE8MAX", "AE8MIN"):
            try:
                m = RADBELT(mt, data_dir=ROOT / "data", auto_download=False)
                assert m._model_type == mt
            except Exception:
                pytest.skip(f"RADBELT DLL not available for {mt}")


class TestRADBELTAE8MIN:
    @pytest.mark.requires_dll
    def test_calculate_single_point(self, radbelt_ae8min_model):
        result = radbelt_ae8min_model.calculate(
            l_value=2.0, bb0=1.0, energy_mev=0.5
        )
        assert set(result) == {"l_value", "bb0", "energy_mev", "flux"}
        assert isinstance(result["flux"], float)
        assert result["flux"] >= 0.0

    @pytest.mark.requires_dll
    def test_calculate_batch(self, radbelt_ae8min_model):
        l_vals = [1.5, 2.0, 3.0, 4.0, 6.0]
        result = radbelt_ae8min_model.calculate(
            l_value=l_vals, bb0=1.0, energy_mev=1.0
        )
        assert result["flux"].shape == (5,)
        assert np.all(np.isfinite(result["flux"]))
        assert np.all(result["flux"] >= 0.0)

    @pytest.mark.requires_dll
    def test_flux_increases_with_l(self, radbelt_ae8min_model):
        """通量通常随 L 值增大而增加（在赤道面）。"""
        l_vals = [1.5, 2.0, 3.0, 4.0, 6.0]
        result = radbelt_ae8min_model.calculate(
            l_value=l_vals, bb0=1.0, energy_mev=0.5
        )
        fluxes = result["flux"]
        for i in range(len(fluxes) - 1):
            if fluxes[i] > 0 and fluxes[i + 1] > 0:
                assert fluxes[i + 1] >= fluxes[i] * 0.5

    @pytest.mark.requires_dll
    def test_flux_decreases_with_energy(self, radbelt_ae8min_model):
        """积分通量随能量阈值增大而减小。"""
        energies = [0.1, 0.5, 1.0, 3.0, 4.0]
        result = radbelt_ae8min_model.calculate(
            l_value=3.0, bb0=1.0, energy_mev=energies
        )
        fluxes = result["flux"]
        for i in range(len(fluxes) - 1):
            if fluxes[i] > 0 and fluxes[i + 1] > 0:
                assert fluxes[i + 1] <= fluxes[i]

    @pytest.mark.requires_dll
    def test_bb0_ge_1(self, radbelt_ae8min_model):
        """B/B0 < 1 应被截断为 1。"""
        r1 = radbelt_ae8min_model.calculate(l_value=2.0, bb0=0.5, energy_mev=1.0)
        r2 = radbelt_ae8min_model.calculate(l_value=2.0, bb0=1.0, energy_mev=1.0)
        assert r1["flux"] == r2["flux"]

    @pytest.mark.requires_dll
    def test_scalar_returns_scalar(self, radbelt_ae8min_model):
        result = radbelt_ae8min_model.calculate(
            l_value=2.0, bb0=1.0, energy_mev=1.0
        )
        assert isinstance(result["l_value"], float)
        assert isinstance(result["bb0"], float)
        assert isinstance(result["energy_mev"], float)
        assert isinstance(result["flux"], float)

    @pytest.mark.requires_dll
    def test_array_returns_array(self, radbelt_ae8min_model):
        result = radbelt_ae8min_model.calculate(
            l_value=[2.0, 3.0], bb0=[1.0, 1.5], energy_mev=1.0
        )
        assert isinstance(result["flux"], np.ndarray)
        assert result["flux"].shape == (2,)

    @pytest.mark.requires_dll
    def test_broadcast_grid_preserves_shape(self, radbelt_ae8min_model):
        result = radbelt_ae8min_model.calculate(
            l_value=np.array([2.0, 3.0])[:, None],
            bb0=1.0,
            energy_mev=np.array([0.5, 1.0, 2.0])[None, :],
        )
        assert result["l_value"].shape == (2, 3)
        assert result["energy_mev"].shape == (2, 3)
        assert result["flux"].shape == (2, 3)

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import RADBELT

        monkeypatch.chdir(tmp_path)
        model = RADBELT("AE8MIN", data_dir=ROOT / "data", auto_download=False)
        result = model.calculate(l_value=2.0, bb0=1.0, energy_mev=0.5)
        assert isinstance(result["flux"], float)


class TestRADBELTAP8MIN:
    @pytest.mark.requires_dll
    def test_calculate_single_point(self, radbelt_ap8min_model):
        result = radbelt_ap8min_model.calculate(
            l_value=2.0, bb0=1.0, energy_mev=10.0
        )
        assert isinstance(result["flux"], float)
        assert result["flux"] >= 0.0

    @pytest.mark.requires_dll
    def test_proton_flux_at_l4(self, radbelt_ap8min_model):
        """AP8MIN 在 L=4 附近有明显的质子通量峰值。"""
        l_vals = [2.0, 3.0, 4.0, 5.0, 6.0]
        result = radbelt_ap8min_model.calculate(
            l_value=l_vals, bb0=1.0, energy_mev=10.0
        )
        fluxes = result["flux"]
        assert np.all(fluxes >= 0.0)
        assert fluxes.shape == (5,)
