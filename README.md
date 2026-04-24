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

Before compiling from source, install the following toolchain and Python dependencies.

### Build prerequisites

- Python 3.8+
- CMake (3.20+)
- C/C++ compiler toolchain
- GNU Fortran compiler (`gfortran`)
- `pip` dependencies

Common install steps:

```bash
python -m pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3 python3-pip cmake build-essential gfortran git
```

#### macOS

```bash
brew install python cmake gcc
```

#### Windows

Install:

- Python
- CMake
- MinGW-w64 toolchain (for `gfortran` support), and keep the MinGW runtime directory
  (`...\\mingw64\\bin`) visible in `PATH`.

Example:

```powershell
winget install -e --id Python.Python.3
winget install -e --id Kitware.CMake
winget install -e --id MSYS2.MSYS2
```

Then in an MSYS2/MinGW shell:

```bash
pacman -S --noconfirm --needed mingw-w64-x86_64-toolchain
```

### Build from source

Compile the native libraries before using a model from a source checkout. Make sure you
run CMake from a shell where the compilers above are available.

```bash
cmake --preset native-release
cmake --build --preset native-release
```

### Prebuilt wheels

If building native libraries is inconvenient, download the matching wheel from the repository
`Releases` page and install it directly with pip.

1. Choose a wheel file that matches your OS and architecture.
   Example naming patterns:
   - `upperatmpy-0.1.0-py3-none-manylinux_x86_64.whl`
   - `upperatmpy-0.1.0-py3-none-win_amd64.whl`
2. Install the wheel.

```bash
python -m pip install /path/to/upperatmpy-0.1.0-py3-none-win_amd64.whl
```

Or install directly from a release URL:

```bash
python -m pip install https://github.com/<OWNER>/<REPO>/releases/download/<TAG>/<WHEEL_FILENAME>.whl
```

After installation, use the package as usual:

```python
from model import MSIS2
from utils.time import doy, seconds_of_day

msis = MSIS2(precision="single")
_ = msis.calculate(day=doy(2023, 1, 1), utsec=seconds_of_day(12,0,0),
                  alt_km=100.0, lat_deg=35.0, lon_deg=116.0, f107a=100.0, f107=100.0)
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

### Download and use release data files manually

If you cannot download data files at runtime, you can fetch them manually from
`GitHub Releases`:

1. Open the release page and download data assets (or a combined data archive) for `msis2data` and `hwm14data`.
2. Extract them so you get a data root directory containing both folders:

```bash
UPPERATMPY_DATA_DIR/
├── msis2data/
└── hwm14data/
```

3. Configure the project to load from this local root.

Linux/macOS example:

```bash
export UPPERATMPY_DATA_DIR=/path/to/UPPERATMPY_DATA_DIR
python -m pip install -U /path/to/upperatmpy.whl  # optional
```

Windows PowerShell example:

```powershell
$env:UPPERATMPY_DATA_DIR = "C:\path\to\UPPERATMPY_DATA_DIR"
```

You can also pass the path directly when constructing a model:

```python
from model import MSIS2, HWM14

