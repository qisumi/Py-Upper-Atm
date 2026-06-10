# MGST Geomagnetic Field Model

MGST (MAGSAT Geomagnetic Spherical Topology) models of Earth's main magnetic field from the MAGSAT satellite mission.

## Supported Models

| Class | Model | Epoch | Degree/Order | Secular Variation |
|-------|-------|-------|-------------|-------------------|
| `MGST80` | MGST(6/80) | 1979.85 | 13 | None |
| `MGST81` | MGST(4/81) | 1980.0 | 13 (constant) + 7 (1st deriv.) | First derivative |

## Usage

```python
from model import MGST80, MGST81

# MGST(6/80) — scalar + fine attitude, Nov 5-6 1979
m80 = MGST80()
r = m80.calculate(year=1979.85, lat_deg=45.0, lon_deg=0.0, alt_km=0.0)
print(r["F_nT"])  # Total field in nT

# MGST(4/81) — 15-day data set with secular variation
m81 = MGST81()
r = m81.calculate(year=1985.0, lat_deg=45.0, lon_deg=0.0, alt_km=0.0)
```

## Returns

| Key | Unit | Description |
|-----|------|-------------|
| `X_nT` | nT | North component |
| `Y_nT` | nT | East component |
| `Z_nT` | nT | Down component (positive downward) |
| `F_nT` | nT | Total field strength |
| `H_nT` | nT | Horizontal component |
| `inclination_deg` | deg | Magnetic inclination |
| `declination_deg` | deg | Magnetic declination |

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `year` | float | — | Decimal year |
| `lat_deg` | float/array | — | Geodetic latitude (°N) |
| `lon_deg` | float/array | — | Geodetic longitude (°E) |
| `alt_km` | float/array | — | Altitude (km) |
| `nmx` | int | 13 | Max degree and order (1–13) |

## References

- R. A. Langel, Initial Geomagnetic Field Model from MAGSAT, NASA TM-80679, 1980.
- R. A. Langel et al., Initial Geomagnetic Field Model from MAGSAT Vector Data, Geophys. Res. Lett. 7, 793, 1980.
