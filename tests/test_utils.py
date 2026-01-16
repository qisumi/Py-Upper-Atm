from __future__ import annotations

import pytest
from datetime import datetime

from model import convert_date_to_day, calculate_seconds_of_day


class TestConvertDateToDay:
    def test_january_first(self):
        assert convert_date_to_day(2023, 1, 1) == 1.0

    def test_mid_year(self):
        result = convert_date_to_day(2023, 7, 15)
        assert result == 196.0

    def test_december_31_non_leap(self):
        assert convert_date_to_day(2023, 12, 31) == 365.0

    def test_december_31_leap_year(self):
        assert convert_date_to_day(2024, 12, 31) == 366.0

    def test_leap_year_february_29(self):
        assert convert_date_to_day(2024, 2, 29) == 60.0


class TestCalculateSecondsOfDay:
    def test_midnight(self):
        assert calculate_seconds_of_day(0, 0, 0.0) == 0.0

    def test_noon(self):
        assert calculate_seconds_of_day(12, 0, 0.0) == 43200.0

    def test_end_of_day(self):
        assert calculate_seconds_of_day(23, 59, 59.0) == 86399.0

    def test_with_minutes(self):
        assert calculate_seconds_of_day(1, 30, 0.0) == 5400.0

    def test_with_fractional_seconds(self):
        result = calculate_seconds_of_day(0, 0, 0.5)
        assert result == 0.5

    def test_combined(self):
        result = calculate_seconds_of_day(12, 30, 45.5)
        expected = 12 * 3600 + 30 * 60 + 45.5
        assert result == expected


class TestUtilityIntegration:
    def test_date_to_day_type(self):
        result = convert_date_to_day(2023, 6, 15)
        assert isinstance(result, float)

    def test_seconds_type(self):
        result = calculate_seconds_of_day(12, 0, 0)
        assert isinstance(result, float)
