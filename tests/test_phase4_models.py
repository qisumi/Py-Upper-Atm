from __future__ import annotations

import importlib
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def test_new_modules_export_only_model():
    for module_name in (
        "pyaeeuv", "pyeuv91", "pyeuvac", "pyphotoelectron",
        "pypvionosphere", "pypvthermosphere", "pyexospherich",
    ):
        module = importlib.import_module(f"model.{module_name}")
        assert module.__all__ == ["Model"]


def test_aeeuv_reads_all_reference_spectra_from_non_repo_cwd(monkeypatch, tmp_path):
    from model import AEEUV

    monkeypatch.chdir(tmp_path)
    model = AEEUV(data_dir=DATA, auto_download=False)
    for name in ("r74113", "f74113", "f76ref", "sc21refw"):
        result = model.calculate(spectrum=name)
        assert result["spectrum"] == name
        assert result["wavelength_angstrom"].ndim == 1
        assert result["wavelength_angstrom"].shape == result["photon_flux_m2_s"].shape
        assert np.all(np.isfinite(result["photon_flux_m2_s"]))
    with pytest.raises(ValueError, match="spectrum"):
        model.calculate(spectrum="solar2000")


@pytest.mark.requires_dll
def test_euvac_reference_and_batch_values():
    from model import EUVAC

    model = EUVAC()
    minimum = model.calculate(f107=74.0, f107a=86.0)
    np.testing.assert_allclose(
        minimum["photon_flux_cm2_s"] / 1.0e9,
        [1.2,.45,4.8,3.1,.46,.21,1.679,.8,6.9,.965,.65,.314,.383,.29,.285,.452,.72,1.27,.357,.53,1.59,.342,.23,.36,.141,.17,.26,.702,.758,1.625,3.537,3.,4.4,1.475,3.5,2.1,2.467],
        rtol=2e-5,
    )
    maximum = model.calculate(f107=[200.0, 74.0], f107a=[200.0, 86.0])
    assert maximum["photon_flux_cm2_s"].shape == (2, 37)
    np.testing.assert_allclose(
        maximum["photon_flux_cm2_s"][0, :4] / 1.0e9,
        [2.642448, .83475, 12.504, 10.3354], rtol=2e-4,
    )


@pytest.mark.requires_dll
def test_euv91_full_reference_output_and_repeatability(tmp_path, monkeypatch):
    from model import EUV91

    monkeypatch.chdir(tmp_path)
    model = EUV91(data_dir=DATA, auto_download=False)
    expected = np.asarray([
        .539e8,.117e9,.131e10,.379e9,.588e10,.455e10,.608e9,.255e10,
        .673e10,.197e10,.896e10,.821e10,.107e10,.422e10,.117e10,.297e9,
        .255e10,.192e10,.662e9,.354e10,.298e10,.115e10,.235e10,.252e10,
        .575e9,.468e9,.312e9,.338e9,.470e9,.117e10,.210e10,.368e10,
        .944e10,.862e10,.107e11,.327e10,.123e11,.800e10,.677e10,
    ])
    first = model.calculate(year=1980, day_of_year=183)
    second = model.calculate(year=1980, day_of_year=183)
    np.testing.assert_allclose(first["photon_flux_cm2_s"], expected, rtol=6e-3)
    np.testing.assert_array_equal(first["photon_flux_cm2_s"], second["photon_flux_cm2_s"])
    assert first["energy_flux_erg_cm2_s"].shape == (39,)
    batch = model.calculate(year=[1980, 1980], day_of_year=[183, 184])
    assert batch["photon_flux_cm2_s"].shape == (2, 39)
    with pytest.raises(ValueError, match="没有日期"):
        model.calculate(year=1968, day_of_year=1)
    with pytest.raises(ValueError, match="没有日期"):
        model.calculate(year=1968, day_of_year=172)


