#!/usr/bin/env python3
"""NetCDF to CSV converter with a human-readable analysis summary."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    import xarray as xr
except ImportError as exc:  # pragma: no cover - guidance for runtime users
    raise SystemExit(
        "This script requires xarray and its dependencies (pandas, numpy). "
        "Please run `pip install xarray pandas numpy` before retrying."
    ) from exc


LINE = "=" * 100
DEFAULT_FLOAT_FORMAT = "%.4f"
REPO_ROOT = Path(__file__).absolute().parents[1]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expand NetCDF (*.nc) files under the data directory into CSV and print a reference analysis summary."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=REPO_ROOT / "data",
        help="NetCDF input directory (default: ./data)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data",
        help="CSV output directory (default: ./data)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default="*.nc",
        help="Glob pattern for matching NetCDF files (default: *.nc)",
    )
    parser.add_argument(
        "--float-format",
        default=DEFAULT_FLOAT_FORMAT,
        help="Float format for CSV export (printf-style, default: %.4f).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwrite when target CSV already exists.",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        default=True,
        help="Only generate CSV, without printing an analysis summary like ERA5_T_20120101_analysis.txt.",
    )
    return parser.parse_args(argv)


def find_nc_files(input_dir: Path, pattern: str) -> List[Path]:
    return sorted(input_dir.glob(pattern))


def _ensure_absolute(path: Path) -> Path:
    return path if path.is_absolute() else (Path.cwd() / path)


def dataset_to_dataframe(ds: xr.Dataset) -> "pd.DataFrame":
    df = ds.to_dataframe().reset_index()
    dims = list(ds.dims)
    data_vars = list(ds.data_vars)
    preferred_order = [col for col in dims + data_vars if col in df.columns]
    remaining = [col for col in df.columns if col not in preferred_order]
    ordered_columns = preferred_order + remaining
    return df[ordered_columns]


def _all_variables(ds: xr.Dataset) -> Iterable[Tuple[str, xr.DataArray]]:
    seen: set[str] = set()
    for mapping in (ds.data_vars, ds.coords):
        for name, data_array in mapping.items():
            if name in seen:
                continue
            seen.add(name)
            yield name, data_array


def _compute_stats(array: np.ndarray) -> Tuple[str, str, str] | None:
    if array.size == 0:
        return None
    if np.issubdtype(array.dtype, np.datetime64):
        flattened = array.astype("datetime64[ns]").reshape(-1)
        valid = flattened[~np.isnat(flattened)]
        if valid.size == 0:
            return None
        as_int = valid.view("int64")
        mean_val = int(np.mean(as_int))
        return (
            str(valid.min()),
            str(valid.max()),
            str(np.datetime64(mean_val, "ns")),
        )
    if np.issubdtype(array.dtype, np.number):
        flattened = array.astype(np.float64).reshape(-1)
        valid = flattened[~np.isnan(flattened)]
        if valid.size == 0:
            return None
        return (
            f"{valid.min():.4f}",
            f"{valid.max():.4f}",
            f"{valid.mean():.4f}",
        )
    return None


def summarize_dataset(ds: xr.Dataset, source: Path) -> None:
    rel_path = (
        source.relative_to(REPO_ROOT) if source.is_relative_to(REPO_ROOT) else source
    )
    print(LINE)
    print(f"Opened file: {rel_path}")
    print(LINE)
    print("\nGlobal attributes:")
    if ds.attrs:
        for key, value in ds.attrs.items():
            print(f"  {key}: {value}")
    else:
        print("  (No global attributes)")

    unlimited_dims = set(ds.encoding.get("unlimited_dims", []))
    print("\nDimension information:")
    if ds.dims:
        for name, length in ds.dims.items():
            is_unlimited = "True" if name in unlimited_dims else "False"
            print(f"  {name}: {length} (unlimited: {is_unlimited})")
    else:
        print("  (No dimension information)")

    print("\nVariable information (names and ranges):")
    print("-" * 100)
    for name, data_array in _all_variables(ds):
        print(f"Variable name: {name}")
        print(f"  Data type: {data_array.dtype}")
        print(f"  Dimensions: {data_array.dims}")
        print(f"  Shape: {tuple(data_array.shape)}")
        attrs = data_array.attrs or {}
        if attrs:
            print("  Attributes:")
            for key, value in attrs.items():
                print(f"    {key}: {value}")
        stats = _compute_stats(np.asarray(data_array.values))
        print("  Data range:")
        if stats is None:
            print("    (Non-numeric/date type or no valid data; skipping statistics)")
        else:
            min_val, max_val, mean_val = stats
            print(f"    Min: {min_val}")
            print(f"    Max: {max_val}")
            print(f"    Mean: {mean_val}")
        print()


def convert_file(
    nc_path: Path,
    output_dir: Path,
    *,
    float_format: str | None,
    overwrite: bool,
    show_summary: bool,
) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{nc_path.stem}.csv"
    if csv_path.exists() and not overwrite:
        print(
            f"Skipped {nc_path.name}: target {csv_path.name} already exists (use --overwrite to overwrite)."
        )
        return False

    with xr.open_dataset(nc_path) as ds:
        if show_summary:
            summarize_dataset(ds, nc_path)
        df = dataset_to_dataframe(ds)
    df.to_csv(csv_path, index=False, float_format=float_format)
    print(f"Exported CSV: {csv_path} ({len(df)} rows × {len(df.columns)} columns)")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    input_dir = _ensure_absolute(args.input_dir)
    output_dir = _ensure_absolute(args.output_dir)
    nc_files = find_nc_files(input_dir, args.pattern)

    if not nc_files:
        print(f"No NetCDF files matching pattern {args.pattern!r} found in {input_dir}.")
        return 1

    converted = 0
    for nc_file in nc_files:
        success = convert_file(
            nc_file,
            output_dir,
            float_format=args.float_format,
            overwrite=args.overwrite,
            show_summary=not args.no_summary,
        )
        if success:
            converted += 1

    print(f"\nTask completed: converted {converted}/{len(nc_files)} files.")
    return 0 if converted else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
