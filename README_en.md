# UpperAtmPy

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Placeholder-lightgrey)

**UpperAtmPy** is a unified Python interface for upper atmospheric models, wrapping standard Fortran implementations for high-performance calculations of neutral temperature, density, and horizontal winds.

The library supports the following models via `ctypes` bindings:
- **NRLMSIS-2.0** (Naval Research Laboratory Mass Spectrometer and Incoherent Scatter Radar, 2020)
- **NRLMSISE-00** (Legacy MSIS-00 model)
- **HWM14** (Horizontal Wind Model 2014)
- **HWM93** (Horizontal Wind Model 1993)

## Features

- **Unified Python API**: Consistent interfaces for all temperature/density and wind models.
- **High Performance**: Direct Fortran DLL calls via `ctypes`.
- **Batch Processing**: Built-in support for vectorization using `numpy`.
- **Type Safety**: Comprehensive type hints and dataclasses for results.
- **No Heavy Dependencies**: Core functionality relies only on `numpy`.

## Requirements

- **Operating System**: Windows (requires DLL compilation)
- **Python**: 3.8+
- **Compilers**: MinGW / gfortran (for compiling the Fortran source code)
- **Python Dependencies**:
  - `numpy` (Required)
  - `pandas`, `xarray` (Optional, for data utilities)

## Installation & Build

This project runs directly from source. You must compile the Fortran DLLs before using the library.

### 1. Clone the Repository
```bash
git clone https://github.com/qisumi/Py-Upper-Atm.git
cd Py-Upper-Atm
```

### 2. Compile DLLs
The project includes PowerShell scripts to compile the Fortran source code using `gfortran`.

**Compile NRLMSIS-2.0:**
```powershell
cd model/pymsis2
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../..
```

**Compile HWM14:**
```powershell
cd model/pyhwm14
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../..
```

*(Repeat for `pyhwm93` and `pymsis00` if needed)*

## Quick Start

### Temperature and Density (NRLMSIS-2.0)

```python
from model import TempDensityModel, convert_date_to_day, calculate_seconds_of_day

# Initialize model
model = TempDensityModel()

# Calculate parameters
day_of_year = convert_date_to_day(2023, 1, 1)
ut_seconds = calculate_seconds_of_day(12, 0, 0)  # 12:00:00 UTC

# Calculate for a single point
result = model.calculate_point(
    day=day_of_year,    # Day of year (1-366)
    utsec=ut_seconds,   # UTC seconds
    alt_km=100.0,       # Altitude in km
    lat_deg=35.0,       # Latitude
    lon_deg=116.0,      # Longitude
    f107a=100.0,        # 81-day average F10.7
    f107=100.0,         # Daily F10.7
    ap7=None            # Optional: Geomagnetic indices
)

print(f"Temperature: {result.T_local_K:.2f} K")
print(f"N2 Density: {result.densities[0]:.2e} cm^-3")
```

### Horizontal Wind (HWM14)

```python
from model import WindModel

# Initialize model
wind_model = WindModel()

# Calculate for a single point
# iyd format: YYYYDDD (e.g., 2023001 for Jan 1, 2023)
meridional, zonal = wind_model.calculate_point(
    iyd=2023001,
    sec=43200.0,        # 12:00:00 UTC
    alt_km=100.0,
    glat_deg=35.0,
    glon_deg=116.0,
    stl_hours=12.0,     # Local solar time
    f107a=100.0,
    f107=100.0,
    ap2=(0.0, 20.0)     # Geomagnetic indices
)

print(f"Meridional Wind (North/South): {meridional:.2f} m/s")
print(f"Zonal Wind (East/West): {zonal:.2f} m/s")
```

## API Overview

The library exposes two main classes in `model/__init__.py`:

### `TempDensityModel`
- `calculate_point(...)`: Computes temperature and density for a single location/time.
- `calculate_batch(...)`: Vectorized computation for arrays of inputs (e.g., altitude profiles).

### `WindModel`
- `calculate_point(...)`: Computes meridional and zonal wind components.
- `calculate_batch(...)`: Vectorized computation for arrays of inputs.

### Helper Functions
- `convert_date_to_day(year, month, day)`
- `calculate_seconds_of_day(hour, minute, second)`

## Project Structure

```
UpperAtmPy/
├── model/
│   ├── __init__.py           # Public API exports
│   ├── temp_density_model.py # Main wrapper class for MSIS
│   ├── wind_model.py         # Main wrapper class for HWM
│   ├── pymsis2/              # NRLMSIS-2.0 Fortran source & build script
│   ├── pymsis00/             # NRLMSISE-00 Fortran source & build script
│   ├── pyhwm14/              # HWM14 Fortran source & build script
│   └── pyhwm93/              # HWM93 Fortran source & build script
├── example/                  # Usage scripts and tests
├── utils/                    # Data processing utilities
├── hwm14data/               # Data files for HWM14
└── quick_run.py             # Demonstration script
```

## License

[License Information Placeholder]
