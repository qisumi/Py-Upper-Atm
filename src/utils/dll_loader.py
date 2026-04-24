"""ctypes DLL loading helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional, Union

PathLike = Union[str, Path]


def resolve_dll_path(dll_path: PathLike) -> Path:
    """Return an absolute DLL path without requiring the file to exist yet."""
    return Path(dll_path).expanduser().resolve(strict=False)


def configure_dll_directories(
    dll_path: PathLike,
    *,
    extra_dirs: Optional[Iterable[PathLike]] = None,
    include_path_dirs: bool = True,
) -> List[object]:
    """
    Add Windows DLL search directories and keep the returned handles alive.

    Python 3.8+ removes PATH from ctypes' default Windows dependency search.
    Native model DLLs are built by Fortran toolchains, so their runtime DLLs may
    live in the compiler bin directory rather than beside the model DLL.
    """
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return []

    candidates = [resolve_dll_path(dll_path).parent]
    if extra_dirs is not None:
        candidates.extend(Path(path) for path in extra_dirs)
    if include_path_dirs:
        candidates.extend(_iter_path_dirs())

    handles: List[object] = []
    seen = set()
    for directory in candidates:
        resolved = _resolve_directory(directory)
        if resolved is None:
            continue

        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)

        try:
            handles.append(os.add_dll_directory(str(resolved)))
        except OSError:
            continue

    return handles


def _iter_path_dirs() -> Iterable[Path]:
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        entry = entry.strip().strip('"')
        if not entry:
            continue

        expanded = os.path.expandvars(entry)
        path = Path(expanded).expanduser()
        if path.is_absolute():
            yield path


def _resolve_directory(path: PathLike) -> Optional[Path]:
    try:
        resolved = Path(path).expanduser().resolve(strict=False)
    except OSError:
        return None

    if resolved.is_dir():
        return resolved
    return None
