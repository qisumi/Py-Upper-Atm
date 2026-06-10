#!/usr/bin/env python3
"""HMR model smoke test — single-point and full grid calculations."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DATA = Path(__file__).resolve().parents[1] / "data"

from model import HMR


def main() -> int:
    m = HMR(data_dir=DATA, auto_download=False)

    # ---- EPOT: Heppner-Maynard models ----
    print("=== Heppner-Maynard Electric Potential ===")
    for model_name in ["A", "BC", "DE"]:
        r = m.calculate(lat_deg=70.0, lon_deg=180.0, model=model_name)
        print(f"  Model {model_name:2s}: Φ = {r['electric_potential_kV']:+.2f} kV")

    # ---- EPOT: latitude scan ----
    print("\n=== Latitude scan (Model A, noon) ===")
    lats = [50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0]
    r = m.calculate(lat_deg=lats, lon_deg=180.0, model="A")
    for lat, pot in zip(lats, r["electric_potential_kV"]):
        print(f"  lat={lat:5.1f}°  Φ={pot:+8.2f} kV")

    # ---- Heelis model ----
    print("\n=== Heelis Convection Model ===")
    r = m.calculate_heelis(lat_deg=70.0, lon_hrs=12.0)
    print(f"  Φ = {r['electric_potential_kV']:+.2f} kV")
    print(f"  dΦ/dlat = {r['dlat_kV_per_rad']:.2f} kV/rad")
    print(f"  dΦ/dlon = {r['dlon_kV_per_rad']:.2f} kV/rad")

    # ---- Conductivity ----
    print("\n=== Conductivity (lat=70°, MLT=12h, Kp=3) ===")
    r = m.calculate_conductivity(lat_deg=70.0, mlt_hrs=12.0, kp=3.0)
    print(f"  Hall:     {r['hall_conductivity_Mho']:.3f} Mho")
    print(f"  Pedersen: {r['pedersen_conductivity_Mho']:.3f} Mho")

    # ---- Full computation ----
    print("\n=== Full computation (Model A, Kp=3.5) ===")
    r = m.calculate_full(kp=3.5, sublat_deg=0.0, f107=80.0, model="A")
    print(f"  Grid shape: {r['electric_potential_kV'].shape}")
    print(f"  Max |Φ|:    {abs(r['electric_potential_kV']).max():.2f} kV")
    print(f"  Max |E_lat|: {abs(r['e_field_lat_mV_m']).max():.2f} mV/m")
    print(f"  Max |E_lon|: {abs(r['e_field_lon_mV_m']).max():.2f} mV/m")
    print(f"  Max Joule:   {r['joule_heating_mW_m2'].max():.2f} mW/m²")
    print(f"  Max |FAC|:   {abs(r['fac_uA_m2']).max():.2f} μA/m²")

    print("\nAll HMR smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
