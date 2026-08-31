from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pytest

from model.pymsis2h2o import Model, _BOLTZMANN_J_K, _Climatology
from tools.build_msis2h2o_climatology import MONTH_MIDPOINT_DAY, write_deterministic_npz


ROOT = Path(__file__).resolve().parents[1]


class FakeMSIS2:
    def calculate(self, **kwargs):
        alt = np.asarray(kwargs["alt_km"], dtype=float)
        shape = alt.shape
        temperature = np.broadcast_to(250.0, shape)
        pressure_hpa = 10.0 ** (1.0 - (alt - 20.0) * 5.0 / 100.0)
        total = pressure_hpa * 100.0 / (_BOLTZMANN_J_K * temperature)
        densities = np.zeros(shape + (10,), dtype=float)
        for index in range(1, 9):
            densities[..., index] = total / 8.0
        if shape == ():
            return {
                "alt_km": float(alt),
                "T_local_K": float(temperature),
                "T_exo_K": 900.0,
                "densities": densities,
            }
        return {
            "alt_km": alt.copy(),
            "T_local_K": temperature.copy(),
            "T_exo_K": np.broadcast_to(900.0, shape).copy(),
            "densities": densities,
        }


def _climatology(fallback_node=False):
    latitude = np.asarray([-82.0, 0.0, 82.0])
    longitude = np.asarray([-180.0, -90.0, 0.0, 90.0])
    pressure = np.asarray([0.00215, 0.01, 0.1, 10.0, 100.0])
    values = np.empty((12, latitude.size, longitude.size, pressure.size), dtype=float)
    for month in range(12):
        for yi, lat in enumerate(latitude):
            for xi, lon in enumerate(longitude):
                for pi, p in enumerate(pressure):
                    values[month, yi, xi, pi] = (
                        4.0 + 0.02 * month + 0.001 * lat + 0.1 * np.cos(np.deg2rad(lon)) + 0.05 * np.log(p)
                    )
    fallback = np.zeros(values.shape, dtype=bool)
    fallback[0, 1, 2, 2] = fallback_node
    return _Climatology(
        MONTH_MIDPOINT_DAY,
        latitude,
        longitude,
        pressure,
        np.log(values),
        fallback,
    )


def _model(climatology=None):
    instance = Model.__new__(Model)
    instance._msis2 = FakeMSIS2()
    instance._climatology = climatology or _climatology()
    return instance


def _kwargs(**changes):
    values = dict(
        day=MONTH_MIDPOINT_DAY[0] + 1.0,
        utsec=0.0,
        alt_km=40.0,
        lat_deg=0.0,
        lon_deg=0.0,
        f107a=100.0,
        f107=100.0,
    )
    values.update(changes)
    return values


def test_grid_node_is_exact_and_scalar_types_are_preserved():
    result = _model().calculate(**_kwargs(alt_km=20.0))
    expected = 4.0 + 0.1 + 0.05 * np.log(10.0)
    assert result["H2O_vmr_ppmv"] == pytest.approx(expected)
    assert isinstance(result["H2O_vmr_ppmv"], float)
    assert isinstance(result["H2O_extrapolated"], bool)
    assert result["densities"].shape == (10,)


def test_december_to_january_and_longitude_seam_are_continuous():
    climatology = _climatology()
    dec = climatology.evaluate(
        np.asarray([365.0, 1.0]),
        np.asarray([86399.0, 0.0]),
        np.asarray([0.0, 0.0]),
        np.asarray([179.999, -180.001]),
        np.asarray([10.0, 10.0]),
    )[0]
    assert abs(dec[0] - dec[1]) < 0.03


def test_broadcast_shape_polar_clamp_and_fallback_flags():
    result = _model(_climatology(fallback_node=True)).calculate(
        **_kwargs(
            day=[MONTH_MIDPOINT_DAY[0] + 1.0, MONTH_MIDPOINT_DAY[0] + 1.0],
            alt_km=[[40.0], [60.0]],
            lat_deg=[[90.0], [0.0]],
            lon_deg=[0.0, 90.0],
        )
    )
    assert result["H2O_vmr_ppmv"].shape == (2, 2)
    assert result["densities"].shape == (2, 2, 10)
    assert result["H2O_latitude_clamped"].tolist() == [[True, True], [False, False]]
    assert result["H2O_climatology_fallback"][1, 0]


def test_scientific_identities_and_raw_msis_compatibility():
    model = _model()
    kwargs = _kwargs(alt_km=[20.0, 50.0, 90.0, 120.0])
    direct = model._msis2.calculate(**kwargs)
    result = model.calculate(**kwargs)
    np.testing.assert_array_equal(result["alt_km"], direct["alt_km"])
    np.testing.assert_array_equal(result["T_local_K"], direct["T_local_K"])
    np.testing.assert_array_equal(result["T_exo_K"], direct["T_exo_K"])
    np.testing.assert_array_equal(result["densities"], direct["densities"])
    np.testing.assert_allclose(
        result["pressure_Pa"],
        result["total_number_density_m3"] * _BOLTZMANN_J_K * result["T_local_K"],
        rtol=1e-14,
    )
    np.testing.assert_allclose(
        result["H2O_number_density_m3"],
        result["total_number_density_m3"] * result["H2O_vmr_ppmv"] * 1e-6,
        rtol=1e-14,
    )
    np.testing.assert_allclose(
        result["H2O_number_density_m3"],
        result["H2O_number_density_cm3"] * 1e6,
        rtol=1e-14,
    )


