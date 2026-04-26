# NRLMSIS 2.0 — Whole-Atmosphere Empirical Temperature and Neutral Species Density Model

[中文文档 (Chinese)](README_zh.md)

## Model Background

NRLMSIS 2.0 is a whole-atmosphere empirical model developed by the Naval Research Laboratory (NRL) for computing temperature and neutral species densities from ground level to the lower exosphere. It is a major upgrade over NRLMSISE-00, officially released in 2020.

Key improvements over NRLMSISE-00:

- **Whole-atmosphere coverage**: Extends the model from the upper atmosphere to the entire atmosphere (ground to lower exosphere), incorporating large volumes of new tropospheric, stratospheric, and mesospheric observations.
- **Improved species separation**: Represents the transition from fully mixed to diffusively separated atmosphere via altitude-dependent effective mass.
- **C² continuous temperature profile**: Temperature profiles are twice continuously differentiable at all altitudes.
- **Global geopotential height function**: Uses a global geopotential height function internally.
- **Extended atomic oxygen**: Atomic oxygen extends down to 50 km; below 85 km it is represented by cubic B-splines decoupled from temperature.
- **New NO density output** (reserved, not yet active in the current version).

**Reference**:
> Emmert, J.T., Drob, D. P., Picone, J. M., Siskind, D. E., Jones Jr., M., et al. (2020). NRLMSIS 2.0: A whole-atmosphere empirical model of temperature and neutral species densities. *Earth and Space Science*.

**Applicable altitude range**: Ground ~ 1000 km

## Input Parameters

| Parameter | Type          | Description                                                                                  |
|-----------|---------------|----------------------------------------------------------------------------------------------|
| `day`     | float / array | Day of year (1.0 ~ 365/366); use `utils.time.doy(year, month, day)`                         |
| `utsec`   | float / array | UT seconds (0 ~ 86400); use `utils.time.seconds_of_day(h, m, s)`                            |
| `alt_km`  | float / array | Altitude (km)                                                                                |
| `lat_deg` | float / array | Geographic latitude (°, -90 ~ 90)                                                            |
| `lon_deg` | float / array | Geographic longitude (°, -180 ~ 180)                                                         |
| `f107a`   | float / array | 81-day mean F10.7 solar radio flux (sfu)                                                     |
| `f107`    | float / array | Daily F10.7 solar radio flux for the previous day (sfu)                                      |
| `ap7`     | list / array  | Geomagnetic activity indices, length 7 (optional, default all 4.0)                           |

### `ap7` array meaning

| Index   | Meaning                                                        |
|---------|----------------------------------------------------------------|
| `[0]`   | Daily Ap average for the day                                   |
| `[1]`   | Current 3-hour ap index                                        |
| `[2]`   | 3-hour ap index 3 hours before current time                    |
| `[3]`   | 3-hour ap index 6 hours before current time                    |
| `[4]`   | 3-hour ap index 9 hours before current time                    |
| `[5]`   | Mean of eight 3-hour ap indices from 12–33 hours prior         |
| `[6]`   | Mean of eight 3-hour ap indices from 36–57 hours prior         |

## Output

`calculate()` returns a dictionary with the following fields:

| Field       | Type          | Description                                        |
|-------------|---------------|----------------------------------------------------|
| `alt_km`    | float / ndarray | Input altitude                                    |
| `T_local_K` | float / ndarray | Local temperature at the specified altitude (K)   |
| `T_exo_K`   | float / ndarray | Exospheric temperature (K)                        |
| `densities` | ndarray       | Density array, shape `(10,)` or `(N, 10)`          |

### `densities` array elements

| Index   | Meaning                                                   | Unit  |
|---------|-----------------------------------------------------------|-------|
| `[0]`   | Total mass density                                        | kg/m³ |
| `[1]`   | N₂ number density                                         | m⁻³   |
| `[2]`   | O₂ number density                                         | m⁻³   |
| `[3]`   | O number density                                          | m⁻³   |
| `[4]`   | He number density                                         | m⁻³   |
| `[5]`   | H number density                                          | m⁻³   |
| `[6]`   | Ar number density                                         | m⁻³   |
| `[7]`   | N number density                                          | m⁻³   |
| `[8]`   | Anomalous oxygen number density                           | m⁻³   |
| `[9]`   | Reserved (NO number density, to be enabled in future)     | m⁻³   |

> **Note**: NRLMSIS 2.0 outputs use **SI units** (kg/m³, m⁻³), unlike NRLMSISE-00 which uses CGS units (g/cm³, cm⁻³). Take care when comparing results.

## Usage Examples

```python
from model import MSIS2
from utils.time import doy, seconds_of_day

model = MSIS2(precision="single")

result = model.calculate(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=250.0,
    lat_deg=39.9,
    lon_deg=116.4,
    f107a=150.0,
    f107=150.0,
    ap7=[4.0] * 7,
)

print(f"Local temperature: {result['T_local_K']:.1f} K")
print(f"Exospheric temperature: {result['T_exo_K']:.1f} K")
print(f"Total mass density: {result['densities'][0]:.2e} kg/m³")
print(f"O number density: {result['densities'][3]:.2e} m⁻³")
```

### Batch calculation

All input parameters accept NumPy arrays and are automatically broadcast:

```python
import numpy as np

batch = model.calculate(
    day=doy(2020, 7, 18),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=np.linspace(50, 500, 10),
    lat_deg=39.9,
    lon_deg=116.4,
    f107a=150.0,
    f107=150.0,
)

# batch["T_local_K"] shape is (10,)
# batch["densities"] shape is (10, 10)
```

## Constructor Parameters

| Parameter       | Default         | Description                                                |
|-----------------|-----------------|------------------------------------------------------------|
| `precision`     | `"single"`      | Computation precision, `"single"` or `"double"`            |
| `dll_path`      | Auto-detected   | Custom DLL path                                            |
| `data_dir`      | Auto-download   | MSIS2 parameter data directory                             |
| `auto_download` | `True`          | Whether to auto-download missing data                      |
| `add_mingw_bin` | `False`         | Whether to add MinGW bin directory to DLL search path (Windows) |
