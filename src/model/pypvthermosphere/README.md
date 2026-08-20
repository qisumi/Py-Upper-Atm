# PVThermosphere

`PVThermosphere` wraps the Pioneer Venus neutral thermosphere model (VTS3).

## Interface

```python
from model import PVThermosphere

result = PVThermosphere().calculate(
    alt_km=250.0, lat_deg=0.0, local_time_hours=12.0,
    f107a=200.0, f107=200.0,
)
```

The constructor optionally accepts `dll_path`. Inputs support NumPy broadcasting; the callable range is 100–250 km and local time is `[0, 24)`. Values below the documented scientific range of 140 km emit `RuntimeWarning` so the original reference-driver cases remain reproducible. Outputs include total mass density, CO2/O/CO/He/N/N2 number densities, and local/exospheric temperatures.

## Files and reference

`pvatmos.for` contains the sanitized VTS3 routines and `pvthermosphere_cshim.F90` exposes the C ABI. Persistent Fortran work arrays are declared explicitly, producing repeatable results across platforms and call order. The model is based on Pioneer Venus thermosphere observations.
