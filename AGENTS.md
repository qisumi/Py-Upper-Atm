# AGENTS.md - AI Coding Agent Guidelines for UpperAtmPy

## Project Overview

UpperAtmPy is a Python wrapper library for upper atmospheric models. The project uses a `src/` layout and exposes one public class per model:

- `model.MSIS2`
- `model.MSIS00`
- `model.HWM14`
- `model.HWM93`
- `model.AuroraOval`
- `model.IGRF`
- `model.CIRA86`
- `model.MSIS86`
- `model.MSISE90`
- `model.Jacchia77`
- `model.MET`
- `model.Chiu`
- `model.Tsyganenko`
- `model.SOLPRO`
- `model.RADBELT`
- `model.SHIELDOSE`
- `model.SOFIP`
- `model.CutoffRigidity`
- `model.GSFC`
- `model.JensenCain`
- `model.MGST80`
- `model.MGST81`
- `model.HMR`
- `model.ISRDrift`
- `model.XuLi`
- `model.AEEUV`
- `model.EUV91`
- `model.EUVAC`
- `model.Photoelectron`
- `model.PVIonosphere`
- `model.PVThermosphere`
- `model.ExosphericH`

Each class provides one public calculation method: `calculate(...)`. Do not reintroduce multi-model wrappers or old helper exports such as `NRLMSIS2`, `gtd7`, `hwm14_eval`, or `hwm93_eval`.

## Build Commands

```bash
cmake --preset native-release
cmake --build --preset native-release
```

## Test Commands

```bash
python -m pytest
python example/test_msis20.py
python example/test_msis00.py
python example/test_hwm14.py
python example/test_hwm93.py
python example/test_aurora.py
python example/test_igrf.py
python example/test_cira86.py
python example/test_msis86.py
python example/test_msise90.py
python example/test_jacchia77.py
python example/test_met.py
python example/test_chiu.py
python example/test_tsyganenko.py
python example/test_solpro.py
python example/test_radbelt.py
python example/test_shieldose.py
python example/test_sofip.py
python example/test_cutoff.py
python example/test_jensen.py
python example/test_mgst.py
python example/test_hmr.py
python example/test_isr_drift.py
python example/test_xuli.py
python -m pytest tests/test_analysis.py tests/test_analysis_ai.py
python example/test_aeeuv.py
python example/test_euv91.py
python example/test_euvac.py
python example/test_photoelectron.py
python example/test_pv_ionosphere.py
python example/test_pv_thermosphere.py
python example/test_exospheric_h.py
```

## Public API Pattern

```python
from model import MSIS2
from utils.time import doy, seconds_of_day

model = MSIS2(precision="single")
result = model.calculate(
    day=doy(2023, 1, 1),
    utsec=seconds_of_day(12, 0, 0),
    alt_km=100.0,
    lat_deg=35.0,
    lon_deg=116.0,
    f107a=100.0,
    f107=100.0,
)
```

MSIS result dictionaries contain:

- `alt_km`
- `T_local_K`
- `T_exo_K`
- `densities`

HWM result dictionaries contain:

- `alt_km`
- `meridional_wind_ms`
- `zonal_wind_ms`

AuroraOval result dictionaries contain:

- `mlt_hours`
- `activity_level`
- `poleward_boundary_deg`
- `equatorward_boundary_deg`

IGRF result dictionaries contain:

- `year` / `lat_deg` / `lon_deg` / `alt_km`
- `B_north_nT` / `B_east_nT` / `B_down_nT` / `B_abs_nT` / `H_nT`
- `inclination_deg` / `declination_deg`
- `L_value` / `icode`

CIRA86 result dictionaries contain:

- Height mode: `month` / `alt_km` / `lat_deg`
- Height mode: `T_K` / `zonal_wind_ms` / `pressure_mb`
- Pressure mode: `month` / `pressure_mb` / `lat_deg`
- Pressure mode: `T_K` / `zonal_wind_ms` / `geopotential_height_m`

MSIS86 result dictionaries contain:

- `alt_km`
- `T_local_K`
- `T_exo_K`
- `densities` (He, O, N2, O2, Ar, TotalMass, H, N)

MSISE90 result dictionaries contain:

- `alt_km`
- `T_local_K`
- `T_exo_K`
- `densities` (He, O, N2, O2, Ar, TotalMass, H, N)

Jacchia77 result dictionaries contain:

