"""
GSFC (Goddard Space Flight Center) geomagnetic field model wrapper.

Supports GSFC 9/80, 12/83, and 11/87 spherical harmonic models.

Public API:
    Model
"""

from __future__ import annotations

import ctypes as C
import math
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np
from utils.dll_loader import configure_dll_directories, resolve_dll_path
from utils.model_data import ensure_model_data

__all__ = ["Model"]

_C_INT = C.c_int
_C_FLOAT = C.c_float

_GSFC_ARGTYPES = [
    _C_INT,             # model (0=GSFC80, 1=GSFC83, 2=GSFC87)
    _C_FLOAT,           # lat
    _C_FLOAT,           # lon
    _C_FLOAT,           # alt
    _C_FLOAT,           # year
    _C_INT,             # jj (0=geodetic, 1=geocentric)
    C.POINTER(_C_FLOAT),  # x (north)
    C.POINTER(_C_FLOAT),  # y (east)
    C.POINTER(_C_FLOAT),  # z (down)
    C.POINTER(_C_FLOAT),  # f (total)
]

_GSFC_MODELS = {0: "GSFC80", 1: "GSFC83", 2: "GSFC87"}


def _needs_text_header_preprocessing(filepath: Path) -> bool:
    """Check if a GSFC data file has a text header instead of a numeric one."""
    with open(filepath, "r") as f:
        first = f.readline()
    # Files with text headers start with spaces + "GSFC"
    return first.lstrip().startswith("GSFC")


def _preprocess_gsfc80(data_dir: Path) -> None:
    """Add a numeric header line to gsfc80.dat if missing.

    The original gsfc80.dat has a text header that the FIDD Fortran driver
    cannot parse. This function detects the text header and replaces it with
    a numeric header line in the same format as gsfc83/87.dat.

    The preprocessing is idempotent: it only runs if the file has the
    original text header format.
    """
    filepath = data_dir / "GSFC80.DAT"
    if not filepath.exists():
        return

    if not _needs_text_header_preprocessing(filepath):
        return  # Already has numeric header

    with open(filepath, "r") as f:
        lines = f.readlines()

    if not lines:
        return

    first = lines[0]

    # Original gsfc80.dat has a text header like:
    #   GSFC(9/80-2)  EPOCH=1980.   FORMAT(2I3,6F11.4)
    # Coefficient data starts on line 1 (index 1), not line 2.

    # Extract epoch from header line (e.g., "EPOCH=1980.")
    epoch = 1980.0  # default
    idx = first.upper().find("EPOCH=")
    if idx >= 0:
        try:
            epoch = float(first[idx + 6:].split()[0].rstrip("."))
        except (ValueError, IndexError):
            pass

    # Parse coefficient data (starts at line 1) to find max degree.
    # Fortran FORMAT(2I3,6F11.4) — fixed-width columns.
    # The file has a main coefficient block (6 values/line), then a blank
    # terminator, then an optional section with third-order time derivatives
    # (2 values/line). We parse both sections.
    maxn = 0
    nmaxt = 0    # max degree with non-zero 1st-order time derivatives
    nmaxtt = 0   # max degree with non-zero 2nd-order time derivatives
    nmxttt = 0   # max degree with non-zero 3rd-order time derivatives
    in_main_block = True

    for line in lines[1:]:
        if line.strip() == '':
            # Blank line — marks end of main coefficient block.
            # Stop parsing entirely; the remaining 2-value lines are
            # third-order derivatives that we skip.
            break
        if len(line) < 6:
            continue

        try:
            n = int(line[0:3])
            m = int(line[3:6])
        except ValueError:
            continue  # Skip non-coefficient lines
        if n <= 0:
            if in_main_block:
                in_main_block = False
            continue

        maxn = max(maxn, n)

        if in_main_block:
            # Main block: check GT/HT (1st-order) and GTT/HTT (2nd-order)
            # Columns: G(6:17), H(17:28), GT(28:39), HT(39:50), GTT(50:61), HTT(61:72)
            if len(line) >= 50:
                try:
                    gt = float(line[28:39])
                    ht = float(line[39:50])
                    if gt != 0.0 or ht != 0.0:
                        nmaxt = max(nmaxt, n)
                except ValueError:
                    pass
            if len(line) >= 61:
                try:
                    gtt = float(line[50:61])
                    htt = float(line[61:72]) if len(line) >= 72 else 0.0
                    if gtt != 0.0 or htt != 0.0:
                        nmaxtt = max(nmaxtt, n)
                except ValueError:
                    pass
        else:
            # After terminator: third-order time derivatives (2 values/line)
            nmxttt = max(nmxttt, n)

    if maxn == 0:
        return  # Can't determine model parameters

    # Build header line: FORMAT(4I2,2I2,2F6.1,I2,...)
    # NMAX, NMAXT, NMAXTT, NMXTTT, MODEXT, K, TZERO, ABAR, MODIND
    header = f"{maxn:2d}{nmaxt:2d}{nmaxtt:2d}{nmxttt:2d}{0:2d}{0:2d}"
    header += f"{epoch:6.1f}{6371.2:6.1f}{0:2d}"
    header = header.ljust(78)

    # Rebuild: new numeric header + original text header as description + coefficients
    with open(filepath, "w") as f:
        f.write(header + "\n")
        for line in lines:
            f.write(line)
        # Add terminator for third-order section if it exists and lacks one
        if nmxttt > 0:
            f.write("  0  0\n")