msis = MSIS2(precision="single", data_dir="C:/path/to/UPPERATMPY_DATA_DIR")
hwm = HWM14(data_dir="C:/path/to/UPPERATMPY_DATA_DIR")
```

## API

Top-level `model` exports only:

- `MSIS2`
- `MSIS00`
- `HWM14`
- `HWM93`

Each class provides `calculate(...)` and returns a plain dictionary.
The model methods accept scalar or broadcastable array inputs.

### Model time helper functions

```python
from utils.time import doy, seconds_of_day
```

- `doy(year, month, day)`: returns day of year (1-366).
- `seconds_of_day(hour, minute=0, second=0.0)`: returns seconds since midnight.

### MSIS2.calculate

Signature:

```python
MSIS2.calculate(*, day, utsec, alt_km, lat_deg, lon_deg, f107a, f107, ap7=None)
```

Input fields:

- `day`: day-of-year, same as `utils.time.doy(...)`.
- `utsec`: UT seconds (0-86400).
- `alt_km`: altitude in km (float or array-like).
- `lat_deg`: geodetic latitude in degrees.
- `lon_deg`: longitude in degrees.
- `f107a`: 81-day average F10.7 solar flux.
- `f107`: daily F10.7 solar flux.
- `ap7`: optional sequence length 7 for geomagnetic activity.

Return fields:

- `alt_km`: output altitude(s), same shape as broadcast inputs.
- `T_local_K`: local temperature (K).
- `T_exo_K`: exospheric temperature (K).
- `densities`: array with shape `(..., 10)` for species:
  `N2, O2, O, He, H, Ar, N, AnomalousO, NO, NPlus`.

### MSIS00.calculate

Signature:

```python
MSIS00.calculate(*, iyd, sec, alt_km, lat_deg, lon_deg, stl_hours, f107a, f107, ap7=None, mass=48, use_anomalous_o=False)
```

Input fields:

- `iyd`: date as integer `YYYYDDD`.
- `sec`: UTC seconds (0-86400).
- `alt_km`: altitude in km.
- `lat_deg`, `lon_deg`: geodetic coordinates in degrees.
- `stl_hours`: local solar time in hours.
- `f107a`: 81-day average F10.7 solar flux.
- `f107`: daily F10.7 solar flux.
- `ap7`: optional sequence length 7.
- `mass`: optional target mass number selector, default `48`.
- `use_anomalous_o`: whether to call anomalous-oxygen mode.

Return fields:

- `alt_km`: output altitude(s).
- `T_local_K`: local temperature (K).
- `T_exo_K`: exospheric temperature (K).
- `densities`: array with shape `(..., 9)` for species:
  `He, O, N2, O2, Ar, H, N, AnomalousO, TotalMass`.

### HWM14.calculate and HWM93.calculate

Both models share the same signature:

```python
calculate(*, iyd, sec, alt_km, glat_deg, glon_deg, stl_hours, f107a, f107, ap2=(0.0, 20.0))
```

Input fields:

- `iyd`: date as integer `YYYYDDD`.
- `sec`: UTC seconds (0-86400).
- `alt_km`: altitude in km.
- `glat_deg`, `glon_deg`: latitude/longitude in degrees.
- `stl_hours`: local solar time in hours.
- `f107a`: 81-day average F10.7 solar flux.
- `f107`: daily F10.7 solar flux.
- `ap2`: optional sequence length 2.

Return fields:

- `alt_km`: output altitude(s).
- `meridional_wind_ms`: meridional (north-south) wind in m/s.
- `zonal_wind_ms`: zonal (east-west) wind in m/s.

### Optional utility modules

These modules are not imported automatically by `import model`.

- `utils.cache`
- `utils.parallel`
- `utils.space_weather`
- `utils.xarray_output`
- `utils.netcdf2csv`

#### `utils.space_weather`

Fetch and cache geomagnetic/solar inputs for model calls.

- `get_indices(date=None, source="celestrak")`: default date is yesterday UTC.
- `get_indices_celestrak(date)`: fetch from CelesTrak space weather file.
- `clear_cache()`: remove cached local files.
- `SpaceWeatherIndices`:
  - `as_msis_params()` returns `{ "f107", "f107a", "ap7" }`
  - `as_hwm_params()` returns `{ "f107", "f107a", "ap2" }`

Usage:

```python
from model import MSIS2
from utils.time import doy, seconds_of_day
from utils.space_weather import get_indices

sw = get_indices()
result = MSIS2(precision="single").calculate(
    day=doy(2023, 1, 1),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=100.0,
    lat_deg=35.0,
    lon_deg=116.0,
    **sw.as_msis_params(),
)
```

#### `utils.cache`

Memoize model/function calls (works for any callable).

- `cached_call(func, cache_size=10000)` returns a wrapped callable.
- wrapper exposes `cache_info()` and `cache_clear()`.

Usage:

```python
from utils.cache import cached_call
from model import MSIS2

msis = MSIS2(precision="single")
cached_calculate = cached_call(msis.calculate)
cached_calculate(...)
cached_calculate(...)
print(cached_calculate.cache_info())
```

#### `utils.parallel`

Run large batches in threads for better throughput.

- `parallel_map(func, items, max_workers=None, show_progress=False)`
- `parallel_batch_compute(compute_func, param_dicts, max_workers=None, show_progress=False)`

Usage:

```python
from utils.parallel import parallel_batch_compute
from utils.time import doy, seconds_of_day
from model import MSIS2

msis = MSIS2(precision="single")

jobs = [dict(day=doy(2023, 1, 1), utsec=seconds_of_day(12,0,0),
             alt_km=a, lat_deg=35.0, lon_deg=116.0,
             f107a=100.0, f107=100.0) for a in [80.0, 100.0, 120.0]]
results = parallel_batch_compute(msis.calculate, jobs, max_workers=4, show_progress=True)
```

#### `utils.xarray_output`

Convert output dictionaries to xarray datasets.

- `msis_to_xarray(result, species_names=None, attrs=None)`
- `hwm_to_xarray(result, attrs=None)`

Usage:

```python
from utils.xarray_output import msis_to_xarray
ds = msis_to_xarray(result, attrs={"model": "MSIS2"})
```

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
