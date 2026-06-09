from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODEL_DATA = ROOT / "data"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def default_solar_params():
    return {
        "f107a": 100.0,
        "f107": 100.0,
    }


@pytest.fixture
def default_geo_params():
    return {
        "alt_km": 100.0,
        "lat_deg": 35.0,
        "lon_deg": 116.0,
    }


@pytest.fixture
def sample_iyd():
    return 2023196


@pytest.fixture
def msis2_model():
    try:
        from model import MSIS2

        return MSIS2(precision="single", data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"NRLMSIS-2.0 DLL not available: {exc}")


@pytest.fixture
def msis00_model():
    try:
        from model import MSIS00

        return MSIS00(data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"MSIS-00 DLL not available: {exc}")


@pytest.fixture
def hwm14_model():
    try:
        from model import HWM14

        return HWM14(data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"HWM14 DLL not available: {exc}")


@pytest.fixture
def hwm93_model():
    try:
        from model import HWM93

        return HWM93(data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"HWM93 DLL not available: {exc}")


@pytest.fixture
def aurora_model():
    try:
        from model import AuroraOval

        return AuroraOval()
    except Exception as exc:
        pytest.skip(f"Aurora Oval DLL not available: {exc}")


@pytest.fixture
def igrf_model():
    try:
        from model import IGRF

        return IGRF(igrf_version=14, data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"IGRF DLL not available: {exc}")


@pytest.fixture
def igrf13_model():
    try:
        from model import IGRF

        return IGRF(igrf_version=13, data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"IGRF-13 DLL not available: {exc}")


@pytest.fixture
def gsfc_model():
    try:
        from model import GSFC

        return GSFC(gsfc_version=87, data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"GSFC DLL not available: {exc}")


@pytest.fixture
def gsfc83_model():
    try:
        from model import GSFC

        return GSFC(gsfc_version=83, data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"GSFC-83 DLL not available: {exc}")


@pytest.fixture
def gsfc80_model():
    try:
        from model import GSFC

        return GSFC(gsfc_version=80, data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"GSFC-80 DLL not available: {exc}")


@pytest.fixture
def cira86_model():
    try:
        from model import CIRA86

        return CIRA86(data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"CIRA-86 data not available: {exc}")


@pytest.fixture
def msis86_model():
    try:
        from model import MSIS86

        return MSIS86(data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"MSIS-86 DLL not available: {exc}")


@pytest.fixture
def msise90_model():
    try:
        from model import MSISE90

        return MSISE90()
    except Exception as exc:
        pytest.skip(f"MSISE-90 DLL not available: {exc}")


@pytest.fixture
def jacchia77_model():
    try:
        from model import Jacchia77

        return Jacchia77()
    except Exception as exc:
        pytest.skip(f"Jacchia 77 DLL not available: {exc}")


@pytest.fixture
def met_model():
    try:
        from model import MET

        return MET()
    except Exception as exc:
        pytest.skip(f"MET DLL not available: {exc}")


@pytest.fixture
def chiu_model():
    try:
        from model import Chiu

        return Chiu()
    except Exception as exc:
        pytest.skip(f"Chiu DLL not available: {exc}")


@pytest.fixture
def tsyganenko_t89_model():
    try:
        from model import Tsyganenko

        return Tsyganenko(model_version="T89")
    except Exception as exc:
        pytest.skip(f"Tsyganenko T89 DLL not available: {exc}")


@pytest.fixture
def tsyganenko_t96_model():
    try:
        from model import Tsyganenko

        return Tsyganenko(model_version="T96")
    except Exception as exc:
        pytest.skip(f"Tsyganenko T96 DLL not available: {exc}")


@pytest.fixture
def tsyganenko_t01_model():
    try:
        from model import Tsyganenko

        return Tsyganenko(model_version="T01")
    except Exception as exc:
        pytest.skip(f"Tsyganenko T01 DLL not available: {exc}")


@pytest.fixture
def tsyganenko_ts04_model():
    try:
        from model import Tsyganenko

        return Tsyganenko(model_version="TS04")
    except Exception as exc:
        pytest.skip(f"Tsyganenko TS04 DLL not available: {exc}")


@pytest.fixture
def solpro_model():
    try:
        from model import SOLPRO

        return SOLPRO()
    except Exception as exc:
        pytest.skip(f"SOLPRO DLL not available: {exc}")


@pytest.fixture
def radbelt_ae8min_model():
    try:
        from model import RADBELT

        return RADBELT("AE8MIN", data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"RADBELT AE8MIN DLL not available: {exc}")


@pytest.fixture
def radbelt_ap8min_model():
    try:
        from model import RADBELT

        return RADBELT("AP8MIN", data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"RADBELT AP8MIN DLL not available: {exc}")


@pytest.fixture
def shieldose_al_model():
    try:
        from model import SHIELDOSE

        return SHIELDOSE(detector=1, unit=2, data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"SHIELDOSE Al DLL not available: {exc}")


@pytest.fixture
def shieldose_si_model():
    try:
        from model import SHIELDOSE

        return SHIELDOSE(detector=3, unit=2, data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"SHIELDOSE Si DLL not available: {exc}")


@pytest.fixture
def sofip_ap8max_model():
    try:
        from model import SOFIP

        return SOFIP("AP8MAX", data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"SOFIP AP8MAX DLL not available: {exc}")


@pytest.fixture
def sofip_ae8min_model():
    try:
        from model import SOFIP

        return SOFIP("AE8MIN", data_dir=MODEL_DATA, auto_download=False)
    except Exception as exc:
        pytest.skip(f"SOFIP AE8MIN DLL not available: {exc}")


@pytest.fixture
def cutoff_model():
    try:
        from model import CutoffRigidity

        return CutoffRigidity()
    except Exception as exc:
        pytest.skip(f"Cutoff Rigidity DLL not available: {exc}")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_dll: marks tests that require compiled DLLs"
    )
