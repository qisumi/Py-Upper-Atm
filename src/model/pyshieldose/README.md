# SHIELDOSE — Radiation Dose Behind Aluminum Shielding

## Overview

SHIELDOSE computes absorbed radiation dose behind aluminum shielding for space applications. It supports four detector materials (Al, H₂O, Si, SiO₂) and three geometry configurations:

- **Slab**: Transmission surface of a finite aluminum slab
- **Semi-infinite**: Dose in a semi-infinite aluminum medium
- **Sphere**: Dose at the center of an aluminum sphere

The model integrates user-provided particle spectra (solar protons, trapped protons, electrons) against pre-calculated mono-energetic depth-dose lookup tables.

## Directory Structure

```text
src/model/pyshieldose/
├── shieldose_cshim.F90    # Fortran computation (spline interpolation, integration, sphere conversion)
├── CMakeLists.txt          # Build configuration
├── __init__.py             # Python wrapper
├── README.md               # This file
└── README_zh.md            # Chinese documentation
```

## Data Files

The model requires `shieldose.dat` which contains:
- Proton dose data (28 energies × 51 depth points)
- Electron dose data (9 energies × 41 depth points × 2 tables)
- Bremsstrahlung dose data (10 energies × 60 depth points × 2 tables)

Data is automatically downloaded on first use via `ensure_model_data()`.

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `detector` | `int` | `1` | Detector material: 1=Al, 2=H₂O, 3=Si, 4=SiO₂ |
| `unit` | `int` | `2` | Depth unit: 1=mils, 2=g/cm², 3=mm |
| `data_dir` | `str/Path` | `None` | Custom data directory |
| `auto_download` | `bool` | `True` | Whether to auto-download missing data files |
| `dll_path` | `str/Path` | `None` | Custom DLL path |

## `calculate(...)` Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `depths` | `float/array` | Positive shielding depth values |
| `solar_proton_energies` | `array` | Solar proton spectrum energies (MeV), 3–101 points |
| `solar_proton_flux` | `array` | Solar proton spectrum flux (/Energy/cm²) |
| `trapped_proton_energies` | `array` | Trapped proton spectrum energies (MeV), 3–101 points |
| `trapped_proton_flux` | `array` | Trapped proton spectrum flux (/Energy/cm²/Time) |
| `electron_energies` | `array` | Electron spectrum energies (MeV), 3–101 points |
| `electron_flux` | `array` | Electron spectrum flux (/Energy/cm²/Time) |
| `eunit` | `float` | Energy unit conversion factor (default 1.0 for /MeV) |
| `tinter` | `float` | Mission duration in unit times (default 1.0) |

## Return Dictionary

| Key | Shape | Description |
|-----|-------|-------------|
| `depths` | scalar or (N,) | Input depths |
| `detector` | dict | `{"id": int, "name": str}` |
| `unit` | dict | `{"id": int, "name": str}` |
| `dose_slab` | (5,) or (N,5) | Slab geometry dose (rads) |
| `dose_semi` | (5,) or (N,5) | Semi-infinite medium dose (rads) |
| `dose_sphere` | (5,) or (N,5) | Sphere center dose (rads) |

Each dose array has 5 columns:
1. Electron dose
2. Bremsstrahlung dose
3. Electron + Bremsstrahlung
4. Trapped proton dose
5. Solar proton dose

## Usage Example

```python
from model import SHIELDOSE
import numpy as np

model = SHIELDOSE(detector=1, unit=2)

result = model.calculate(
    depths=np.array([0.1, 0.5, 1.0, 5.0]),
    electron_energies=[0.1, 1.0, 5.0],
    electron_flux=[1e4, 1e3, 1e2],
    trapped_proton_energies=[0.1, 1.0, 10.0, 100.0],
    trapped_proton_flux=[1e4, 1e3, 1e2, 1e1],
    tinter=86400.0,  # 1 day
)

print(result["dose_slab"])  # [N, 5] array of doses in rads
```

## References

- Seltzer, S. M. (1980). *SHIELDOSE: A Computer Code for Space-Shielding Radiation Dose Calculations*. NBS Technical Note 1116.
- Seltzer, S. M. (1979). *Calculation of Photonuclear Reaction Products and Their Contributions to Dose Behind Shielding*. IEEE Trans. Nuclear Sci. NS-26, 4896.
