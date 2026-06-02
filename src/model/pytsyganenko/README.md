# Tsyganenko Magnetic Field Models (T89 / T96 / T01 / TS04)

## Background

The Tsyganenko models are empirical data-based magnetospheric magnetic field
models that compute the external (magnetospheric current) contribution to the
geomagnetic field. Four versions are available:

- **T89** (Tsyganenko 1989): Simplest version, driven by the Kp index.
- **T96** (Tsyganenko 1996): Adds solar wind dynamic pressure, Dst, and IMF
  By/Bz as inputs.
- **T01** (Tsyganenko 2001): Extends T96 with two additional magnetospheric
  activity indices G1 and G2.
- **TS04** (Tsyganenko & Sitnov 2004): Uses six weighted parameters (W1–W6)
  to describe the time-integrated magnetospheric state during storms.

The module is built on **Geopack-2005** for coordinate transformations
(GEI ↔ GSM) and the Earth's internal dipole field. The Fortran sources are
compiled into shared libraries and wrapped via `ctypes` following the project's
standard `Model.calculate(...)` interface.

**No external data files are required** — all empirical coefficients are
hard-coded in the Fortran source.

## Directory Structure

```text
pytsyganenko/
├── geopack_2005.for                # Geopack-2005 coordinate transforms & dipole field
├── t89.for                         # T89 model (T89C + T89 subroutines)
├── t96.for                         # T96 model (T96_01 + internal subroutines)
├── t01.for                         # T01 model (T01_01 + internal subroutines)
├── ts04.for                        # TS04 model (T04_s + internal subroutines)
├── tsyganenko_t89_cshim.F90        # C ABI shim for T89
├── tsyganenko_t96_cshim.F90        # C ABI shim for T96
├── tsyganenko_t01_cshim.F90        # C ABI shim for T01
├── tsyganenko_ts04_cshim.F90       # C ABI shim for TS04
├── CMakeLists.txt                  # Builds four DLLs
├── __init__.py                     # Python Model class
├── README.md                       # This file (English)
└── README_zh.md                    # Chinese documentation
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_version` | required | Model version: `"T89"`, `"T96"`, `"T01"`, or `"TS04"` |
| `dll_path` | auto-detected | Custom path to the compiled DLL |

## Input Parameters

### Position (required)

| Parameter | Type | Description |
|-----------|------|-------------|
| `x_re` | float / array | GSM X coordinate (Earth radii, Re) |
| `y_re` | float / array | GSM Y coordinate (Earth radii, Re) |
| `z_re` | float / array | GSM Z coordinate (Earth radii, Re) |

### Time / Tilt Angle (choose one)

Option 1 — provide date/time components; the model computes the dipole tilt
angle internally via RECALC:

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | int | Year (e.g. 2000) |
| `doy` | int | Day of year (1–366) |
| `hour` | int | Hour (0–23), default 0 |
| `minute` | int | Minute (0–59), default 0 |
| `second` | int | Second (0–59), default 0 |

Option 2 — provide the dipole tilt angle directly (skips RECALC):

| Parameter | Type | Description |
|-----------|------|-------------|
| `tilt_rad` | float | Dipole tilt angle (radians) |

### Model-Specific Parameters

#### T89

| Parameter | Type | Description |
|-----------|------|-------------|
| `kp_index` | int (1–7) | Kp geomagnetic activity level |

#### T96

| Parameter | Type | Description |
|-----------|------|-------------|
| `pdyn_nPa` | float | Solar wind dynamic pressure (nPa) |
| `dst_nT` | float | Dst index (nT) |
| `by_imf_nT` | float | IMF By component (nT, GSM) |
| `bz_imf_nT` | float | IMF Bz component (nT, GSM) |

#### T01

T01 requires all T96 parameters plus:

| Parameter | Type | Description |
|-----------|------|-------------|
| `g1` | float | Magnetospheric activity index G1 |
| `g2` | float | Magnetospheric activity index G2 |

#### TS04

| Parameter | Type | Description |
|-----------|------|-------------|
| `pdyn_nPa` | float | Solar wind dynamic pressure (nPa) |
| `dst_nT` | float | Dst index (nT) |
| `by_imf_nT` | float | IMF By component (nT, GSM) |
| `bz_imf_nT` | float | IMF Bz component (nT, GSM) |
| `w1`–`w6` | float | Six storm-time driving parameters |

