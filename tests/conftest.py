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


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_dll: marks tests that require compiled DLLs"
    )
