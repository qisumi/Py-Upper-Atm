# UpperAtmPy

[中文文档 (Chinese)](README_zh.md)

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT%20%2B%20third--party%20terms-blue)

**UpperAtmPy** is an AI-first upper-atmosphere analysis platform backed by a
large collection of deterministic scientific models. It turns Chinese or
English questions into validated analysis plans, executes the native models,
compares their results, and produces evidence-grounded reports that remain
fully reproducible from Python or the command line.

AI is deliberately separated from scientific computation: AI may select a
workflow and explain calculated evidence, while every atmospheric or
geomagnetic value still comes from the repository's established model code.

## AI-First Atmospheric Analysis

The primary UpperAtmPy workflow is intelligent, bilingual model analysis:

- **Natural-language planning**: convert Chinese or English requests into a
  strict, machine-checkable `AnalysisPlan`.
- **Smart model comparison**: normalize compatible MSIS-family and internal
  geomagnetic models, intersect validity domains, align exact coordinates, and
  compare canonical physical quantities.
- **Sensitivity analysis**: sweep one scientific input while holding the other
  conditions fixed.
- **Evidence-grounded interpretation**: explain only deterministic report
  metrics, retain warnings and citations, and label numerical claims with
  evidence keys.
- **Reproducible delivery**: export Markdown, JSON, and executable Python code;
  use the same engine through the API, CLI, or publishable Codex Skill.

### Ask a bilingual analysis question

The dependency-free rule planner is the default intelligent path:

```bash
upperatmpy-analysis ask --language en --query "Compare MSIS2 and MSIS00: year 2020, day of year 172, 12:00 UT, altitude 100 to 500 km, step 10 km, latitude 35, longitude 116, F10.7a=150, F10.7=150, local temperature."
```

For optional AI planning and narrative interpretation, install the separate AI
dependency and explicitly select a provider model:

```bash
python -m pip install "upperatmpy[ai]"
upperatmpy-analysis ask --provider openai --ai-model YOUR_MODEL --query "..."
```

Missing dates, locations, solar fluxes, and other scientific inputs are rejected
rather than guessed. AI never calculates or alters model values.

### Deterministic Python API

```python
from upperatmpy_analysis import AnalysisPlan, execute_plan

plan = AnalysisPlan(
    models=["MSIS2", "MSIS00"],
    inputs={
        "year": 2020,
        "day_of_year": 172,
        "utsec": 43200,
        "alt_km": {"start": 100, "stop": 500, "step": 10, "num": None},
        "lat_deg": 35,
        "lon_deg": 116,
        "f107a": 150,
        "f107": 150,
    },
    quantities=["T_local_K", "O_cm3"],
    baseline="MSIS2",
    language="en",
)
report = execute_plan(plan)
print(report.to_markdown())
```

The CLI exposes the same deterministic engine:

```bash
upperatmpy-analysis catalog --language en
upperatmpy-analysis compare --plan plan.json --format markdown
upperatmpy-analysis sensitivity --model MSIS2 --base-inputs base.json --parameter f107 --values 70,100,150,200
```

### Publishable bilingual Skill

The repository includes the externally distributable Codex Skill at
[`skills/upperatmpy-atmospheric-analysis/`](skills/upperatmpy-atmospheric-analysis/).
It is maintained in version control and is not installed into a developer's
local Skills directory. A normal tag release packages it automatically as
`upperatmpy-atmospheric-analysis-<tag>.zip`.

## Scientific Model Library

The intelligent analysis layer is backed by these public model classes:

