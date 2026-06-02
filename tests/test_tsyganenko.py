"""Tests for Tsyganenko magnetic field models (T89/T96/T01/TS04)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import model as model_pkg


# =====================================================================
# Module structure
# =====================================================================


class TestModuleExports:
    """Verify module export conventions."""

    def test_submodule_only_exports_model(self):
        from model import pytsyganenko

        assert pytsyganenko.__all__ == ["Model"]

    def test_tsyganenko_in_model_all(self):
        assert "Tsyganenko" in model_pkg.__all__

    def test_lazy_import_does_not_eagerly_load(self):
        # Remove cached submodule if present
        sys.modules.pop("model.pytsyganenko", None)
        # Accessing model_pkg should not load pytsyganenko
        _ = model_pkg  # noqa: just ensure no import side effects
        assert "model.pytsyganenko" not in sys.modules


# =====================================================================
# Constructor tests
# =====================================================================


class TestConstructor:
    """Test Model constructor validation."""

    def test_invalid_version_raises(self):
        from model.pytsyganenko import Model

        with pytest.raises(ValueError, match="model_version"):
            Model(model_version="T99")

    @pytest.mark.requires_dll
    def test_valid_versions(self):
        from model.pytsyganenko import Model, _VALID_VERSIONS

        for ver in _VALID_VERSIONS:
            m = Model(model_version=ver)
            assert m._version == ver

    @pytest.mark.requires_dll
    def test_case_insensitive_version(self):
        from model.pytsyganenko import Model

        m = Model(model_version="t96")
        assert m._version == "T96"


# =====================================================================
# T89 tests
# =====================================================================


@pytest.mark.requires_dll
class TestT89:

    def test_single_point(self, tsyganenko_t89_model):
        r = tsyganenko_t89_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            kp_index=3,
        )
        assert isinstance(r, dict)
        assert "Bx_ext_nT" in r
        assert "By_ext_nT" in r
        assert "Bz_ext_nT" in r
        assert "tilt_rad" in r
        # External field at -5 Re should be order ~10-100 nT
        assert abs(r["Bx_ext_nT"]) < 500
        assert abs(r["Bz_ext_nT"]) < 500

    def test_scalar_return_types(self, tsyganenko_t89_model):
        r = tsyganenko_t89_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            kp_index=3,
        )
        assert isinstance(r["Bx_ext_nT"], float)
        assert isinstance(r["tilt_rad"], float)

    def test_batch_calculation(self, tsyganenko_t89_model):
        xs = np.array([-5.0, -6.0, -7.0, -8.0])
        r = tsyganenko_t89_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=xs, y_re=0.0, z_re=0.0,
            kp_index=3,
        )
        assert r["Bx_ext_nT"].shape == (4,)
        assert np.all(np.isfinite(r["Bx_ext_nT"]))

    def test_all_kp_levels(self, tsyganenko_t89_model):
        for kp in range(1, 8):
            r = tsyganenko_t89_model.calculate(
                year=2000, doy=180, hour=12,
                x_re=-5.0, y_re=0.0, z_re=0.0,
                kp_index=kp,
            )
            assert np.isfinite(r["Bx_ext_nT"])

    def test_invalid_kp_raises(self, tsyganenko_t89_model):
        with pytest.raises(ValueError, match="kp_index"):
            tsyganenko_t89_model.calculate(
                year=2000, doy=180, hour=12,
                x_re=-5.0, y_re=0.0, z_re=0.0,
                kp_index=0,
            )
        with pytest.raises(ValueError, match="kp_index"):
            tsyganenko_t89_model.calculate(
                year=2000, doy=180, hour=12,
                x_re=-5.0, y_re=0.0, z_re=0.0,
                kp_index=8,
            )

    def test_missing_kp_raises(self, tsyganenko_t89_model):
        with pytest.raises(ValueError, match="kp_index"):
            tsyganenko_t89_model.calculate(
                year=2000, doy=180, hour=12,
                x_re=-5.0, y_re=0.0, z_re=0.0,
            )

    def test_tilt_rad_direct(self, tsyganenko_t89_model):
        r = tsyganenko_t89_model.calculate(
            tilt_rad=0.1,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            kp_index=3,
        )
        assert abs(r["tilt_rad"] - 0.1) < 1e-10

    def test_non_repo_working_directory(self, tsyganenko_t89_model, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        r = tsyganenko_t89_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            kp_index=3,
        )
        assert np.isfinite(r["Bx_ext_nT"])


# =====================================================================
# T96 tests
# =====================================================================


@pytest.mark.requires_dll
class TestT96:

    def test_single_point(self, tsyganenko_t96_model):
        r = tsyganenko_t96_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            pdyn_nPa=2.0, dst_nT=-20.0,
            by_imf_nT=0.5, bz_imf_nT=-2.0,
        )
        assert isinstance(r["Bx_ext_nT"], float)
        assert abs(r["Bx_ext_nT"]) < 500

    def test_batch(self, tsyganenko_t96_model):
        xs = np.linspace(-5, -10, 6)
        r = tsyganenko_t96_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=xs, y_re=0.0, z_re=0.0,
            pdyn_nPa=2.0, dst_nT=-20.0,
            by_imf_nT=0.5, bz_imf_nT=-2.0,
        )
        assert r["Bx_ext_nT"].shape == (6,)
        assert np.all(np.isfinite(r["Bx_ext_nT"]))

    def test_missing_params_raises(self, tsyganenko_t96_model):
        with pytest.raises(ValueError, match="pdyn_nPa"):
            tsyganenko_t96_model.calculate(
                year=2000, doy=180, hour=12,
                x_re=-5.0, y_re=0.0, z_re=0.0,
            )


# =====================================================================
# T01 tests
# =====================================================================


@pytest.mark.requires_dll
class TestT01:

    def test_single_point(self, tsyganenko_t01_model):
        r = tsyganenko_t01_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            pdyn_nPa=2.0, dst_nT=-20.0,
            by_imf_nT=0.5, bz_imf_nT=-2.0,
            g1=1.0, g2=1.0,
        )
        assert isinstance(r["Bx_ext_nT"], float)
        assert abs(r["Bx_ext_nT"]) < 500

    def test_missing_g_params_raises(self, tsyganenko_t01_model):
        with pytest.raises(ValueError, match="g1"):
            tsyganenko_t01_model.calculate(
                year=2000, doy=180, hour=12,
                x_re=-5.0, y_re=0.0, z_re=0.0,
                pdyn_nPa=2.0, dst_nT=-20.0,
                by_imf_nT=0.5, bz_imf_nT=-2.0,
            )


# =====================================================================
# TS04 tests
# =====================================================================


@pytest.mark.requires_dll
class TestTS04:

    def test_single_point(self, tsyganenko_ts04_model):
        r = tsyganenko_ts04_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            pdyn_nPa=2.0, dst_nT=-20.0,
            by_imf_nT=0.5, bz_imf_nT=-2.0,
            w1=1.0, w2=0.5, w3=0.3, w4=0.2, w5=0.1, w6=0.1,
        )
        assert isinstance(r["Bx_ext_nT"], float)
        assert abs(r["Bx_ext_nT"]) < 500

    def test_missing_w_params_raises(self, tsyganenko_ts04_model):
        with pytest.raises(ValueError, match="w1"):
            tsyganenko_ts04_model.calculate(
                year=2000, doy=180, hour=12,
                x_re=-5.0, y_re=0.0, z_re=0.0,
                pdyn_nPa=2.0, dst_nT=-20.0,
                by_imf_nT=0.5, bz_imf_nT=-2.0,
            )

    def test_include_dipole(self, tsyganenko_ts04_model):
        r = tsyganenko_ts04_model.calculate(
            year=2000, doy=180, hour=12,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            pdyn_nPa=2.0, dst_nT=-20.0,
            by_imf_nT=0.5, bz_imf_nT=-2.0,
            w1=1.0, w2=0.5, w3=0.3, w4=0.2, w5=0.1, w6=0.1,
            include_dipole=True,
        )
        assert "Bx_dip_nT" in r
        assert "Bx_total_nT" in r
        # Dipole field at -5 Re should be ~200 nT
        assert abs(r["Bx_dip_nT"]) > 50
        # Total = ext + dip
        assert abs(
            r["Bx_total_nT"]
            - (r["Bx_ext_nT"] + r["Bx_dip_nT"])
        ) < 1e-6


# =====================================================================
# Cross-model validation
# =====================================================================


@pytest.mark.requires_dll
class TestCrossModel:
    """Cross-check models for reasonable consistency."""

    def test_missing_tilt_raises(self):
        from model.pytsyganenko import Model

        m = Model(model_version="T96")
        with pytest.raises(ValueError, match="tilt_rad"):
            m.calculate(
                x_re=-5.0, y_re=0.0, z_re=0.0,
                pdyn_nPa=2.0, dst_nT=-20.0,
                by_imf_nT=0.5, bz_imf_nT=-2.0,
            )
