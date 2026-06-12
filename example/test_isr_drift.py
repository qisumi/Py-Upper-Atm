from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import ISRDrift


def test_single_point(model: ISRDrift) -> None:
    result = model.calculate(
        mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
    )
    print(
        "[Single Point] "
        f"potential={result['potential_V']:.2f} V, "
        f"poleward={result['poleward_drift_ms']:.2f} m/s, "
        f"eastward={result['eastward_drift_ms']:.2f} m/s"
    )
    assert np.isfinite(result["potential_V"])
    assert np.isfinite(result["poleward_drift_ms"])
    assert np.isfinite(result["eastward_drift_ms"])


def test_seasonal_modes(model: ISRDrift) -> None:
    for mode in range(5):
        result = model.calculate(
            mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
            seasonal_avg=mode,
        )
        print(
            f"  seasonal_avg={mode}: "
            f"potential={result['potential_V']:.2f} V"
        )
        assert np.isfinite(result["potential_V"])


def test_broadcast_eval(model: ISRDrift) -> None:
    mlat = np.linspace(30, 60, 7)
    mlon = np.zeros_like(mlat)
    doy = np.full_like(mlat, 172.0)
    ut = np.full_like(mlat, 12.0)

    result = model.calculate(
        mlat_deg=mlat, mlon_deg=mlon, doy=doy, ut_hours=ut,
    )
    print(
        "[Broadcast] "
        f"potential shape={result['potential_V'].shape}"
    )
    assert result["potential_V"].shape == (7,)
    assert np.all(np.isfinite(result["potential_V"]))


if __name__ == "__main__":
    print("Running ISR Ion Drift Model wrapper smoke test...")
    model = ISRDrift()
    test_single_point(model)
    test_seasonal_modes(model)
    test_broadcast_eval(model)
    print("All ISR Drift tests passed.")
