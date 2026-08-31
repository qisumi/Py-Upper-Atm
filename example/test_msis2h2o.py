"""Bilingual MSIS2H2O smoke example."""

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import MSIS2H2O


def main() -> None:
    model = MSIS2H2O(data_dir=ROOT / "data", auto_download=False)
    result = model.calculate(
        day=196.0,
        utsec=43200.0,
        alt_km=np.asarray([20.0, 50.0, 90.0, 120.0]),
        lat_deg=35.0,
        lon_deg=116.0,
        f107a=100.0,
        f107=100.0,
    )
    print("H2O VMR / 水汽体积混合比 (ppmv):", result["H2O_vmr_ppmv"])
    print("H2O density / 水分子数密度 (cm^-3):", result["H2O_number_density_cm3"])
    print("Constrained extrapolation / 受约束外推:", result["H2O_extrapolated"])
    assert result["densities"].shape == (4, 10)
    assert np.all(np.isfinite(result["H2O_number_density_cm3"]))
    assert np.all(result["H2O_number_density_cm3"] >= 0.0)


if __name__ == "__main__":
    main()
