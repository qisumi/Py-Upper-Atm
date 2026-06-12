# ISRDrift — ISR Ion Drift Model (Richmond et al., 1980)

[中文文档 (Chinese)](README_zh.md)

## Model Background

The Incoherent Scatter Radar (ISR) ion drift model computes quiet-day ionospheric electrostatic pseudo-potential and E x B drift velocities at 300 km altitude for solar minimum conditions. The model is based on spherical harmonic analyses of incoherent scatter radar observations.

This module compiles the Fortran model into a shared library and wraps it via `ctypes` as the `ISRDrift` class, following the project's unified `Model.calculate(...)` interface.

**No external data files are required** — all 128 coefficients are hard-coded in the Fortran source.

**References**:

> Richmond, A. D., et al., *An empirical model of quiet-day ionospheric electric fields at middle and low latitudes*, J. Geophys. Res. **85**, 4658, 1980.

## Directory Structure

```
pyisrdrift/
├── isr_drift.for          # Fortran 77 EFIELD subroutine
├── isr_drift_cshim.F90    # C ABI shim, exports isr_drift_eval()
├── CMakeLists.txt         # CMake target isr_drift
├── __init__.py            # Python Model class
└── README.md              # This file
```

## Fortran Interface

### `isr_drift.for` — `EFIELD` subroutine

```fortran
SUBROUTINE EFIELD(XMLAT, XMLON, DAYNO, UT, ISEASAV, IUTAV, POT, VU, VE)
```

| Parameter | Direction | Type      | Description                                                       |
|-----------|-----------|-----------|-------------------------------------------------------------------|
| `XMLAT`   | input     | `real`    | Magnetic latitude (°)                                             |
| `XMLON`   | input     | `real`    | Magnetic east longitude (°)                                       |
| `DAYNO`   | input     | `real`    | Day of year (1.0 = Jan 1, up to 365.24)                           |
| `UT`      | input     | `real`    | Universal time (hours)                                            |
| `ISEASAV` | input     | `integer` | Seasonal averaging mode (0–4, see below)                          |
| `IUTAV`   | input     | `integer` | UT averaging mode (0 or 1, see below)                             |
| `POT`     | output    | `real`    | Electrostatic pseudo-potential (V)                                |
| `VU`      | output    | `real`    | Poleward/upward drift velocity perpendicular to B in the magnetic meridian plane (m/s) |
| `VE`      | output    | `real`    | Eastward drift velocity (m/s)                                     |

**Seasonal averaging modes (`ISEASAV`)**:

| Value | Meaning                                     |
|-------|---------------------------------------------|
| 0     | No seasonal averaging; use `DAYNO` directly |
| 1     | Average over November – February            |
| 2     | Average over May – August                   |
| 3     | Average over March, April, September, October |
| 4     | Annual average (`DAYNO` is ignored)         |

**UT averaging mode (`IUTAV`)**:

| Value | Meaning                                       |
|-------|-----------------------------------------------|
| 0     | No UT averaging                               |
| 1     | Average over all UT at fixed magnetic local time |

### `isr_drift_cshim.F90` — C ABI

```c
void isr_drift_eval(float xmlat, float xmlon, float dayno, float ut,
                    int isea, int iutav, float *pot, float *vu, float *ve);
```

## Input Parameters

| Parameter       | Type          | Description                                                       |
|-----------------|---------------|-------------------------------------------------------------------|
| `mlat_deg`      | float / array | Magnetic latitude (°)                                             |
| `mlon_deg`      | float / array | Magnetic east longitude (°)                                       |
| `doy`           | float / array | Day of year (1.0–365.24), 1.0 = January 1                         |
| `ut_hours`      | float / array | Universal time (hours)                                            |
| `seasonal_avg`  | int           | Seasonal averaging mode (0–4, default 0)                          |
| `ut_avg`        | int           | UT averaging mode (0 or 1, default 0)                             |

## Output

`calculate()` returns a dictionary with the following fields:

| Field                | Type            | Description                                     |
|----------------------|-----------------|-------------------------------------------------|
| `mlat_deg`           | float / ndarray | Input magnetic latitude (°)                     |
| `mlon_deg`           | float / ndarray | Input magnetic east longitude (°)               |
| `doy`                | float / ndarray | Input day of year                               |
| `ut_hours`           | float / ndarray | Input universal time (hours)                    |
| `potential_V`        | float / ndarray | Electrostatic pseudo-potential (V)              |
| `poleward_drift_ms`  | float / ndarray | Poleward E x B drift velocity (m/s)             |
| `eastward_drift_ms`  | float / ndarray | Eastward E x B drift velocity (m/s)             |

## Usage Examples

### Single-point calculation

```python
from model import ISRDrift

model = ISRDrift()
result = model.calculate(
    mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
)

print(f"Potential: {result['potential_V']:.2f} V")
print(f"Poleward drift: {result['poleward_drift_ms']:.2f} m/s")
print(f"Eastward drift: {result['eastward_drift_ms']:.2f} m/s")
```

### Batch calculation

```python
import numpy as np

mlat = np.linspace(30, 60, 7)
mlon = np.zeros_like(mlat)
doy = np.full_like(mlat, 172.0)
ut = np.full_like(mlat, 12.0)

result = model.calculate(mlat_deg=mlat, mlon_deg=mlon, doy=doy, ut_hours=ut)
print(result["potential_V"].shape)           # (7,)
print(result["poleward_drift_ms"].shape)     # (7,)
print(result["eastward_drift_ms"].shape)     # (7,)
```

### Seasonal averaging modes

```python
for mode in range(5):
    r = model.calculate(
        mlat_deg=45.0, mlon_deg=0.0, doy=172.0, ut_hours=12.0,
        seasonal_avg=mode,
    )
    print(f"seasonal_avg={mode}: potential={r['potential_V']:.2f} V")
```

## Constructor Parameters

| Parameter  | Default       | Description       |
|------------|---------------|-------------------|
| `dll_path` | Auto-detected | Custom DLL path   |

## Coordinate Notes

- Input coordinates use the **magnetic coordinate system** defined by Richmond et al. (1980).
- Output drift components are perpendicular to the geomagnetic field at 300 km altitude.
- Results are geophysically meaningful only for magnetic latitudes between approximately **-65° and +65°**.

## Acknowledgement

Please acknowledge the software provider (NSSDC/CCMC) and the model author (A. D. Richmond) in any publication that results from work using this software.
