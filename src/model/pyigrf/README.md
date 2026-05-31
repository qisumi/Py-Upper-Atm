# IGRF — International Geomagnetic Reference Field

[中文文档 (Chinese)](README_zh.md)

## Model Background

The International Geomagnetic Reference Field (IGRF) is an internationally
standardized spherical-harmonic representation of Earth's main magnetic field.
This module builds the Fortran implementation as a shared library and exposes it
through `ctypes` as the `IGRF` class, following the project's unified
`Model.calculate(...)` interface.

The wrapper supports both IGRF-13 and IGRF-14. IGRF-14 is the default and uses
the 2025 epoch coefficients and secular-variation terms for forward estimates
through 2030. L-shell values are computed by the bundled `SHELLG` routine.

External coefficient files are required. They are resolved through
`utils.model_data.ensure_model_data()`, so callers may use automatic download,
`UPPERATMPY_DATA_DIR`, or the constructor's `data_dir` argument.

## Directory Structure

```text
pyigrf/
├── igrf.for           # Fortran 77 IGRF and SHELLG routines
├── igrf_cshim.F90     # C ABI shim exported for ctypes
├── CMakeLists.txt     # CMake target igrf
├── __init__.py        # Python Model class
├── README.md          # English documentation
└── README_zh.md       # Chinese documentation
```

## Fortran Interface

Core routines in `igrf.for`:

| Routine | Description |
|---------|-------------|
| `FELDCOF(YEAR, DIMO)` | Loads DGRF/IGRF coefficients and computes the dipole moment. |
| `FELDG(GLAT, GLON, ALT, BNORTH, BEAST, BDOWN, BABS)` | Synthesizes north/east/down and total magnetic field components in Gauss. |
| `SHELLG(GLAT, GLON, ALT, DIMO, FL, ICODE, B0)` | Computes the L-shell parameter. |
| `GETSHC(IU, FSPEC, NMAX, ERAD, GH, IER)` | Reads coefficient files from the configured data directory. |

The C ABI shim exports:

```c
void igrf_set_data_root(const char *path);
void igrf_set_version(int ver);
void igrf_eval(float xlat, float xlong, float year, float height,
               float *bnorth, float *beast, float *bdown, float *babs,
               float *xl, int *icode);
```

The Fortran layer returns magnetic field components in Gauss. The Python wrapper
converts them to nT and derives horizontal intensity, inclination, and
declination.

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | float / array | Decimal year, for example `2024.5`. |
| `lat_deg` | float / array | Geodetic latitude in degrees, north positive. |
| `lon_deg` | float / array | Geodetic longitude in degrees, east positive. |
| `alt_km` | float / array | Altitude above sea level in km. |

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
| `B_north_nT` | nT | Northward magnetic field component. |
| `B_east_nT` | nT | Eastward magnetic field component. |
| `B_down_nT` | nT | Downward magnetic field component, positive downward. |
| `B_abs_nT` | nT | Total field intensity. |
| `H_nT` | nT | Horizontal field intensity. |
| `inclination_deg` | degrees | Magnetic inclination, positive downward. |
| `declination_deg` | degrees | Magnetic declination, positive eastward. |
| `L_value` | dimensionless | L-shell parameter from `SHELLG`. |
| `icode` | int / ndarray | L-value status code: `1` normal, `2` unphysical conjugate point, `3` approximation. |

## Usage Examples

### Single-point calculation

```python
from model import IGRF

model = IGRF(igrf_version=14)
result = model.calculate(
    year=2024.5,
    lat_deg=39.9,
    lon_deg=116.4,
    alt_km=0.0,
)

print(f"Total field: {result['B_abs_nT']:.1f} nT")
print(f"Declination: {result['declination_deg']:.2f} deg")
print(f"L value:     {result['L_value']:.3f}")
```

### Batch calculation

```python
from model import IGRF

model = IGRF()
result = model.calculate(
    year=2024.5,
    lat_deg=[30.0, 40.0, 50.0],
    lon_deg=[116.0, 116.0, 116.0],
    alt_km=[0.0, 100.0, 200.0],
)

print(result["B_abs_nT"].shape)  # (3,)
print(result["L_value"])
```

### Use local data without network access

```python
from model import IGRF

model = IGRF(
    igrf_version=14,
    data_dir="C:/path/to/UPPERATMPY_DATA_DIR",
    auto_download=False,
)
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dll_path` | Auto-detected | Custom path to `igrf.dll` or `libigrf.so`. |
| `igrf_version` | `14` | IGRF generation, either `13` or `14`. |
| `data_dir` | Auto-resolved | Data root containing `igrf13data/` or `igrf14data/`. |
| `auto_download` | `True` | Download missing coefficient files when possible. |

## Data Files

The data root contains version-specific coefficient directories:

```text
UPPERATMPY_DATA_DIR/
├── igrf13data/
└── igrf14data/
```

IGRF-13 uses DGRF/IGRF coefficient files through 2020 and secular variation
through 2025. IGRF-14 uses updated DGRF-2020, IGRF-2025, and 2025-2030 secular
variation coefficients.

## References

- Alken, P., Thébault, E., Beggan, C. D., et al. (2021). International Geomagnetic Reference Field: the thirteenth generation. *Earth, Planets and Space*, 73, 49. https://doi.org/10.1186/s40623-020-01288-x
- IGRF-14 special issue collection: https://link.springer.com/collections/jecafgcbaf
