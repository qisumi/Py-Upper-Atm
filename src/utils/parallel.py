from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional, TypeVar, Any
import os

T = TypeVar("T")

_DEFAULT_MAX_WORKERS = min(8, (os.cpu_count() or 4))


def parallel_map(
    func: Callable[..., T],
    items: List[Any],
    max_workers: Optional[int] = None,
    show_progress: bool = False,
) -> List[T]:
    if max_workers is None:
        max_workers = _DEFAULT_MAX_WORKERS

    if len(items) <= 1 or max_workers <= 1:
        return [func(item) for item in items]

    results = [None] * len(items)

    try:
        from tqdm import tqdm

        _has_tqdm = True
    except ImportError:
        _has_tqdm = False

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(func, item): idx for idx, item in enumerate(items)
        }

        iterator = as_completed(future_to_idx)
        if show_progress and _has_tqdm:
            iterator = tqdm(iterator, total=len(items), desc="Processing")

        for future in iterator:
            idx = future_to_idx[future]
            results[idx] = future.result()

    return results


def parallel_batch_compute(
    compute_func: Callable[..., T],
    param_dicts: List[dict],
    max_workers: Optional[int] = None,
    show_progress: bool = False,
) -> List[T]:
    def _call_with_kwargs(kwargs_dict: dict) -> T:
        return compute_func(**kwargs_dict)

    return parallel_map(
        _call_with_kwargs,
        param_dicts,
        max_workers=max_workers,
        show_progress=show_progress,
    )


__all__ = ["parallel_map", "parallel_batch_compute"]
