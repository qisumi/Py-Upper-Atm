"""Tsyganenko magnetic field models smoke test."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import Tsyganenko


def test_single_point():
    """Single-point calculation for each model version."""
    for ver, kwargs in [
        ("T89", dict(kp_index=3)),
        ("T96", dict(pdyn_nPa=2.0, dst_nT=-20.0, by_imf_nT=0.5, bz_imf_nT=-2.0)),
        ("T01", dict(pdyn_nPa=2.0, dst_nT=-20.0, by_imf_nT=0.5, bz_imf_nT=-2.0,
                     g1=1.0, g2=1.0)),
        ("TS04", dict(pdyn_nPa=2.0, dst_nT=-20.0, by_imf_nT=0.5, bz_imf_nT=-2.0,
                      w1=1.0, w2=0.5, w3=0.3, w4=0.2, w5=0.1, w6=0.1)),
    ]:
        m = Tsyganenko(model_version=ver)
        r = m.calculate(
            year=2000, doy=180, hour=12, minute=0, second=0,
            x_re=-5.0, y_re=0.0, z_re=0.0,
            **kwargs,
        )
        print(f"{ver}: Bx={r['Bx_ext_nT']:+.3f}  "
              f"By={r['By_ext_nT']:+.3f}  "
              f"Bz={r['Bz_ext_nT']:+.3f} nT  "
              f"tilt={r['tilt_rad']:.4f} rad")


def test_batch():
    """Batch calculation along the tail."""
    m = Tsyganenko(model_version="T96")
    xs = np.linspace(-5, -15, 11)
    r = m.calculate(
        year=2000, doy=180, hour=12,
        x_re=xs, y_re=0.0, z_re=0.0,
        pdyn_nPa=2.0, dst_nT=-20.0,
        by_imf_nT=0.5, bz_imf_nT=-2.0,
    )
    print("\nT96 batch along X_GSM (Y=0, Z=0):")
    for i, x in enumerate(xs):
        print(f"  X={x:+6.1f} Re: "
              f"Bx={r['Bx_ext_nT'][i]:+8.3f}  "
              f"By={r['By_ext_nT'][i]:+8.3f}  "
              f"Bz={r['Bz_ext_nT'][i]:+8.3f} nT")


def test_dipole():
    """Total field including internal dipole."""
    m = Tsyganenko(model_version="TS04")
    r = m.calculate(
        year=2000, doy=180, hour=12,
        x_re=-5.0, y_re=0.0, z_re=0.0,
        pdyn_nPa=2.0, dst_nT=-20.0,
        by_imf_nT=0.5, bz_imf_nT=-2.0,
        w1=1.0, w2=0.5, w3=0.3, w4=0.2, w5=0.1, w6=0.1,
        include_dipole=True,
    )
    print("\nTS04 with dipole field at (-5, 0, 0) Re:")
    for key in ["Bx_ext_nT", "By_ext_nT", "Bz_ext_nT",
                "Bx_dip_nT", "By_dip_nT", "Bz_dip_nT",
                "Bx_total_nT", "By_total_nT", "Bz_total_nT"]:
        print(f"  {key:16s} = {r[key]:+10.3f} nT")


if __name__ == "__main__":
    test_single_point()
    test_batch()
    test_dipole()
