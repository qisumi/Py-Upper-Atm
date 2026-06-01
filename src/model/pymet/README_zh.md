# MET — Marshall Engineering Thermosphere Model

## Model Background

The Marshall Engineering Thermosphere (MET) model was developed by Mike Hickey at NASA Marshall Space Flight Center in 1987. It is based on a modified Jacchia 1970 model optimized for engineering applications.

The model provides temperature profiles, number density profiles for major neutral species (N2, O2, O, Ar, He, H), total density, pressure, and other thermodynamic parameters over the altitude range 90–2500 km.

This module compiles the Fortran source into a shared library and wraps it via `ctypes` as the `MET` class, following the project's unified `Model.calculate(...)` interface.

**No external data files are required** — all coefficients are hard-coded in the Fortran source.

**References**:

> Hickey, M. P., "Marshall Engineering Thermosphere Model," NASA/MSFC, 1987.

## Directory Structure

```
pymet/
├── met.for              # Fortran 77 original model subroutines
├── met_cshim.F90        # C ABI shim, exports met_eval()
├── CMakeLists.txt       # CMake target met
├── __init__.py          # Python Model class
└── README_zh.md         # This file
```

## Fortran Interface

### `met.for` — `J70` subroutine

```fortran
SUBROUTINE J70(INDATA, OUTDATA)
```

| Parameter | Direction | Type | Description |
|-----------|-----------|------|-------------|
| `INDATA` | input | `REAL*4(12)` | Input data array |
| `OUTDATA` | output | `REAL*4(12)` | Output data array |

**Input array elements**:

| Index | Description |
|-------|-------------|
| 1 | Altitude (km) |
| 2 | Latitude (degrees) |
| 3 | Longitude (degrees) |
| 4 | Year (2 digits) |
| 5 | Month |
| 6 | Day |
| 7 | Hour |
| 8 | Minute |
| 9 | Geomagnetic index type (1=Kp, 2=Ap) |
| 10 | F10.7 solar radio noise flux |
| 11 | 162-day average F10.7 |
| 12 | Geomagnetic activity index |

**Output array elements**:

| Index | Description |
|-------|-------------|
| 1 | Exospheric temperature (K) |
| 2 | Temperature at altitude Z (K) |
| 3 | N2 number density (per m³) |
| 4 | O2 number density (per m³) |
| 5 | O number density (per m³) |
| 6 | Ar number density (per m³) |
| 7 | He number density (per m³) |
| 8 | H number density (per m³) |
| 9 | Average molecular weight |
| 10 | Total density (kg/m³) |
| 11 | log10(total density) |
| 12 | Total pressure (Pa) |

### `met_cshim.F90` — C ABI

```c
void met_eval(
    float *indata,   // Input array (12 elements)
    float *outdata,  // Output array (12 elements)
    float *auxdata   // Auxiliary output array (5 elements)
);
```

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `alt_km` | float / array | Altitude (km) |
| `lat_deg` | float / array | Geodetic latitude (degrees) |
| `lon_deg` | float / array | Geodetic longitude (degrees) |
| `year` | float / array | Year (2 digits) |
| `month` | float / array | Month (1-12) |
| `day` | float / array | Day of month |
| `hour` | float / array | Hour (0-23) |
| `minute` | float / array | Minute (0-59) |
| `geo_index_type` | float / array | Geomagnetic index type (1=Kp, 2=Ap) |
| `f107` | float / array | F10.7 solar radio noise flux |
| `f107a` | float / array | 162-day average F10.7 |
| `ap` | float / array | Geomagnetic activity index Ap |

## Output

`calculate()` returns a dictionary with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `alt_km` | float / ndarray | Output altitude(s) |
| `lat_deg` | float / ndarray | Latitude (degrees) |
| `lon_deg` | float / ndarray | Longitude (degrees) |
| `T_exo_K` | float / ndarray | Exospheric temperature (K) |
| `T_local_K` | float / ndarray | Local temperature at altitude Z (K) |
| `N2_m3` | float / ndarray | N2 number density (per m³) |
| `O2_m3` | float / ndarray | O2 number density (per m³) |
| `O_m3` | float / ndarray | O number density (per m³) |
| `Ar_m3` | float / ndarray | Ar number density (per m³) |
| `He_m3` | float / ndarray | He number density (per m³) |
| `H_m3` | float / ndarray | H number density (per m³) |
| `mean_molecular_weight` | float / ndarray | Average molecular weight |
| `total_density_kg_m3` | float / ndarray | Total mass density (kg/m³) |
| `log10_density` | float / ndarray | log10 of total density |
| `pressure_Pa` | float / ndarray | Total pressure (Pa) |
| `gravity_m_s2` | float / ndarray | Gravitational acceleration (m/s²) |
| `gamma` | float / ndarray | Ratio of specific heats |
| `scale_height_m` | float / ndarray | Pressure scale-height (m) |
| `cp` | float / ndarray | Specific heat at constant pressure |
| `cv` | float / ndarray | Specific heat at constant volume |

## Usage Examples

### Single-point calculation

```python
from model import MET

model = MET()
result = model.calculate(
    alt_km=200.0,
    lat_deg=35.0,
    lon_deg=116.0,
    year=23,  # 2023
    month=7,
    day=15,
    hour=12,
    minute=0,
    geo_index_type=2,  # Ap
    f107=100.0,
    f107a=100.0,
    ap=15.0,
)

print(f"Exospheric temperature: {result['T_exo_K']:.2f} K")
print(f"Local temperature: {result['T_local_K']:.2f} K")
print(f"Total density: {result['total_density_kg_m3']:.2e} kg/m³")
```

### Profile calculation

```python
import numpy as np

alts = np.arange(100, 501, 50)  # 100-500 km, every 50 km
result = model.calculate(
    alt_km=alts,
    lat_deg=35.0,
    lon_deg=116.0,
    year=23,
    month=7,
    day=15,
    hour=12,
    minute=0,
    geo_index_type=2,
    f107=100.0,
    f107a=100.0,
    ap=15.0,
)

print(f"Temperature range: [{result['T_local_K'].min():.1f}, {result['T_local_K'].max():.1f}] K")
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dll_path` | Auto-detected | Custom DLL path |

## Model Notes

- The model is valid for altitudes 90–2500 km
- Based on modified Jacchia 1970 model
- Includes seasonal-latitudinal variation corrections
- Includes helium density seasonal-latitudinal variation corrections
- All output is in MKS units

## References

1. Jacchia, L. G., "New Static Models of the Thermosphere and Exosphere with Empirical Temperature Profiles," SAO Special Report No. 313, 1970.

2. Hickey, M. P., "Marshall Engineering Thermosphere Model," NASA/MSFC, ED44, 1987.
