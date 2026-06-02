"""SOLPRO solar proton fluence model smoke test."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import SOLPRO


def test_single_point():
    """Single-point calculation at different confidence levels."""
    m = SOLPRO()
    for conf in [80, 90, 95, 99]:
        r = m.calculate(duration_months=12, confidence_pct=conf)
        print(f"\n12 months, {conf}% confidence:")
        print(f"  AL events: {r['n_al_events']}")
        for i in range(10):
            energy = 10 * (i + 1)
            print(f"  E > {energy:3d} MeV: {r['fluence_cm2'][i]:.3e} protons/cm²")


def test_batch():
    """Batch calculation across mission durations."""
    m = SOLPRO()
    durs = np.array([1, 3, 6, 12, 24, 48, 72], dtype=float)
    r = m.calculate(duration_months=durs, confidence_pct=90)

    print("\n\nSOLPRO at 90% confidence by mission duration:")
    print(f"{'Months':>7s}  {'AL evts':>7s}  {'E>10 MeV':>12s}  {'E>100 MeV':>12s}")
    print("-" * 45)
    for i, d in enumerate(durs):
        print(f"{d:7.0f}  {r['n_al_events'][i]:7d}  "
              f"{r['fluence_cm2'][i, 0]:12.3e}  {r['fluence_cm2'][i, 9]:12.3e}")


if __name__ == "__main__":
    test_single_point()
    test_batch()
