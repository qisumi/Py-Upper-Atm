# NRLMSISE-00 — Empirical Neutral Atmosphere Model

[中文文档 (Chinese)](README_zh.md)

## Model Background

NRLMSISE-00 is an empirical neutral atmosphere model developed by the Naval Research Laboratory (NRL) for computing temperature and neutral particle densities from ground level to the lower exosphere. Released in 2000, it is the successor to the MSIS series models (MSIS-86, MSISE-90).

Key features of NRLMSISE-00:

- **Rich data foundation**: Fitted against a large volume of satellite drag data, significantly improving thermospheric density accuracy.
- **Revised lower thermospheric O₂ and O**: Improved density distributions for molecular and atomic oxygen in the lower thermosphere.
- **Nonlinear solar activity terms**: Additional nonlinear solar activity corrections.
- **Anomalous oxygen**: At high altitudes (> 500 km), hot atomic oxygen or ionized oxygen can significantly affect satellite drag. The model groups these species as "anomalous oxygen", whose number density is returned via output array `D(9)`.

**Reference**:
> Picone, J. M., Hedin, A. E., Drob, D. P., & Aikin, A. C. (2002). NRLMSISE-00 empirical model of the atmosphere: Statistical comparisons and scientific issues. *Journal of Geophysical Research: Space Physics*, 107(A12).

**Applicable altitude range**: Ground ~ 1000 km

## Input Parameters

| Parameter | Type          | Description                                                                                    |
|-----------|---------------|------------------------------------------------------------------------------------------------|
| `iyd`     | int / array   | Day of year as YYYYDDD (e.g. `2023001`); the year is effectively ignored by the model          |
| `sec`     | float / array | UT seconds (0 ~ 86400)                                                                         |
| `alt_km`  | float / array | Altitude (km)                                                                                  |
| `lat_deg` | float / array | Geographic latitude (°)                                                                        |
| `lon_deg` | float / array | Geographic longitude (°)                                                                       |
| `stl_hours` | float / array | Local apparent solar time (hours, 0 ~ 24). Typically `sec/3600 + lon_deg/15`                 |
| `f107a`   | float / array | 81-day mean F10.7 solar radio flux (sfu)                                                       |
| `f107`    | float / array | Daily F10.7 solar radio flux for the previous day (sfu)                                        |
| `ap7`     | list / array  | Geomagnetic activity indices, length 7 (optional, default all 4.0)                             |
| `mass`    | int           | Mass number selector, default 48 = all species; set to a specific mass to compute that species only |
| `use_anomalous_o` | bool  | Whether to include anomalous oxygen in total mass density (default `False`)                   |

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
| `densities` | ndarray       | Density array, shape `(9,)` or `(N, 9)`            |

### `densities` array elements

| Index   | Meaning                       | Unit     |
|---------|-------------------------------|----------|
| `[0]`   | He number density             | cm⁻³     |
| `[1]`   | O number density              | cm⁻³     |
| `[2]`   | N₂ number density             | cm⁻³     |
| `[3]`   | O₂ number density             | cm⁻³     |
| `[4]`   | Ar number density             | cm⁻³     |
| `[5]`   | Total mass density            | g/cm³    |
| `[6]`   | H number density              | cm⁻³     |
| `[7]`   | N number density              | cm⁻³     |
| `[8]`   | Anomalous oxygen number density | cm⁻³   |

> **Regarding D(6) total mass density**: When `use_anomalous_o=False` (default, calls GTD7), total mass density includes He, O, N₂, O₂, Ar, H, N but **excludes** anomalous oxygen. When `use_anomalous_o=True` (calls GTD7D), total mass density becomes "effective drag total mass density" **including** anomalous oxygen.

> **Note**: NRLMSISE-00 outputs use **CGS units** (g/cm³, cm⁻³), unlike NRLMSIS 2.0 which uses SI units. Take care when comparing results.

## Usage Examples

```python
from model import MSIS00

model = MSIS00()

result = model.calculate(
    iyd=2023001,
    sec=12.0 * 3600,
    alt_km=200.0,
    lat_deg=40.0,
    lon_deg=-75.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
)

print(f"Local temperature: {result['T_local_K']:.1f} K")
print(f"Exospheric temperature: {result['T_exo_K']:.1f} K")
print(f"O number density: {result['densities'][1]:.2e} cm⁻³")
print(f"Total mass density: {result['densities'][5]:.2e} g/cm³")
```

### High-altitude calculation with anomalous oxygen

```python
result = model.calculate(
    iyd=2023001,
    sec=43200.0,
    alt_km=600.0,
    lat_deg=0.0,
    lon_deg=0.0,
    stl_hours=12.0,
    f107a=200.0,
    f107=200.0,
    use_anomalous_o=True,
)
# result["densities"][5] includes anomalous oxygen effective total mass density
```

### Batch calculation

```python
import numpy as np

batch = model.calculate(
    iyd=2023001,
    sec=43200.0,
    alt_km=np.linspace(100, 500, 5),
    lat_deg=40.0,
    lon_deg=-75.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
)
# batch["densities"] shape is (5, 9)
```

## Constructor Parameters

| Parameter       | Default         | Description                                            |
|-----------------|-----------------|--------------------------------------------------------|
| `dll_path`      | Auto-detected   | Custom DLL path                                        |
| `data_dir`      | —               | Reserved parameter (MSISE-00 requires no external data)|
| `auto_download` | `True`          | Reserved parameter                                     |
