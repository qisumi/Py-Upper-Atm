"""Model data discovery and first-run download helpers."""

from __future__ import annotations

import importlib.metadata
import hashlib
import shutil
import json
import os
import zipfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

DATA_ENV_VAR = "UPPERATMPY_DATA_DIR"
HWM14_ENV_VAR = "HWMPATH"
DATA_TAG_ENV_VAR = "UPPERATMPY_DATA_TAG"
_MANIFEST_NAME = "model_data_manifest.json"
_USER_AGENT = "UpperAtmPy/0.1.1 model-data"
_GITHUB_RELEASE_BASE = "https://github.com/qisumi/Py-Upper-Atm/releases/download"
_DATA_BUNDLE_PREFIX = "upperatmpy-model-data"
_DEFAULT_DATA_TAG = "model-data-v1"


class ModelDataError(RuntimeError):
    """Raised when required model data cannot be located or downloaded."""


def ensure_model_data(
    model_name: str,
    *,
    data_dir: Optional[Union[str, Path]] = None,
    auto_download: bool = True,
) -> Path:
    """
    Ensure that all data files required by a model exist.

    The returned path is the data root containing legacy subdirectories such as
    ``msis2data`` and ``hwm14data``.
    """

    model_key = _normalize_model_name(model_name)
    root = resolve_data_root(model_key, data_dir=data_dir)
    entries = _manifest_entries(model_key)
    if not entries:
        return root

    missing = [entry for entry in entries if not _is_valid_file(root / str(entry["path"]), entry)]
    if not missing:
        return root

    if not auto_download:
        raise ModelDataError(_missing_data_message(model_key, root, missing))

    for entry in missing:
        _download_entry(root, entry)

    return root


def resolve_data_root(
    model_name: str,
    *,
    data_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """Resolve the data root according to constructor args, env vars, then cache."""

    model_key = _normalize_model_name(model_name)
    if data_dir is not None:
        path = _expand_path(data_dir)
        if model_key == "hwm14":
            return _normalize_hwm14_root(path)
        return path

    if model_key == "hwm14":
        hwmpath = os.environ.get(HWM14_ENV_VAR)
        if hwmpath:
            return _normalize_hwm14_root(_expand_path(hwmpath))

    env_dir = os.environ.get(DATA_ENV_VAR)
    if env_dir:
        return _expand_path(env_dir)

    return default_data_root()


def default_data_root() -> Path:
    """Return the default project-local UpperAtmPy data directory."""

    return (Path.cwd() / ".upperatmpy").resolve()


def _download_entry(root: Path, entry: Dict[str, object]) -> None:
    relative_path = _safe_relative_path(str(entry["path"]))
    destination = root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = destination.with_name(destination.name + ".tmp")

    expected_hash = str(entry["sha256"]).lower()
    expected_size = int(entry["size"])

    last_error = None
    for url in _entry_urls(entry):
        if str(url).lower().endswith(".zip"):
            try:
                if _download_from_bundle(root, url, str(entry["path"]), expected_size, expected_hash):
                    return
            except (OSError, urllib.error.URLError, zipfile.BadZipFile, ModelDataError) as exc:
                last_error = exc
                continue
            continue

        digest = hashlib.sha256()
        total = 0
        request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60) as response, tmp_path.open("wb") as fh:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    fh.write(chunk)
                    digest.update(chunk)
                    total += len(chunk)
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
            _unlink_quietly(tmp_path)
            continue

        actual_hash = digest.hexdigest()
        if total == expected_size and actual_hash == expected_hash:
            os.replace(str(tmp_path), str(destination))
            return

        _unlink_quietly(tmp_path)
        last_error = ModelDataError(
            "模型数据校验失败：{path}\n"
            "期望 size={expected_size}, sha256={expected_hash}\n"
            "实际 size={actual_size}, sha256={actual_hash}".format(
                path=relative_path,
                expected_size=expected_size,
                expected_hash=expected_hash,
                actual_size=total,
                actual_hash=actual_hash,
            )
        )

    if last_error is None:
        last_error = RuntimeError("没有可用下载地址")
    raise ModelDataError(_download_error_message(str(entry["model"]), root, entry, last_error))


def _entry_urls(entry: Dict[str, object]) -> List[str]:
    urls: List[str] = []
    release_tag = _release_tag()
    if release_tag:
        file_name = str(Path(str(entry["path"])).name)
        urls.append(_release_file_url(release_tag, file_name))
        bundle_url = _release_bundle_url(release_tag)
        if bundle_url is not None:
            urls.append(bundle_url)
    if "url" in entry and entry["url"]:
        urls.append(str(entry["url"]))
    for url in entry.get("fallback_urls", []) or []:
        urls.append(str(url))
    normalized = []
    seen = set()
    for url in urls:
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        normalized.append(url)
    return normalized


def _release_tag() -> str:
    override = os.environ.get(DATA_TAG_ENV_VAR, "").strip()
    if override:
        return _normalize_release_tag(override)

    try:
        version = importlib.metadata.version("upperatmpy")
    except Exception:
        version = None
    if not version:
        version = _package_version()
    if not version:
        return _DEFAULT_DATA_TAG
    return _normalize_release_tag(version)


