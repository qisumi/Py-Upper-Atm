# Chiu Ionospheric Electron Density Model

[中文文档 (Chinese)](README_zh.md)

## Model Background

The Chiu ionospheric model is an empirical electron density model that combines three modified Chapman functions for the E, F1, and F2 layers. It describes ionospheric electron density profiles over roughly 90-500 km.

Inputs include solar activity, local time, season, geographic latitude, geomagnetic latitude/longitude, and magnetic dip angle. This module compiles the Fortran source into a shared library and wraps it via `ctypes` as the `Chiu` class, following the project's unified `Model.calculate(...)` interface.

**No external data files are required** - all empirical coefficients are hard-coded in the Fortran source.

## Directory Structure

```text
pychiu/
├── chiu.for          # Fortran 77 model subroutine
├── chiu_cshim.F90    # C ABI shim, exports chiu_eval()
├── CMakeLists.txt    # CMake target chiu
├── __init__.py       # Python Model class
├── README.md         # English documentation
└── README_zh.md      # Chinese documentation
```

## Fortran Interface

### `chiu.for` - `IONDEN` subroutine

```fortran
SUBROUTINE IONDEN(QTOT, QI, Z, RZUR, PHI, TMO, RLT, RLTM, RLGM, DIP)
```

| Parameter | Direction | Type | Description |
|-----------|-----------|------|-------------|
| `QTOT` | output | `real` | Total electron density, in units of `1.0E5 cm^-3` |
| `QI` | output | `real(3)` | E, F1, and F2 layer electron densities, in units of `1.0E5 cm^-3` |
| `Z` | input | `real` | Altitude in km, 90-500; set to 0 to return layer peak densities |
| `RZUR` | input | `real` | Zurich smoothed sunspot number |
| `PHI` | input | `real` | Local time angle in radians from midnight; 0 is midnight, pi is noon |
| `TMO` | input | `real` | Annual time in months from December 15 of the previous year |
| `RLT` | input | `real` | Geographic latitude in radians |
| `RLTM` | input | `real` | Geomagnetic latitude in radians |
| `RLGM` | input | `real` | Geomagnetic east longitude in radians |
| `DIP` | input | `real` | Geomagnetic dip angle in radians |

### `chiu_cshim.F90` - C ABI

```c
void chiu_eval(float *indata, float *outdata);
```

`indata` contains 8 input values: `Z, RZUR, PHI, TMO, RLT, RLTM, RLGM, DIP`. `outdata` contains 4 output values: `QTOT, QI_E, QI_F1, QI_F2`.

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `alt_km` | float / array | Altitude in km, 90-500; set to 0 to return layer peak densities |
| `sunspot_number` | float / array | Zurich smoothed sunspot number |
| `local_time_rad` | float / array | Local time angle in radians from midnight; 0 is midnight, pi is noon |
| `month_from_dec15` | float / array | Annual time in months from December 15 of the previous year |
| `geo_lat_rad` | float / array | Geographic latitude in radians |
| `geo_mag_lat_rad` | float / array | Geomagnetic latitude in radians |
| `geo_mag_lon_rad` | float / array | Geomagnetic east longitude in radians |
| `dip_angle_rad` | float / array | Geomagnetic dip angle in radians |

## Output

`calculate()` returns a dictionary with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `alt_km` | float / ndarray | Input altitude |
| `sunspot_number` | float / ndarray | Input sunspot number |
| `Ne_total_cm3` | float / ndarray | Total electron density (cm^-3) |
| `Ne_E_cm3` | float / ndarray | E layer electron density (cm^-3) |
| `Ne_F1_cm3` | float / ndarray | F1 layer electron density (cm^-3) |
| `Ne_F2_cm3` | float / ndarray | F2 layer electron density (cm^-3) |

## Usage Examples

### Single-point calculation

```python
import math
from model import Chiu

model = Chiu()
result = model.calculate(
    alt_km=300.0,
    sunspot_number=100.0,
    local_time_rad=math.pi,
    month_from_dec15=6.0,
    geo_lat_rad=math.radians(35.0),
    geo_mag_lat_rad=math.radians(25.0),
    geo_mag_lon_rad=math.radians(120.0),
    dip_angle_rad=math.radians(45.0),
)

print(f"Total electron density: {result['Ne_total_cm3']:.1f} cm^-3")
print(f"F2 layer electron density: {result['Ne_F2_cm3']:.1f} cm^-3")
```

### Altitude profile

```python
alts = [100.0, 200.0, 300.0, 400.0, 500.0]
result = model.calculate(
    alt_km=alts,
    sunspot_number=100.0,
    local_time_rad=math.pi,
    month_from_dec15=6.0,
    geo_lat_rad=math.radians(35.0),
    geo_mag_lat_rad=math.radians(25.0),
    geo_mag_lon_rad=math.radians(120.0),
    dip_angle_rad=math.radians(45.0),
)

print(result["Ne_total_cm3"].shape)  # (5,)
```

### Peak density mode

```python
result = model.calculate(
    alt_km=0.0,
    sunspot_number=100.0,
    local_time_rad=math.pi,
    month_from_dec15=6.0,
    geo_lat_rad=math.radians(35.0),
    geo_mag_lat_rad=math.radians(25.0),
    geo_mag_lon_rad=math.radians(120.0),
    dip_angle_rad=math.radians(45.0),
)

print(result["Ne_E_cm3"], result["Ne_F1_cm3"], result["Ne_F2_cm3"])
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dll_path` | Auto-detected | Custom DLL path |

## Model Notes

- `alt_km=0` is a special mode defined by the original model: `Ne_total_cm3` returns 0, while the layer fields return E, F1, and F2 peak densities.
- The original Fortran output unit is `1.0E5 cm^-3`; the Python wrapper converts values to `cm^-3`.
- All inputs support numpy broadcasting. Scalar inputs return Python scalars, and array inputs return `numpy.ndarray`.

## References

1. Ching, B. K., and Chiu, Y. T., "A phenomenological model of global ionospheric electron density in the E-, F1- and F2-regions", Journal of Atmospheric and Terrestrial Physics, 35, 1615, 1973.

2. Chiu, Y. T., "An improved phenomenological model of ionospheric density", Journal of Atmospheric and Terrestrial Physics, 37, 1563, 1975.
