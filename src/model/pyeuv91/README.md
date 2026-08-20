# EUV91

`EUV91` wraps the revised SERF2 solar irradiance model. A deterministic `bind(C)` shim evaluates 39 wavelength bands using coefficients and exact daily proxy-index records parsed by Python.

## Interface

```python
from model import EUV91

result = EUV91().calculate(year=1980, day_of_year=183)
```

The constructor accepts `dll_path`, `data_dir`, and `auto_download`. Inputs may be scalars or broadcastable arrays. Only dates present in `euv91ix2.dat` are accepted; missing days raise `ValueError` and are never interpolated. Results contain the date, band start/end wavelengths, `photon_flux_cm2_s`, and `energy_flux_erg_cm2_s`.

## Files and reference

`euv91_cshim.F90` exposes the native calculation. `euv91coe.txt` and `euv91ix2.dat` provide the model coefficients and historical indices. Work arrays are reinitialized on every call so repeated and batched evaluations are order-independent.
