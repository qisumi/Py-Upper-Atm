# EUVAC

`EUVAC` implements the Torr 37-bin solar EUV photon-flux parameterization using daily and 81-day-mean F10.7 indices.

## Interface

```python
from model import EUVAC

result = EUVAC().calculate(f107=80.0, f107a=80.0)
```

The constructor optionally accepts `dll_path`. `f107` and `f107a` must be finite positive scalars or broadcastable arrays. The result returns the broadcast inputs, `bin_index` 1–37, and `photon_flux_cm2_s` with a final dimension of 37.

## Files and reference

`euvac_cshim.F90` contains the C ABI implementation and `CMakeLists.txt` builds `euvac.dll` or `libeuvac.so`. The 37-bin coefficients follow the EUVAC/Torr reference implementation supplied with the source material.
