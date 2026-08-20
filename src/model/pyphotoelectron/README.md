# Photoelectron

`Photoelectron` wraps Richards' simplified ionospheric photoelectron-flux model. It evaluates 100 one-eV bins centered from 0.5 to 99.5 eV.

## Interface

```python
from model import Photoelectron

result = Photoelectron().calculate(
    alt_km=148.0, sza_deg=0.0,
    electron_temperature_K=1000.0, neutral_temperature_K=800.0,
    O_cm3=1e10, O2_cm3=1e9, N2_cm3=1e9,
    electron_density_cm3=1e6, f107=71.0,
)
```

All point inputs support NumPy broadcasting. Supply either `f107` or exactly nine `euv_factors`, not both. The result contains `energy_eV`, total and per-steradian differential flux, and `attenuation_factor`. The wrapper warns above 350 km or when attenuation falls below 0.14, matching the scientific limits documented by the original implementation.

## Files and reference

`photoelectron.for` contains the Richards (1992) numerical model; `photoelectron_cshim.F90` exposes a state-free C ABI. The constructor optionally accepts `dll_path`.
