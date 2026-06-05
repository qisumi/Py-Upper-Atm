# SOFIP — Short Orbital Flux Integration Program

## Overview

SOFIP computes mission-averaged trapped radiation fluxes along spacecraft trajectories using the AP-8 / AE-8 radiation belt models. Developed by Stassinopoulos et al. at NASA/GSFC, it integrates flux contributions at each point of an orbit to produce energy-dependent averaged integral, differential, and difference-integral spectra.

The program also estimates solar proton fluence for trajectory segments with weak geomagnetic shielding (L >= 5) using the SOLPRO model, weighted by the exposure fraction.

SOFIP supports four radiation belt map types:

- **AP8MAX** — Solar maximum trapped proton model
- **AP8MIN** — Solar minimum trapped proton model
- **AE8MAX** — Solar maximum trapped electron model
- **AE8MIN** — Solar minimum trapped electron model

## Directory Structure

```text
src/model/pysofip/
├── sofip_legacy.for      # Original Fortran 77 source (TRARA1, TRARA2, DSPCTR, SOFIP_SOLPRO)
├── sofip_cshim.F90       # Fortran 90 C ABI shim (data loading, orbit integration)
├── CMakeLists.txt         # Build configuration
├── __init__.py            # Python wrapper
├── README.md              # This file
└── README_zh.md           # Chinese documentation
```

## Fortran Interface

The shim exposes three C-callable subroutines:

| Subroutine | Description |
|------------|-------------|
| `sofip_load_data(ihead, nmap, map)` | Loads radiation belt map data (same format as RADBELT) |
| `sofip_integrate(...)` | Main orbit-averaged flux integration |
| `sofip_is_loaded(flag)` | Checks whether map data has been loaded |

The integration routine calls legacy subroutines from `sofip_legacy.for`:

- **TRARA1** — Per-point flux lookup from the radiation belt map for 30 energy levels
- **DSPCTR** — Differential spectrum computation from log-integral fluxes
- **SOFIP_SOLPRO** — Solar proton fluence calculation (mission duration and confidence level)

## Data Files

The model reuses RADBELT ASCII data files (`ap8max.asc`, `ap8min.asc`, `ae8max.asc`, `ae8min.asc`) located under `radbeltdata/`. Data is automatically resolved on construction via `ensure_model_data("radbelt", ...)`.

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_type` | `str` | (required) | Radiation belt model: `"AP8MAX"`, `"AP8MIN"`, `"AE8MAX"`, `"AE8MIN"` |
| `dll_path` | `str/Path` | `None` | Custom DLL/SO path |
| `data_dir` | `str/Path` | `None` | Custom data directory |
| `auto_download` | `bool` | `True` | Whether to auto-download missing data files |

## `calculate(...)` Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `times` | `array` | Trajectory time values (hours) |
| `b_field` | `array` | Magnetic field strength along trajectory (gauss) |
| `l_shell` | `array` | McIlwain L-shell parameter (Earth radii) |
| `duration_months` | `float` | Mission duration (months) for solar proton calculation, default 12 |
| `confidence_pct` | `int` | Confidence level (%) for solar proton calculation (80-99), default 90 |

The three trajectory arrays (`times`, `b_field`, `l_shell`) must have the same length.

## Return Dictionary

| Key | Shape | Description |
|-----|-------|-------------|
| `energy_levels` | (30,) | Energy thresholds (MeV) |
| `integral_flux` | (30,) | Orbit-averaged integral flux (#/cm^2/s) |
| `differential_flux` | (30,) | Differential flux (#/cm^2/s/keV) |
| `difference_flux` | (30,) | Difference integral flux (#/cm^2/s/DE) |
| `solar_proton_energy` | (20,) | Solar proton energy levels (MeV) |
| `solar_proton_fluence` | (20,) | Solar proton fluence (#/cm^2), weighted by exposure |
| `n_al_events` | scalar | Number of Anomalous Large (AL) solar proton events |
| `exposure_factor` | scalar | Fraction of orbit with weak geomagnetic shielding |
| `lzone_counts` | (4,) | L-shell zone point counts: [0..1.1), [1.1..2.8), [2.8..11), [11+ or negative] |
| `total_time_hours` | scalar | Total trajectory time (hours) |
| `time_step_minutes` | scalar | Time step between trajectory points (minutes) |

### Energy Levels

**Proton models (AP8MAX/AP8MIN):** 2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 100, 125, 150, 175, 200, 250, 300, 350, 400, 500 MeV

**Electron models (AE8MAX/AE8MIN):** 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5, 4.75, 5.0, 5.5, 6.0, 6.5, 7.0 MeV

**Solar proton energies:** 10, 20, 30, ..., 200 MeV (20 levels)

## Usage Example

```python
from model import SOFIP
import numpy as np

# Create model for solar maximum protons
model = SOFIP(model_type="AP8MAX")

# Define a simple circular orbit trajectory
n_points = 100
times = np.linspace(0, 1.5, n_points)  # 1.5 hours
l_shell = np.full(n_points, 4.0)       # L = 4.0 Earth radii
b_field = np.full(n_points, 0.005)     # 0.005 gauss

result = model.calculate(
    times=times,
    b_field=b_field,
    l_shell=l_shell,
    duration_months=12.0,
    confidence_pct=90,
)

print("Energy levels (MeV):", result["energy_levels"])
print("Integral flux (#/cm2/s):", result["integral_flux"])
print("Solar proton fluence (#/cm2):", result["solar_proton_fluence"])
print("Exposure factor:", result["exposure_factor"])
print("L-zone counts:", result["lzone_counts"])
print("Total time (hours):", result["total_time_hours"])
```

## References

- Stassinopoulos, E. G., Mead, G. D., Tykka, A. J., & Armstrong, T. W. (1977). *SOFIP: Short Orbital Flux Integration Program*. NASA/GSFC.
- Sawyer, D. M. & Vette, J. I. (1976). *AP-8 Trapped Proton Environment for Solar Maximum and Solar Minimum*. NSSDC/WDC-A-R&S 76-06.
- Vette, J. I. (1991). *The AE-8 Trapped Electron Model Environment*. NSSDC/WDC-A-R&S 91-24.
- King, J. H. (1974). *Solar Proton Fluences for 1977-1983 Space Missions*. J. Spacecraft Rockets, 11(6), 401-408.
