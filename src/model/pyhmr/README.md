# Heppner-Maynard-Rich Electric Field Model

High-latitude ionospheric electric potential model based on OGO 6 and DE 2 electric field measurements.

## Supported Models

| Model | IMF Condition | Description |
|-------|--------------|-------------|
| `A` | Bz < 0, By < 0 | Northern hemisphere |
| `BC` | Bz < 0, By > 0 | Northern hemisphere |
| `DE` | Bz < 0, By < 0 | Southern hemisphere |
| `heelis` | Bz > 0 | Heelis convection model |

## Usage

### Electric Potential Only

```python
from model import HMR

m = HMR()

# Heppner-Maynard potential at one point
r = m.calculate(lat_deg=70.0, lon_deg=180.0, model="A")
print(r["electric_potential_kV"])

# Heelis convection model
r = m.calculate_heelis(lat_deg=70.0, lon_hrs=12.0)
```

### Conductivity

```python
r = m.calculate_conductivity(lat_deg=70.0, mlt_hrs=12.0, kp=3.0)
print(r["hall_conductivity_Mho"])
print(r["pedersen_conductivity_Mho"])
```

### Full Computation

```python
r = m.calculate_full(kp=3.5, sublat_deg=0.0, f107=80.0, model="A")
# Returns 41x25 grid (lat 50-90°, MLT 0-24h)
print(r["electric_potential_kV"].shape)  # (41, 25)
print(r["e_field_lat_mV_m"])             # mV/m
print(r["joule_heating_mW_m2"])          # mW/m²
print(r["fac_uA_m2"])                    # μA/m²
```

## Returns

### `calculate()` — Electric Potential

| Key | Unit | Description |
|-----|------|-------------|
| `electric_potential_kV` | kV | Electric potential |

### `calculate_heelis()` — Heelis Model

| Key | Unit | Description |
|-----|------|-------------|
| `electric_potential_kV` | kV | Electric potential |
| `dlat_kV_per_rad` | kV/rad | Latitude gradient |
| `dlon_kV_per_rad` | kV/rad | Local time gradient |

### `calculate_full()` — Full Grid

| Key | Unit | Description |
|-----|------|-------------|
| `electric_potential_kV` | kV | Electric potential (41×25) |
| `e_field_lat_mV_m` | mV/m | Latitude electric field |
| `e_field_lon_mV_m` | mV/m | Local time electric field |
| `hall_conductivity_Mho` | Mho | Hall conductivity |
| `pedersen_conductivity_Mho` | Mho | Pedersen conductivity |
| `joule_heating_mW_m2` | mW/m² | Joule heating rate |
| `fac_uA_m2` | μA/m² | Field-aligned current |
| `lat_grid_deg` | deg | Latitude grid (50–90°) |
| `mlt_grid_hrs` | hrs | MLT grid (0–24h) |

## References

- J. P. Heppner and N. C. Maynard, Empirical high-latitude electric field models, J. Geophys. Res., 92, 4467, 1987.
- P. A. Heelis et al., An analytical model of high-latitude ionospheric convection, J. Geophys. Res., 87, 6339, 1982.
