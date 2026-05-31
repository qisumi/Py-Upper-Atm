# CIRA-86 Wrapper

This directory provides the COSPAR International Reference Atmosphere 1986
(CIRA-86) table wrapper exposed as `model.CIRA86`.

## Background

CIRA-86 is a COSPAR reference atmosphere. This wrapper reads the corrected ASCII
tables from `TODO/CIRA/cira86ascii`, covering monthly zonal-mean temperature,
zonal wind, pressure, and geopotential height from 0-120 km and 80S-80N.

## Files

```text
src/model/pycira86/
├── __init__.py      # Model class plus table parsing/interpolation
├── README.md
└── README_zh.md
```

Runtime data lives under `cira86data/` in the model data root, such as
`data/cira86data/` in the source tree.

## Interface

The original `cirat.for` program is an interactive table viewer for legacy
binary data. This port reads the official ASCII tables directly and does not
need a native DLL.

```python
from model import CIRA86

cira = CIRA86(data_dir="data", auto_download=False)
result = cira.calculate(month=1, lat_deg=0.0, alt_km=100.0)
```

## API

```python
CIRA86.calculate(*, month, lat_deg, alt_km=None, pressure_mb=None)
```

- `month`: month number, 1-12.
- `lat_deg`: geodetic latitude in degrees, north positive, -80 to 80.
- `alt_km`: height-coordinate input in km, 0 to 120.
- `pressure_mb`: pressure-coordinate input in mb.

Specify exactly one of `alt_km` and `pressure_mb`.

Height-coordinate results contain `month`, `alt_km`, `lat_deg`, `T_K`,
`zonal_wind_ms`, and `pressure_mb`.

Pressure-coordinate results contain `month`, `pressure_mb`, `lat_deg`, `T_K`,
`zonal_wind_ms`, and `geopotential_height_m`.

Scalar inputs return Python scalars; array inputs are numpy-broadcast and return
arrays with the broadcast shape.

## References

- CIRA 1986, D. Rees (ed.), Advances in Space Research, Volume 8, Numbers 5-6, 1988.
- E. L. Fleming, S. Chandra, M. R. Schoeberl, and J. J. Barnett, NASA TM 100697, 1988.
