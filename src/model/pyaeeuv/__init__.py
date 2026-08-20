"""Atmosphere Explorer solar EUV reference spectra."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Union

import numpy as np

from utils.model_data import ensure_model_data

__all__ = ["Model"]

_SPECTRA = {"r74113", "f74113", "f76ref", "sc21refw"}
_ROW_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)\s*(.*)$"
)
_TAIL_RE = re.compile(
    r"^(.*?)(?:\s+([12])\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?))?\s*$"
)


class Model:
    """AE-EUV 历史参考光谱表封装。"""

    def __init__(
        self,
        *,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        root = ensure_model_data(
            "aeeuv", data_dir=data_dir, auto_download=auto_download
        )
        self._data_dir = root / "aeeuvdata"
        self._cache = {}

    def calculate(self, *, spectrum: str = "f74113") -> dict:
        """读取指定参考谱，通量单位为 photons/(m²·s)。"""
        name = str(spectrum).strip().lower()
        if name not in _SPECTRA:
            raise ValueError(
                "spectrum 必须是 r74113、f74113、f76ref 或 sc21refw"
            )
        if name not in self._cache:
            self._cache[name] = _parse_spectrum(self._data_dir / f"{name}.dat")
        result = self._cache[name]
        return {
            "spectrum": name,
            "wavelength_angstrom": result["wavelength_angstrom"].copy(),
            "photon_flux_m2_s": result["photon_flux_m2_s"].copy(),
            "line_or_range": result["line_or_range"].copy(),
            "group_type": result["group_type"].copy(),
            "adjustment_factor": result["adjustment_factor"].copy(),
        }


def _parse_spectrum(path: Path) -> dict:
    wavelength = []
    flux = []
    labels = []
    group_type = []
    adjustment = []
    with path.open("r", encoding="ascii", errors="ignore") as fh:
        for raw in fh:
            match = _ROW_RE.match(raw)
            if match is None:
                continue
            wave, value, tail = match.groups()
            tail_match = _TAIL_RE.match(tail)
            label, group, factor = tail_match.groups() if tail_match else (tail, None, None)
            wavelength.append(float(wave))
            flux.append(float(value) * 1.0e10)
            labels.append(label.strip())
            group_type.append(int(group) if group is not None else -1)
            adjustment.append(float(factor) if factor is not None else np.nan)
    if not wavelength:
        raise ValueError(f"无法解析 AE-EUV 光谱文件：{path}")
    return {
        "wavelength_angstrom": np.asarray(wavelength, dtype=float),
        "photon_flux_m2_s": np.asarray(flux, dtype=float),
        "line_or_range": np.asarray(labels, dtype=object),
        "group_type": np.asarray(group_type, dtype=int),
        "adjustment_factor": np.asarray(adjustment, dtype=float),
    }
