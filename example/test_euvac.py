from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import EUVAC


def test_euvac():
    print(EUVAC().calculate(f107=100.0, f107a=100.0)["photon_flux_cm2_s"])


if __name__ == "__main__":
    test_euvac()
