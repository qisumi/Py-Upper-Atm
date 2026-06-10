#!/usr/bin/env python3
"""MGST model smoke test — single-point and batch calculations."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DATA = Path(__file__).resolve().parents[1] / "data"

from model import MGST80, MGST81


def main() -> int:
    # ---- MGST(6/80) ----
    print("=== MGST(6/80) epoch 1979.85 ===")
    m80 = MGST80(data_dir=DATA, auto_download=False)
    r = m80.calculate(year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0)
    print(f"  F = {r['F_nT']:.1f} nT  X={r['X_nT']:.1f} Y={r['Y_nT']:.1f} Z={r['Z_nT']:.1f}")
    print(f"  Incl={r['inclination_deg']:.1f}°  Decl={r['declination_deg']:.1f}°")

    # ---- MGST(4/81) ----
    print("\n=== MGST(4/81) epoch 1980.0 ===")
    m81 = MGST81(data_dir=DATA, auto_download=False)
    r = m81.calculate(year=1980.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0)
    print(f"  F = {r['F_nT']:.1f} nT  X={r['X_nT']:.1f} Y={r['Y_nT']:.1f} Z={r['Z_nT']:.1f}")
    print(f"  Incl={r['inclination_deg']:.1f}°  Decl={r['declination_deg']:.1f}°")

    # ---- Batch ----
    print("\n=== Batch: equator to pole ===")
    lats = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    r = m81.calculate(year=1980.0, lat_deg=lats, lon_deg=0.0, alt_km=0.0)
    for lat, f in zip(lats, r["F_nT"]):
        print(f"  lat={lat:5.1f}°  F={f:.1f} nT")

    # ---- Different altitudes ----
    print("\n=== Altitude profile at lat=45° ===")
    alts = [0.0, 100.0, 300.0, 500.0, 1000.0]
    r = m81.calculate(year=1980.0, lat_deg=45.0, lon_deg=0.0, alt_km=alts)
    for alt, f in zip(alts, r["F_nT"]):
        print(f"  alt={alt:6.1f} km  F={f:.1f} nT")

    print("\nAll MGST smoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
