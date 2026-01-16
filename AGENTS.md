# AGENTS.md - AI Coding Agent Guidelines for UpperAtmPy

## Project Overview

UpperAtmPy is a Python wrapper library for upper atmospheric models, providing unified interfaces for:
- **NRLMSIS-2.0** (temperature and density model)
- **NRLMSISE-00** (legacy temperature and density model)  
- **HWM14** (Horizontal Wind Model 2014)
- **HWM93** (Horizontal Wind Model 1993)

The project wraps Fortran DLLs using Python `ctypes` for Windows environments.

---

## Build Commands

### Fortran DLL Compilation (Windows/PowerShell)

```powershell
# MSIS 2.0 model (requires gfortran/MinGW)
cd model/pymsis2
powershell -ExecutionPolicy Bypass -File compile.ps1

# HWM14 model
cd model/pyhwm14
powershell -ExecutionPolicy Bypass -File compile.ps1

# HWM93 model
cd model/pyhwm93
powershell -ExecutionPolicy Bypass -File compile.ps1
```

### Running the Project

```bash
# Quick demonstration of all models
python quick_run.py

# Run individual examples
python example/test_msis20.py
python example/test_hwm14.py
python example/test_hwm93.py
python example/test_msis00.py
```

---

## Test Commands

**No formal test framework is configured.** Tests are example scripts in `example/` directory.

```bash
# Run all example/test scripts
python example/test_msis20.py
python example/test_hwm14.py
python example/test_msis00.py
python example/test_hwm93.py

# Grid computation examples
python example/grid_msis.py
python example/grid_hwm.py
```

---

## Dependencies

Core dependencies (not formally specified - inferred from code):
- `numpy` - Required for batch operations
- `pandas` - For data utilities
- `xarray` - For NetCDF utilities
- `tqdm` - Optional, for progress bars

---

## Code Style Guidelines

### Imports

```python
# Standard order: future -> stdlib -> third-party -> local
from __future__ import annotations

import os
import sys
import ctypes as C
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import numpy as np

# Local imports using relative paths within packages
from .pymsis2 import NRLMSIS2, MSISResult, doy, seconds_of_day
```

### Formatting

- **Line length**: ~100 characters (flexible)
- **Indentation**: 4 spaces
- **String quotes**: Double quotes preferred for docstrings, single/double for strings
- **Trailing commas**: Used in multiline collections

### Type Hints

```python
# Always use type hints for function signatures
def calculate_point(
    self,
    *,
    day: float,
    utsec: float,
    alt_km: float,
    lat_deg: float,
    lon_deg: float,
    f107a: float,
    f107: float,
    ap7: Optional[Sequence[float]] = None
) -> TempDensityResult:

# Use Union for multiple types
alt_km: Union[float, Sequence[float]]

# Use Tuple for fixed-length sequences  
dn10: Tuple[float, float, float, float, float, float, float, float, float, float]
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `TempDensityModel`, `MSISResult` |
| Functions | snake_case | `calculate_point`, `convert_date_to_day` |
| Constants | UPPER_SNAKE | `SPECIES`, `DEFAULT_FLOAT_FORMAT` |
| Private | _prefix | `_has_msis`, `_dll_path`, `_HAS_NUMPY` |
| Parameters | snake_case | `alt_km`, `lat_deg`, `f107a` |

### Docstrings

Use Chinese docstrings for user-facing APIs (this is a Chinese project):

```python
def calculate_point(self, ...) -> TempDensityResult:
    """
    计算单点的温度和密度

    Args:
        day: 年内日数（1-366）
        utsec: UTC时间（秒，0-86400）
        alt_km: 高度（公里）
        lat_deg: 纬度（度）
        lon_deg: 经度（度）
        f107a: 81天平均F10.7太阳通量
        f107: 当天F10.7太阳通量
        ap7: 地磁活动指数，长度为7的序列

    Returns:
        TempDensityResult: 包含温度和密度结果的对象
    """