class Model:
    """GSFC geomagnetic field model ctypes wrapper.

    Supports GSFC 9/80, 12/83, and 11/87 models.
    """

    def __init__(
        self,
        dll_path: Optional[Union[str, Path]] = None,
        *,
        gsfc_version: int = 87,
        data_dir: Optional[Union[str, Path]] = None,
        auto_download: bool = True,
    ) -> None:
        if gsfc_version not in (80, 83, 87):
            raise ValueError(
                f"gsfc_version 必须为 80、83 或 87，当前值: {gsfc_version}"
            )
        self._gsfc_version = gsfc_version
        self._model_id = {80: 0, 83: 1, 87: 2}[gsfc_version]

        data_root = ensure_model_data(
            "gsfc",
            data_dir=data_dir,
            auto_download=auto_download,
        )

        # GSFC data files live in a gsfcdata/ subdirectory
        self._data_root = data_root / "gsfcdata"

        # Preprocess gsfc80.dat if needed (only when using GSFC-80)
        if gsfc_version == 80:
            _preprocess_gsfc80(self._data_root)

        base = Path(__file__).resolve().parent
        if dll_path is None:
            dll_name = "gsfc.dll" if os.name == "nt" else "libgsfc.so"
            dll_path = base / dll_name
        self._dll_path = resolve_dll_path(dll_path)
        self._dll_directory_handles = configure_dll_directories(self._dll_path)

        self._dll = C.cdll.LoadLibrary(str(self._dll_path))
        self._set_data_root(self._data_root)

        self._gsfc_eval = self._dll.gsfc_eval
        self._gsfc_eval.restype = None
        self._gsfc_eval.argtypes = _GSFC_ARGTYPES

    def _set_data_root(self, data_dir: Path) -> None:
        set_data_root = self._dll.gsfc_set_data_root
        set_data_root.argtypes = [C.c_char_p]
        set_data_root.restype = None
        set_data_root(os.fsencode(str(data_dir)) + b"\x00")

    def calculate(
        self,
        *,
        year,
        lat_deg,
        lon_deg,
        alt_km,
    ) -> dict:
        """
        计算地磁场分量。

        参数：
            year: 十进制年份（如 1985.5），标量或数组。
            lat_deg: 地理纬度（度，北正），标量或数组。
            lon_deg: 地理经度（度，东正），标量或数组。
            alt_km: 海拔高度（km），标量或数组。

        返回：
            包含地磁场分量（nT）的字典。
        """
        # Re-set data root before each call in case multiple
        # Model instances share the same DLL.
        self._set_data_root(self._data_root)
        return _calculate_gsfc(
            self._gsfc_eval,
            self._model_id,
            year=year,
            lat_deg=lat_deg,
            lon_deg=lon_deg,
            alt_km=alt_km,
        )


