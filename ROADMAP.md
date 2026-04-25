# UpperAtmPy Development Roadmap

[中文版 (Chinese)](ROADMAP_zh.md)

## Current Status

The following models have been fully ported and are available in the `src/model/` package:

| Model | Class | Description | Status |
|-------|-------|-------------|--------|
| NRLMSIS-2.0 | `MSIS2` | Neutral atmosphere temperature & density | Done |
| NRLMSISE-00 | `MSIS00` | Neutral atmosphere temperature & density | Done |
| HWM14 | `HWM14` | Horizontal neutral wind | Done |
| HWM93 | `HWM93` | Horizontal neutral wind | Done |

## Planned Models

All models below are sourced from the `TODO/` directory (CCMC ModelWeb Archive). Each will be ported following the established pattern: Fortran/C source compiled to DLL via CMake, wrapped with `ctypes`, and exposed as a single `Model.calculate(...)` class.

### Phase 1 — Atmospheric & Ionospheric Extensions

These models extend the existing neutral atmosphere and ionosphere capabilities and share similar FFI characteristics with the already-ported models.

| Model | Directory | Description | Language | External Data |
|-------|-----------|-------------|----------|---------------|
| IGRF-13 | `TODO/IGRF` | International Geomagnetic Reference Field — computes geomagnetic field components (X, Y, Z, F), L-value, dip angle, declination from 1945 onward | Fortran 77 | DGRF/IGRF coefficient `.dat` files (1945–2025) |
| CIRA-86 | `TODO/CIRA` | COSPAR International Reference Atmosphere 1986 — temperature, pressure, zonal wind, geopotential height for 0–120 km | Fortran 77 | 24 binary + 12 ASCII monthly tables |
| Jacchia 1977 | `TODO/Jacchi-Reference-Atmosphere` | Jacchia reference atmosphere — temperature and number density profiles (N2, O2, O, Ar, He, H) from 90–2500+ km | Fortran 77 | None (hard-coded) |
| MET | `TODO/MET-Model` | Marshall Engineering Thermosphere — modified Jacchia 1970/71 thermospheric model for engineering applications | Fortran 77 | None (hard-coded) |
| MSIS-86 | `TODO/MSIS/MSIS86` | MSIS-86 / CIRA-86 thermosphere model — historical MSIS generation | Fortran 77 | `msis86.dat` (binary coefficients) |
| MSISE-90 | `TODO/MSIS/MSIS90` | MSISE-90 — extended MSIS-86 downward to ground level | Fortran 77 | None (hard-coded) |
| Chiu Ionospheric Model | `TODO/Chiu-Ionospheric-Model` | Empirical ionospheric electron density — E, F1, F2 layer densities (90–500 km) | Fortran 77 | None (hard-coded) |

### Phase 2 — Magnetospheric & Radiation Belt Models

These models address magnetospheric physics and the radiation environment, critical for space weather and spacecraft mission planning.

| Model | Directory | Description | Language | External Data |
|-------|-----------|-------------|----------|---------------|
| Tsyganenko (T89/T96/T01/TS04) | `TODO/Tsyganenko-Models` | Data-based magnetospheric magnetic field models — external field contribution, field line tracing | Fortran 77 | None (hard-coded); includes Geopack-2005 |
| RADBELT (AP8/AE8) | `TODO/RADBELT` | Trapped radiation environment — omnidirectional proton/electron fluxes (AP8MAX/MIN, AE8MAX/MIN) | Fortran 77 / C | 8 binary/ASCII flux maps (~80K each) |
| SHIELDOSE | `TODO/SHIELDOSE` | Radiation dose behind aluminum shielding — trapped, solar proton, and electron environments | Fortran 77 | `shieldose.dat` (binary dose-depth data) |
| SOLPRO | `TODO/SOLPRO` | Interplanetary solar proton fluence at 1 AU — mission duration and confidence-level based | Fortran IV | None (hard-coded) |
| SOFIP | `TODO/SOFIP` | Short Orbital Flux Integration Program — mission-averaged fluxes along spacecraft trajectories using AP8/AE8 | Fortran 77 | Binary radiation belt maps |
| Geomagnetic Cutoff Rigidity | `TODO/Geomagnetic-Cutoff-Rigidity` | Cosmic ray cutoff rigidity thresholds — charged particle trajectory prediction | Fortran 77 | None (uses IGRF internally) |

### Phase 3 — Geomagnetic & Electric Field Models

Spherical harmonic geomagnetic field models and high-latitude ionospheric electric field models.

