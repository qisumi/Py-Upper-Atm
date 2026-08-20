# PVIonosphere

`PVIonosphere` implements the Pioneer Venus empirical electron-density and electron-temperature fits.

## Interface

```python
from model import PVIonosphere

result = PVIonosphere().calculate(alt_km=200.0, sza_deg=30.0)
```

The constructor accepts `dll_path`, `data_dir`, and `auto_download`. Inputs support scalar or broadcastable arrays; altitude is limited to 150–3000 km. Results include the broadcast coordinates plus both `log10_electron_density_cm3`/`electron_density_cm3` and `log10_electron_temperature_K`/`electron_temperature_K`.

## Files and reference

Python parses `fsmod.dat` and `fsmodt.dat` and passes their coefficients to `pvionosphere_cshim.F90`; the native routine never opens files or depends on the current working directory. The fits are derived from Pioneer Venus ionospheric observations.
