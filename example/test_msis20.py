from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL_DATA = ROOT / "data"
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model import MSIS2
from utils.time import doy, seconds_of_day


model = MSIS2(precision="single", data_dir=MODEL_DATA, auto_download=False)

result = model.calculate(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12, 0, 0.0),
    alt_km=250.0,
    lat_deg=39.9,
    lon_deg=116.4,
    f107a=150.0,
    f107=150.0,
    ap7=[4.0] * 7,
)
print(result)

batch = model.calculate(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=[50, 100, 150, 200, 250, 300, 350, 400, 450, 500],
    lat_deg=39.9,
    lon_deg=116.4,
    f107a=150.0,
    f107=150.0,
)
for alt, temp, density in zip(
    batch["alt_km"],
    batch["T_local_K"],
    batch["densities"][:, 1],
):
    print(alt, temp, density)
