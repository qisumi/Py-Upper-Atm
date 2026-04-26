# HWM93 — Horizontal Wind Model (1993)

[中文文档 (Chinese)](README_zh.md)

## Model Background

HWM93 (Horizontal Wind Model 1993) is an earlier empirical horizontal wind field model co-developed by the Naval Research Laboratory (NRL) and NASA/GSFC. It computes neutral atmospheric horizontal wind speeds for the mesosphere and lower thermosphere. It is one of the most widely used versions in the HWM series.

Key features of HWM93:

- **Focused on the mesosphere and lower thermosphere**: The model empirically fits horizontal winds across 0–500 km, but is best constrained by data in the mesosphere and lower thermosphere (~80–200 km).
- **Multi-source data fusion**: Uses satellite mass spectrometer / incoherent scatter data from AE-C, AE-D, AE-E, DE-2, as well as ground-based incoherent scatter radar observations.
- **Geomagnetic activity correction**: Supports high-latitude wind field correction via geomagnetic indices (Ap).

> **Note**: HWM93 is an earlier model with limited accuracy at high latitudes, high altitudes, and during strong geomagnetic activity. For higher accuracy, consider using HWM14.

**Reference**:
> Hedin, A. E., Fleming, E. L., Manson, A. H., Schmidlin, F. J., Avery, S. K., et al. (1996). Empirical wind model for the upper, middle and lower atmosphere. *Journal of Atmospheric and Terrestrial Physics*, 58(13), 1421-1447.

**Applicable altitude range**: Ground ~ 500 km

## Input Parameters

| Parameter | Type          | Description                                                       |
|-----------|---------------|-------------------------------------------------------------------|
| `iyd`     | int / array   | Day of year as YYYYDDD (e.g. `2023001`)                          |
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
from model import HWM93

model = HWM93()

result = model.calculate(
    iyd=2023001,
    sec=0.0,
    alt_km=100.0,
    glat_deg=40.0,
    glon_deg=116.0,
    stl_hours=0.0,
    f107a=150.0,
    f107=150.0,
    ap2=(4.0, 4.0),
)

print(f"Meridional wind: {result['meridional_wind_ms']:.3f} m/s")
print(f"Zonal wind: {result['zonal_wind_ms']:.3f} m/s")
```

### Multi-altitude batch calculation

```python
result = model.calculate(
    iyd=2023001,
    sec=43200.0,
    alt_km=[50.0, 100.0, 150.0, 200.0, 250.0],
    glat_deg=40.0,
    glon_deg=116.0,
    stl_hours=12.0,
    f107a=150.0,
    f107=150.0,
    ap2=(4.0, 4.0),
)

for alt, wm, wz in zip(
    result["alt_km"],
    result["meridional_wind_ms"],
    result["zonal_wind_ms"],
):
    print(f"Alt {alt:.0f} km: meridional={wm:.3f} m/s, zonal={wz:.3f} m/s")
```

## Constructor Parameters

| Parameter       | Default         | Description                                   |
|-----------------|-----------------|-----------------------------------------------|
| `dll_path`      | Auto-detected   | Custom DLL path                               |
| `data_dir`      | —               | Reserved parameter (HWM93 requires no external data) |
| `auto_download` | `True`          | Reserved parameter                            |

## Comparison with HWM14

| Feature             | HWM93        | HWM14            |
|---------------------|--------------|------------------|
| Release year        | 1993         | 2014             |
| Observation volume  | Limited      | Greatly expanded |
| High-latitude accuracy | Limited   | Significantly improved |
| Lower thermosphere accuracy | Good | Good          |
| Geomagnetic correction | Basic     | More comprehensive |
| External data files | Not required | Required         |
