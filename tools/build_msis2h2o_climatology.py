#!/usr/bin/env python3
"""Build the deterministic MSIS2H2O climatology from MLS Level-3 files.

This development-only builder requires ``netCDF4``. The generated artifact is
an ordinary NumPy ``.npz`` file and therefore adds no runtime dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np


PRODUCT_DOI = "10.5067/Aura/MLS/DATA/3538"
MONTH_MIDPOINT_DAY = np.asarray(
    [15.5, 45.0, 74.5, 105.0, 135.5, 166.0, 196.5, 227.5, 258.0, 288.5, 319.0, 349.5],
    dtype=np.float64,
)


def combine_years(
    annual_average_ppmv: np.ndarray,
    annual_nvalues: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute the nvalues-weighted climatology and zonal fallback mask.

    Negative annual retrieval means participate in the linear weighted mean.
    Only after all years have been combined are missing or non-positive cells
    replaced by the weighted zonal mean for the same month/latitude/pressure.
    """

    average = np.asarray(annual_average_ppmv, dtype=np.float64)
    counts = np.asarray(annual_nvalues, dtype=np.float64)
    if average.shape != counts.shape or average.ndim != 5:
        raise ValueError("annual average/nvalues 必须同形且为 (year, month, lat, lon, pressure)")
    valid = np.isfinite(average) & np.isfinite(counts) & (counts > 0.0)
    weights = np.where(valid, counts, 0.0)
    numerator = np.sum(np.where(valid, average * counts, 0.0), axis=0, dtype=np.float64)
    denominator = np.sum(weights, axis=0, dtype=np.float64)
    return _finalize_weighted(numerator, denominator)


def _finalize_weighted(numerator: np.ndarray, denominator: np.ndarray):
    climatology = np.divide(
        numerator,
        denominator,
        out=np.full(numerator.shape, np.nan, dtype=np.float64),
        where=denominator > 0.0,
    )

    bad = ~np.isfinite(climatology) | (climatology <= 0.0)
    # longitude is axis 2 after the year dimension has been removed
    zonal_numerator = np.sum(numerator, axis=2, dtype=np.float64)
    zonal_denominator = np.sum(denominator, axis=2, dtype=np.float64)
    zonal = np.divide(
        zonal_numerator,
        zonal_denominator,
        out=np.full(zonal_numerator.shape, np.nan, dtype=np.float64),
        where=zonal_denominator > 0.0,
    )
    repairable = bad & np.broadcast_to(
        (np.isfinite(zonal) & (zonal > 0.0))[:, :, None, :],
        climatology.shape,
    )
    climatology[repairable] = np.broadcast_to(zonal[:, :, None, :], climatology.shape)[repairable]
    fallback_mask = repairable

    unresolved = ~np.isfinite(climatology) | (climatology <= 0.0)
    if np.any(unresolved):
        indices = np.argwhere(unresolved)
        preview = ", ".join(str(tuple(int(v) for v in row)) for row in indices[:5])
        raise ValueError(
            "zonal fallback 后仍有 %d 个缺失或非正格点: %s"
            % (indices.shape[0], preview)
        )
    return climatology, fallback_mask