@pytest.mark.requires_dll
def test_photoelectron_reference_case_and_warnings():
    from model import Photoelectron

    model = Photoelectron()
    result = model.calculate(
        alt_km=148.0, sza_deg=53.0,
        electron_temperature_K=577.0, neutral_temperature_K=577.0,
        O_cm3=1.6e10, O2_cm3=2.3e9, N2_cm3=3.1e10,
        electron_density_cm3=2.0e5, N_2D_cm3=2.6e3,
        O_plus_2D_cm3=4.0e-2, f107=None, euv_factors=np.ones(9),
    )
    np.testing.assert_allclose(
        result["photoelectron_flux_per_eV_cm2_s"][:5],
        [2.44e9, 5.36e9, 1.40e8, 6.92e8, 1.26e9], rtol=6e-3,
    )
    assert result["attenuation_factor"] == pytest.approx(.19, rel=.03)
    assert result["energy_eV"].shape == (100,)
    with pytest.raises(ValueError, match="只能指定一个"):
        model.calculate(
            alt_km=148, sza_deg=53, electron_temperature_K=577,
            neutral_temperature_K=577, O_cm3=1, O2_cm3=1, N2_cm3=1,
            electron_density_cm3=1, f107=100, euv_factors=np.ones(9),
        )


@pytest.mark.requires_dll
def test_pv_ionosphere_scalar_batch_and_formula():
    from model import PVIonosphere

    model = PVIonosphere(data_dir=DATA, auto_download=False)
    result = model.calculate(alt_km=200.0, sza_deg=30.0)
    assert result["log10_electron_density_cm3"] == pytest.approx(5.0182538, rel=2e-6)
    assert result["electron_temperature_K"] == pytest.approx(2453.7408, rel=2e-6)
    batch = model.calculate(alt_km=[150.0, 200.0, 300.0], sza_deg=30.0)
    assert batch["electron_density_cm3"].shape == (3,)
    assert np.all(np.isfinite(batch["electron_temperature_K"]))


@pytest.mark.requires_dll
def test_pv_thermosphere_original_driver_outputs():
    from model import PVThermosphere

    model = PVThermosphere()
    midnight = model.calculate(
        alt_km=250.0, lat_deg=0.0, local_time_hours=0.0, f107a=200.0, f107=200.0
    )
    noon = model.calculate(
        alt_km=250.0, lat_deg=0.0, local_time_hours=12.0, f107a=200.0, f107=200.0
    )
    np.testing.assert_allclose(
        [midnight["total_density_g_cm3"], midnight["CO2_cm3"], midnight["O_cm3"],
         midnight["CO_cm3"], midnight["He_cm3"], midnight["N_cm3"], midnight["N2_cm3"]],
        [3.70e-18,1.09e-7,2.78e3,2.39e-2,5.46e5,7.53e1,1.23e-2], rtol=.015,
    )
    np.testing.assert_allclose(
        [noon["T_exo_K"], noon["T_local_K"]], [308.1, 308.0], rtol=5e-4
    )
    batch = model.calculate(
        alt_km=[200.0, 250.0], lat_deg=0.0, local_time_hours=[0.0, 12.0],
        f107a=200.0, f107=200.0,
    )
    assert batch["CO2_cm3"].shape == (2,)
    assert np.all(np.isfinite(batch["total_density_g_cm3"]))

    with pytest.warns(RuntimeWarning, match="低于 140"):
        reference = model.calculate(
            alt_km=[250.0, 250.0, 110.0, 130.0, 150.3],
            lat_deg=[0.0, 0.0, -31.3, -37.9, 16.3],
            local_time_hours=[0.0, 12.0, 6.8, 8.5, 5.3],
            f107a=[200.0, 200.0, 166.0, 166.0, 179.2],
            f107=[200.0, 200.0, 190.0, 190.0, 200.3],
        )
    actual = np.column_stack([reference[name] for name in (
        "total_density_g_cm3", "CO2_cm3", "O_cm3", "CO_cm3", "He_cm3",
        "N_cm3", "N2_cm3", "T_exo_K", "T_local_K",
    )])
    expected = np.asarray([
        [3.70e-18,1.09e-7,2.78e3,2.39e-2,5.46e5,7.53e1,1.23e-2,133.8,133.8],
        [5.52e-16,3.58e3,1.95e7,2.93e5,9.63e5,4.88e5,5.90e4,308.1,308.0],
        [4.96e-9,6.60e13,3.32e10,3.83e10,3.92e8,3.73e5,3.07e12,254.2,170.9],
        [3.27e-11,4.12e11,1.47e10,1.27e10,2.29e7,3.44e8,3.46e10,293.3,184.4],
        [6.83e-14,2.79e8,1.20e9,1.98e8,3.22e7,9.32e6,1.39e8,175.4,144.1],
    ])
    np.testing.assert_allclose(actual, expected, rtol=.015)


