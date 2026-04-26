from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import AuroraOval


def test_single_point(model: AuroraOval) -> None:
    result = model.calculate(mlt_hours=12.0, activity_level=3)
    print(
        "[Single Point] "
        f"poleward={result['poleward_boundary_deg']:.2f}°, "
        f"equatorward={result['equatorward_boundary_deg']:.2f}°"
    )
    assert np.isfinite(result["poleward_boundary_deg"])
    assert np.isfinite(result["equatorward_boundary_deg"])
    assert result["poleward_boundary_deg"] > result["equatorward_boundary_deg"]


def test_broadcast_eval(model: AuroraOval) -> None:
    mlt = np.linspace(0, 24, 25)
    levels = np.full_like(mlt, 3, dtype=int)

    result = model.calculate(mlt_hours=mlt, activity_level=levels)
    print(
        "[Broadcast] "
        f"poleward shape={result['poleward_boundary_deg'].shape}, "
        f"equatorward shape={result['equatorward_boundary_deg'].shape}"
    )
    assert result["poleward_boundary_deg"].shape == (25,)
    assert result["equatorward_boundary_deg"].shape == (25,)


def test_all_activity_levels(model: AuroraOval) -> None:
    for level in range(7):
        result = model.calculate(mlt_hours=0.0, activity_level=level)
        print(
            f"  level={level}: "
            f"poleward={result['poleward_boundary_deg']:.2f}°, "
            f"equatorward={result['equatorward_boundary_deg']:.2f}°"
        )
        assert 50 < result["poleward_boundary_deg"] < 90
        assert 50 < result["equatorward_boundary_deg"] < 90


if __name__ == "__main__":
    print("Running Feldstein auroral oval wrapper smoke test...")
    model = AuroraOval()
    test_single_point(model)
    test_broadcast_eval(model)
    test_all_activity_levels(model)
    print("All aurora oval tests passed.")
