# HWM14 — Horizontal Wind Model (2014)

[中文文档 (Chinese)](README_zh.md)

## Model Background

HWM14 (Horizontal Wind Model 2014) is an empirical horizontal wind field model developed by the Naval Research Laboratory (NRL). It computes neutral atmospheric horizontal wind speeds from the ground to approximately 500 km altitude. It is the latest version in the HWM series (HWM87, HWM90, HWM93, HWM07).

Key features of HWM14:

- **Extended altitude coverage**: The upper boundary was slightly extended from HWM07's ~500 km, and the model reaches down to ground level.
- **Extensive new observations**: Incorporates satellite wind data (DE-2, UARS/WINDII, TIMED/TIDI, CHAMP/STAR, etc.) as well as ground-based radar and lidar measurements.
- **Improved meridional and zonal winds**: Corrects systematic biases from previous versions at high latitudes and in the mesosphere.
- **Whole-atmosphere consistency**: Can be paired with NRLMSIS 2.0 for a consistent description of temperature, density, and wind fields.

**Reference**:
> Drob, D. P., Emmert, J. T., Meriwether, J. W., Makela, J. J., Doornbos, E., et al. (2015). An update to the Horizontal Wind Model (HWM): The quiet time thermosphere. *Earth and Space Science*, 2(7), 301-319.

**Applicable altitude range**: Ground ~ 500 km

## Input Parameters

| Parameter | Type          | Description                                                       |
|-----------|---------------|-------------------------------------------------------------------|
| `iyd`     | int / array   | Day of year as YYYYDDD (e.g. `2025290`)                          |
| `sec`     | float / array | UT seconds (0 ~ 86400)                                            |
| `alt_km`  | float / array | Altitude (km)                                                     |
| `glat_deg`  | float / array | Geographic latitude (°)                                         |
| `glon_deg`  | float / array | Geographic longitude (°)                                        |
| `stl_hours` | float / array | Local apparent solar time (hours, 0 ~ 24)                       |
| `f107a`   | float / array | 81-day mean F10.7 solar radio flux (sfu)                          |
| `f107`    | float / array | Daily F10.7 solar radio flux for the previous day (sfu)          |
| `ap2`     | tuple / array | Geomagnetic activity indices, length 2 (optional, default `(0.0, 20.0)`) |

### `ap2` array meaning

| Index   | Meaning                         |
|---------|---------------------------------|
| `[0]`   | Daily Ap average for the day    |
| `[1]`   | Current 3-hour ap index         |

## Output

`calculate()` returns a dictionary with the following fields:

| Field                 | Type          | Description                                     |
|-----------------------|---------------|-------------------------------------------------|
| `alt_km`              | float / ndarray | Input altitude                                |
| `meridional_wind_ms`  | float / ndarray | Meridional wind speed (m/s), positive = northward |
| `zonal_wind_ms`       | float / ndarray | Zonal wind speed (m/s), positive = eastward   |

## Usage Examples

```python
from model import HWM14

model = HWM14()

result = model.calculate(
    iyd=2025290,
    sec=43200.0,
    alt_km=250.0,
    glat_deg=30.0,
    glon_deg=114.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
    ap2=(0.0, 20.0),
)

print(f"Meridional wind: {result['meridional_wind_ms']:.3f} m/s")
print(f"Zonal wind: {result['zonal_wind_ms']:.3f} m/s")
```

### Batch calculation (lat-lon grid)

```python
import numpy as np

lat = np.linspace(-60, 60, 5)
lon = np.linspace(0, 360, 9)
lat_grid, lon_grid = np.meshgrid(lat, lon, indexing="ij")

result = model.calculate(
    iyd=2025290,
    sec=43200.0,
    alt_km=250.0,
    glat_deg=lat_grid,
    glon_deg=lon_grid,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
)

# result["meridional_wind_ms"].shape == (5, 9)
# result["zonal_wind_ms"].shape == (5, 9)
```

## Constructor Parameters

| Parameter       | Default         | Description                             |
|-----------------|-----------------|-----------------------------------------|
| `dll_path`      | Auto-detected   | Custom DLL path                         |
| `data_dir`      | Auto-download   | HWM14 data file directory               |
| `auto_download` | `True`          | Whether to auto-download missing data   |
