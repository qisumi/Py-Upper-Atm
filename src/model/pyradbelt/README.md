# RADBELT — AP-8 / AE-8 Trapped Radiation Models

[中文文档 (Chinese)](README_zh.md)

## Model Background

The RADBELT model implements the NASA AP-8 and AE-8 trapped radiation environment models developed by J. I. Vette and colleagues at NSSDC. These models provide omnidirectional integral fluxes of trapped protons (AP-8) and electrons (AE-8) in the Earth's radiation belts as a function of L-value (McIlwain parameter), magnetic field strength ratio (B/B0), and particle energy.

Two solar activity variants are available for each particle type:
- **AP8MAX / AP8MIN**: Proton fluxes at solar maximum / minimum
- **AE8MAX / AE8MIN**: Electron fluxes at solar maximum / minimum

The models use empirically derived flux maps that are interpolated in L-B/B0-energy space by the TRARA1/TRARA2 subroutines (Bilitza, 1988).

This module compiles the Fortran subroutines into a shared library and wraps them via `ctypes` as the `RADBELT` class, following the project's unified `Model.calculate(...)` interface.

**References**:

> Vette, J. I., *The AE-8 Trapped Electron Model Environment*, NSSDC Report 91-24, 1991.

> Vette, J. I., *The AP-8 Trapped Proton Environment for Solar Maximum and Solar Minimum*, NSSDC Report, 1991.

> Bilitza, D., *Radbelt - Trapped Radiation models*, NSSDC-ID: PT-14A, 1988.

## Directory Structure

```
pyradbelt/
├── trmfun.for           # Fortran 77 core interpolation subroutines (TRARA1, TRARA2)
├── radbelt_cshim.F90    # C ABI shim, exports radbelt_load_data() and radbelt_calc_flux()
├── CMakeLists.txt       # CMake target radbelt
├── __init__.py          # Python Model class
└── README.md            # This file
```

## Fortran Interface

### `trmfun.for` — Core Subroutines

```fortran
SUBROUTINE TRARA1(DESCR, MAP, FL, BB0, E, F, N)
```

| Parameter | Direction | Type        | Description                                              |
|-----------|-----------|-------------|----------------------------------------------------------|
| `DESCR`   | input     | `INTEGER(8)`| Header array from data file                              |
| `MAP`     | input     | `INTEGER(*)`| Flux map array from data file                            |
| `FL`      | input     | `REAL`      | L-value (McIlwain parameter)                             |
| `BB0`     | input     | `REAL`      | B/B0 — magnetic field strength normalized to equatorial  |
| `E`       | input     | `REAL(N)`   | Array of energies in MeV                                 |
| `F`       | output    | `REAL(N)`   | log10(integral flux) in particles/(cm²·s)                |
| `N`       | input     | `INTEGER`   | Number of energies                                       |

### `radbelt_cshim.F90` — C ABI

```c
void radbelt_load_data(int *ihead, int nmap, int *map);
void radbelt_calc_flux(float l_value, float bb0, float *energies, float *flux, int n);
```

## Input Parameters

| Parameter    | Type          | Description                                                 |
|-------------|---------------|-------------------------------------------------------------|
| `l_value`   | float / array | L-value (McIlwain magnetic shell parameter), 1.0–15.6      |
| `bb0`       | float / array | B/B0 ratio (magnetic field / equatorial field), ≥ 1.0      |
| `energy_mev`| float / array | Particle energy in MeV                                      |

### Energy Ranges

| Model Type | Particle | Valid Energy Range (MeV) |
|-----------|----------|--------------------------|
| AP8MAX, AP8MIN | Protons | 0.1 – 400 |
| AE8MAX, AE8MIN | Electrons | 0.04 – 7.0 |

## Output

`calculate()` returns a dictionary with the following fields:

| Field         | Type          | Description                                                |
|---------------|---------------|------------------------------------------------------------|
| `l_value`     | float / ndarray | Input L-value(s)                                         |
| `bb0`         | float / ndarray | Input B/B0 value(s)                                      |
| `energy_mev`  | float / ndarray | Input energy value(s) (MeV)                              |
| `flux`        | float / ndarray | log10(omnidirectional integral flux) [particles/(cm²·s)] |

Note: When the flux is zero or negative (outside model coverage), `flux` is returned as 0.0.

## Usage Examples

### Single-point calculation

```python
from model import RADBELT

model = RADBELT("AE8MIN")
result = model.calculate(l_value=3.0, bb0=1.0, energy_mev=1.0)

import math
flux_linear = 10 ** result["flux"]
print(f"log10(flux) = {result['flux']:.4f}")
print(f"flux = {flux_linear:.2e} particles/(cm²·s)")
```

### Batch calculation over L-values

```python
import numpy as np

l_vals = [1.5, 2.0, 3.0, 4.0, 6.0]
result = model.calculate(l_value=l_vals, bb0=1.0, energy_mev=0.5)

for l, f in zip(l_vals, result["flux"]):
    print(f"L={l:.1f}: log10(flux)={f:.4f}")
```

### Compare proton and electron models

```python
from model import RADBELT

proton_model = RADBELT("AP8MIN")
electron_model = RADBELT("AE8MIN")

p = proton_model.calculate(l_value=3.0, bb0=1.0, energy_mev=10.0)
e = electron_model.calculate(l_value=3.0, bb0=1.0, energy_mev=1.0)

print(f"Proton flux (>10 MeV): {10**p['flux']:.2e} cm⁻²s⁻¹")
print(f"Electron flux (>1 MeV): {10**e['flux']:.2e} cm⁻²s⁻¹")
```

## Constructor Parameters

| Parameter      | Default       | Description                                    |
|----------------|---------------|------------------------------------------------|
| `model_type`   | (required)    | One of `"AP8MAX"`, `"AP8MIN"`, `"AE8MAX"`, `"AE8MIN"` |
| `dll_path`     | Auto-detected | Custom DLL path                                |
| `data_dir`     | `None`        | Custom data directory (auto-downloaded if not set) |
| `auto_download`| `True`        | Whether to auto-download missing data files    |

## Coordinate Notes

- **L-value**: McIlwain magnetic shell parameter. L=1 corresponds to the Earth's surface; L≈6.6 is at geostationary orbit.
- **B/B0**: Ratio of local magnetic field strength to the equatorial field strength on the same field line. B/B0=1 at the magnetic equator; B/B0>1 away from the equator.
- For L-value and B/B0 computation from geographic coordinates, use the `IGRF` model with `L_value` output.

## Acknowledgement

Please acknowledge the software provider (NSSDC) and the model authors (J. I. Vette et al.) in any publication that results from work using this software and in any software program/application that includes this model code.
