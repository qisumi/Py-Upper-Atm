from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import EUV91


def test_euv91():
    result = EUV91(data_dir=ROOT / "data", auto_download=False).calculate(year=1980, day_of_year=183)
    print(result["photon_flux_cm2_s"])


if __name__ == "__main__":
    test_euv91()