- `alt_km`
- `Tinf_K`
- `T_local_K`
- `N2_cm3` / `O2_cm3` / `O_cm3` / `Ar_cm3` / `He_cm3` / `H_cm3`
- `total_density_cm3`
- `mean_molecular_weight`

MET result dictionaries contain:

- `alt_km` / `lat_deg` / `lon_deg`
- `T_exo_K` / `T_local_K`
- `N2_m3` / `O2_m3` / `O_m3` / `Ar_m3` / `He_m3` / `H_m3`
- `mean_molecular_weight`
- `total_density_kg_m3` / `log10_density`
- `pressure_Pa`
- `gravity_m_s2` / `gamma` / `scale_height_m`
- `cp` / `cv`

Chiu result dictionaries contain:

- `alt_km` / `sunspot_number`
- `Ne_total_cm3`
- `Ne_E_cm3` / `Ne_F1_cm3` / `Ne_F2_cm3`

Tsyganenko result dictionaries contain:

- `tilt_rad`
- `Bx_ext_nT` / `By_ext_nT` / `Bz_ext_nT`
- (if `include_dipole=True`) `Bx_dip_nT` / `By_dip_nT` / `Bz_dip_nT`
- (if `include_dipole=True`) `Bx_total_nT` / `By_total_nT` / `Bz_total_nT`

SOLPRO result dictionaries contain:

- `duration_months` / `confidence_pct`
- `fluence_cm2` (shape `(10,)` for scalar, `(N, 10)` for batch; columns = 10, 20, …, 100 MeV)
- `n_al_events`

RADBELT result dictionaries contain:

- `l_value` / `bb0` / `energy_mev`
- `flux` — log10(omnidirectional integral flux) [particles/(cm²·s)]

SHIELDOSE result dictionaries contain:

- `depths` / `detector` / `unit`
- `dose_slab` — 有限平板透射面剂量 [ndepth, 5] (rads)
- `dose_semi` — 半无限介质剂量 [ndepth, 5] (rads)
- `dose_sphere` — 球体中心剂量 [ndepth, 5] (rads)
- 各剂量矩阵的 5 列: [电子, 轫致辐射, 电子+轫致, 捕获质子, 太阳质子]

SOFIP result dictionaries contain:

