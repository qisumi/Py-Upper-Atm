# Xu-Li Neutral Sheet Model

Magnetotail equatorial neutral sheet position model (Xu & Li, CAS Beijing).

## Background

The Xu-Li model computes the Z-position of the geomagnetic tail neutral sheet
in GSM (Geocentric Solar Magnetospheric) coordinates. Three variants are
provided, all of which join the tilted equatorial plane smoothly to the neutral
sheet, making them usable across the entire magnetosphere including the
near-tail region:

- **AEN** (Analytical Equatorial Neutral) — single closed-form expression
  (Zhu & Xu, 1994; Wang & Xu, 1994)
- **SEN** (Standard Equatorial Neutral) — three-region piecewise model
  (Xu, 1992)
- **DEN** (Displaced Equatorial Neutral) — displaced neutral sheet with
  approximately equal cross-sectional areas above and below
  (Xu, 1991)

The magnetopause boundary uses the Sibeck et al. (1991) model.

## Fortran Interface

The merged source (`xuli.for`) contains seven subroutines:

| Subroutine | Description |
|---|---|
| `STIL(DOY, HR, TMI, TILA)` | Compute dipole tilt angle |
| `SMPF(XSM, RMP, IM)` | Magnetopause cross-section radius |
| `SAEN(TILA, XSM, YSM, ZAEN, RMP, IE)` | AEN neutral sheet |
| `SSEN(TILA, XSM, YSM, ZSEN, RMP, IE)` | SEN neutral sheet |
| `SDEN(TILA, XSM, YSM, ZDEN, RMP, IE)` | DEN neutral sheet |
| `SD1(TIL, H, H1, XSM, D)` | Displaced parameter (DEN) |
| `SFA4(AA, BB, CC, DD, X)` | Quartic root finder (DEN) |

### Key subroutine signatures

```
SAEN(TILA, XSM, YSM, ZAEN, RMP, IE)
SSEN(TILA, XSM, YSM, ZSEN, RMP, IE)
SDEN(TILA, XSM, YSM, ZDEN, RMP, IE)
```

| Parameter | Type | Direction | Description |
|---|---|---|---|
| TILA | REAL | IN | Dipole tilt angle (degrees) |
| XSM | REAL | IN | GSM X position (Earth Radii, negative tailward) |
| YSM | REAL | IN | GSM Y position (Earth Radii) |
| ZAEN/ZSEN/ZDEN | REAL | OUT | Neutral sheet Z position (Earth Radii) |
| RMP | REAL | OUT | Magnetopause radius at XSM (Earth Radii) |
| IE | INTEGER | OUT | 1 = inside magnetopause, 2 = outside |

Note: `IE` follows Fortran 77 implicit typing (I–N → INTEGER).

## C ABI

The C shim (`xuli_cshim.F90`) exposes two functions:

### `xuli_eval`

```c
void xuli_eval(
    float tila, float xsm, float ysm,
    float *zaen, float *zsen, float *zden, float *rmp,
    int *ie_aen, int *ie_sen, int *ie_den
);
```

Computes all three neutral sheet variants at once.

### `xuli_tilt`

```c
void xuli_tilt(float doy, float ut_hours, float *tilt_deg);
```

Computes the dipole tilt angle from day-of-year and universal time.

## Python API

### Constructor

```python
Model(dll_path=None)
```

- `dll_path`: Optional path to the compiled DLL/SO. Auto-detected if omitted.

### `calculate()`

```python
result = model.calculate(
    *,
    x_re: float | np.ndarray,
    y_re: float | np.ndarray,
    doy: float | np.ndarray = None,
    ut_hours: float | np.ndarray = None,
    tilt_angle_deg: float | np.ndarray = None,
) -> dict
```

Provide either `tilt_angle_deg` **or** both `doy` + `ut_hours`:

- If `tilt_angle_deg` is given, it is used directly as the dipole tilt angle.
- Otherwise, `doy` and `ut_hours` are required; the model computes the tilt
  angle internally.

### Input parameters

| Parameter | Type | Units | Description |
|---|---|---|---|
| `x_re` | float or array | Earth Radii | GSM X coordinate (negative tailward) |
| `y_re` | float or array | Earth Radii | GSM Y coordinate |
| `doy` | float or array | — | Day of year (1.0–366.0) |
| `ut_hours` | float or array | hours | Universal time |
| `tilt_angle_deg` | float or array | degrees | Dipole tilt angle (override) |

### Output dictionary

| Key | Type | Description |
|---|---|---|
| `x_re` | float or ndarray | Echoed input |
| `y_re` | float or ndarray | Echoed input |
| `tilt_angle_deg` | float or ndarray | Dipole tilt angle used |
| `zaen_re` | float or ndarray | AEN neutral sheet Z (RE) |
| `zsen_re` | float or ndarray | SEN neutral sheet Z (RE) |
| `zden_re` | float or ndarray | DEN neutral sheet Z (RE) |
| `rmp_re` | float or ndarray | Magnetopause radius at XSM (RE) |
| `ie_aen` | int or ndarray | 1=inside, 2=outside magnetopause (AEN) |
| `ie_sen` | int or ndarray | 1=inside, 2=outside magnetopause (SEN) |
| `ie_den` | int or ndarray | 1=inside, 2=outside magnetopause (DEN) |

Scalar inputs produce scalar outputs; array inputs produce numpy arrays with
broadcast shape.

## Usage Examples

### Single point with date/time

```python
from model import XuLi

model = XuLi()
result = model.calculate(x_re=-10.0, y_re=0.0, doy=172.0, ut_hours=12.0)
print(f"ZAEN = {result['zaen_re']:.3f} RE")
print(f"ZSEN = {result['zsen_re']:.3f} RE")
print(f"ZDEN = {result['zden_re']:.3f} RE")
```

### Direct tilt angle

```python
result = model.calculate(x_re=-15.0, y_re=5.0, tilt_angle_deg=20.0)
```

### Batch computation

```python
import numpy as np

xs = np.linspace(-5, -30, 6)
result = model.calculate(x_re=xs, y_re=0.0, tilt_angle_deg=15.0)
print(result["zaen_re"])  # array of ZAEN values
```

## Coordinate System

All positions are in GSM (Geocentric Solar Magnetospheric) coordinates,
measured in Earth Radii (RE ≈ 6371.2 km):
- **X**: positive sunward, negative tailward
- **Y**: positive duskward
- **Z**: positive northward (perpendicular to X in the plane containing
  the dipole axis)

The dipole tilt angle is the angle between the geomagnetic dipole axis and
the GSM Z-axis, varying with season (±23.5° annual) and UT (±11.7° diurnal).

## References

1. Xu, R.-L., A Displaced Equatorial Neutral Sheet Surface Observed on
   ISEE-2 Satellite, J. Atmospheric and Terrestrial Phys., 58, 1085, 1991.
2. Xu, R.-L., Dynamics of the Neutral Sheet in the Magnetotail during
   Substorm, Advances in solar-terrestrial science of China, ed. by W.-R.
   Hu et al., China Science Press, 1992.
3. Zhu, M. and R.-L. Xu, A continuous neutral sheet model and a normal
   curved coordinate system in the magnetotail, Chinese J. Space Science,
   14(4), 269, 1994.
4. Wang, Z.-D. and R.-L. Xu, Neutral Sheet Observed on ISEE Satellite,
   Geophysical Research Letter, 21(19), 2087, 1994.
5. Sibeck, D. G., R. E. Lopez, and R. C. Roelof, Solar wind control of
   the magnetopause shape, location, and motion, J. Geophys. Res., 96,
   5489, 1991.
