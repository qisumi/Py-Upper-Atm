# Jensen & Cain (1962) Geomagnetic Field Model

## Overview

The Jensen & Cain (1962) model is an early spherical harmonic model of the Earth's main magnetic field. It was widely used for calculating geomagnetic coordinates during early satellite missions.

**Reference**: D. C. Jensen and J. C. Cain, "An Interim Geomagnetic Field," *J. Geophys. Res.* 67, 3568, 1962.

## Model Characteristics

- **Epoch**: 1960.0
- **Maximum degree and order**: 6 (48 non-zero coefficients)
- **Data source**: ~74,000 ground observations of H and F since 1940
- **Coordinate system**: Geodetic (oblateness not accounted for in coefficient determination)
- **Time variation**: None (no secular variation coefficients)

## Directory Structure

```
pyjensen/
├── fieldg.for           # Fortran 77 source (FIELDG and FIELD subroutines)
├── jensen_cshim.F90     # Fortran 90 C ABI shim
├── CMakeLists.txt        # CMake build configuration
├── __init__.py           # Python Model class
├── README.md             # This file
└── README_zh.md          # Chinese documentation
```

## Fortran Interface

### FIELDG Subroutine

```fortran
SUBROUTINE FIELDG(DLAT, DLONG, ALT, TM, NMX, L, X, Y, Z, F)
```

**Inputs:**
- `DLAT` — Geodetic latitude (degrees, north positive)
- `DLONG` — Geodetic longitude (degrees, east positive)
- `ALT` — Altitude above sea level (km)
- `TM` — Decimal year (e.g., 1960.0)
- `NMX` — Maximum degree and order (1–6)
- `L` — Control flag (0 = use embedded coefficients, >0 = read from file)

**Outputs:**
- `X` — North component of B (nT)
- `Y` — East component of B (nT)
- `Z` — Down component of B (nT, positive downward)
- `F` — Total field strength |B| (nT)

## Python API

### Constructor

```python
from model import JensenCain

model = JensenCain(
    dll_path=None,      # Path to DLL (auto-detected if None)
    data_dir=None,      # Path to data directory
    auto_download=True,  # Auto-download data if not found
)
```

### calculate() Method

```python
result = model.calculate(
    year=1960.0,      # Decimal year (scalar or array)
    lat_deg=45.0,     # Geodetic latitude (degrees, north positive)
    lon_deg=0.0,      # Geodetic longitude (degrees, east positive)
    alt_km=0.0,       # Altitude above sea level (km)
    nmx=6,            # Maximum degree and order (1–6, default 6)
)
```

### Return Dictionary

| Key | Description | Unit |
|-----|-------------|------|
| `year` | Input year | - |
| `lat_deg` | Input latitude | degrees |
| `lon_deg` | Input longitude | degrees |
| `alt_km` | Input altitude | km |
| `X_nT` | North component | nT |
| `Y_nT` | East component | nT |
| `Z_nT` | Down component | nT |
| `F_nT` | Total field strength | nT |
| `H_nT` | Horizontal component | nT |
| `inclination_deg` | Magnetic inclination (dip angle) | degrees |
| `declination_deg` | Magnetic declination | degrees |

## Usage Example

```python
from model import JensenCain

# Single point calculation
model = JensenCain()
result = model.calculate(
    year=1960.0,
    lat_deg=45.0,
    lon_deg=0.0,
    alt_km=0.0,
)
print(f"Total field: {result['F_nT']:.1f} nT")

# Batch calculation
import numpy as np
lats = np.linspace(-90, 90, 19)
result = model.calculate(
    year=1960.0,
    lat_deg=lats,
    lon_deg=0.0,
    alt_km=0.0,
)
print(f"Field range: {result['F_nT'].min():.1f} to {result['F_nT'].max():.1f} nT")
```

## Limitations

- No time variation (secular variation) — coefficients are for epoch 1960.0 only
- Lower accuracy compared to modern models (e.g., IGRF)
- Oblateness of Earth not accounted for in coefficient determination
- Maximum degree and order limited to 6

## References

1. Jensen, D. C. and Cain, J. C. (1962). An Interim Geomagnetic Field. *Journal of Geophysical Research*, 67(9), 3568–3569.
