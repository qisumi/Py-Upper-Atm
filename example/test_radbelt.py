"""
Smoke test for RADBELT (AP-8 / AE-8) trapped radiation model.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import RADBELT

DATA_DIR = ROOT / "data"


def test_single_point(model: RADBELT) -> None:
    result = model.calculate(l_value=2.0, bb0=1.0, energy_mev=0.5)
    print(
        f"[Single Point] L=2.0, B/B0=1.0, E=0.5 MeV: "
        f"log10(flux)={result['flux']:.4f}"
    )
    assert np.isfinite(result["flux"])
    assert isinstance(result["flux"], float)


def test_batch_calculation(model: RADBELT) -> None:
    l_vals = [1.5, 2.0, 3.0, 4.0, 6.0]
    bb0 = 1.0
    energy = 1.0

    result = model.calculate(l_value=l_vals, bb0=bb0, energy_mev=energy)
    print(f"[Batch] E={energy} MeV, B/B0={bb0}:")
    for l, f in zip(l_vals, result["flux"]):
        flux_linear = 10**f if f > 0 else 0.0
        print(f"  L={l:.1f}: log10(flux)={f:.4f}, flux={flux_linear:.2e} cm^-2 s^-1")
    assert result["flux"].shape == (5,)


def test_energy_array(model: RADBELT) -> None:
    energies = [0.1, 0.5, 1.0, 3.0, 4.0]
    result = model.calculate(l_value=3.0, bb0=1.0, energy_mev=energies)
    print(f"[Energy Array] L=3.0, B/B0=1.0:")
    for e, f in zip(energies, result["flux"]):
        flux_linear = 10**f if f > 0 else 0.0
        print(f"  E={e:.1f} MeV: log10(flux)={f:.4f}, flux={flux_linear:.2e} cm^-2 s^-1")
    assert result["flux"].shape == (5,)


if __name__ == "__main__":
    print("Running RADBELT smoke test...")

    print("\n=== AE8MIN (electrons, solar minimum) ===")
    model_e = RADBELT("AE8MIN", data_dir=DATA_DIR, auto_download=False)
    test_single_point(model_e)
    test_batch_calculation(model_e)
    test_energy_array(model_e)

    print("\n=== AP8MIN (protons, solar minimum) ===")
    model_p = RADBELT("AP8MIN", data_dir=DATA_DIR, auto_download=False)
    test_single_point(model_p)
    test_batch_calculation(model_p)
    test_energy_array(model_p)

    print("\nAll RADBELT tests passed.")
