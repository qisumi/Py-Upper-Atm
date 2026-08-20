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
| Auroral Oval | `AuroraOval` | Feldstein auroral oval boundary (Holzworth & Meng) | Done |
| IGRF-13/14 | `IGRF` | Int'l Geomagnetic Reference Field — computes field components (X, Y, Z, F, H), dip, declination, L-value from 1900 onward | Done |
| CIRA-86 | `CIRA86` | COSPAR International Reference Atmosphere 1986 — monthly mean temperature, pressure, zonal wind, and geopotential height tables for 0-120 km | Done |
| MSIS-86 | `MSIS86` | MSIS-86 / CIRA-86 thermosphere model — neutral temperature and density above 85 km | Done |
| MSISE-90 | `MSISE90` | MSISE-90 — extended MSIS-86 downward to ground level | Done |
| Jacchia 1977 | `Jacchia77` | Jacchia reference atmosphere — temperature and species density profiles (N2, O2, O, Ar, He, H) for 90–2500 km | Done |
| MET | `MET` | Marshall Engineering Thermosphere — modified Jacchia 1970 model for engineering applications | Done |
| Chiu | `Chiu` | Chiu ionospheric electron density — E, F1, F2 layer densities (90–500 km) | Done |
| Tsyganenko (T89/T96/T01/TS04) | `Tsyganenko` | Data-based magnetospheric magnetic field models — external field contribution in GSM coordinates | Done |
| SOLPRO | `SOLPRO` | Interplanetary solar proton fluence at 1 AU — mission duration and confidence-level based | Done |
| RADBELT (AP8/AE8) | `RADBELT` | Trapped radiation environment — omnidirectional proton/electron fluxes (AP8MAX/MIN, AE8MAX/MIN) | Done |
| SHIELDOSE | `SHIELDOSE` | Radiation dose behind aluminum shielding — trapped, solar proton, and electron environments | Done |
| SOFIP | `SOFIP` | Short Orbital Flux Integration Program — mission-averaged fluxes along spacecraft trajectories using AP8/AE8 | Done |
| Geomagnetic Cutoff Rigidity | `CutoffRigidity` | Cosmic ray cutoff rigidity thresholds — charged particle trajectory prediction (IGRF-95) | Done |
| GSFC Geomagnetic Field | `GSFC` | GSFC geomagnetic field models (80, 83, 87) — spherical harmonic field components at any location | Done |
| Jensen & Cain (1962) | `JensenCain` | Early spherical harmonic geomagnetic field model (degree 6, epoch 1960.0) | Done |
| MGST Geomagnetic Field | `MGST80`, `MGST81` | MGST geomagnetic field models from MAGSAT data — epochs 1979.85 and 1980.0 | Done |
| Heppner-Maynard-Rich | `HMR` | High-latitude ionospheric electric potential, conductivity, Joule heating, and field-aligned current | Done |
| ISR Ion Drift | `ISRDrift` | Quiet-day ionospheric E×B drifts at 300 km (Richmond et al., 1980) | Done |
| Xu-Li Neutral Sheet | `XuLi` | Magnetotail equatorial neutral sheet position (SEN, DEN, AEN variants) | Done |
| AE-EUV Reference Spectra | `AEEUV` | Historical solar EUV reference spectra | Done |
| Revised SERF2 EUV91 | `EUV91` | Date-driven 39-bin solar EUV flux | Done |
| EUVAC | `EUVAC` | F10.7-driven 37-bin solar EUV flux | Done |
| Photoelectron | `Photoelectron` | Richards ionospheric photoelectron spectrum | Done |
| Pioneer Venus Ionosphere | `PVIonosphere` | Venus electron density and temperature | Done |
| Pioneer Venus Thermosphere | `PVThermosphere` | Venus neutral density and temperature | Done |
| Exospheric Hydrogen | `ExosphericH` | Hodges terrestrial exospheric H density | Done |

## Planned Models

All models below are sourced from the `TODO/` directory (CCMC ModelWeb Archive). Native-code models will follow the established pattern: Fortran/C source compiled to DLL via CMake, wrapped with `ctypes`, and exposed as a single `Model.calculate(...)` class. Table-only models may be exposed through the same Python API without a DLL.

### Phase 1 — Atmospheric & Ionospheric Extensions

_No remaining models in this phase._

### Phase 2 — Magnetospheric & Radiation Belt Models

These models address magnetospheric physics and the radiation environment, critical for space weather and spacecraft mission planning.

_No remaining models in this phase._

### Phase 3 — Geomagnetic & Electric Field Models

Spherical harmonic geomagnetic field models and high-latitude ionospheric electric field models.

_No remaining models in this phase._

### Phase 4 — Solar Irradiance & Planetary Models

Solar EUV flux models and planetary atmosphere models.

_No remaining models in this phase._

### Not Planned for Porting

The following items are documentation-only, Java tools, or duplicates and are not targeted for Python wrapping.

| Item | Directory | Reason |
|------|-----------|--------|
| Archived Models Info Pages | `TODO/Archived-Models-InfoPages` | HTML documentation catalogue only — no source code |
| Revised SERF2 Solar EUV Flux | `TODO/Revised-SERF2-Solar-EUV-Flux-Mode` | Duplicate of `TODO/EUV` — same content |
| Solar2000 | `TODO/EUV/solar2000` | Only an external availability notice is archived; no redistributable source, coefficients, or reference output |
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