def _package_version() -> Optional[str]:
    path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not path.is_file():
        return None

    in_project = False
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith("["):
                    if stripped == "[project]":
                        in_project = True
                        continue
                    if in_project:
                        break
                    in_project = False
                    continue
                if in_project and stripped.startswith("version"):
                    _, value = stripped.split("=", 1)
                    return value.strip().strip("'\"")
    except OSError:
        return None
    return None


def _normalize_release_tag(tag: str) -> str:
    tag = tag.strip()
    if not tag:
        return _DEFAULT_DATA_TAG
    return tag if tag.startswith("v") else f"v{tag}"


def _release_file_url(release_tag: str, file_name: str) -> str:
    return f"{_GITHUB_RELEASE_BASE}/{release_tag}/{file_name}"


def _release_bundle_url(release_tag: str) -> Optional[str]:
    # Newer release assets are packed as `upperatmpy-model-data-vX.Y.Z.zip`.
    if release_tag.startswith("v"):
        return f"{_GITHUB_RELEASE_BASE}/{release_tag}/{_DATA_BUNDLE_PREFIX}-{release_tag}.zip"
    return None


def _download_from_bundle(
    root: Path,
    url: str,
    path: str,
    expected_size: int,
    expected_hash: str,
) -> bool:
    archive = root / ".upperatmpy-model-data.zip"
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as fh:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            fh.write(chunk)

    target = str(_safe_relative_path(path).as_posix())
    with zipfile.ZipFile(archive) as zf:
        if target not in zf.namelist():
            _unlink_quietly(archive)
            raise ModelDataError(
                "数据压缩包中未包含目标文件：{path}".format(path=target)
            )
        destination = root / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(target) as source, destination.open("wb") as target_file:
            shutil.copyfileobj(source, target_file)

    _unlink_quietly(archive)
    destination = root / target
    if destination.stat().st_size != expected_size or not _is_valid_file(destination, {"path": target, "size": expected_size, "sha256": expected_hash}):
        _unlink_quietly(destination)
        raise ModelDataError("bundle 内文件校验失败：{path}".format(path=target))
    return True


def _is_valid_file(path: Path, entry: Dict[str, object]) -> bool:
    if not path.is_file():
        return False

    expected_size = int(entry["size"])
    if path.stat().st_size != expected_size:
        return False

    expected_hash = str(entry["sha256"]).lower()
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected_hash


def _manifest_entries(model_name: str) -> List[Dict[str, object]]:
    model_key = _normalize_model_name(model_name)
    manifest = _load_manifest()
    entries = []
    for entry in manifest.get("files", []):
        if _normalize_model_name(str(entry.get("model", ""))) == model_key:
            copied = dict(entry)
            copied["path"] = str(_safe_relative_path(str(copied["path"]))).replace("\\", "/")
            entries.append(copied)
    return entries


def _load_manifest() -> Dict[str, object]:
    path = Path(__file__).resolve().with_name(_MANIFEST_NAME)
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _missing_data_message(
    model_name: str,
    root: Path,
    entries: Sequence[Dict[str, object]],
) -> str:
    missing = ", ".join(str(entry["path"]) for entry in entries)
    return (
        "模型 {model} 缺少数据文件：{missing}\n"
        "当前数据目录：{root}\n"
        "请启用自动下载，或通过构造参数 data_dir 指定数据目录，"
        "也可以设置环境变量 {env_var}。"
    ).format(model=model_name, missing=missing, root=root, env_var=DATA_ENV_VAR)


def _download_error_message(
    model_name: str,
    root: Path,
    entry: Dict[str, object],
    exc: BaseException,
) -> str:
    return (
        "模型 {model} 数据文件下载失败：{path}\n"
        "下载地址：{url}\n"
        "当前数据目录：{root}\n"
        "原因：{exc}\n"
        "如果处于离线环境，请手动准备数据目录，并通过 data_dir 或 {env_var} 指定。"
    ).format(
        model=model_name,
        path=entry.get("path"),
        url=", ".join(_entry_urls(entry)),
        root=root,
        exc=exc,
        env_var=DATA_ENV_VAR,
    )


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or any(part == ".." for part in path.parts):
        raise ModelDataError("manifest 中包含不安全的数据路径：{0}".format(value))
    return path


def _expand_path(value: Union[str, Path]) -> Path:
    return Path(value).expanduser().resolve()


def _normalize_hwm14_root(path: Path) -> Path:
    if path.name.lower() == "hwm14data":
        return path.parent
    if (path / "hwm123114.bin").exists() or (path / "dwm07b104i.dat").exists():
        return path.parent
    return path


def _normalize_model_name(model_name: str) -> str:
    key = model_name.lower().replace("-", "").replace("_", "")
    aliases = {
        "nrlmsis2": "msis2",
        "nrlmsis20": "msis2",
        "msis20": "msis2",
        "hwm14": "hwm14",
        "hwm93": "hwm93",
        "msis00": "msis00",
        "nrlmsise00": "msis00",
    }
    return aliases.get(key, key)


def _unlink_quietly(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


__all__ = [
    "DATA_ENV_VAR",
    "HWM14_ENV_VAR",
    "ModelDataError",
    "default_data_root",
    "ensure_model_data",
    "resolve_data_root",
]