- **MSIS2**: NRLMSIS-2.0 temperature and density
- **MSIS00**: NRLMSISE-00 temperature and density
- **HWM14**: Horizontal Wind Model 2014
- **HWM93**: Horizontal Wind Model 1993
- **AuroraOval**: Feldstein auroral oval boundary (Holzworth & Meng)
- **IGRF**: International Geomagnetic Reference Field 13/14, including field components and L-value
- **CIRA86**: COSPAR International Reference Atmosphere 1986 tables for 0-120 km
- **MSIS86**: MSIS-86 / CIRA-86 thermosphere model — neutral temperature and density above 85 km
- **MSISE90**: MSISE-90 neutral atmosphere model — extends MSIS-86 downward to ground level
- **Jacchia77**: Jacchia 1977 Reference Atmosphere — temperature and species density profiles (N2, O2, O, Ar, He, H) for 90–2500 km
- **MET**: Marshall Engineering Thermosphere — modified Jacchia 1970 model for engineering applications
- **Chiu**: Chiu ionospheric electron density — E, F1, F2 layer densities (90–500 km)
- **Tsyganenko**: Tsyganenko magnetospheric magnetic field models (T89/T96/T01/TS04) — external field in GSM coordinates
- **SOLPRO**: Interplanetary solar proton fluence at 1 AU — mission duration and confidence-level based
- **RADBELT**: AP-8 / AE-8 trapped radiation models — omnidirectional integral proton/electron fluxes (AP8MAX/MIN, AE8MAX/MIN)
- **SHIELDOSE**: Radiation dose behind aluminum shielding — trapped, solar proton, and electron environments
- **SOFIP**: Short Orbital Flux Integration Program — mission-averaged fluxes along spacecraft trajectories using AP8/AE8
- **CutoffRigidity**: Geomagnetic cutoff rigidity — cosmic ray trajectory prediction (Smart & Shea, IGRF-95)
- **GSFC**: GSFC geomagnetic field models (80, 83, 87) — spherical harmonic field components at any location
- **JensenCain**: Jensen & Cain (1962) geomagnetic field — spherical harmonic model, epoch 1960.0, degree 6
- **MGST80**: MGST(6/80) geomagnetic field — MAGSAT scalar + fine attitude, epoch 1979.85, degree 13
- **MGST81**: MGST(4/81) geomagnetic field — MAGSAT 15-day data with secular variation, epoch 1980.0
- **HMR**: Heppner-Maynard-Rich electric field — high-latitude ionospheric potential, conductivity, Joule heating, FAC
- **ISRDrift**: Quiet-day ionospheric E x B drifts at 300 km (Richmond et al., 1980)
- **XuLi**: Magnetotail neutral sheet position (SEN/DEN/AEN variants, Xu & Li)
- **AEEUV**: Atmosphere Explorer reference solar EUV spectra
- **EUV91**: Revised SERF2 historical 39-band solar EUV irradiance
- **EUVAC**: F10.7-driven Torr 37-band solar EUV photon flux
- **Photoelectron**: Richards simplified ionospheric photoelectron flux
- **PVIonosphere**: Pioneer Venus electron density and temperature
- **PVThermosphere**: Pioneer Venus VTS3 neutral thermosphere
- **ExosphericH**: Hodges third-order spherical-harmonic exospheric hydrogen

## Key Features

- AI-first bilingual planning, comparison, sensitivity analysis, and
  evidence-grounded reporting.
- Strict separation between optional AI reasoning and deterministic scientific
  calculations.
- Publishable bilingual Codex Skill plus Python and CLI workflows.
- One public interface per model: `Model.calculate(...)`.
- Top-level lazy aliases: `MSIS2`, `MSIS00`, `HWM14`, `HWM93`, `AuroraOval`, `IGRF`, `CIRA86`, `MSIS86`, `MSISE90`, `Jacchia77`, `MET`, `Chiu`, `Tsyganenko`, `SOLPRO`, `RADBELT`, `SHIELDOSE`, `SOFIP`, `CutoffRigidity`, `GSFC`, `JensenCain`, `MGST80`, `MGST81`, `HMR`, `ISRDrift`, `XuLi`, `AEEUV`, `EUV91`, `EUVAC`, `Photoelectron`, `PVIonosphere`, `PVThermosphere`, `ExosphericH`.
- Single-point and numpy-broadcast batch inputs through the same method.
- Model outputs are plain dictionaries.
- Utilities live under `utils`, not `model`.

## License