def write_deterministic_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> str:
    """Write a byte-reproducible compressed NumPy archive and return SHA-256."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as output:
        with zipfile.ZipFile(
            output,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for name in sorted(arrays):
                buffer = io.BytesIO()
                np.lib.format.write_array(
                    buffer,
                    np.ascontiguousarray(arrays[name]),
                    allow_pickle=False,
                )
                info = zipfile.ZipInfo(name + ".npy", date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, buffer.getvalue(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return sha256_file(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source_manifest(path: Path) -> Dict[str, object]:
    with Path(path).open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("product_doi") != PRODUCT_DOI:
        raise ValueError("源清单 product_doi 不正确")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or len(sources) != 20:
        raise ValueError("源清单必须固定包含 20 个年度文件")
    years = [int(item["year"]) for item in sources]
    if years != list(range(2005, 2025)):
        raise ValueError("源清单年份必须精确为 2005--2024")
    return manifest


def verify_source_files(source_dir: Path, manifest: Mapping[str, object]) -> Sequence[Path]:
    paths = []
    for source in manifest["sources"]:
        path = Path(source_dir) / str(source["filename"])
        if not path.is_file():
            raise FileNotFoundError("缺少 MLS 年度文件: %s" % path)
        expected = str(source["sha256"]).lower()
        if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
            raise ValueError("源清单尚未固定 SHA-256: %s" % source["filename"])
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(
                "MLS 年度文件 SHA-256 不匹配: %s\nexpected=%s\nactual=%s"
                % (source["filename"], expected, actual)
            )
        paths.append(path)
    return paths


def build_climatology(
    source_paths: Sequence[Path],
    output_path: Path,
) -> str:
    numerator = None
    denominator = None
    reference_axes = None
    for path in source_paths:
        average, nvalues, axes = read_annual_file(path)
        if reference_axes is None:
            reference_axes = axes
        else:
            _assert_matching_axes(reference_axes, axes, path)
        valid = np.isfinite(average) & np.isfinite(nvalues) & (nvalues > 0.0)
        annual_numerator = np.where(valid, average * nvalues, 0.0)
        annual_denominator = np.where(valid, nvalues, 0.0)
        if numerator is None:
            numerator = annual_numerator
            denominator = annual_denominator
        else:
            numerator += annual_numerator
            denominator += annual_denominator

    climatology, fallback = _finalize_weighted(numerator, denominator)
    latitude, longitude, pressure = reference_axes
    arrays = {
        "fallback_mask": fallback.astype(np.bool_),
        "latitude_deg": latitude.astype(np.float64),
        "log_vmr_ppmv": np.log(climatology).astype(np.float64),
        "longitude_deg": longitude.astype(np.float64),
        "month_midpoint_day": MONTH_MIDPOINT_DAY,
        "pressure_hpa": pressure.astype(np.float64),
        "source_years": np.arange(2005, 2025, dtype=np.int16),
    }
    return write_deterministic_npz(output_path, arrays)


def read_annual_file(path: Path):
    try:
        import netCDF4
    except ImportError as exc:
        raise RuntimeError("构建 MSIS2H2O 气候态需要开发依赖 netCDF4") from exc

    with netCDF4.Dataset(path, mode="r") as dataset:
        candidates = []
        for group in _walk_groups(dataset):
            lower_names = {name.lower(): name for name in group.variables}
            if getattr(group, "path", "") != "/H2O PressureGrid":
                continue
            value_name = "average" if "average" in lower_names else "value"
            if value_name not in lower_names or "nvalues" not in lower_names:
                continue
            average_var = group.variables[lower_names[value_name]]
            axis_map = _axis_dimension_map(group, dataset, average_var.dimensions)
            if set(axis_map) == {"month", "latitude", "longitude", "pressure"}:
                candidates.append((group, average_var, group.variables[lower_names["nvalues"]], axis_map))
        if len(candidates) != 1:
            names = [getattr(item[0], "path", "<root>") for item in candidates]
            raise ValueError("无法唯一定位 MLS 月-纬度-经度-压力组: %s" % names)

        group, average_var, nvalues_var, axis_map = candidates[0]
        average = _filled_array(average_var[:])
        nvalues = _filled_array(nvalues_var[:])
        if average.shape != nvalues.shape:
            raise ValueError("average 与 nvalues 形状不同: %s" % path)
        order = [axis_map[name] for name in ("month", "latitude", "longitude", "pressure")]
        average = np.moveaxis(average, order, range(4))
        nvalues = np.moveaxis(nvalues, order, range(4))
        if average.shape[0] != 12:
            raise ValueError("年度 Level-3 文件必须包含 12 个月: %s" % path)

        latitude = _coordinate_values(group, dataset, average_var.dimensions[axis_map["latitude"]])
        longitude = _coordinate_values(group, dataset, average_var.dimensions[axis_map["longitude"]])
        pressure_var = _coordinate_variable(group, dataset, average_var.dimensions[axis_map["pressure"]])
        pressure = _filled_array(pressure_var[:]).reshape(-1)
        pressure_units = str(getattr(pressure_var, "units", "hPa")).strip().lower()
        if pressure_units in ("pa", "pascal", "pascals"):
            pressure = pressure / 100.0
        elif pressure_units not in ("hpa", "mb", "mbar", "millibar", "millibars"):
            raise ValueError("未知压力单位 %r: %s" % (pressure_units, path))

        units = str(getattr(average_var, "units", "")).strip().lower()
        if "ppmv" in units or "ppm" in units:
            scale = 1.0
        elif units in ("", "1", "vmr", "mol/mol", "mol mol-1", "mol mol^-1"):
            scale = 1.0e6
        else:
            raise ValueError("未知 H2O average 单位 %r: %s" % (units, path))
        average = average * scale

    latitude_order = np.argsort(latitude)
    longitude = (longitude + 180.0) % 360.0 - 180.0
    longitude_order = np.argsort(longitude)
    pressure_order = np.argsort(pressure)
    latitude = latitude[latitude_order]
    longitude = longitude[longitude_order]
    pressure = pressure[pressure_order]
    average = average[:, latitude_order, :, :][:, :, longitude_order, :][:, :, :, pressure_order]
    nvalues = nvalues[:, latitude_order, :, :][:, :, longitude_order, :][:, :, :, pressure_order]

    # ML3MBH2O V005 recommends 316--0.00215 hPa and approximately ±82°.
    # The valid grid-cell centers are ±80° with bounds at ±82°. Extend the
    # endpoint cell value to its bin boundary so runtime clamping has the
    # documented ±82° threshold without inventing a polar gradient.
    pressure_selection = (pressure >= 0.00215) & (pressure <= 316.3)
    latitude_selection = (latitude >= -80.0) & (latitude <= 80.0)
    pressure = pressure[pressure_selection]
    latitude = latitude[latitude_selection]
    average = average[:, latitude_selection, :, :][:, :, :, pressure_selection]
    nvalues = nvalues[:, latitude_selection, :, :][:, :, :, pressure_selection]
    pressure[0] = 0.00215
    latitude = np.concatenate(([-82.0], latitude, [82.0]))
    average = np.concatenate((average[:, :1, :, :], average, average[:, -1:, :, :]), axis=1)
    nvalues = np.concatenate((nvalues[:, :1, :, :], nvalues, nvalues[:, -1:, :, :]), axis=1)

    if np.any(np.diff(latitude) <= 0.0) or np.any(np.diff(longitude) <= 0.0) or np.any(np.diff(pressure) <= 0.0):
        raise ValueError("MLS 坐标包含重复值或未能严格排序: %s" % path)
    return average, nvalues, (latitude, longitude, pressure)


def _walk_groups(group) -> Iterable[object]:
    yield group
    for child in group.groups.values():
        yield from _walk_groups(child)


def _axis_dimension_map(group, root, dimensions: Sequence[str]) -> Dict[str, int]:
    result = {}
    for index, dimension in enumerate(dimensions):
        lower = dimension.lower()
        if "lat" in lower:
            result["latitude"] = index
        elif "lon" in lower:
            result["longitude"] = index
        elif "press" in lower or lower in ("lev", "level"):
            result["pressure"] = index
        elif "month" in lower or "time" in lower:
            result["month"] = index
    # Some files use opaque dimension names but descriptive coordinate vars.
    for index, dimension in enumerate(dimensions):
        if index in result.values():
            continue
        try:
            variable = _coordinate_variable(group, root, dimension)
        except KeyError:
            continue
        name = (dimension + " " + str(getattr(variable, "standard_name", "")) + " " + str(getattr(variable, "long_name", ""))).lower()
        if "latitude" in name:
            result["latitude"] = index
        elif "longitude" in name:
            result["longitude"] = index
        elif "pressure" in name:
            result["pressure"] = index
        elif "month" in name or "time" in name:
            result["month"] = index
    return result


def _coordinate_variable(group, root, dimension: str):
    current = group
    while current is not None:
        if dimension in current.variables:
            return current.variables[dimension]
        current = getattr(current, "parent", None)
    aliases = {
        "latitude": ("lat", "latitude"),
        "longitude": ("lon", "longitude"),
        "pressure": ("pressure", "lev", "level"),
    }
    lower_dimension = dimension.lower()
    for names in aliases.values():
        if any(name in lower_dimension for name in names):
            for candidate in names:
                for scope in (group, root):
                    lower_names = {name.lower(): name for name in scope.variables}
                    if candidate in lower_names:
                        return scope.variables[lower_names[candidate]]
    raise KeyError(dimension)


def _coordinate_values(group, root, dimension: str) -> np.ndarray:
    return _filled_array(_coordinate_variable(group, root, dimension)[:]).reshape(-1)


def _filled_array(value) -> np.ndarray:
    if np.ma.isMaskedArray(value):
        return np.asarray(value.filled(np.nan), dtype=np.float64)
    return np.asarray(value, dtype=np.float64)


def _assert_matching_axes(reference, candidate, path: Path) -> None:
    for name, expected, actual in zip(("latitude", "longitude", "pressure"), reference, candidate):
        if expected.shape != actual.shape or not np.allclose(expected, actual, rtol=0.0, atol=1.0e-10):
            raise ValueError("%s 坐标与其他年份不一致: %s" % (name, path))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("msis2h2o_sources.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-output-sha256")
    args = parser.parse_args(argv)

    manifest = load_source_manifest(args.manifest)
    paths = verify_source_files(args.source_dir, manifest)
    actual = build_climatology(paths, args.output)
    expected = args.expected_output_sha256 or manifest.get("output_sha256")
    print("output=%s" % args.output)
    print("sha256=%s" % actual)
    if expected and expected != actual:
        raise SystemExit("输出 SHA-256 不匹配: expected=%s actual=%s" % (expected, actual))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
