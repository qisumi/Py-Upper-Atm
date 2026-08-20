from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import Photoelectron


def test_photoelectron():
    result = Photoelectron().calculate(
        alt_km=148.0, sza_deg=53.0, electron_temperature_K=577.0,
        neutral_temperature_K=577.0, O_cm3=1.6e10, O2_cm3=2.3e9,
        N2_cm3=3.1e10, electron_density_cm3=2.0e5,
        N_2D_cm3=2.6e3, O_plus_2D_cm3=4.0e-2,
    )
    print(result["photoelectron_flux_per_eV_cm2_s"][:10])


if __name__ == "__main__":
    test_photoelectron()
