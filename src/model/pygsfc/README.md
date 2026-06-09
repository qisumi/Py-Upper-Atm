# GSFC — Goddard Space Flight Center Geomagnetic Field Models

[中文文档 (Chinese)](README_zh.md)

## Model Background

The GSFC geomagnetic field models are a series of spherical harmonic models
developed at NASA's Goddard Space Flight Center. This module wraps the Fortran 77
implementation (subroutines FIDD, FID, MAGF) as a shared library and exposes it
through `ctypes` as the `GSFC` class, following the project's unified
`Model.calculate(...)` interface.

Three model versions are supported:

| Version | Model | Epoch | Max Degree |
|---------|-------|-------|------------|
| 80 | GSFC 9/80 | 1980.0 | 9 |
| 83 | GSFC 12/83 | 1980.0 | 14 |
| 87 | GSFC 11/87 | 1982.0 | 14 |

The models support time-dependent coefficients with up to third-order secular
variation terms. Both geodetic and geocentric coordinate systems are supported.

External coefficient data files are required. They are resolved through
`utils.model_data.ensure_model_data()`, so callers may use
`UPPERATMPY_DATA_DIR`, the constructor's `data_dir` argument, or automatic
download when matching release assets are available.

## Directory Structure

```text
pygsfc/
├── gsfcsub.for        # Fortran 77 source (FIDD, FID, MAGF)
├── gsfc_cshim.F90     # C ABI shim exported for ctypes
├── CMakeLists.txt     # CMake target gsfc
├── __init__.py        # Python Model class
├── README.md          # English documentation
└── README_zh.md       # Chinese documentation
```

## Fortran Interface

Core routines in `gsfcsub.for`:

| Routine | Description |
|---------|-------------|
| `FIDD(MODEL, JJ, DLAT, DLONG, ALT1, TM, X, Y, Z, F)` | Driver routine. Opens the coefficient file and calls FID. |
| `FID(IU, J, MM, NEXT, IDST, DLAT, DLONG, Q1, TM, DST, NMX, L, X, Y, Z, F)` | Core evaluator. Reads coefficients and computes time-dependent field. |
| `MAGF` | Field computation via spherical harmonic synthesis. |

The C ABI shim exports:

```c
void gsfc_set_data_root(const char *path);
void gsfc_eval(int model, float lat, float lon, float alt, float year,
               int jj, float *x, float *y, float *z, float *f);
```

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | float / array | Decimal year, for example `1985.5`. |
| `lat_deg` | float / array | Geodetic latitude in degrees, north positive. |
| `lon_deg` | float / array | Geodetic longitude in degrees, east positive. |
| `alt_km` | float / array | Geodetic altitude in km above sea level. |

Scalar inputs return scalar values. Array inputs are broadcast with NumPy and
return arrays with the broadcast shape.

## Output

`calculate()` returns a dictionary with the following fields:

| Field | Unit / Type | Description |
|-------|-------------|-------------|
| `year` | float / ndarray | Broadcast input year. |
| `lat_deg` | float / ndarray | Broadcast input latitude. |
| `lon_deg` | float / ndarray | Broadcast input longitude. |
| `alt_km` | float / ndarray | Broadcast input altitude. |
| `X_nT` | nT | Northward magnetic field component. |
| `Y_nT` | nT | Eastward magnetic field component. |
| `Z_nT` | nT | Downward magnetic field component, positive downward. |
| `F_nT` | nT | Total field intensity. |
| `H_nT` | nT | Horizontal field intensity. |
| `inclination_deg` | degrees | Magnetic inclination, positive downward. |
| `declination_deg` | degrees | Magnetic declination, positive eastward. |

## Usage Examples

### Single-point calculation

```python
from model import GSFC

model = GSFC(gsfc_version=87)
result = model.calculate(
    year=1985.0,
    lat_deg=39.9,
    lon_deg=116.4,
    alt_km=0.0,
)

print(f"Total field: {result['F_nT']:.1f} nT")
print(f"Declination: {result['declination_deg']:.2f} deg")
```

### Batch calculation

```python
from model import GSFC

model = GSFC(gsfc_version=87)
result = model.calculate(
    year=1985.0,
    lat_deg=[30.0, 40.0, 50.0],
    lon_deg=[116.0, 116.0, 116.0],
    alt_km=[0.0, 100.0, 200.0],
)

print(result["F_nT"].shape)  # (3,)
```

### Compare model versions

```python
from model import GSFC

m80 = GSFC(gsfc_version=80)
m83 = GSFC(gsfc_version=83)
m87 = GSFC(gsfc_version=87)

r80 = m80.calculate(year=1980.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
r83 = m83.calculate(year=1980.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
r87 = m87.calculate(year=1980.0, lat_deg=39.9, lon_deg=116.4, alt_km=0.0)
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dll_path` | Auto-detected | Custom path to `gsfc.dll` or `libgsfc.so`. |
| `gsfc_version` | `87` | Model version: `80`, `83`, or `87`. |
| `data_dir` | Auto-resolved | Data root containing the `gsfcdata/` directory. |
| `auto_download` | `True` | Download missing coefficient files when matching release assets are available. |

## Data Files

The data root contains three ASCII coefficient files:

```text
UPPERATMPY_DATA_DIR/
└── gsfcdata/
    ├── GSFC80.DAT    # GSFC 9/80 coefficients
    ├── GSFC83.DAT    # GSFC 12/83 coefficients
    └── GSFC87.DAT    # GSFC 11/87 coefficients
```

## References

- Cain, J. C., Davis, W. M., and Jensen, D. C. (1965). A proposed model for the
  international geomagnetic reference field—1965. *Journal of Geophysical Research*,
  70(15), 3647–3652.
- GSFC geomagnetic field model coefficients: `TODO/GSFC-Model-Coefficients/`