Original UpperAtmPy wrappers, build files, tests, examples, and documentation
are licensed under the MIT License. Third-party model source code and data are
not relicensed by UpperAtmPy and remain subject to their upstream terms; see
[LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

In particular, NRLMSIS 2.0 files under `src/model/pymsis2/` carry upstream
academic, non-commercial terms from the U.S. Government / Naval Research
Laboratory. Review the upstream notice before redistribution or non-academic
use.

## Build

Before compiling from source, install the following toolchain and Python dependencies.

### Build prerequisites

- Python 3.8+
- CMake (3.20+)
- C/C++ compiler toolchain
- GNU Fortran compiler (`gfortran`)
- `pip` dependencies

Common install steps:

```bash
python -m pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3 python3-pip cmake build-essential gfortran git
```

#### macOS

```bash
brew install python cmake gcc
```

#### Windows

Install:

- Python
- CMake
- MinGW-w64 toolchain (for `gfortran` support), and keep the MinGW runtime directory
  (`...\\mingw64\\bin`) visible in `PATH`.

Example:

```powershell
winget install -e --id Python.Python.3
winget install -e --id Kitware.CMake
winget install -e --id MSYS2.MSYS2
```

Then in an MSYS2/MinGW shell:

```bash
pacman -S --noconfirm --needed mingw-w64-x86_64-toolchain
```

### Build from source

Compile the native libraries before using a model from a source checkout. Make sure you
run CMake from a shell where the compilers above are available.

```bash
cmake --preset native-release
cmake --build --preset native-release
```

### Prebuilt wheels

If building native libraries is inconvenient, download the matching wheel from the repository
`Releases` page and install it directly with pip.

1. Choose a wheel file that matches your OS and architecture.
   Example naming patterns:
   - `upperatmpy-0.2.0-py3-none-manylinux_x86_64.whl`
   - `upperatmpy-0.2.0-py3-none-win_amd64.whl`
2. Install the wheel.

```bash
python -m pip install /path/to/upperatmpy-0.2.0-py3-none-win_amd64.whl
```

Quick compatibility rule:

- `py3-none-win_amd64` wheels can be installed on **any supported CPython 3.x** on Windows x86_64.
- `py3-none-manylinux_x86_64` wheels can be installed on **any supported CPython 3.x** on Linux x86_64.
- `py3-none-any` (if available) can be installed on any platform with the same Python major version.

Or install directly from a release URL:

```bash
python -m pip install https://github.com/<OWNER>/<REPO>/releases/download/<TAG>/<WHEEL_FILENAME>.whl
```

After installation, import model classes from `model`. See
[Model Documentation](#model-documentation) for model-specific constructor
arguments, `calculate(...)` signatures, inputs, outputs, and examples.

## Data Files

MSIS2, HWM14, IGRF, CIRA86, MSIS86, AEEUV, EUV91, PVIonosphere, and ExosphericH need external model data. By default UpperAtmPy resolves
`.upperatmpy` under the current project directory and downloads missing files
from the current package version's release tag (for example `v0.2.0`) on first
model instantiation when a download manifest is available. CIRA86 currently
uses the local `cira86data/` ASCII tables. For offline use, pass
`data_dir=...` or set `UPPERATMPY_DATA_DIR` to a data root containing the legacy
`msis2data/`, `hwm14data/`, `igrf13data/`, `igrf14data/`, `cira86data/`, `aeeuvdata/`, `euv91data/`, `pvionospheredata/`, and `exospherichdata/` subdirectories. In
the source tree, that root is `data/`.

`UPPERATMPY_DATA_TAG` can force a specific release tag for data download.

### Download and use release data files manually

If you cannot download data files at runtime, you can fetch them manually from
`GitHub Releases`:

1. Open the release page and download the combined model-data archive (or the individual model data assets).
2. Extract them so you get a data root directory containing the needed folders:

```bash
UPPERATMPY_DATA_DIR/
├── msis2data/
├── msis86data/
├── hwm14data/
├── igrf13data/
├── igrf14data/
├── cira86data/
├── aeeuvdata/
├── euv91data/
├── pvionospheredata/
└── exospherichdata/
```

3. Configure the project to load from this local root.

Linux/macOS example:

```bash
export UPPERATMPY_DATA_DIR=/path/to/UPPERATMPY_DATA_DIR
python -m pip install -U /path/to/upperatmpy.whl  # optional
```

Windows PowerShell example:

```powershell
$env:UPPERATMPY_DATA_DIR = "C:\path\to\UPPERATMPY_DATA_DIR"
```

## API

Top-level `model` exports only:

- `MSIS2`
- `MSIS00`
- `HWM14`
- `HWM93`
- `AuroraOval`
- `IGRF`
- `CIRA86`
- `MSIS86`
- `MSISE90`
- `Jacchia77`
- `MET`
- `Chiu`
- `Tsyganenko`
- `SOLPRO`
- `RADBELT`
- `SHIELDOSE`
- `SOFIP`
- `CutoffRigidity`
- `GSFC`
- `JensenCain`
- `MGST80`
- `MGST81`
- `HMR`
- `ISRDrift`
- `XuLi`
- `AEEUV`
- `EUV91`
- `EUVAC`
- `Photoelectron`
- `PVIonosphere`
- `PVThermosphere`
- `ExosphericH`

Each class provides `calculate(...)` and returns a plain dictionary.
The model methods accept scalar or broadcastable array inputs.

### Time Helpers

- `utils.time.doy(year, month, day)`: returns day of year (1-366).
- `utils.time.seconds_of_day(hour, minute=0, second=0.0)`: returns seconds since midnight.

## Model Documentation

Each model directory under `src/model/` contains its own `README.md` with detailed documentation covering model background, Fortran interface, constructor options, input/output parameters, and usage examples:

- [NRLMSIS 2.0](src/model/pymsis2/README.md)
- [NRLMSISE-00](src/model/pymsis00/README.md)
- [HWM14](src/model/pyhwm14/README.md)
- [HWM93](src/model/pyhwm93/README.md)
- [AuroraOval](src/model/pyaurora/README.md)
- [IGRF](src/model/pyigrf/README.md)
- [CIRA86](src/model/pycira86/README.md)
- [MSIS86](src/model/pymsis86/README.md)
- [MSISE90](src/model/pymsise90/README.md)
- [Jacchia77](src/model/pyjacchia77/README.md)
- [MET](src/model/pymet/README.md)
- [Chiu](src/model/pychiu/README.md)
- [Tsyganenko](src/model/pytsyganenko/README.md)
- [SOLPRO](src/model/pysolpro/README.md)
- [RADBELT](src/model/pyradbelt/README.md)
- [SHIELDOSE](src/model/pyshieldose/README.md)
- [SOFIP](src/model/pysofip/README.md)
- [CutoffRigidity](src/model/pycutoff/README.md)
- [GSFC](src/model/pygsfc/README.md)
- [JensenCain](src/model/pyjensen/README.md)
- [MGST](src/model/pymgst/README.md)
- [HMR](src/model/pyhmr/README.md)
- [ISRDrift](src/model/pyisrdrift/README.md)
- [XuLi](src/model/pyxuli/README.md)
- [AEEUV](src/model/pyaeeuv/README.md)
- [EUV91](src/model/pyeuv91/README.md)
- [EUVAC](src/model/pyeuvac/README.md)
- [Photoelectron](src/model/pyphotoelectron/README.md)
- [PVIonosphere](src/model/pypvionosphere/README.md)
- [PVThermosphere](src/model/pypvthermosphere/README.md)
- [ExosphericH](src/model/pyexospherich/README.md)

### Optional utility modules

These modules are not imported automatically by `import model`.

- `utils.cache`
- `utils.parallel`
- `utils.space_weather`
- `utils.xarray_output`
- `utils.netcdf2csv`

#### `utils.space_weather`

Fetch and cache geomagnetic/solar inputs for model calls.

- `get_indices(date=None, source="celestrak")`: default date is yesterday UTC.
- `get_indices_celestrak(date)`: fetch from CelesTrak space weather file.
- `clear_cache()`: remove cached local files.
- `SpaceWeatherIndices`:
  - `as_msis_params()` returns `{ "f107", "f107a", "ap7" }`
  - `as_hwm_params()` returns `{ "f107", "f107a", "ap2" }`

#### `utils.cache`

Memoize model/function calls (works for any callable).

- `cached_call(func, cache_size=10000)` returns a wrapped callable.
- wrapper exposes `cache_info()` and `cache_clear()`.

#### `utils.parallel`

Run large batches in threads for better throughput.

- `parallel_map(func, items, max_workers=None, show_progress=False)`
- `parallel_batch_compute(compute_func, param_dicts, max_workers=None, show_progress=False)`

#### `utils.xarray_output`

Convert output dictionaries to xarray datasets.

- `msis_to_xarray(result, species_names=None, attrs=None)`
- `hwm_to_xarray(result, attrs=None)`

## Project Structure

```text
UpperAtmPy/
├── src/
│   ├── model/
│   │   ├── __init__.py      # Lazy aliases for all public model classes
│   │   ├── pymsis2/         # NRLMSIS-2.0 wrapper and Fortran sources
│   │   ├── pymsis00/        # NRLMSISE-00 wrapper and Fortran sources
│   │   ├── pyhwm14/         # HWM14 wrapper and Fortran sources
│   │   ├── pyhwm93/         # HWM93 wrapper and Fortran sources
│   │   ├── pyaurora/        # Feldstein auroral oval (Holzworth & Meng)
│   │   ├── pyigrf/          # IGRF-13/14 geomagnetic field wrapper
│   │   ├── pycira86/        # CIRA-86 table wrapper
│   │   ├── pymsis86/        # MSIS-86 thermosphere model wrapper
│   │   ├── pymsise90/       # MSISE-90 neutral atmosphere wrapper
│   │   ├── pyjacchia77/     # Jacchia 1977 Reference Atmosphere wrapper
│   │   ├── pymet/           # Marshall Engineering Thermosphere wrapper
│   │   ├── pychiu/          # Chiu ionospheric electron density wrapper
│   │   ├── pytsyganenko/    # Tsyganenko magnetospheric field model wrapper (T89/T96/T01/TS04)
│   │   ├── pysolpro/        # SOLPRO solar proton fluence model wrapper
│   │   ├── pyradbelt/       # RADBELT AP-8/AE-8 trapped radiation wrapper
│   │   ├── pyshieldose/     # SHIELDOSE radiation dose behind shielding wrapper
│   │   ├── pysofip/          # SOFIP Short Orbital Flux Integration Program wrapper
│   │   ├── pycutoff/         # Geomagnetic Cutoff Rigidity (Smart & Shea, IGRF-95)
│   │   ├── pygsfc/           # GSFC geomagnetic field models (80, 83, 87)
│   │   ├── pyjensen/         # Jensen & Cain (1962) geomagnetic field wrapper
│   │   ├── pymgst/           # MGST80/MGST81 geomagnetic field wrappers
│   │   ├── pyhmr/            # Heppner-Maynard-Rich electric field wrapper
│   │   ├── pyisrdrift/       # ISR ion drift model wrapper (Richmond et al., 1980)
│   │   ├── pyxuli/           # Xu-Li neutral sheet model wrapper (SEN/DEN/AEN)
│   │   ├── pyaeeuv/          # Atmosphere Explorer EUV reference spectra
│   │   ├── pyeuv91/          # Revised SERF2 EUV irradiance wrapper
│   │   ├── pyeuvac/          # EUVAC 37-band solar flux wrapper
│   │   ├── pyphotoelectron/  # Richards photoelectron model wrapper
│   │   ├── pypvionosphere/   # Pioneer Venus ionosphere wrapper
│   │   ├── pypvthermosphere/ # Pioneer Venus thermosphere wrapper
│   │   └── pyexospherich/    # Hodges exospheric hydrogen model
│   ├── upperatmpy_analysis/  # Deterministic comparison, sensitivity, CLI, optional AI
│   └── utils/
│       ├── cache.py
│       ├── parallel.py
│       ├── space_weather.py
│       ├── time.py
│       └── xarray_output.py
├── skills/
│   └── upperatmpy-atmospheric-analysis/ # Publishable bilingual Codex Skill
├── example/
├── tests/
├── data/
│   ├── hwm14data/
│   ├── igrf13data/
│   ├── igrf14data/
│   ├── cira86data/
│   ├── msis2data/
│   ├── msis86data/
│   ├── aeeuvdata/
│   ├── euv91data/
│   ├── pvionospheredata/
│   ├── exospherichdata/
│   ├── mgst/
│   └── hmr/
└── ROADMAP.md
```

Each model directory under `src/model/` contains model-specific English and
Chinese README files. See [Model Documentation](#model-documentation).
