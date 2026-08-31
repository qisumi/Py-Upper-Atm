# MSIS2H2O — NRLMSIS 2.0 with Aura MLS H2O

[中文文档](README_zh.md)

`model.MSIS2H2O` preserves the four native `MSIS2` outputs and adds water-vapor
volume mixing ratio and number density. It combines NRLMSIS 2.0 dry-atmosphere
state variables with a deterministic monthly climatology built from NASA Aura
MLS `ML3MBH2O` V005 annual Level-3 files for 2005–2024.

This is a fixed climatology, not weather or a daily observation for the input
year. MLS is used inside its recommended 316–0.00215 hPa pressure interval.
Lower pressures, normally around 90–120 km, use a constrained log(VMR)-log(p)
tail and are always marked by `H2O_extrapolated=True`; they must not be
interpreted as observation-accuracy estimates.

## Inputs and constructor

`calculate(...)` has the same keyword-only inputs as `MSIS2` and supports
NumPy broadcasting: `day`, `utsec`, `alt_km`, `lat_deg`, `lon_deg`, `f107a`,
`f107`, and optional `ap7`. `alt_km` is restricted to 20–120 km.

The constructor accepts all `MSIS2` options and adds `h2o_data_path=None` for
an explicit compact climatology file. Otherwise it resolves
`msis2h2odata/mls_ml3mbh2o_v005_2005-2024_climatology.npz` through the normal
UpperAtmPy model-data mechanism.

## Outputs

The unchanged MSIS2 fields are `alt_km`, `T_local_K`, `T_exo_K`, and
`densities` (last dimension remains 10). Additional fields are:

| Field | Unit / meaning |
|---|---|
| `total_number_density_m3` | sum of N2, O2, O, He, H, Ar, N, and anomalous O, m^-3 |
| `pressure_Pa` | `N_total * k_B * T_local`, Pa |
| `H2O_vmr_ppmv` | climatological H2O volume mixing ratio, ppmv |
| `H2O_number_density_m3` | H2O number density, m^-3 |
| `H2O_number_density_cm3` | H2O number density, cm^-3 |
| `H2O_extrapolated` | pressure is below the MLS 0.00215 hPa ceiling |
| `H2O_latitude_clamped` | latitude was clamped to the nearest ±82° MLS edge |
| `H2O_climatology_fallback` | one or more interpolation corners used a zonal-mean repair |

Month-midpoint time, latitude, periodic longitude, and pressure are
interpolated linearly in log(VMR)-log(p) space. `utsec` supplies the fractional
day. Annual Level-3 `average` values are combined in linear VMR space using
`nvalues`; valid negative annual retrievals are retained in that average.

## Example

```python
from model import MSIS2H2O

model = MSIS2H2O(precision="single")
result = model.calculate(
    day=196, utsec=43200, alt_km=[50, 90, 120],
    lat_deg=35, lon_deg=116, f107a=100, f107=100,
)
print(result["H2O_number_density_cm3"])
print(result["H2O_extrapolated"])
```

## Reproducibility and attribution

The development-time builder is
`tools/build_msis2h2o_climatology.py`; runtime requires only NumPy. The pinned
source manifest records 20 CMR granule IDs, URLs, input SHA-256 values, the
output SHA-256, and product DOI.

Please cite NRLMSIS 2.0 and NASA Aura MLS. MLS product DOI:
`10.5067/Aura/MLS/DATA/3538`.