- `energy_levels` — 能量阈值 (MeV)，形状 (30,)
- `integral_flux` — 平均积分通量 (#/cm²/s)，形状 (30,)
- `differential_flux` — 微分通量 (#/cm²/s/keV)，形状 (30,)
- `difference_flux` — 差分积分通量 (#/cm²/s/DE)，形状 (30,)
- `solar_proton_energy` — 太阳质子能量 (MeV)，形状 (20,)
- `solar_proton_fluence` — 太阳质子注量 (#/cm²)，形状 (20,)
- `n_al_events` — AL 事件数
- `exposure_factor` — 暴露因子
- `lzone_counts` — L 壳区间点计数，形状 (4,)
- `total_time_hours` — 总轨迹时间 (小时)
- `time_step_minutes` — 时间步长 (分钟)

CutoffRigidity result dictionaries contain (single trajectory mode):

- `rigidity_gv` / `result_code` / `fate`
- `asymptotic_latitude_deg` / `asymptotic_longitude_deg` / `path_length_re`

CutoffRigidity result dictionaries contain (scan mode):

- `cutoff_rigidity_gv` / `fate`
- `asymptotic_latitude_deg` / `asymptotic_longitude_deg` / `path_length_re`
- `n_trajectories_computed` / `rigidity_gv` (ndarray) / `trajectory_results` (ndarray)

GSFC result dictionaries contain:
- `year`, `lat_deg`, `lon_deg`, `alt_km` — broadcast inputs
- `X_nT`, `Y_nT`, `Z_nT`, `F_nT`, `H_nT` — field components in nT
- `inclination_deg`, `declination_deg` — derived angles

JensenCain result dictionaries contain:
- `year`, `lat_deg`, `lon_deg`, `alt_km` — broadcast inputs
- `X_nT`, `Y_nT`, `Z_nT`, `F_nT`, `H_nT` — field components in nT
- `inclination_deg`, `declination_deg` — derived angles

MGST80/MGST81 result dictionaries contain:
- `year`, `lat_deg`, `lon_deg`, `alt_km` — broadcast inputs
- `X_nT`, `Y_nT`, `Z_nT`, `F_nT`, `H_nT` — field components in nT
- `inclination_deg`, `declination_deg` — derived angles

HMR result dictionaries contain (calculate — EPOT):
- `lat_deg`, `lon_deg` — broadcast inputs
- `electric_potential_kV` — electric potential in kV

HMR result dictionaries contain (calculate_full — grid):
- `electric_potential_kV` — electric potential (41×25 grid)
- `e_field_lat_mV_m`, `e_field_lon_mV_m` — electric field components
- `hall_conductivity_Mho`, `pedersen_conductivity_Mho` — conductivities
- `joule_heating_mW_m2` — Joule heating rate
- `fac_uA_m2` — field-aligned current
- `lat_grid_deg`, `mlt_grid_hrs` — grid axes

ISRDrift result dictionaries contain:
- `mlat_deg`, `mlon_deg`, `doy`, `ut_hours` — broadcast inputs
- `potential_V` — electrostatic pseudo-potential (V)
- `poleward_drift_ms` — upward/poleward E x B drift (m/s)
- `eastward_drift_ms` — eastward E x B drift (m/s)

XuLi result dictionaries contain:
- 'x_re', 'y_re', 'tilt_angle_deg' -- broadcast inputs
- 'zaen_re', 'zsen_re', 'zden_re' -- neutral sheet Z positions (Earth Radii)
- 'rmp_re' -- magnetopause radius (Earth Radii)
- 'ie_aen', 'ie_sen', 'ie_den' -- 1=inside, 2=outside magnetopause

AEEUV result dictionaries contain:
- `spectrum`
- `wavelength_angstrom` / `photon_flux_m2_s`
- `line_or_range` / `group_type` / `adjustment_factor`

EUV91 result dictionaries contain:
- `year` / `day_of_year`
- `wavelength_start_angstrom` / `wavelength_end_angstrom`
- `photon_flux_cm2_s` / `energy_flux_erg_cm2_s` (final dimension 39)

EUVAC result dictionaries contain:
- `f107` / `f107a`
- `bin_index` (1–37)
- `photon_flux_cm2_s` (final dimension 37)

Photoelectron result dictionaries contain:
- `energy_eV` (0.5–99.5 eV, shape `(100,)`)
- `photoelectron_flux_per_eV_cm2_s`
- `photoelectron_flux_per_eV_cm2_s_sr`
- `attenuation_factor`

PVIonosphere result dictionaries contain:
- `alt_km` / `sza_deg`
- `log10_electron_density_cm3` / `electron_density_cm3`
- `log10_electron_temperature_K` / `electron_temperature_K`

PVThermosphere result dictionaries contain:
- `alt_km` / `lat_deg` / `local_time_hours` / `f107a` / `f107`
- `total_density_g_cm3`
- `CO2_cm3` / `O_cm3` / `CO_cm3` / `He_cm3` / `N_cm3` / `N2_cm3`
- `T_exo_K` / `T_local_K`

ExosphericH result dictionaries contain:
- `radius_km` / `colatitude_deg` / `longitude_deg`
- `season` / `f107`
- `H_cm3`

## Intelligent Analysis API

- `upperatmpy_analysis.AnalysisPlan` is the strict, JSON-serializable execution plan.
- `upperatmpy_analysis.execute_plan(...)` compares only models in one compatibility group.
- `upperatmpy_analysis.analyze_sensitivity(...)` performs deterministic one-factor sweeps.
- `upperatmpy-analysis` is the public CLI for catalogs, comparison, sensitivity, planning, and evidence explanation.
- Scientific values must always come from model execution. Optional AI can only produce a validated plan or explain the report evidence.
- Keep AI dependencies under the `ai` optional dependency group; importing `upperatmpy_analysis` must not import an AI SDK or load model DLLs.
- The publishable bilingual Skill lives at `skills/upperatmpy-atmospheric-analysis/`. Validate it with the skill-creator `quick_validate.py`; do not install it into a local Skills directory during repository work.
- The release workflow packages that directory as `upperatmpy-atmospheric-analysis-<tag>.zip`; keep its exact-content check synchronized with Skill resources.

## Project Structure

```text
UpperAtmPy/
├── src/
│   ├── model/
│   │   ├── __init__.py
│   │   ├── pymsis2/
│   │   ├── pymsis00/
│   │   ├── pyhwm14/
│   │   ├── pyhwm93/
│   │   ├── pyigrf/
│   │   ├── pycira86/
│   │   ├── pyaurora/
│   │   ├── pymsis86/
│   │   ├── pymsise90/
│   │   ├── pyjacchia77/
│   │   ├── pymet/
│   │   ├── pychiu/
│   │   ├── pytsyganenko/
│   │   ├── pysolpro/
│   │   ├── pyradbelt/
│   │   ├── pyshieldose/
│   │   ├── pysofip/
│   │   ├── pycutoff/
│   │   ├── pygsfc/
│   │   ├── pyjensen/
│   │   ├── pymgst/
│   │   ├── pyhmr/
│   │   ├── pyisrdrift/
│   │   ├── pyxuli/           # Xu-Li 中性片模型封装（SEN/DEN/AEN）
│   │   ├── pyaeeuv/
│   │   ├── pyeuv91/
│   │   ├── pyeuvac/
│   │   ├── pyphotoelectron/
│   │   ├── pypvionosphere/
│   │   ├── pypvthermosphere/
│   │   └── pyexospherich/
│   ├── upperatmpy_analysis/
│   └── utils/
│       ├── cache.py
│       ├── parallel.py
│       ├── space_weather.py
│       ├── time.py
│       └── xarray_output.py
├── example/
├── tests/
├── skills/
│   └── upperatmpy-atmospheric-analysis/
├── data/
│   ├── hwm14data/
│   ├── igrf13data/
│   ├── igrf14data/
│   ├── cira86data/
│   └── msis2data/
```

## Code Style Guidelines

- Use type hints for public function and method signatures.
- Keep user-facing docstrings and errors in Chinese where practical.
- Prefer keyword-only arguments for model calculation methods.
- Keep each model module's `__all__` to `["Model"]`.
- `model.__all__` must stay `["MSIS2", "MSIS00", "HWM14", "HWM93", "AuroraOval", "IGRF", "CIRA86", "MSIS86", "MSISE90", "Jacchia77", "MET", "Chiu", "Tsyganenko", "SOLPRO", "RADBELT", "SHIELDOSE", "SOFIP", "CutoffRigidity", "GSFC", "JensenCain", "MGST80", "MGST81", "HMR", "ISRDrift", "XuLi", "AEEUV", "EUV91", "EUVAC", "Photoelectron", "PVIonosphere", "PVThermosphere", "ExosphericH"]`.
- Utility code belongs in `src/utils`, not `src/model`.
- Cross-model analysis code belongs in `src/upperatmpy_analysis`, not `src/model` or `src/utils`.
- `import model` must not load any model DLL; DLLs should load when a concrete model is instantiated.

## CI, Release, and Native Model Pitfalls

Use this checklist before tagging a release or adding a native model. These items cover failures previously seen in tag-triggered GitHub Actions releases, source/wheel packaging, Git LFS data handling, and Fortran initialization.

### Release Tags and GitHub Actions

- The release workflow is triggered by pushed tags matching `v*`; `git push` only pushes the branch. Push the release tag explicitly with `git push origin vX.Y.Z` or use `git push --follow-tags` after creating an annotated tag.
- Before pushing a release tag, make sure `pyproject.toml` `version` matches the tag without the leading `v`. The workflow checks this and fails when they differ.
- Do not force-move a published release tag casually. If a tag already ran and failed after publication, prefer bumping the patch version and creating a new tag.
- To distinguish "not triggered" from "triggered then failed", check both the remote tag and Actions runs:

```bash
git ls-remote origin refs/tags/vX.Y.Z refs/tags/vX.Y.Z^{}
gh run list --repo qisumi/Py-Upper-Atm --limit 10
```

- Useful CI-debug commands:

```bash
gh auth status
gh run view <run-id> --json status,conclusion,jobs
gh run watch <run-id> --exit-status
gh run view <run-id> --log-failed
gh api /repos/qisumi/Py-Upper-Atm/actions/jobs/<job-id>/logs
```

### Packaging Checks for New Native Models

- When adding a native model, update `.github/workflows/release.yml` wherever the workflow validates package contents.
- The source distribution check must expect the new module's `CMakeLists.txt` and required source files.
- The wheel content check must include the native library path for both platforms, for example `model/pyfoo/foo.dll` on Windows and `model/pyfoo/libfoo.so` on Linux.
- If the model uses external data, update the release data packaging step and `src/utils/model_data_manifest.json` so the packaged data, file sizes, and hashes match the committed/downloaded files.
- Before tagging, run local packaging checks where practical:

```bash
python -m build --wheel --sdist
python -m pytest
```

### Git LFS and Model Data

- `data/**` is tracked through Git LFS. Verify `git-lfs` is installed and active before adding data files, otherwise Actions checkout may warn that files "should have been pointers, but weren't".
- Do not rewrite or strip fixed-width Fortran `.DAT` files unless the model has been verified after the change; trailing spaces may be significant for legacy readers.
- When changing data files, update every consumer: package data list, manifest hashes, documentation, and tests that load from a non-repo working directory.

### Fortran and ctypes Stability

- Do not rely on uninitialized Fortran local variables, implicit `SAVE` behavior, or compiler-dependent persistence. Windows and Linux builds can behave differently.
- Initialize coefficient, work, and COMMON-backed arrays deterministically before use, especially when a DLL can switch between model versions in one Python process.
- Recompute derived constants each call if they are local values used after a first-call guard.
- Avoid initialization checks based on possibly uninitialized array contents.
- Treat COMMON block size mismatch compiler warnings as real bugs; fix dimensions to match across declarations.
- Tests for native wrappers should include finite-value assertions with `math.isfinite()` or `np.isfinite()`, not only type and shape checks.
- For models supporting multiple versions through one DLL, test multiple versions in the same Python process and in isolated subprocesses.
- When embedding paths in `python -c` tests, use `repr(str(path))` or `Path.as_posix()` so Windows backslashes are not interpreted as escapes.

## New Model Integration Tutorial

The steps below assume the TODO directory already contains Fortran source code and a C ABI shim (`*_cshim.F90`). The example integrates `TODO/FooModel` as `model.Foo`.

### Step 1 — Create module directory and copy sources

```
src/model/pyfoo/
├── foo.for            # Fortran source (subroutines only, no interactive main program)
├── foo_cshim.F90      # C ABI shim, exports functions for ctypes
└── CMakeLists.txt     # Create new
```

Copy the Fortran source and shim from `TODO/` into `src/model/pyfoo/`. If the original source contains an interactive `read`/`print` main program, keep only the subroutine portions.

### Step 2 — Write `CMakeLists.txt`

Reference `src/model/pyaurora/CMakeLists.txt`:

```cmake
add_library(
  foo                          # Target name, also determines DLL file name
  SHARED
    foo.for                    # Fortran 77 source
    foo_cshim.F90              # Fortran 90 shim
)

upperatmpy_set_output(foo "${CMAKE_CURRENT_SOURCE_DIR}")
upperatmpy_use_gnu_legacy_fortran(foo.for)   # Only needed for Fortran 77
upperatmpy_link_static_gnu_runtime(foo)

install(
  TARGETS foo
  RUNTIME DESTINATION model/pyfoo
  LIBRARY DESTINATION model/pyfoo
)
```

Notes:
- Fortran 90/95 sources do **not** need `upperatmpy_use_gnu_legacy_fortran`.
- On Windows, `upperatmpy_set_output` strips the `lib` prefix automatically, producing `foo.dll`; on Linux the output is `libfoo.so`.

### Step 3 — Register in root `CMakeLists.txt`

Edit the project root `CMakeLists.txt` and append one line at the end of the existing `add_subdirectory` block:

```cmake
add_subdirectory(src/model/pyfoo)
```

### Step 4 — Write the Python wrapper `__init__.py`

Create a `Model` class in `src/model/pyfoo/__init__.py`. Key conventions:

```python
__all__ = ["Model"]

class Model:
    def __init__(self, dll_path=None, ...):
        # Resolve DLL path (reference existing models)
        # Load DLL, set argtypes/restype
        ...

    def calculate(self, *, ...):
        # Keyword-only arguments
        # Scalar inputs return scalars; array inputs are broadcast and return arrays
        # Return a plain dict
        ...
```

Required conventions:
- `__all__ = ["Model"]` — do not export any other names.
- `calculate(...)` must use `*,` to enforce keyword-only arguments.
- Scalar inputs return `float`/`int`; array inputs return `numpy.ndarray`.
- DLL name uses `os.name == "nt"`: `foo.dll` on Windows, `libfoo.so` on Linux.
- Models requiring `data_dir` must use `ensure_model_data()`; models without external data (e.g. AuroraOval) omit this parameter.
- All DLL loading must go through `resolve_dll_path` and `configure_dll_directories` from `utils.dll_loader`.

### Step 5 — Register in `src/model/__init__.py`

Append an entry to the `_LAZY_EXPORTS` dictionary:

```python
_LAZY_EXPORTS = {
    "MSIS2": ("model.pymsis2", "Model"),
    "MSIS00": ("model.pymsis00", "Model"),
    "HWM14": ("model.pyhwm14", "Model"),
    "HWM93": ("model.pyhwm93", "Model"),
    "AuroraOval": ("model.pyaurora", "Model"),
    "Foo": ("model.pyfoo", "Model"),          # New entry
}
```

Also update the model list in the module docstring.

### Step 6 — Add example script

Create `example/test_foo.py` with single-point and batch smoke tests.

Reference `example/test_aurora.py` for the structure: set `sys.path` → import model → define test functions → `if __name__ == "__main__"` entry point.

### Step 7 — Add pytest tests

1. Create `tests/test_foo.py`, referencing `tests/test_aurora.py`.
2. Add a model fixture in `tests/conftest.py` (wrapped in `try/except`, calling `pytest.skip` when the DLL is unavailable).

Tests must cover:
- `__all__ == ["Model"]` check
- Single-point calculation return types and value ranges
- Batch (array) calculation shape verification
- Loading from a non-repo working directory
- Invalid parameter value error handling (if applicable)

### Step 8 — Update `AGENTS.md`

Modify the following sections:

| Section | Action |
|---------|--------|
| `model.Foo` list | Append new model class name |
| Test Commands | Append `python example/test_foo.py` |
| Result dictionary docs | Append new model's return fields |
| Project Structure | Append `pyfoo/` directory |
| `model.__all__` constraint | Add `"Foo"` to the list |

### Step 9 — Update `README.md` and `README_zh.md`

Synchronize the following sections in both files:

| Section | Action |
|---------|--------|
| Supported models | Append line: `- **Foo**: description` |
| Features | Update top-level lazy alias list |
| API → `model` exports | Append `- Foo` |
| Model Documentation | Append links to `src/model/pyfoo/README.md` and `src/model/pyfoo/README_zh.md` as appropriate |
| Project Structure | Append `pyfoo/` line with comment |

### Step 10 — Update `ROADMAP.md` and `ROADMAP_zh.md`

| Location | Action |
|----------|--------|
| Current Status table | Append a row for `Foo` with status Done |
| Planned table (corresponding Phase) | Remove that model's entry |

### Step 11 — Write module README

Create both module README files:

- `src/model/pyfoo/README.md` in English, referencing `src/model/pyaurora/README.md`.
- `src/model/pyfoo/README_zh.md` in Chinese, referencing `src/model/pyaurora/README_zh.md`.

Content should cover: model background, directory structure, Fortran interface description, input/output parameters, usage examples, constructor parameters, references.

### Step 12 — Build and verify

```bash
cmake --preset native-release
cmake --build --preset native-release
python example/test_foo.py
python -m pytest tests/test_foo.py -v
```

Verify `model.__all__` includes the new model name:

```bash
python -c "import sys; sys.path.insert(0,'src'); import model; print(model.__all__)"
```

---

### File Change Checklist

| # | File | Action |
|---|------|--------|
| 1 | `src/model/pyfoo/` | Create directory |
| 2 | `src/model/pyfoo/*.for`, `*_cshim.F90` | Copy sources |
| 3 | `src/model/pyfoo/CMakeLists.txt` | Create new |
| 4 | `src/model/pyfoo/__init__.py` | Create new |
| 5 | `CMakeLists.txt` | Append `add_subdirectory` |
| 6 | `src/model/__init__.py` | Append `_LAZY_EXPORTS` entry |
| 7 | `example/test_foo.py` | Create new |
| 8 | `tests/test_foo.py` | Create new |
| 9 | `tests/conftest.py` | Append fixture |
| 10 | `src/model/pyfoo/README.md` / `src/model/pyfoo/README_zh.md` | Create new English and Chinese module README files |
| 11 | `AGENTS.md` | Update model list, structure, constraints |
| 12 | `README.md` | Update model list, API, structure |
| 13 | `README_zh.md` | Sync changes from README.md |
| 14 | `ROADMAP.md` | Move from planned to done |
| 15 | `ROADMAP_zh.md` | Sync changes from ROADMAP.md |

## FFI Notes

- DLLs are loaded with `ctypes`.
- Windows builds may require MinGW runtime directories to be discoverable.
- HWM14 uses `HWMPATH`; default it to existing local data if the user has not set it.
- Do not delete or overwrite compiled DLLs or Fortran sources unless explicitly requested.
