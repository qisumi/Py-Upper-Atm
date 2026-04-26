# AuroraOval — Feldstein Auroral Oval Boundary Model (Holzworth & Meng Parameterization)

[中文文档 (Chinese)](README_zh.md)

## Model Background

Feldstein (1963) empirically characterized the auroral oval morphology as a function of geomagnetic activity level. Holzworth and Meng (1975) fitted seven-parameter Fourier series coefficients for seven Feldstein ovals corresponding to geomagnetic activity levels 0–6, providing a mathematical parameterization of the auroral oval boundaries.

This module compiles the Fortran model into a shared library and wraps it via `ctypes` as the `AuroraOval` class, following the project's unified `Model.calculate(...)` interface.

**No external data files are required** — all Fourier coefficients are hard-coded in the Fortran source.

**References**:

> Feldstein, Y. I., *On Morphology and Auroral and Magnetic Disturbances at High Latitudes*, Geomagn. Aeron. **3**, 138, 1963.

> Holzworth, R. H., & Meng, C.-I., *Mathematical Representation of the Auroral Oval*, Geophys. Res. Lett. **2**, 377, 1975.

## Directory Structure

```
pyaurora/
├── oval.for           # Fortran 77 oval subroutine
├── oval_cshim.F90     # C ABI shim, exports oval_eval()
├── CMakeLists.txt     # CMake target aurora_oval
├── __init__.py        # Python Model class
└── README.md          # This file
```

## Fortran Interface

### `oval.for` — `oval` subroutine

```fortran
subroutine oval(xmlt, iql, pcgl, ecgl)
```

| Parameter | Direction | Type      | Description                                                |
|-----------|-----------|-----------|------------------------------------------------------------|
| `xmlt`    | input     | `real`    | Magnetic local time (hours)                                |
| `iql`     | input     | `integer` | Geomagnetic activity level, 0 (quiet) to 6 (active)       |
| `pcgl`    | output    | `real`    | Poleward boundary corrected geomagnetic latitude (°)       |
| `ecgl`    | output    | `real`    | Equatorward boundary corrected geomagnetic latitude (°)    |

### `oval_cshim.F90` — C ABI

```c
void oval_eval(float xmlt, int iql, float *pcgl, float *ecgl);
```

## Input Parameters

| Parameter | Type          | Description                                                             |
|-----------|---------------|-------------------------------------------------------------------------|
| `mlt_hours`      | float / array | Magnetic local time (hours), in Corrected Geomagnetic Latitude system   |
| `activity_level` | int / array   | Geomagnetic activity level, 0 (quiet) to 6 (active)                    |

## Output

`calculate()` returns a dictionary with the following fields:

| Field                      | Type          | Description                                        |
|----------------------------|---------------|----------------------------------------------------|
| `mlt_hours`                | float / ndarray | Input MLT value(s)                                |
| `activity_level`           | int / ndarray   | Input activity level value(s)                     |
| `poleward_boundary_deg`    | float / ndarray | Poleward boundary corrected geomagnetic latitude (°) |
| `equatorward_boundary_deg` | float / ndarray | Equatorward boundary corrected geomagnetic latitude (°) |

## Usage Examples

### Single-point calculation

```python
from model import AuroraOval

model = AuroraOval()
result = model.calculate(mlt_hours=12.0, activity_level=3)

print(f"Poleward boundary: {result['poleward_boundary_deg']:.2f}°")
print(f"Equatorward boundary: {result['equatorward_boundary_deg']:.2f}°")
```

### Batch calculation

```python
import numpy as np

mlt = np.linspace(0, 24, 25)
levels = np.full_like(mlt, 3, dtype=int)

result = model.calculate(mlt_hours=mlt, activity_level=levels)
print(result["poleward_boundary_deg"].shape)       # (25,)
print(result["equatorward_boundary_deg"].shape)     # (25,)
```

### Iterate all activity levels

```python
for level in range(7):
    r = model.calculate(mlt_hours=0.0, activity_level=level)
    print(f"level={level}: poleward={r['poleward_boundary_deg']:.2f}°, "
          f"equatorward={r['equatorward_boundary_deg']:.2f}°")
```

## Constructor Parameters

| Parameter  | Default         | Description              |
|------------|-----------------|--------------------------|
| `dll_path` | Auto-detected   | Custom DLL path          |

## Coordinate Notes

- Input MLT uses the **Corrected Geomagnetic Coordinate System**.
- Output latitudes are **Corrected Geomagnetic Latitude (CGL)**.
- For coordinate conversions between geographic and corrected geomagnetic:
  - Online: https://nssdc.gsfc.nasa.gov/space/cgm/cgm.html
  - Offline: https://nssdc.gsfc.nasa.gov/pub/models/geomagnetic/geo_cgm/geo-cgm.for

## Acknowledgement

Please acknowledge the software provider (NSSDC) and the model authors (Holzworth & Meng) in any publication that results from work using this software and in any software program/application that includes this model code.
