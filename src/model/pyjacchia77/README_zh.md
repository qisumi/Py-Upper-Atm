# Jacchia 1977 Reference Atmosphere Model

## Model Background

The Jacchia 1977 Reference Atmosphere is an empirical thermospheric model published by L. G. Jacchia in 1977. It provides temperature profiles and number density profiles for major neutral species (N2, O2, O, Ar, He, H) over the altitude range 90–2500+ km.

This module compiles the Fortran source into a shared library and wraps it via `ctypes` as the `Jacchia77` class, following the project's unified `Model.calculate(...)` interface.

**No external data files are required** — all coefficients are hard-coded in the Fortran source.

**References**:

> Jacchia, L. G., "Thermospheric Temperature, Density and Composition: New Models," SAO Special Report No. 375 (Smithsonian Institution Astrophysical Observatory, Cambridge, MA, March 15, 1977).

## Directory Structure

```
pyjacchia77/
├── j77sri.for              # Fortran 77 original model subroutine
├── jacchia77_cshim.F90     # C ABI shim, exports jacchia77_eval()
├── CMakeLists.txt          # CMake target jacchia77
├── __init__.py             # Python Model class
└── README_zh.md            # This file
```

## Fortran Interface

### `j77sri.for` — `j77sri` subroutine

```fortran
subroutine j77sri(maxz, Tinf, Z, T, CN2, CO2, CO, CAr, CHe, CH, CM, WM)
```

| Parameter | Direction | Type | Description |
|-----------|-----------|------|-------------|
| `maxz` | input | `integer` | Maximum altitude (km), determines array size |
| `Tinf` | input | `real` | Exospheric temperature (K) |
| `Z` | output | `real(0:maxz)` | Altitude array (km) |
| `T` | output | `real(0:maxz)` | Temperature array (K) |
| `CN2` | output | `real(0:maxz)` | N2 number density (cm⁻³) |
| `CO2` | output | `real(0:maxz)` | O2 number density (cm⁻³) |
| `CO` | output | `real(0:maxz)` | O number density (cm⁻³) |
| `CAr` | output | `real(0:maxz)` | Ar number density (cm⁻³) |
| `CHe` | output | `real(0:maxz)` | He number density (cm⁻³) |
| `CH` | output | `real(0:maxz)` | H number density (cm⁻³) |
| `CM` | output | `real(0:maxz)` | Total number density (cm⁻³) |
| `WM` | output | `real(0:maxz)` | Mean molecular weight (g/mol) |

### `jacchia77_cshim.F90` — C ABI

```c
void jacchia77_eval(
    float Tinf,        // Exospheric temperature (K)
    float *alt_km,     // Altitude array (km)
    int n_alt,         // Number of altitudes
    float *T_out,      // Temperature output (K)
    float *N2_out,     // N2 number density output (cm⁻³)
    float *O2_out,     // O2 number density output (cm⁻³)
    float *O_out,      // O number density output (cm⁻³)
    float *Ar_out,     // Ar number density output (cm⁻³)
    float *He_out,     // He number density output (cm⁻³)
    float *H_out,      // H number density output (cm⁻³)
    float *rho_out,    // Total number density output (cm⁻³)
    float *W_out       // Mean molecular weight output (g/mol)
);
```

## Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `alt_km` | float / array | Altitude (km), range 0–2500 |
| `Tinf_K` | float | Exospheric temperature (K), scalar |

## Output

`calculate()` returns a dictionary with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `alt_km` | float / ndarray | Output altitude(s), same shape as broadcast inputs |
| `Tinf_K` | float | Exospheric temperature (K) |
| `T_local_K` | float / ndarray | Local temperature (K) |
| `N2_cm3` | float / ndarray | N2 number density (cm⁻³) |
| `O2_cm3` | float / ndarray | O2 number density (cm⁻³) |
| `O_cm3` | float / ndarray | O number density (cm⁻³) |
| `Ar_cm3` | float / ndarray | Ar number density (cm⁻³) |
| `He_cm3` | float / ndarray | He number density (cm⁻³) |
| `H_cm3` | float / ndarray | H number density (cm⁻³) |
| `total_density_cm3` | float / ndarray | Total number density (cm⁻³) |
| `mean_molecular_weight` | float / ndarray | Mean molecular weight (g/mol) |

## Usage Examples

### Single-point calculation

```python
from model import Jacchia77

model = Jacchia77()
result = model.calculate(alt_km=200.0, Tinf_K=1000.0)

print(f"Temperature: {result['T_local_K']:.2f} K")
print(f"N2: {result['N2_cm3']:.2e} cm⁻³")
print(f"O: {result['O_cm3']:.2e} cm⁻³")
```

### Profile calculation

```python
import numpy as np

alts = np.arange(90, 501, 10)  # 90-500 km, every 10 km
result = model.calculate(alt_km=alts, Tinf_K=1000.0)

print(f"Temperature range: [{result['T_local_K'].min():.1f}, {result['T_local_K'].max():.1f}] K")
```

### Different exospheric temperatures

```python
for Tinf in [600.0, 800.0, 1000.0, 1200.0, 1500.0]:
    result = model.calculate(alt_km=200.0, Tinf_K=Tinf)
    print(f"Tinf={Tinf:.0f} K: T={result['T_local_K']:.2f} K")
```

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dll_path` | Auto-detected | Custom DLL path |

## Model Notes

- The model is valid for altitudes 90–2500 km
- For altitudes below 90 km, the U.S. Standard Atmosphere 1976 is used
- For 86–89 km, the barometric equation is used to connect
- For altitudes above 90 km, the Jacchia 1977 model is used
- H atom densities are only calculated when maximum altitude ≥ 500 km and altitude ≥ 150 km

## References

1. Jacchia, L. G., "Thermospheric Temperature, Density and Composition: New Models," SAO Special Report No. 375, Smithsonian Institution Astrophysical Observatory, Cambridge, MA, March 15, 1977.

2. U.S. Committee on Extension to the Standard Atmosphere, "U.S. Standard Atmospheres 1976," USGPO, Washington, DC, 1976.

3. Chamberlain, J. W., and D. M. Hunten, "Theory of Planetary Atmospheres," Academic Press, NY, 1987.
