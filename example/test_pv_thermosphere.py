from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import PVThermosphere


def test_pv_thermosphere():
    print(PVThermosphere().calculate(
        alt_km=250.0, lat_deg=0.0, local_time_hours=12.0,
        f107a=200.0, f107=200.0,
    ))


if __name__ == "__main__":
    test_pv_thermosphere()
