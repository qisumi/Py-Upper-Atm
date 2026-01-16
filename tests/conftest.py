from __future__ import annotations

import pytest
from datetime import datetime
from typing import Optional


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
def sample_datetime():
    return datetime(2023, 7, 15, 12, 30, 0)


@pytest.fixture
def sample_iyd():
    return 2023196


@pytest.fixture
def sample_day():
    return 196.0


@pytest.fixture
def sample_utsec():
    return 45000.0


@pytest.fixture
def temp_density_model_msis2():
    try:
        from model import TempDensityModel

        return TempDensityModel(model_version="msis2")
    except (ImportError, RuntimeError):
        pytest.skip("MSIS-2.0 DLL not available")


@pytest.fixture
def temp_density_model_msis00():
    try:
        from model import TempDensityModel

        return TempDensityModel(model_version="msis00")
    except (ImportError, RuntimeError):
        pytest.skip("MSIS-00 DLL not available")


@pytest.fixture
def wind_model_hwm14():
    try:
        from model import WindModel

        return WindModel(model_version="hwm14")
    except (ImportError, RuntimeError):
        pytest.skip("HWM14 DLL not available")


@pytest.fixture
def wind_model_hwm93():
    try:
        from model import WindModel

        return WindModel(model_version="hwm93")
    except (ImportError, RuntimeError):
        pytest.skip("HWM93 DLL not available")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_dll: marks tests that require compiled DLLs"
    )
