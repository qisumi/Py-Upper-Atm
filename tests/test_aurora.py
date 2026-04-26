from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


class TestAuroraOval:
    def test_module_only_exports_model(self):
        from model.pyaurora import __all__

        assert __all__ == ["Model"]

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, aurora_model):
        result = aurora_model.calculate(mlt_hours=12.0, activity_level=3)

        assert set(result) == {
            "mlt_hours",
            "activity_level",
            "poleward_boundary_deg",
            "equatorward_boundary_deg",
        }
        assert isinstance(result["poleward_boundary_deg"], float)
        assert isinstance(result["equatorward_boundary_deg"], float)
        assert 50 < result["poleward_boundary_deg"] < 90
        assert 50 < result["equatorward_boundary_deg"] < 90
        assert result["poleward_boundary_deg"] > result["equatorward_boundary_deg"]

    @pytest.mark.requires_dll
    def test_calculate_batch(self, aurora_model):
        mlt = [0.0, 6.0, 12.0, 18.0]
        levels = [0, 1, 2, 3]
        result = aurora_model.calculate(mlt_hours=mlt, activity_level=levels)

        assert result["poleward_boundary_deg"].shape == (4,)
        assert result["equatorward_boundary_deg"].shape == (4,)
        assert np.all(np.isfinite(result["poleward_boundary_deg"]))
        assert np.all(np.isfinite(result["equatorward_boundary_deg"]))

    @pytest.mark.requires_dll
    def test_all_activity_levels(self, aurora_model):
        for level in range(7):
            result = aurora_model.calculate(mlt_hours=12.0, activity_level=level)
            assert 50 < result["poleward_boundary_deg"] < 90
            assert 50 < result["equatorward_boundary_deg"] < 90

    @pytest.mark.requires_dll
    def test_invalid_activity_level_raises_error(self, aurora_model):
        with pytest.raises(ValueError, match="activity_level"):
            aurora_model.calculate(mlt_hours=12.0, activity_level=7)

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(
        self, monkeypatch, tmp_path
    ):
        from model import AuroraOval

        monkeypatch.chdir(tmp_path)
        model = AuroraOval()
        result = model.calculate(mlt_hours=12.0, activity_level=3)
        assert isinstance(result["poleward_boundary_deg"], float)
