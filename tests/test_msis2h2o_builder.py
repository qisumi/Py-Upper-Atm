from __future__ import annotations

import hashlib

import numpy as np
import pytest

from tools.build_msis2h2o_climatology import combine_years, write_deterministic_npz


def test_nvalues_weighting_preserves_negative_annual_means():
    average = np.asarray([-2.0, 4.0], dtype=float).reshape(2, 1, 1, 1, 1)
    counts = np.asarray([1.0, 3.0], dtype=float).reshape(2, 1, 1, 1, 1)
    climatology, fallback = combine_years(average, counts)
    assert climatology.item() == pytest.approx(2.5)
    assert not fallback.item()


def test_nonpositive_cell_uses_weighted_zonal_fallback():
    average = np.asarray([-1.0, 5.0], dtype=float).reshape(1, 1, 1, 2, 1)
    counts = np.asarray([1.0, 3.0], dtype=float).reshape(1, 1, 1, 2, 1)
    climatology, fallback = combine_years(average, counts)
    np.testing.assert_allclose(climatology.reshape(-1), [3.5, 5.0])
    assert fallback.reshape(-1).tolist() == [True, False]


def test_unresolved_zonal_fallback_fails():
    average = np.asarray([-1.0, -2.0], dtype=float).reshape(1, 1, 1, 2, 1)
    counts = np.ones_like(average)
    with pytest.raises(ValueError, match="仍有"):
        combine_years(average, counts)


def test_deterministic_npz_has_fixed_bytes(tmp_path):
    arrays = {
        "z": np.asarray([3.0, 4.0]),
        "a": np.asarray([1, 2], dtype=np.int16),
    }
    first = tmp_path / "first.npz"
    second = tmp_path / "second.npz"
    digest1 = write_deterministic_npz(first, arrays)
    digest2 = write_deterministic_npz(second, dict(reversed(list(arrays.items()))))
    assert digest1 == digest2
    assert digest1 == "70fa8d9b3b9e5f19710dc46853b97f1a7b55569e6a0f465353e4fb4d36dbde89"
    assert first.read_bytes() == second.read_bytes()
    assert digest1 == hashlib.sha256(first.read_bytes()).hexdigest()
