from __future__ import annotations

from utils.cache import cached_call
from utils.time import doy, seconds_of_day


class TestDoy:
    def test_january_first(self):
        assert doy(2023, 1, 1) == 1.0

    def test_mid_year(self):
        assert doy(2023, 7, 15) == 196.0

    def test_december_31_non_leap(self):
        assert doy(2023, 12, 31) == 365.0

    def test_december_31_leap_year(self):
        assert doy(2024, 12, 31) == 366.0

    def test_leap_year_february_29(self):
        assert doy(2024, 2, 29) == 60.0


class TestSecondsOfDay:
    def test_midnight(self):
        assert seconds_of_day(0, 0, 0.0) == 0.0

    def test_noon(self):
        assert seconds_of_day(12, 0, 0.0) == 43200.0

    def test_end_of_day(self):
        assert seconds_of_day(23, 59, 59.0) == 86399.0

    def test_with_minutes(self):
        assert seconds_of_day(1, 30, 0.0) == 5400.0

    def test_with_fractional_seconds(self):
        result = seconds_of_day(0, 0, 0.5)
        assert result == 0.5

    def test_combined(self):
        result = seconds_of_day(12, 30, 45.5)
        expected = 12 * 3600 + 30 * 60 + 45.5
        assert result == expected


class TestCacheHelpers:
    def test_cached_call_preserves_original_arguments(self):
        calls = []

        def func(values):
            calls.append(values)
            return sum(values)

        cached = cached_call(func)
        assert cached([1, 2, 3]) == 6
        assert cached([1, 2, 3]) == 6

        assert calls == [[1, 2, 3]]
        assert cached.cache_info().hits == 1
        assert cached.cache_info().misses == 1
