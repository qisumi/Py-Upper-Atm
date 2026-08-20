from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import ExosphericH


def test_exospheric_h():
    model = ExosphericH(data_dir=ROOT / "data", auto_download=False)
    print(model.calculate(
        radius_km=7000.0, colatitude_deg=90.0, longitude_deg=0.0,
        season="equinox", f107=80,
    ))


if __name__ == "__main__":
    test_exospheric_h()