```

### Error Handling

```python
# Use try/except for optional imports
try:
    import numpy as np
    _HAS_NUMPY = True
except Exception:
    np = None
    _HAS_NUMPY = False

# Raise descriptive errors with Chinese messages
if not _has_msis:
    raise RuntimeError("温度密度模型组件未正确加载")

if len(ap7) != 7:
    raise ValueError("ap7 长度必须为 7")
```

### Class Structure

```python
@dataclass
class TempDensityResult:
    """Result dataclass with typed fields"""
    alt_km: float
    T_local_K: float
    T_exo_K: float
    densities: Tuple[float, ...]

class TempDensityModel:
    """
    Model class pattern:
    - __init__ loads DLL and sets up ctypes
    - calculate_point for single-point computation
    - calculate_batch for vectorized computation
    """
    def __init__(self, dll_path: Optional[str] = None, ...):
        ...
    
    def calculate_point(self, *, ...) -> TempDensityResult:
        ...
    
    def calculate_batch(self, *, ...) -> List[TempDensityResult]:
        ...
```

### Keyword-Only Arguments

Use `*` to force keyword arguments for clarity:

```python
def calc(
    self,
    *,  # All following args are keyword-only
    day: float,
    utsec: float,
    alt_km: float,
    ...
) -> MSISResult:
```

---

## Project Structure

```
UpperAtmPy/
├── model/                    # Core model wrappers
│   ├── __init__.py          # Public API exports
│   ├── temp_density_model.py # MSIS wrapper (unified interface)
│   ├── wind_model.py        # HWM wrapper (unified interface)
│   ├── pymsis2/             # NRLMSIS-2.0 ctypes wrapper
│   │   ├── __init__.py      # NRLMSIS2 class, doy(), seconds_of_day()
│   │   ├── compile.ps1      # Build script for DLL
│   │   └── *.F90            # Fortran source files
│   ├── pymsis00/            # NRLMSISE-00 wrapper
│   ├── pyhwm14/             # HWM14 wrapper
│   └── pyhwm93/             # HWM93 wrapper
├── example/                  # Usage examples and tests
├── utils/                    # Utility scripts (NetCDF conversion)
├── hwm14data/               # HWM14 data files
├── msis2data/               # MSIS parameter files
├── docs/                    # Documentation (Chinese)
└── quick_run.py             # Quick demo script
```

---

## ctypes FFI Patterns

When working with Fortran DLL wrappers:

```python
import ctypes as C

# Load DLL
self._dll = C.CDLL(str(dll_path))

# Get function reference
self._func = getattr(self._dll, "function_name")

# Define signature
FT = C.c_float  # or C.c_double for double precision
self._func.argtypes = [FT, FT, C.POINTER(FT), ...]
self._func.restype = None

# Create buffers for output
self._output_buf = (FT * 10)()

# Call function
self._func(FT(value), ..., self._output_buf)

# Extract results
result = tuple(float(self._output_buf[i]) for i in range(10))
```

---

## Important Notes

1. **Windows-specific**: DLL loading uses Windows paths and `os.add_dll_directory()`
2. **MinGW dependency**: Fortran code compiled with gfortran requires MinGW runtime
3. **Precision**: Models support single (`c_float`) or double (`c_double`) precision
4. **Data files**: HWM models require data files in `hwm14data/` or via `HWMPATH` env var
5. **No pip install**: Project is used by running scripts directly from repository root
6. **Chinese documentation**: Comments and docs are primarily in Chinese

---

## Common Modifications

### Adding a New Model Wrapper

1. Create new package under `model/` (e.g., `model/pynewmodel/`)
2. Add `__init__.py` with ctypes wrapper class
3. Add `compile.ps1` for Fortran compilation
4. Export from `model/__init__.py`
5. Add example script in `example/`

### Modifying API Signatures

- Keep backward compatibility with existing parameter names
- Use `Optional` types with `None` defaults for new parameters
- Update Chinese docstrings
- Add to `__all__` exports
