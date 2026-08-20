from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import AEEUV


def test_aeeuv():
    result = AEEUV(data_dir=ROOT / "data", auto_download=False).calculate(spectrum="f74113")
    print(result["wavelength_angstrom"][:5], result["photon_flux_m2_s"][:5])


if __name__ == "__main__":
    test_aeeuv()
