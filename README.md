# UpperAtmPy

[中文文档 (Chinese)](README_zh.md)

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Placeholder-lightgrey)

**UpperAtmPy** is a unified Python interface for upper atmospheric models, wrapping standard Fortran implementations for efficient computation of neutral temperature, density, and horizontal wind fields.

The library supports the following models via `ctypes` bindings:
- **NRLMSIS-2.0** (Naval Research Laboratory Mass Spectrometer and Incoherent Scatter Radar Model, 2020)
- **NRLMSISE-00** (Legacy MSIS-00 model)
- **HWM14** (Horizontal Wind Model 2014)
- **HWM93** (Horizontal Wind Model 1993)

## Features

- **Unified Python API**: Consistent interface for all temperature/density and wind models.
- **Cross-platform**: Supports Windows, Linux, and macOS with PowerShell and Bash build scripts.
- **High Performance**: Direct calls to Fortran shared libraries via `ctypes`.
- **Batch Processing**: Built-in vectorized computation using `numpy`.
- **Parallel Computing**: Multi-threaded parallel computation support for large-scale batch calculations.
- **Result Caching**: Built-in LRU cache mechanism to avoid redundant computation.
- **Space Weather Data**: Automatic retrieval of F10.7, Ap, and other geomagnetic activity indices.
- **xarray Integration**: Convert results to xarray Datasets for downstream analysis.
- **Type Safety**: Comprehensive type hints and result dataclasses.
- **Lightweight**: Core functionality depends only on `numpy`.

## Requirements

- **OS**: Windows / Linux / macOS
- **Python**: 3.8+
- **Compiler**: gfortran (MinGW on Windows)
- **Python Dependencies**:
  - `numpy` (required)
  - `xarray` (optional, for data conversion)
  - `pandas` (optional, for data utilities)
  - `tqdm` (optional, for progress bars)

## Installation & Build

This project runs directly from source. Before using the library, you must compile the Fortran shared libraries.

### 1. Clone the Repository
```bash
git clone https://github.com/qisumi/Py-Upper-Atm.git
cd Py-Upper-Atm
```

### 2. Compile Shared Libraries
The project includes both PowerShell (Windows) and Bash (Linux/macOS) build scripts.

**Windows (PowerShell):**
```powershell
# Compile NRLMSIS-2.0
cd model/pymsis2
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../..

# Compile HWM14
cd model/pyhwm14
powershell -ExecutionPolicy Bypass -File compile.ps1
cd ../..
```

**Linux / macOS (Bash):**
```bash
# Compile NRLMSIS-2.0
cd model/pymsis2
chmod +x compile.sh && ./compile.sh
cd ../..

# Compile HWM14
cd model/pyhwm14
chmod +x compile.sh && ./compile.sh
cd ../..
```

*(Repeat for `pyhwm93` and `pymsis00` as needed.)*

## Quick Start

### Temperature & Density (NRLMSIS-2.0)

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

The library exposes the following components from `model/__init__.py`:

### Core Model Classes

#### `TempDensityModel`
- `calculate_point(...)`: Compute temperature and density at a single location/time.
- `calculate_batch(...)`: Vectorized computation over input arrays (e.g., altitude profiles).

#### `WindModel`
- `calculate_point(...)`: Compute meridional and zonal wind components.
- `calculate_batch(...)`: Vectorized computation over input arrays.

### Result Dataclasses
- `TempDensityResult`: Temperature and density computation result
- `WindResult`: Wind computation result

### Cached Models
- `CachedModel`: Temperature/density model wrapper with LRU cache
- `CachedWindModel`: Wind model wrapper with LRU cache

### Space Weather
- `SpaceWeatherIndices`: Space weather indices dataclass
- `get_indices(date)`: Retrieve space weather indices for a given date

### Parallel Computing
- `parallel_map(func, items)`: Parallel mapping function
- `parallel_batch_compute(compute_func, param_dicts)`: Parallel batch computation

### xarray Integration
- `temp_density_results_to_xarray(results)`: Convert temperature/density results to xarray Dataset
- `wind_results_to_xarray(results)`: Convert wind results to xarray Dataset

### Utility Functions
- `convert_date_to_day(year, month, day)`: Convert date to day of year
- `calculate_seconds_of_day(hour, minute, second)`: Convert time to seconds
- `calculate_wind_at_point(...)`: Convenience function for wind computation
- `calculate_wind_batch(...)`: Convenience function for batch wind computation

## Project Structure

```
UpperAtmPy/
├── model/
│   ├── __init__.py           # Public API exports
│   ├── temp_density_model.py # Main MSIS wrapper class
│   ├── wind_model.py         # Main HWM wrapper class
│   ├── cache.py              # Result caching module
│   ├── parallel.py           # Parallel computing module
│   ├── space_weather.py      # Space weather index retrieval
│   ├── xarray_output.py      # xarray data conversion
│   ├── pymsis2/              # NRLMSIS-2.0 Fortran source and build scripts
│   ├── pymsis00/             # NRLMSISE-00 Fortran source and build scripts
│   ├── pyhwm14/              # HWM14 Fortran source and build scripts
│   └── pyhwm93/              # HWM93 Fortran source and build scripts
├── example/                  # Usage scripts and tests
├── utils/                    # Data processing utilities
├── hwm14data/               # HWM14 data files
└── quick_run.py             # Demo script
```

## License

See [LICENSE](LICENSE) for details.