### Optional

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_dipole` | bool | `False` | Also compute internal dipole field and total field |

## Output

`calculate()` returns a dictionary:

### Default output (`include_dipole=False`)

| Field | Type | Description |
|-------|------|-------------|
| `tilt_rad` | float | Dipole tilt angle used (radians) |
| `Bx_ext_nT` | float / ndarray | External field GSM X component (nT) |
| `By_ext_nT` | float / ndarray | External field GSM Y component (nT) |
| `Bz_ext_nT` | float / ndarray | External field GSM Z component (nT) |

### Additional output (`include_dipole=True`)

| Field | Type | Description |
|-------|------|-------------|
| `Bx_dip_nT` | float / ndarray | Internal dipole field X component (nT) |
| `By_dip_nT` | float / ndarray | Internal dipole field Y component (nT) |
| `Bz_dip_nT` | float / ndarray | Internal dipole field Z component (nT) |
| `Bx_total_nT` | float / ndarray | Total field X component (nT) |
| `By_total_nT` | float / ndarray | Total field Y component (nT) |
| `Bz_total_nT` | float / ndarray | Total field Z component (nT) |

## Usage Examples

### T89 single point

```python
from model import Tsyganenko

model = Tsyganenko(model_version="T89")
result = model.calculate(
    year=2000, doy=180, hour=12, minute=0, second=0,
    x_re=-5.0, y_re=0.0, z_re=0.0,
    kp_index=3,
)

print(f"External Bx: {result['Bx_ext_nT']:.2f} nT")
print(f"External Bz: {result['Bz_ext_nT']:.2f} nT")
print(f"Dipole tilt:  {result['tilt_rad']:.4f} rad")
```

### T96 with dipole field

```python
model = Tsyganenko(model_version="T96")
result = model.calculate(
    year=2000, doy=180, hour=12,
    x_re=-6.6, y_re=0.0, z_re=0.0,
    pdyn_nPa=2.0, dst_nT=-20.0,
    by_imf_nT=0.5, bz_imf_nT=-2.0,
    include_dipole=True,
)

print(f"External: ({result['Bx_ext_nT']:.2f}, {result['By_ext_nT']:.2f}, {result['Bz_ext_nT']:.2f}) nT")
print(f"Total:    ({result['Bx_total_nT']:.2f}, {result['By_total_nT']:.2f}, {result['Bz_total_nT']:.2f}) nT")
```

### T01 with direct tilt angle

```python
model = Tsyganenko(model_version="T01")
result = model.calculate(
    tilt_rad=0.15,
    x_re=-10.0, y_re=2.0, z_re=1.0,
    pdyn_nPa=2.0, dst_nT=-20.0,
    by_imf_nT=0.5, bz_imf_nT=-2.0,
    g1=1.0, g2=1.0,
)
```

### TS04 batch calculation

```python
import numpy as np

model = Tsyganenko(model_version="TS04")
result = model.calculate(
    year=2000, doy=180, hour=12,
    x_re=np.array([-5.0, -6.6, -10.0]),
    y_re=0.0, z_re=0.0,
    pdyn_nPa=2.0, dst_nT=-20.0,
    by_imf_nT=0.5, bz_imf_nT=-2.0,
    w1=0.5, w2=0.5, w3=0.5, w4=0.5, w5=0.5, w6=0.5,
)

print(result["Bx_ext_nT"].shape)  # (3,)
```

## Notes

- All inputs support numpy broadcasting. Scalar inputs return Python scalars;
  array inputs return `numpy.ndarray`.
- Position coordinates use the GSM (Geocentric Solar Magnetospheric) system,
  in units of Earth radii (Re ≈ 6371.2 km).
- By default, only the external (magnetospheric) field is returned. Set
  `include_dipole=True` to also compute the internal dipole field and total
  field.
- Geopack-2005 includes a built-in IGRF dipole approximation and does not
  depend on external IGRF coefficient files.
- If both time parameters and `tilt_rad` are provided, `tilt_rad` takes
  precedence.

## References

1. Tsyganenko, N. A., "A magnetospheric magnetic field model with a warped
   tail current sheet", Planet. Space Sci., 37, 5–20, 1989.

2. Tsyganenko, N. A., "Effects of the solar wind conditions on the global
   magnetospheric configuration as deduced from data-based field models",
   Eur. Space Agency Spec. Publ., ESA SP-389, 181, 1996.

3. Tsyganenko, N. A., "A model of the near magnetosphere with a dawn-dusk
   asymmetry: 1. Mathematical structure", Space Sci. Rev., 108, 79, 2003.

4. Tsyganenko, N. A., and M. I. Sitnov, "Modeling the dynamics of the inner
   magnetosphere during strong geomagnetic storms", J. Geophys. Res., 110,
   A03208, 2005.
