from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable, NamedTuple, TypeVar

T = TypeVar("T")


def make_hashable(obj: Any) -> Any:
    """Convert common containers to hashable structures for cache-key construction."""
    if isinstance(obj, (list, tuple)):
        return tuple(make_hashable(item) for item in obj)
    if isinstance(obj, dict):
        return tuple(sorted((key, make_hashable(value)) for key, value in obj.items()))
    if isinstance(obj, set):
        return tuple(sorted(make_hashable(item) for item in obj))
    if hasattr(obj, "shape") and hasattr(obj, "dtype") and hasattr(obj, "tolist"):
        return (
            obj.__class__.__module__,
            str(obj.dtype),
            tuple(obj.shape),
            make_hashable(obj.tolist()),
        )
    return obj


class CacheInfo(NamedTuple):
    hits: int
    misses: int
    maxsize: int
    currsize: int


def cached_call(func: Callable[..., T], *, cache_size: int = 10000) -> Callable[..., T]:
    """
    Create a keyword-argument cache wrapper for any function.

    This utility does not assume a model interface; pass a concrete callable
    directly, for example `cached_call(model.calculate)`.
    """

    cache: OrderedDict[Any, T] = OrderedDict()
    hits = 0
    misses = 0

    def wrapper(*args: Any, **kwargs: Any) -> T:
        nonlocal hits, misses

        key = (make_hashable(args), make_hashable(kwargs))
        if key in cache:
            hits += 1
            cache.move_to_end(key)
            return cache[key]

        misses += 1
        result = func(*args, **kwargs)
        cache[key] = result
        cache.move_to_end(key)
        if cache_size >= 0 and len(cache) > cache_size:
            cache.popitem(last=False)
        return result

    def cache_info() -> CacheInfo:
        return CacheInfo(hits, misses, cache_size, len(cache))

    def cache_clear() -> None:
        nonlocal hits, misses
        cache.clear()
        hits = 0
        misses = 0

    wrapper.cache_info = cache_info  # type: ignore[attr-defined]
    wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
    return wrapper


__all__ = ["make_hashable", "cached_call", "CacheInfo"]
