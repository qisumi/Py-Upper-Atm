"""
UpperAtmPy model package.

Only concrete model classes are exported:
- MSIS2
- MSIS00
- HWM14
- HWM93

Exports are lazy so `import model` does not load any model DLL.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, List

_LAZY_EXPORTS = {
    "MSIS2": ("model.pymsis2", "Model"),
    "MSIS00": ("model.pymsis00", "Model"),
    "HWM14": ("model.pyhwm14", "Model"),
    "HWM93": ("model.pyhwm93", "Model"),
}

__all__ = list(_LAZY_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> List[str]:
    return sorted(set(globals()) | set(__all__))
