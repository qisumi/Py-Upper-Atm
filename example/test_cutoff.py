from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import CutoffRigidity


def test_single_trajectory(model: CutoffRigidity) -> None:
    """Test a single allowed trajectory at mid-latitude."""
    result = model.calculate(
        lat_deg=40.0,
        lon_deg=0.0,
        rigidity_gv=10.0,
        zenith_deg=0.0,
        azimuth_deg=0.0,
    )
    print(
        f"[Single] PC=10.0 GV, fate={result['fate']}, "
        f"asymptotic lat={result['asymptotic_latitude_deg']:.1f}°, "
        f"lon={result['asymptotic_longitude_deg']:.1f}°, "
        f"path={result['path_length_re']:.3f} RE"
    )
    assert result["result_code"] in (-1, 0, 1)


def test_cutoff_scan(model: CutoffRigidity) -> None:
    """Scan rigidities to find the cutoff at equator."""
    result = model.calculate(
        lat_deg=0.0,
        lon_deg=0.0,
        start_rigidity_gv=15.0,
        delta_rigidity_mv=100.0,
        max_trajectories=200,
    )
    n = result["n_trajectories_computed"]
    print(
        f"[Scan] Computed {n} trajectories, "
        f"cutoff={result['cutoff_rigidity_gv']:.2f} GV, "
        f"fate={result['fate']}"
    )
    assert n > 0


def test_batch_trajectory(model: CutoffRigidity) -> None:
    """Test broadcast inputs for single-trajectory mode."""
    result = model.calculate(
        lat_deg=np.array([0.0, 40.0]),
        lon_deg=0.0,
        rigidity_gv=np.array([15.0, 10.0]),
    )
    print(
        "[Batch] fates="
        f"{result['fate'].tolist()}, paths={result['path_length_re']}"
    )
    assert result["result_code"].shape == (2,)


if __name__ == "__main__":
    print("Running Geomagnetic Cutoff Rigidity smoke test...")
    model = CutoffRigidity()
    test_single_trajectory(model)
    test_cutoff_scan(model)
    test_batch_trajectory(model)
    print("All cutoff rigidity tests passed.")
