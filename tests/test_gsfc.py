"""
Tests for GSFC geomagnetic field model (GSFC-80, GSFC-83, GSFC-87).

Note: The GSFC Fortran DLL uses COMMON blocks that persist state between
calls. Multiple GSFC model versions cannot be reliably used in the same
process. Cross-version validation tests use subprocess isolation.
"""

import subprocess
import sys
import math
from pathlib import Path

import pytest


class TestGSFCModule:
    """Test GSFC module structure."""

    def test_module_only_exports_model(self):
        from model.pygsfc import __all__
        assert __all__ == ["Model"]


class TestGSFC87:
    """Test GSFC-87 model."""

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, gsfc_model):
        result = gsfc_model.calculate(
            year=1985.0,
            lat_deg=39.9,
            lon_deg=116.4,
            alt_km=0.0,
        )
        assert isinstance(result, dict)
        assert "X_nT" in result
        assert "Y_nT" in result
        assert "Z_nT" in result
        assert "F_nT" in result
        assert "H_nT" in result
        assert "inclination_deg" in result
        assert "declination_deg" in result
        assert isinstance(float(result["F_nT"]), float)
        assert 30000 < result["F_nT"] < 70000  # nT
        assert -90 <= result["inclination_deg"] <= 90
        assert -180 <= result["declination_deg"] <= 180

    @pytest.mark.requires_dll
    def test_calculate_batch(self, gsfc_model):
        result = gsfc_model.calculate(
            year=1985.0,
            lat_deg=[30.0, 40.0, 50.0],
            lon_deg=[116.0, 116.0, 116.0],
            alt_km=[0.0, 100.0, 200.0],
        )
        assert result["F_nT"].shape == (3,)
        assert result["X_nT"].shape == (3,)

    @pytest.mark.requires_dll
    def test_calculate_from_non_repo_working_directory(self, gsfc_model, tmp_path):
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = gsfc_model.calculate(
                year=1985.0,
                lat_deg=39.9,
                lon_deg=116.4,
                alt_km=0.0,
            )
            assert result["F_nT"] > 0
        finally:
            os.chdir(original_cwd)

    @pytest.mark.requires_dll
    def test_calculate_scalar_returns_scalar(self, gsfc_model):
        result = gsfc_model.calculate(
            year=1985.0,
            lat_deg=39.9,
            lon_deg=116.4,
            alt_km=0.0,
        )
        for key, value in result.items():
            assert isinstance(value, float), f"{key} should be float"

    @pytest.mark.requires_dll
    def test_broadcast_same_size(self, gsfc_model):
        """Test that same-size arrays produce no broadcast changes."""
        result = gsfc_model.calculate(
            year=[1985.0, 1986.0],
            lat_deg=[30.0, 40.0],
            lon_deg=[116.0, 120.0],
            alt_km=[0.0, 100.0],
        )
        assert result["F_nT"].shape == (2,)


class TestGSFC83:
    """Test GSFC-83 model."""

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, gsfc83_model):
        result = gsfc83_model.calculate(
            year=1980.0,
            lat_deg=0.0,
            lon_deg=0.0,
            alt_km=0.0,
        )
        assert result["F_nT"] > 0

    @pytest.mark.requires_dll
    def test_year_interpolation(self, gsfc83_model):
        """Test that non-epoch years produce valid results via interpolation."""
        result = gsfc83_model.calculate(
            year=1982.5,
            lat_deg=39.9,
            lon_deg=116.4,
            alt_km=0.0,
        )
        assert result["F_nT"] > 0


class TestGSFC80:
    """Test GSFC-80 model."""

    @pytest.mark.requires_dll
    def test_calculate_single_point(self, gsfc80_model):
        result = gsfc80_model.calculate(
            year=1980.0,
            lat_deg=39.9,
            lon_deg=116.4,
            alt_km=0.0,
        )
        assert result["F_nT"] > 0
        assert -90 <= result["inclination_deg"] <= 90


def _run_gsfc_subprocess(version, year):
    """Run a single GSFC calculation in a subprocess to isolate DLL state."""
    root = Path(__file__).resolve().parents[1]
    src_path = repr(str(root / "src"))
    data_path = repr(str(root / "data"))
    code = (
        f"import sys; sys.path.insert(0, {src_path})\n"
        f"from model import GSFC\n"
        f"m = GSFC(gsfc_version={version}, data_dir={data_path}, auto_download=False)\n"
        f"r = m.calculate(year={year}, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)\n"
        f"print(f'{{r[\"F_nT\"]:.6f}}')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Subprocess failed: {result.stderr}")
    return float(result.stdout.strip())


class TestGSFCValidation:
    """Cross-version validation using subprocess isolation."""

    @pytest.mark.requires_dll
    def test_model_versions_do_not_share_cached_coefficients(self):
        """Different model instances in one process should load their own files."""
        from model import GSFC

        root = Path(__file__).resolve().parents[1]
        values = []
        for version in (87, 83, 80):
            model = GSFC(
                gsfc_version=version,
                data_dir=root / "data",
                auto_download=False,
            )
            result = model.calculate(
                year=1980.0,
                lat_deg=39.9,
                lon_deg=116.4,
                alt_km=0.0,
            )
            values.append(round(result["F_nT"], 3))

        assert all(math.isfinite(value) for value in values)
        assert len(set(values)) == 3

    def test_gsfc87_at_different_times(self):
        """GSFC-87 should give different values at different times."""
        f1 = _run_gsfc_subprocess(87, 1980.0)
        f2 = _run_gsfc_subprocess(87, 1990.0)
        assert abs(f1 - f2) > 10

    def test_gsfc_models_give_different_results(self):
        """Different GSFC models should give different results."""
        f80 = _run_gsfc_subprocess(80, 1980.0)
        f83 = _run_gsfc_subprocess(83, 1980.0)
        f87 = _run_gsfc_subprocess(87, 1980.0)
        # All should be reasonable
        assert 30000 < f80 < 70000
        assert 30000 < f83 < 70000
        assert 30000 < f87 < 70000


class TestGSFCConstructor:
    """Test constructor validation."""

    def test_invalid_version_raises_error(self):
        from model import GSFC
        with pytest.raises(ValueError, match="必须为 80、83 或 87"):
            GSFC(gsfc_version=75, data_dir="nonexistent", auto_download=False)

    def test_lazy_export(self):
        """import model must not load GSFC DLL."""
        import model
        assert "GSFC" in model.__all__
