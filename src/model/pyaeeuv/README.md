# AEEUV

`AEEUV` reads the four Atmosphere Explorer reference EUV spectra distributed with the original model material. It is a NumPy/data-table model and does not load a native library.

## Interface

```python
from model import AEEUV

result = AEEUV().calculate(spectrum="f74113")
```

The constructor accepts `data_dir` and `auto_download`. `spectrum` is one of `r74113`, `f74113`, `f76ref`, or `sc21refw`. The result contains `wavelength_angstrom`, `photon_flux_m2_s`, `line_or_range`, `group_type`, and `adjustment_factor`; array columns preserve the source-file order. Data are resolved through UpperAtmPy's model-data mechanism, so the model also works outside the repository.

## Files and reference

`__init__.py` parses `data/aeeuvdata/*.dat`. The files are the AE-EUV reference spectra and retain their original labels and adjustment metadata.