def _calculate_one(
    gsfc_func,
    model_id: int,
    lat_deg: float,
    lon_deg: float,
    year: float,
    alt_km: float,
) -> dict:
    x = _C_FLOAT()
    y = _C_FLOAT()
    z = _C_FLOAT()
    f = _C_FLOAT()

    gsfc_func(
        _C_INT(model_id),
        _C_FLOAT(float(lat_deg)),
        _C_FLOAT(float(lon_deg)),
        _C_FLOAT(float(alt_km)),
        _C_FLOAT(float(year)),
        _C_INT(0),  # jj=0 for geodetic coordinates
        C.byref(x),
        C.byref(y),
        C.byref(z),
        C.byref(f),
    )

    xn = float(x.value)
    yn = float(y.value)
    zn = float(z.value)
    fn = float(f.value)
    h = math.sqrt(xn * xn + yn * yn) if xn != 0.0 or yn != 0.0 else 0.0

    return {
        "X_nT": xn,
        "Y_nT": yn,
        "Z_nT": zn,
        "F_nT": fn,
        "H_nT": h,
        "inclination_deg": math.degrees(math.atan2(zn, h)) if h > 0 else 0.0,
        "declination_deg": math.degrees(math.atan2(yn, xn)),
    }


def _calculate_gsfc(
    gsfc_func,
    model_id: int,
    *,
    year,
    lat_deg,
    lon_deg,
    alt_km,
) -> dict:
    year_arr, lat_arr, lon_arr, alt_arr = np.broadcast_arrays(
        np.asarray(year, dtype=float),
        np.asarray(lat_deg, dtype=float),
        np.asarray(lon_deg, dtype=float),
        np.asarray(alt_km, dtype=float),
    )
    shape = year_arr.shape
    flat_count = int(year_arr.size)

    # Pre-allocate output arrays
    x_arr = np.empty(flat_count, dtype=float)
    y_arr = np.empty(flat_count, dtype=float)
    z_arr = np.empty(flat_count, dtype=float)
    f_arr = np.empty(flat_count, dtype=float)
    h_arr = np.empty(flat_count, dtype=float)
    incl = np.empty(flat_count, dtype=float)
    decl = np.empty(flat_count, dtype=float)

    flat_inputs = (
        lat_arr.reshape(-1),
        lon_arr.reshape(-1),
        year_arr.reshape(-1),
        alt_arr.reshape(-1),
    )

    for i, vals in enumerate(zip(*flat_inputs)):
        result = _calculate_one(gsfc_func, model_id, *vals)
        x_arr[i] = result["X_nT"]
        y_arr[i] = result["Y_nT"]
        z_arr[i] = result["Z_nT"]
        f_arr[i] = result["F_nT"]
        h_arr[i] = result["H_nT"]
        incl[i] = result["inclination_deg"]
        decl[i] = result["declination_deg"]

    scalar_input = shape == ()
    if scalar_input:
        return {
            "year": float(year_arr),
            "lat_deg": float(lat_arr),
            "lon_deg": float(lon_arr),
            "alt_km": float(alt_arr),
            "X_nT": float(x_arr[0]),
            "Y_nT": float(y_arr[0]),
            "Z_nT": float(z_arr[0]),
            "F_nT": float(f_arr[0]),
            "H_nT": float(h_arr[0]),
            "inclination_deg": float(incl[0]),
            "declination_deg": float(decl[0]),
        }

    return {
        "year": year_arr.astype(float),
        "lat_deg": lat_arr.astype(float),
        "lon_deg": lon_arr.astype(float),
        "alt_km": alt_arr.astype(float),
        "X_nT": x_arr.reshape(shape),
        "Y_nT": y_arr.reshape(shape),
        "Z_nT": z_arr.reshape(shape),
        "F_nT": f_arr.reshape(shape),
        "H_nT": h_arr.reshape(shape),
        "inclination_deg": incl.reshape(shape),
        "declination_deg": decl.reshape(shape),
    }
