"""Xu-Li Neutral Sheet Model — smoke test / usage example."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import XuLi


def test_single_point():
    """Compute neutral sheet position at a single point in the magnetotail."""
    model = XuLi()
    result = model.calculate(
        x_re=-10.0,
        y_re=0.0,
        doy=172.0,
        ut_hours=12.0,
    )
    print("=== Single point (doy=172, UT=12, X=-10 RE, Y=0 RE) ===")
    print(f"  Tilt angle     : {result['tilt_angle_deg']:.4f} deg")
    print(f"  ZAEN (AEN)     : {result['zaen_re']:.4f} RE")
    print(f"  ZSEN (SEN)     : {result['zsen_re']:.4f} RE")
    print(f"  ZDEN (DEN)     : {result['zden_re']:.4f} RE")
    print(f"  RMP            : {result['rmp_re']:.4f} RE")
    print(f"  IE (AEN/SEN/DEN): {result['ie_aen']}/{result['ie_sen']}/{result['ie_den']}")


def test_with_tilt_angle():
    """Compute neutral sheet using a directly specified tilt angle."""
    model = XuLi()
    result = model.calculate(
        x_re=-15.0,
        y_re=5.0,
        tilt_angle_deg=20.0,
    )
    print("\n=== Direct tilt angle (20 deg, X=-15 RE, Y=5 RE) ===")
    print(f"  ZAEN (AEN) : {result['zaen_re']:.4f} RE")
    print(f"  ZSEN (SEN) : {result['zsen_re']:.4f} RE")
    print(f"  ZDEN (DEN) : {result['zden_re']:.4f} RE")
    print(f"  RMP        : {result['rmp_re']:.4f} RE")


def test_tail_profile():
    """Sweep X from -5 to -30 RE at Y=0 to show how Z varies."""
    model = XuLi()
    xs = [-5.0, -10.0, -15.0, -20.0, -25.0, -30.0]
    result = model.calculate(
        x_re=xs,
        y_re=0.0,
        tilt_angle_deg=15.0,
    )
    print("\n=== Tail profile (tilt=15 deg, Y=0 RE) ===")
    print(f"{'X (RE)':>8s}  {'ZAEN':>8s}  {'ZSEN':>8s}  {'ZDEN':>8s}  {'RMP':>8s}")
    for i in range(len(xs)):
        print(
            f"{result['x_re'][i]:8.1f}  "
            f"{result['zaen_re'][i]:8.4f}  "
            f"{result['zsen_re'][i]:8.4f}  "
            f"{result['zden_re'][i]:8.4f}  "
            f"{result['rmp_re'][i]:8.4f}"
        )


if __name__ == "__main__":
    test_single_point()
    test_with_tilt_angle()
    test_tail_profile()
