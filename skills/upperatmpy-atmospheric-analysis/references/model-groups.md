# UpperAtmPy comparison groups / 模型比较分组

Use only models in the same row for direct numerical differences.
仅对同一行内的模型直接求差。

| Group | Models | Required canonical inputs | Default common quantities |
|---|---|---|---|
| `neutral_atmosphere` | `MSIS2`, `MSIS00`, `MSIS86`, `MSISE90` | `year`, `day_of_year`, `utsec`, `alt_km`, `lat_deg`, `lon_deg`, `f107a`, `f107` | `T_local_K`, `T_exo_K` |
| `geomagnetic_internal` | `IGRF`, `GSFC`, `JensenCain`, `MGST80`, `MGST81` | `year`, `alt_km`, `lat_deg`, `lon_deg` | `B_abs_nT` |

Optional neutral-atmosphere inputs are `local_time_hours` and `ap7`. When local
solar time is omitted, the executor derives it deterministically from UT and
longitude. `ap7` must be a finite length-7 vector or an `(N, 7)` array.

## Canonical quantities / 统一物理量

- Temperatures: `T_local_K`, `T_exo_K` in K.
- Neutral species: `He_cm3`, `O_cm3`, `N2_cm3`, `O2_cm3`, `Ar_cm3`, `H_cm3`,
  `N_cm3`, and when available `AnomalousO_cm3`, all in cm^-3.
- Total mass density: `total_mass_density_kg_m3`. Native MSIS g/cm^3 values are
  converted deterministically to kg/m^3.
- Magnetic components: `B_north_nT`, `B_east_nT`, `B_down_nT`, `B_abs_nT`, and
  `H_nT` in nT; `inclination_deg` and `declination_deg` in degrees.

## Important intersections / 重要有效域交集

- Adding `MSIS86` restricts shared altitude to 85–1000 km.
- Other catalogued MSIS models use 0–1000 km in this analysis layer.
- Geomagnetic comparison uses 0–1000 km, latitude -90–90 degrees, and longitude
  -180–360 degrees. IGRF additionally enforces 1900–2030.
- Historical geomagnetic models are intended near their source epochs. Keep the
  generated warning even when the numerical API accepts another year.

The live machine-readable source of truth is
`upperatmpy_analysis.catalog.MODELS`; use `upperatmpy-analysis catalog --format
json` when the installed version may differ from this reference.
