# AGENTS.md - AI Coding Agent Guidelines for UpperAtmPy

## Project Overview

UpperAtmPy is a Python wrapper library for upper atmospheric models. The project uses a `src/` layout and exposes one public class per model:

- `model.MSIS2`
- `model.MSIS00`
- `model.HWM14`
- `model.HWM93`

Each class provides one public calculation method: `calculate(...)`. Do not reintroduce multi-model wrappers or old helper exports such as `NRLMSIS2`, `gtd7`, `hwm14_eval`, or `hwm93_eval`.

## Build Commands

```powershell
cd src/model/pymsis2
powershell -ExecutionPolicy Bypass -File compile.ps1

cd src/model/pymsis00
powershell -ExecutionPolicy Bypass -File compile.ps1

cd src/model/pyhwm14
powershell -ExecutionPolicy Bypass -File compile.ps1

cd src/model/pyhwm93
powershell -ExecutionPolicy Bypass -File compile.ps1
```

## Test Commands

```bash
python -m pytest
python quick_run.py
python example/test_msis20.py
python example/test_msis00.py
python example/test_hwm14.py
python example/test_hwm93.py
```

## Public API Pattern

```python
from model import MSIS2
from utils.time import doy, seconds_of_day

model = MSIS2(precision="single")
result = model.calculate(
    day=doy(2023, 1, 1),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=100.0,
    lat_deg=35.0,
    lon_deg=116.0,
    f107a=100.0,
    f107=100.0,
)
```

MSIS result dictionaries contain:

- `alt_km`
- `T_local_K`
- `T_exo_K`
- `densities`

HWM result dictionaries contain:

- `alt_km`
- `meridional_wind_ms`
- `zonal_wind_ms`

## Project Structure

```text
UpperAtmPy/
├── src/
│   ├── model/
│   │   ├── __init__.py
│   │   ├── pymsis2/
│   │   ├── pymsis00/
│   │   ├── pyhwm14/
│   │   └── pyhwm93/
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

## Code Style Guidelines

- Use type hints for public function and method signatures.
- Keep user-facing docstrings and errors in Chinese where practical.
- Prefer keyword-only arguments for model calculation methods.
- Keep each model module's `__all__` to `["Model"]`.
- `model.__all__` must stay `["MSIS2", "MSIS00", "HWM14", "HWM93"]`.
- Utility code belongs in `src/utils`, not `src/model`.
- `import model` must not load any model DLL; DLLs should load when a concrete model is instantiated.

## FFI Notes

- DLLs are loaded with `ctypes`.
- Windows builds may require MinGW runtime directories to be discoverable.
- HWM14 uses `HWMPATH`; default it to existing local data if the user has not set it.
- Do not delete or overwrite compiled DLLs or Fortran sources unless explicitly requested.
