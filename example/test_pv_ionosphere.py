from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import PVIonosphere


def test_pv_ionosphere():
    model = PVIonosphere(data_dir=ROOT / "data", auto_download=False)
    print(model.calculate(alt_km=[150.0, 200.0, 300.0], sza_deg=30.0))


if __name__ == "__main__":
    test_pv_ionosphere()