| Model | Directory | Description | Language | External Data |
|-------|-----------|-------------|----------|---------------|
| GSFC Models | `TODO/GSFC-Model-Coefficients` | GSFC geomagnetic field models (9/65, 12/66, 10/68, 8/69, 80, 83, 87) — field components at any location | Fortran 77 | 5 binary `.dat` coefficient files |
| Jensen & Cain (1962) | `TODO/Jensen-Cain-Model-Coefficients` | Early spherical harmonic geomagnetic field model (degree 12, epoch ~1962) | Fortran 77 | `jensen_cain_62.dat` (binary) |
| MGST Coefficients | `TODO/MGST-Model-Coefficients-All` | MGST geomagnetic field model coefficients for epochs 1980 and 1981 | Data only | 2 binary `.dat` files |
| Heppner-Maynard-Rich | `TODO/Heppner-Maynard-Rich_Electric-Field-Model` | High-latitude ionospheric electric potential — spherical harmonic fits, Joule heating | Fortran 77 | `hmcoef.dat` (binary) |
| ISR Ion Drift | `TODO/ISR-Ion-Drift-Model` | Incoherent Scatter Radar ion drift model — quiet-day E×B drifts at 300 km | Fortran 77 | None (hard-coded) |
| Auroral Oval | `TODO/Auroral-Oval-Representation` | Feldstein auroral oval boundary model — poleward/equatorward boundaries via Fourier series | Fortran 77/90 | None (hard-coded) |
| Xu-Li Neutral Sheet | `TODO/Xu-Li-Neutral-Sheet-Model` | Magnetotail equatorial neutral sheet position (SEN, DEN, AEN variants) | Fortran 77 | None (hard-coded) |

### Phase 4 — Solar Irradiance & Planetary Models

Solar EUV flux models and planetary atmosphere models.

| Model | Directory | Description | Language | External Data |
|-------|-----------|-------------|----------|---------------|
| EUV (AE-EUV / EUV91 / EUVAC / SOLAR2000) | `TODO/EUV` | Solar EUV irradiance models (18–1050 Å) — thermospheric/ionospheric input | Fortran 77 | Coefficient files, proxy indices, reference spectra |
| Photoelectron Code | `TODO/photoelectron_code` | Photoelectron flux model — 120–500 km, solar zenith angle driven | Fortran 77 | None (hard-coded) |
| Pioneer Venus Ionosphere | `TODO/PV-Ionosphere-Mode` | Venus ionospheric electron density & temperature — solar zenith angle and altitude | Fortran 77 | `fsmod.dat`, `fsmodt.dat` (binary) |
| Pioneer Venus Thermosphere | `TODO/PV-Thermosphere-Model` | Venus neutral atmosphere densities (CO2, O, CO, He, N, N2) — MSIS-like structure | Fortran 77 | None (hard-coded) |
| Exospheric H Model | `TODO/Exospheric-H-Model` | Exospheric hydrogen density (40 radii × 4 solar conditions) — spherical harmonic expansion | Data only | `h_exos.dat` (binary) |

### Not Planned for Porting

The following items are documentation-only, Java tools, or duplicates and are not targeted for Python wrapping.

| Item | Directory | Reason |
|------|-----------|--------|
| Archived Models Info Pages | `TODO/Archived-Models-InfoPages` | HTML documentation catalogue only — no source code |
| Revised SERF2 Solar EUV Flux | `TODO/Revised-SERF2-Solar-EUV-Flux-Mode` | Duplicate of `TODO/EUV` — same content |
| LWS / MineTool | `TODO/LWS` | Java-based data mining tool — not a Fortran/C model |
| HWM93 (in TODO) | `TODO/HWM93` | Already ported as `model.HWM93` |

## Porting Guidelines

Each model port should follow the established conventions in `AGENTS.md`:

1. **Source layout**: Create a subdirectory under `src/model/` (e.g., `src/model/pyigrf/`).
2. **Build system**: Add the Fortran/C sources to `CMakeLists.txt` with a new target producing a shared library (DLL/.so/.dylib).
3. **Python wrapper**: Implement a `Model` class with a single `calculate(...)` method accepting keyword-only arguments.
4. **Lazy loading**: Register the new class in `src/model/__init__.py` via `_LAZY_EXPORTS`.
5. **Module `__all__`**: Each model module exports only `["Model"]`.
6. **Return value**: `calculate(...)` returns a plain `dict`.
7. **Tests**: Add at least one test in `tests/` and an example script in `example/`.
8. **Utilities**: Shared helpers go in `src/utils/`, never in `src/model/`.
