# MSISE-90 — MSISE-90 Neutral Atmosphere Model

[中文文档 (Chinese)](README_zh.md)

## Model Background

MSISE-90 (Mass Spectrometer Incoherent Scatter Extended, 1990) is an empirical neutral atmosphere model developed by A.E. Hedin. It extends the MSIS-86 model downward to ground level, providing temperature and species number densities from the surface to the lower exosphere.

The model takes into account solar activity (F10.7 flux), geomagnetic activity (Ap index), local time, latitude, longitude, and seasonal variations through a spherical harmonic expansion.

This module compiles the Fortran source into a shared library and wraps it via `ctypes` as the `MSISE90` class, following the project's unified `Model.calculate(...)` interface.

**References**:

> Hedin, A.E., *Extension of the MSIS Thermosphere Model into the Middle and Lower Atmosphere*, J. Geophys. Res. **96**, 1159-1172, 1991.

## Directory Structure

```
pymsise90/
├── msise90.for         # Fortran 77 source (GTD6 and helper subroutines)
├── msise90_cshim.F90   # C ABI shim, exports gtd6_eval()
├── CMakeLists.txt      # CMake target msise90
├── __init__.py         # Python Model class
├── build/              # Compiled DLL (created by CMake)
└── README.md           # This file
```

## Fortran Interface

### `msise90.for` — `GTD6` subroutine

```fortran
SUBROUTINE GTD6(IYD, SEC, ALT, GLAT, GLONG, STL, F107A, F107, AP, MASS, D, T)
```

| Parameter | Direction | Type      | Description                                                |
|-----------|-----------|-----------|------------------------------------------------------------|
| `IYD`     | input     | `INTEGER` | Year and day as `YYYYDDD` (e.g., 1990172)                 |
| `SEC`     | input     | `REAL`    | Universal time in seconds                                  |
| `ALT`     | input     | `REAL`    | Altitude in km (0 km to thermosphere)                      |
| `GLAT`    | input     | `REAL`    | Geodetic latitude in degrees                               |
| `GLONG`   | input     | `REAL`    | Geodetic longitude in degrees                              |
| `STL`     | input     | `REAL`    | Local apparent solar time in hours                         |
| `F107A`   | input     | `REAL`    | 3-month average of F10.7 solar flux                       |
| `F107`    | input     | `REAL`    | Daily F10.7 flux for previous day                         |
| `AP`      | input     | `REAL(7)` | Magnetic index (daily Ap or 7-element history)            |
| `MASS`    | input     | `INTEGER` | Mass number selector (48 = all species)                   |
| `D`       | output    | `REAL(8)` | Species number densities (see below)                      |
| `T`       | output    | `REAL(2)` | Temperatures (exo, local)                                 |

Output densities `D(1..8)`:

| Index | Species      | Unit     |
|-------|-------------|----------|
| 1     | He          | cm⁻³     |
| 2     | O           | cm⁻³     |
| 3     | N2          | cm⁻³     |
| 4     | O2          | cm⁻³     |
| 5     | Ar          | cm⁻³     |
| 6     | Total Mass  | g/cm³    |
| 7     | H           | cm⁻³     |
| 8     | N           | cm⁻³     |

Output temperatures `T(1..2)`:

| Index | Description              | Unit |
|-------|--------------------------|------|
| 1     | Exospheric temperature   | K    |
| 2     | Temperature at altitude  | K    |

### `msise90_cshim.F90` — C ABI

```c
void gtd6_eval(int iyd, float sec, float alt, float glat, float glong,
               float stl, float f107a, float f107,
               const float ap[7], int mass, float d_out[8], float t_out[2]);
```

## Input Parameters

| Parameter    | Type          | Description                                                             |
|-------------|---------------|-------------------------------------------------------------------------|
| `iyd`       | int           | Date as `YYYYDDD` (e.g., 1990172)                                      |
| `sec`       | float         | UTC seconds (0-86400)                                                   |
| `alt_km`    | float / array | Altitude in km (0 km to thermosphere)                                   |
| `lat_deg`   | float / array | Geodetic latitude in degrees                                            |
| `lon_deg`   | float / array | Geodetic longitude in degrees                                           |
| `stl_hours` | float         | Local apparent solar time in hours                                      |
| `f107a`     | float         | 81-day average F10.7 solar flux                                        |
| `f107`      | float         | Daily F10.7 solar flux for previous day                                |
| `ap7`       | array-like    | Optional 7-element Ap history; default `[4.0] * 7`                     |
| `mass`      | int           | Mass number selector; default `48` (all species)                       |

## Output

`calculate()` returns a dictionary with the following fields:

| Field        | Type          | Description                           |
|-------------|---------------|---------------------------------------|
| `alt_km`    | float / ndarray | Output altitude(s)                  |
| `T_local_K` | float / ndarray | Temperature at altitude (K)         |
| `T_exo_K`   | float / ndarray | Exospheric temperature (K)          |
| `densities` | ndarray       | Shape `(..., 8)`: He, O, N2, O2, Ar, TotalMass, H, N |

## Usage Examples

### Single-point calculation

```python
from model import MSISE90

model = MSISE90()
result = model.calculate(
    iyd=1990172,
    sec=29000.0,
    alt_km=400.0,
    lat_deg=60.0,
    lon_deg=-70.0,
    stl_hours=16.0,
    f107a=150.0,
    f107=150.0,
)

print(f"Exospheric temperature: {result['T_exo_K']:.1f} K")
print(f"Local temperature: {result['T_local_K']:.1f} K")
print(f"O density: {result['densities'][1]:.3e} cm-3")
```

### Surface calculation

```python
result = model.calculate(
    iyd=1990172,
    sec=29000.0,
    alt_km=0.0,  # Ground level
    lat_deg=60.0,
    lon_deg=-70.0,
    stl_hours=16.0,
    f107a=150.0,
    f107=150.0,
)

print(f"Surface temperature: {result['T_local_K']:.1f} K")
print(f"N2 density: {result['densities'][2]:.3e} cm-3")
```

### Batch calculation

```python
import numpy as np

altitudes = np.linspace(0.0, 500.0, 11)
result = model.calculate(
    iyd=1990172,
    sec=29000.0,
    alt_km=altitudes,
    lat_deg=60.0,
    lon_deg=-70.0,
    stl_hours=16.0,
    f107a=150.0,
    f107=150.0,
)

print(result["T_local_K"].shape)    # (11,)
print(result["densities"].shape)    # (11, 8)
```

## Constructor Parameters

| Parameter    | Default       | Description                    |
|-------------|---------------|--------------------------------|
| `dll_path`  | Auto-detected | Custom DLL path                |

## MASS Parameter

The `mass` parameter selects which species to compute:

| Value | Description                    |
|-------|--------------------------------|
| 0     | Temperature only               |
| 1     | H                              |
| 4     | He                             |
| 14    | N                              |
| 16    | O                              |
| 28    | N2                             |
| 32    | O2                             |
| 40    | Ar                             |
| 48    | All species + total mass       |
| 49    | O2 + total mass                |