def test_exospheric_h_table_node_interpolation_and_spherical_mean():
    from model import ExosphericH

    model = ExosphericH(data_dir=DATA, auto_download=False)
    node = model.calculate(
        radius_km=6640.0, colatitude_deg=90.0, longitude_deg=0.0,
        season="equinox", f107=80,
    )
    assert node["H_cm3"] > 0.0
    midpoint = model.calculate(
        radius_km=math.sqrt(6640.0 * 6648.0), colatitude_deg=90.0,
        longitude_deg=0.0, season="equinox", f107=80,
    )
    assert np.isfinite(midpoint["H_cm3"])

    colat = np.linspace(0.5, 179.5, 180)
    lon = np.linspace(0.0, 359.0, 360)
    cc, ll = np.meshgrid(colat, lon, indexing="ij")
    density = model.calculate(
        radius_km=6640.0, colatitude_deg=cc, longitude_deg=ll,
        season="equinox", f107=80,
    )["H_cm3"]
    weights = np.sin(np.deg2rad(colat))[:, None]
    spherical_mean = np.sum(density * weights) / (np.sum(weights) * density.shape[1])
    assert spherical_mean == pytest.approx(304534.0, rel=3e-4)
    with pytest.raises(ValueError, match="f107"):
        model.calculate(radius_km=7000, colatitude_deg=90, longitude_deg=0,
                        season="equinox", f107=100)


@pytest.mark.requires_dll
def test_phase4_validation_and_nonfinite_inputs():
    from model import EUV91, EUVAC, ExosphericH, Photoelectron, PVIonosphere, PVThermosphere

    with pytest.raises(ValueError):
        EUVAC().calculate(f107=np.nan, f107a=100.0)
    with pytest.raises(ValueError):
        EUV91(data_dir=DATA, auto_download=False).calculate(year=1980.5, day_of_year=183)
    with pytest.raises(ValueError):
        Photoelectron().calculate(
            alt_km=np.inf, sza_deg=0, electron_temperature_K=500,
            neutral_temperature_K=500, O_cm3=1, O2_cm3=1, N2_cm3=1,
            electron_density_cm3=1,
        )
    with pytest.raises(ValueError):
        PVIonosphere(data_dir=DATA, auto_download=False).calculate(alt_km=200, sza_deg=np.nan)
    with pytest.raises(ValueError):
        PVThermosphere().calculate(
            alt_km=200, lat_deg=0, local_time_hours=24, f107a=100, f107=100
        )
    with pytest.raises(ValueError):
        ExosphericH(data_dir=DATA, auto_download=False).calculate(
            radius_km=62127, colatitude_deg=90, longitude_deg=0
        )


@pytest.mark.requires_dll
def test_native_phase4_models_in_isolated_subprocess(tmp_path):
    code = """
import numpy as np
from model import EUV91, EUVAC, Photoelectron, PVIonosphere, PVThermosphere
data = r'%s'
values = [
    EUV91(data_dir=data, auto_download=False).calculate(year=1980, day_of_year=183)['photon_flux_cm2_s'],
    EUVAC().calculate(f107=100, f107a=100)['photon_flux_cm2_s'],
    Photoelectron().calculate(alt_km=148, sza_deg=53, electron_temperature_K=577,
        neutral_temperature_K=577, O_cm3=1.6e10, O2_cm3=2.3e9, N2_cm3=3.1e10,
        electron_density_cm3=2e5, f107=71)['photoelectron_flux_per_eV_cm2_s'],
    PVIonosphere(data_dir=data, auto_download=False).calculate(alt_km=200, sza_deg=30)['electron_density_cm3'],
    PVThermosphere().calculate(alt_km=200, lat_deg=0, local_time_hours=12,
        f107a=200, f107=200)['total_density_g_cm3'],
]
assert all(np.all(np.isfinite(value)) for value in values)
""" % DATA.as_posix()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env,
        text=True, capture_output=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
