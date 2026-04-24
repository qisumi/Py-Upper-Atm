# UpperAtmPy

[中文文档 (Chinese)](README_zh.md)

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Placeholder-lightgrey)

**UpperAtmPy** provides direct Python wrappers for upper atmospheric model DLLs. The project uses a `src/` layout and exposes one public class per model.

Supported models:

- **MSIS2**: NRLMSIS-2.0 temperature and density
- **MSIS00**: NRLMSISE-00 temperature and density
- **HWM14**: Horizontal Wind Model 2014
- **HWM93**: Horizontal Wind Model 1993

## Features

- One public interface per model: `Model.calculate(...)`.
- Top-level lazy aliases: `MSIS2`, `MSIS00`, `HWM14`, `HWM93`.
- Single-point and numpy-broadcast batch inputs through the same method.
- Model outputs are plain dictionaries.
- Utilities live under `utils`, not `model`.

## Build

Compile the native libraries before using a model from a source checkout.

```bash
cmake --preset native-release
cmake --build --preset native-release
```

## Quick Start

```python
from model import HWM14, MSIS2
from utils.time import doy, seconds_of_day

msis = MSIS2(precision="single")
atmosphere = msis.calculate(
    day=doy(2023, 1, 1),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=[100.0, 200.0, 300.0],
    lat_deg=35.0,
    lon_deg=116.0,
    f107a=100.0,
    f107=100.0,
)
print(atmosphere["T_local_K"])
print(atmosphere["densities"])

hwm = HWM14()
wind = hwm.calculate(
    iyd=2023001,
    sec=43200.0,
    alt_km=100.0,
    glat_deg=35.0,
    glon_deg=116.0,
    stl_hours=12.0,
    f107a=100.0,
    f107=100.0,
)
print(wind["meridional_wind_ms"], wind["zonal_wind_ms"])
```

MSIS2 and HWM14 need external model data. By default UpperAtmPy resolves
`.upperatmpy` under the current project directory and downloads missing files
from the project-maintained release manifest on first model instantiation. For offline use, pass
`data_dir=...` or set `UPPERATMPY_DATA_DIR` to a data root containing the legacy
`msis2data/` and `hwm14data/` subdirectories. In the source tree, that root is
`data/`.

## API

Top-level `model` exports only:

- `MSIS2`
- `MSIS00`
- `HWM14`
- `HWM93`

Each class provides `calculate(...)` and returns a dictionary.

MSIS dictionaries contain:

- `alt_km`
- `T_local_K`
- `T_exo_K`
- `densities`

HWM dictionaries contain:

- `alt_km`
- `meridional_wind_ms`
- `zonal_wind_ms`

Time helpers:

```python
from utils.time import doy, seconds_of_day
```

Optional utility modules:

- `utils.cache`
- `utils.parallel`
- `utils.space_weather`
- `utils.xarray_output`
- `utils.netcdf2csv`

## Project Structure

```text
UpperAtmPy/
├── src/
│   ├── model/
│   │   ├── __init__.py      # Lazy aliases: MSIS2, MSIS00, HWM14, HWM93
│   │   ├── pymsis2/         # NRLMSIS-2.0 wrapper and Fortran sources
│   │   ├── pymsis00/        # NRLMSISE-00 wrapper and Fortran sources
│   │   ├── pyhwm14/         # HWM14 wrapper and Fortran sources
│   │   └── pyhwm93/         # HWM93 wrapper and Fortran sources
│   └── utils/
│       ├── cache.py
│       ├── parallel.py
│       ├── space_weather.py
│       ├── time.py
│       └── xarray_output.py
├── example/
├── tests/
├── data/
│   ├── hwm14data/
│   └── msis2data/
└── quick_run.py
```

## Test

```bash
python -m pytest
python quick_run.py
```
