# AGENTS.md - AI Coding Agent Guidelines for UpperAtmPy

## Project Overview

UpperAtmPy is a Python wrapper library for upper atmospheric models. The project uses a `src/` layout and exposes one public class per model:

- `model.MSIS2`
- `model.MSIS00`
- `model.HWM14`
- `model.HWM93`
- `model.AuroraOval`

Each class provides one public calculation method: `calculate(...)`. Do not reintroduce multi-model wrappers or old helper exports such as `NRLMSIS2`, `gtd7`, `hwm14_eval`, or `hwm93_eval`.

## Build Commands

```bash
cmake --preset native-release
cmake --build --preset native-release
```

## Test Commands

```bash
python -m pytest
python quick_run.py
python example/test_msis20.py
python example/test_msis00.py
python example/test_hwm14.py
python example/test_hwm93.py
python example/test_aurora.py
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
│   │   └── pyaurora/
│   └── utils/
│       ├── cache.py
│       ├── parallel.py
│       ├── space_weather.py
│       ├── time.py
│       └── xarray_output.py
├── example/
├── tests/
├── data/
│   ├── hwm14data/
│   └── msis2data/
└── quick_run.py
```

## Code Style Guidelines

- Use type hints for public function and method signatures.
- Keep user-facing docstrings and errors in Chinese where practical.
- Prefer keyword-only arguments for model calculation methods.
- Keep each model module's `__all__` to `["Model"]`.
- `model.__all__` must stay `["MSIS2", "MSIS00", "HWM14", "HWM93", "AuroraOval"]`.
- Utility code belongs in `src/utils`, not `src/model`.
- `import model` must not load any model DLL; DLLs should load when a concrete model is instantiated.

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
| API → New `Foo.calculate` subsection | Include signature, input fields, return fields |
| Project Structure | Append `pyfoo/` line with comment |

### Step 10 — Update `ROADMAP.md` and `ROADMAP_zh.md`

| Location | Action |
|----------|--------|
| Current Status table | Append a row for `Foo` with status Done |
| Planned table (corresponding Phase) | Remove that model's entry |

### Step 11 — Write module README

Create `src/model/pyfoo/README.md` in Chinese, referencing `src/model/pyaurora/README.md`. Content should cover: model background, directory structure, Fortran interface description, input/output parameters, usage examples, constructor parameters, references.

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
| 10 | `src/model/pyfoo/README.md` | Create new |
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
