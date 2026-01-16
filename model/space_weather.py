from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os


_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".space_weather_cache")
_CACHE_TTL_HOURS = 6


@dataclass
class SpaceWeatherIndices:
    date: datetime
    f107: float
    f107a: float
    ap: float
    ap_array: Tuple[float, ...]
    kp: Optional[float] = None

    def as_msis_params(self) -> Dict[str, float]:
        return {
            "f107": self.f107,
            "f107a": self.f107a,
            "ap7": list(self.ap_array) if len(self.ap_array) >= 7 else [self.ap] * 7,
        }

    def as_hwm_params(self) -> Dict[str, float]:
        return {
            "f107": self.f107,
            "f107a": self.f107a,
            "ap2": (0.0, self.ap),
        }


def _fetch_url(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "UpperAtmPy/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _get_cache_path(date: datetime) -> str:
    if not os.path.exists(_CACHE_DIR):
        os.makedirs(_CACHE_DIR, exist_ok=True)
    return os.path.join(_CACHE_DIR, f"sw_{date.strftime('%Y%m%d')}.json")


def _load_cached(date: datetime) -> Optional[Dict]:
    cache_path = _get_cache_path(date)
    if not os.path.exists(cache_path):
        return None

    mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
    if datetime.now() - mtime > timedelta(hours=_CACHE_TTL_HOURS):
        return None

    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(date: datetime, data: Dict) -> None:
    try:
        cache_path = _get_cache_path(date)
        with open(cache_path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def get_indices_celestrak(date: datetime) -> SpaceWeatherIndices:
    cached = _load_cached(date)
    if cached:
        return SpaceWeatherIndices(
            date=date,
            f107=cached["f107"],
            f107a=cached["f107a"],
            ap=cached["ap"],
            ap_array=tuple(cached.get("ap_array", [cached["ap"]] * 7)),
            kp=cached.get("kp"),
        )

    url = "https://celestrak.org/SpaceData/SW-Last5Years.txt"

    try:
        content = _fetch_url(url)
    except urllib.error.URLError as e:
        raise ConnectionError(f"无法连接到 CelesTrak: {e}")

    target_date_str = date.strftime("%Y %m %d")
    f107 = 100.0
    f107a = 100.0
    ap = 4.0
    ap_array = [4.0] * 7
    kp = None
    found = False

    for line in content.split("\n"):
        if line.startswith(target_date_str) or line.startswith(
            date.strftime("%Y  %m  %d")
        ):
            parts = line.split()
            if len(parts) >= 30:
                try:
                    kp_sum = sum(
                        float(parts[i]) for i in range(12, 20) if parts[i] != "-1"
                    )
                    kp = kp_sum / 8.0 if kp_sum > 0 else None

                    ap_daily = float(parts[22]) if parts[22] != "-1" else 4.0
                    ap = ap_daily
                    ap_array = [ap_daily] * 7

                    f107_idx = 26 if len(parts) > 26 else -1
                    if f107_idx > 0 and parts[f107_idx] != "-1":
                        f107 = float(parts[f107_idx])

                    f107a_idx = 28 if len(parts) > 28 else -1
                    if f107a_idx > 0 and parts[f107a_idx] != "-1":
                        f107a = float(parts[f107a_idx])

                    found = True
                    break
                except (ValueError, IndexError):
                    pass

    if not found:
        for line in reversed(content.split("\n")):
            parts = line.split()
            if len(parts) >= 30:
                try:
                    if parts[26] != "-1" and float(parts[26]) > 0:
                        f107 = float(parts[26])
                        f107a = float(parts[28]) if parts[28] != "-1" else f107
                        ap = float(parts[22]) if parts[22] != "-1" else 4.0
                        ap_array = [ap] * 7
                        break
                except (ValueError, IndexError):
                    continue

    cache_data = {
        "f107": f107,
        "f107a": f107a,
        "ap": ap,
        "ap_array": ap_array,
        "kp": kp,
    }
    _save_cache(date, cache_data)

    return SpaceWeatherIndices(
        date=date,
        f107=f107,
        f107a=f107a,
        ap=ap,
        ap_array=tuple(ap_array),
        kp=kp,
    )


def get_indices(
    date: Optional[datetime] = None,
    source: str = "celestrak",
) -> SpaceWeatherIndices:
    if date is None:
        date = datetime.utcnow() - timedelta(days=1)

    if source.lower() == "celestrak":
        return get_indices_celestrak(date)
    else:
        raise ValueError(f"不支持的数据源: {source}，可选: 'celestrak'")


def clear_cache() -> int:
    if not os.path.exists(_CACHE_DIR):
        return 0

    count = 0
    for f in os.listdir(_CACHE_DIR):
        if f.startswith("sw_") and f.endswith(".json"):
            try:
                os.remove(os.path.join(_CACHE_DIR, f))
                count += 1
            except Exception:
                pass
    return count


__all__ = [
    "SpaceWeatherIndices",
    "get_indices",
    "get_indices_celestrak",
    "clear_cache",
]
