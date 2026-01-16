from __future__ import annotations

from functools import lru_cache
from typing import Optional, Tuple, Callable, TypeVar
from dataclasses import dataclass

T = TypeVar("T")


def make_hashable(obj) -> tuple:
    if isinstance(obj, (list, tuple)):
        return tuple(make_hashable(item) for item in obj)
    elif isinstance(obj, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
    elif isinstance(obj, set):
        return tuple(sorted(make_hashable(item) for item in obj))
    else:
        return obj


class CachedModel:
    def __init__(self, model, cache_size: int = 10000):
        self._model = model
        self._cache_size = cache_size
        self._cache_enabled = True
        self._setup_cache()

    def _setup_cache(self):
        @lru_cache(maxsize=self._cache_size)
        def _cached_calculate(key: tuple):
            params = dict(key)
            if "ap7" in params and params["ap7"] is not None:
                params["ap7"] = list(params["ap7"])
            return self._model.calculate_point(**params, validate=False)

        self._cached_calculate = _cached_calculate

    def calculate_point(self, **kwargs) -> T:
        if not self._cache_enabled:
            return self._model.calculate_point(**kwargs)

        validate = kwargs.pop("validate", True)
        if validate:
            from .temp_density_model import _validate_temp_density_inputs

            _validate_temp_density_inputs(
                alt_km=kwargs.get("alt_km", 0),
                lat_deg=kwargs.get("lat_deg", 0),
                lon_deg=kwargs.get("lon_deg", 0),
                day=kwargs.get("day"),
                utsec=kwargs.get("utsec"),
                f107a=kwargs.get("f107a"),
                f107=kwargs.get("f107"),
            )

        if "ap7" in kwargs and kwargs["ap7"] is not None:
            kwargs["ap7"] = tuple(kwargs["ap7"])

        key = tuple(sorted(kwargs.items()))
        return self._cached_calculate(key)

    def cache_info(self):
        return self._cached_calculate.cache_info()

    def cache_clear(self):
        self._cached_calculate.cache_clear()

    def enable_cache(self):
        self._cache_enabled = True

    def disable_cache(self):
        self._cache_enabled = False

    def __getattr__(self, name):
        return getattr(self._model, name)


class CachedWindModel:
    def __init__(self, model, cache_size: int = 10000):
        self._model = model
        self._cache_size = cache_size
        self._cache_enabled = True
        self._setup_cache()

    def _setup_cache(self):
        @lru_cache(maxsize=self._cache_size)
        def _cached_calculate(key: tuple):
            params = dict(key)
            if "ap2" in params and params["ap2"] is not None:
                params["ap2"] = list(params["ap2"])
            return self._model.calculate_point(**params, validate=False)

        self._cached_calculate = _cached_calculate

    def calculate_point(self, **kwargs) -> T:
        if not self._cache_enabled:
            return self._model.calculate_point(**kwargs)

        validate = kwargs.pop("validate", True)
        if validate:
            from .wind_model import _validate_wind_inputs

            _validate_wind_inputs(
                alt_km=kwargs.get("alt_km", 0),
                glat_deg=kwargs.get("glat_deg", 0),
                glon_deg=kwargs.get("glon_deg", 0),
                sec=kwargs.get("sec"),
                stl_hours=kwargs.get("stl_hours"),
                f107a=kwargs.get("f107a"),
                f107=kwargs.get("f107"),
            )

        if "ap2" in kwargs and kwargs["ap2"] is not None:
            kwargs["ap2"] = tuple(kwargs["ap2"])

        key = tuple(sorted(kwargs.items()))
        return self._cached_calculate(key)

    def cache_info(self):
        return self._cached_calculate.cache_info()

    def cache_clear(self):
        self._cached_calculate.cache_clear()

    def enable_cache(self):
        self._cache_enabled = True

    def disable_cache(self):
        self._cache_enabled = False

    def __getattr__(self, name):
        return getattr(self._model, name)


__all__ = ["CachedModel", "CachedWindModel", "make_hashable"]