def test_altitude_boundaries_and_extrapolation_are_finite_nonnegative():
    model = _model()
    result = model.calculate(**_kwargs(alt_km=[20.0, 80.0, 100.0, 120.0]))
    assert result["H2O_extrapolated"].tolist() == [False, False, True, True]
    assert np.all(np.isfinite(result["H2O_vmr_ppmv"]))
    assert np.all(result["H2O_vmr_ppmv"] >= 0.0)
    # Pressure decreases as altitude rises; the constrained tail cannot grow.
    assert result["H2O_vmr_ppmv"][3] <= result["H2O_vmr_ppmv"][2]
    with pytest.raises(ValueError, match="20--120"):
        model.calculate(**_kwargs(alt_km=19.999))
    with pytest.raises(ValueError, match="20--120"):
        model.calculate(**_kwargs(alt_km=120.001))


def test_mls_top_pressure_boundary_switch_is_exact():
    climatology = _climatology()
    pressure = np.asarray([0.00215, np.nextafter(0.00215, 0.0)])
    flags = climatology.evaluate(
        np.asarray([15.5, 15.5]),
        np.asarray([0.0, 0.0]),
        np.asarray([0.0, 0.0]),
        np.asarray([0.0, 0.0]),
        pressure,
    )[1]
    assert flags.tolist() == [False, True]


def test_load_from_non_repo_directory_with_explicit_climatology(monkeypatch, tmp_path):
    path = tmp_path / "fixture.npz"
    climatology = _climatology()
    write_deterministic_npz(
        path,
        {
            "month_midpoint_day": climatology.month_midpoint_day,
            "latitude_deg": climatology.latitude_deg,
            "longitude_deg": climatology.longitude_deg,
            "pressure_hpa": climatology.pressure_hpa,
            "log_vmr_ppmv": climatology.log_vmr_ppmv,
            "fallback_mask": climatology.fallback_mask,
        },
    )
    monkeypatch.chdir(tmp_path)
    loaded = _Climatology.load(Path(path))
    assert loaded.log_vmr_ppmv.shape == climatology.log_vmr_ppmv.shape


def test_repository_climatology_and_manifests_have_fixed_hashes():
    source_manifest = json.loads((ROOT / "tools" / "msis2h2o_sources.json").read_text(encoding="utf-8"))
    runtime_manifest = json.loads((ROOT / "src" / "utils" / "model_data_manifest.json").read_text(encoding="utf-8"))
    artifact = ROOT / source_manifest["output"]
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert len(source_manifest["sources"]) == 20
    assert [item["year"] for item in source_manifest["sources"]] == list(range(2005, 2025))
    assert all(len(item["sha256"]) == 64 for item in source_manifest["sources"])
    assert digest == source_manifest["output_sha256"]
    entry = next(item for item in runtime_manifest["files"] if item["model"] == "msis2h2o")
    assert entry["sha256"] == digest
    assert entry["size"] == artifact.stat().st_size


@pytest.mark.requires_dll
def test_real_msis2_fields_are_exactly_compatible(msis2_model, msis2h2o_model):
    kwargs = _kwargs(
        day=196.0,
        alt_km=np.asarray([20.0, 50.0, 90.0, 120.0]),
        lat_deg=35.0,
        lon_deg=116.0,
    )
    direct = msis2_model.calculate(**kwargs)
    extended = msis2h2o_model.calculate(**kwargs)
    for field in ("alt_km", "T_local_K", "T_exo_K", "densities"):
        np.testing.assert_array_equal(extended[field], direct[field])
    assert extended["densities"].shape == (4, 10)


@pytest.mark.requires_dll
def test_real_model_loads_outside_repository(monkeypatch, tmp_path):
    from model import MSIS2H2O

    monkeypatch.chdir(tmp_path)
    model = MSIS2H2O(data_dir=ROOT / "data", auto_download=False)
    result = model.calculate(**_kwargs(alt_km=100.0))
    assert np.isfinite(result["H2O_number_density_cm3"])
    assert result["H2O_extrapolated"]


@pytest.mark.requires_dll
def test_real_extrapolated_tail_is_nonincreasing(msis2h2o_model):
    result = msis2h2o_model.calculate(**_kwargs(alt_km=np.linspace(95.0, 120.0, 26)))
    assert np.all(result["H2O_extrapolated"])
    assert np.all(np.diff(result["H2O_vmr_ppmv"]) <= 1.0e-12)
    assert np.all(np.isfinite(result["H2O_number_density_m3"]))
    assert np.all(result["H2O_number_density_m3"] >= 0.0)
