# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Summary

UpperAtmPy wraps compiled Fortran atmospheric models as Python classes via ctypes. Each model lives in `src/model/py*/`, compiled to a shared library (DLL/.so) by CMake, and exposed as a single `Model.calculate(...)` class with keyword-only arguments and numpy broadcasting.

Supported models: MSIS2, MSIS00, HWM14, HWM93, AuroraOval, IGRF (13/14).

## Build & Test Commands

```bash
# Build Fortran shared libraries (requires CMake ≥3.20, Ninja, gfortran)
cmake --preset native-release
cmake --build --preset native-release

# Run all tests
python -m pytest

# Skip slow or DLL-dependent tests
python -m pytest -m "not slow"
python -m pytest -m "not requires_dll"

# Run a single test file
python -m pytest tests/test_aurora.py -v

# Smoke-test a single model
python example/test_aurora.py

```

## Architecture

**Source layout:** `src/model/` (model wrappers), `src/utils/` (shared utilities). Tests in `tests/`, examples in `example/`.

**Build chain:** scikit-build-core → CMake → Ninja → gfortran. Each `src/model/py*/CMakeLists.txt` compiles Fortran source + a C-ABI shim (`*_cshim.F90`) into a shared library placed next to the Python package.

**DLL loading flow:** `utils/dll_loader.py` (`resolve_dll_path`, `configure_dll_directories`) locates the compiled DLL. DLLs load lazily — `import model` must never trigger DLL loading; instantiation of a concrete model class does.

**Data management:** `utils/model_data.py` + `model_data_manifest.json` handle auto-download of model data files (MSIS parameters, HWM coefficients, IGRF coefficient files) from GitHub Releases with SHA256 verification. Data is excluded from wheels/sdist. Override with `UPPERATMPY_DATA_DIR` env var or `data_dir` constructor argument.

**Lazy exports:** `src/model/__init__.py` uses `__getattr__` + `_LAZY_EXPORTS` dict so `from model import MSIS2` only loads the submodule on first access.

## Key Conventions

- `__all__ = ["Model"]` in every model submodule; `model.__all__ = ["MSIS2", "MSIS00", "HWM14", "HWM93", "AuroraOval", "IGRF"]`
- `calculate()` methods use `*,` (keyword-only arguments); return plain dicts
- Scalar inputs → scalar outputs; array inputs → numpy array outputs (broadcasting)
- DLL names: `foo.dll` on Windows, `libfoo.so` on Linux (checked via `os.name == "nt"`)
- Models needing external data call `ensure_model_data()` in `__init__`; models without data (e.g., AuroraOval) omit it
- All DLL loading goes through `utils.dll_loader`
- User-facing docstrings and errors in Chinese
- Type hints on all public signatures
- Utility code goes in `src/utils/`, never in `src/model/`

## Adding a New Model

Follow the 12-step tutorial in [AGENTS.md](AGENTS.md) which covers: creating the module directory with Fortran sources and CMakeLists.txt, writing the Python wrapper, registering in `__init__.py`, adding tests/fixtures, and updating docs/README/ROADMAP. Key files to touch: `src/model/pyfoo/` (new), root `CMakeLists.txt`, `src/model/__init__.py`, `tests/conftest.py`, and both `README.md`/`README_zh.md`.

## CI

[`.github/workflows/release.yml`](.github/workflows/release.yml) builds on Ubuntu and Windows (MSYS2/UCRT64), runs pytest, builds wheels, packages data as a ZIP asset, and creates a GitHub Release on `v*` tags.
