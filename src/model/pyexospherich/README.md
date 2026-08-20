# ExosphericH

`ExosphericH` implements the Hodges (1994) third-order spherical-harmonic model of terrestrial exospheric hydrogen.

## Interface

```python
from model import ExosphericH

result = ExosphericH().calculate(
    radius_km=10000.0, colatitude_deg=45.0, longitude_deg=0.0,
    season="equinox", f107=80,
)
```

The constructor accepts `data_dir` and `auto_download`. Inputs broadcast with NumPy. Radius is restricted to 6640–62126 km; `season` is `equinox` or `solstice`; F10.7 is one of 80, 130, 180, or 230. The model interpolates coefficients in log radius and base density logarithmically, without extrapolation, and returns `H_cm3`.

## Files and reference

`__init__.py` evaluates the fixed degree-3 normalized spherical harmonics without SciPy. `h_exos.dat` contains the eight Hodges tables and its tabulated coefficients use the documented `1e-4` scale. Reference: Hodges, *JGR*, 1994, doi:10.1029/94JA02183.
