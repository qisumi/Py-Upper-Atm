from __future__ import annotations

import hashlib

import pytest

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


class TestModelData:
    def test_constructor_data_dir_overrides_env(self, monkeypatch, tmp_path):
        from utils.model_data import DATA_ENV_VAR, resolve_data_root

        explicit = tmp_path / "explicit"
        env_dir = tmp_path / "env"
        monkeypatch.setenv(DATA_ENV_VAR, str(env_dir))

        assert resolve_data_root("msis2", data_dir=explicit) == explicit.resolve()

    def test_hwm14_constructor_data_dir_can_point_at_legacy_data_dir(self, tmp_path):
        from utils.model_data import resolve_data_root

        hwm_data = tmp_path / "hwm14data"
        hwm_data.mkdir()

        assert resolve_data_root("hwm14", data_dir=hwm_data) == tmp_path.resolve()

    def test_hwm14_hwmpath_can_point_at_legacy_data_dir(self, monkeypatch, tmp_path):
        from utils.model_data import HWM14_ENV_VAR, resolve_data_root

        hwm_data = tmp_path / "hwm14data"
        hwm_data.mkdir()
        monkeypatch.setenv(HWM14_ENV_VAR, str(hwm_data))

        assert resolve_data_root("hwm14") == tmp_path.resolve()

    def test_default_data_root_is_project_local(self, monkeypatch, tmp_path):
        from utils.model_data import default_data_root

        monkeypatch.chdir(tmp_path)

        assert default_data_root() == tmp_path / ".upperatmpy"

    def test_missing_data_without_auto_download_reports_configuration(
        self, monkeypatch, tmp_path
    ):
        import utils.model_data as model_data

        monkeypatch.setattr(
            model_data,
            "_load_manifest",
            lambda: {
                "files": [
                    {
                        "model": "msis2",
                        "path": "msis2data/test.parm",
                        "url": "https://example.invalid/test.parm",
                        "sha256": "0" * 64,
                        "size": 1,
                    }
                ]
            },
        )

        with pytest.raises(model_data.ModelDataError) as excinfo:
            model_data.ensure_model_data("msis2", data_dir=tmp_path, auto_download=False)

        message = str(excinfo.value)
        assert "UPPERATMPY_DATA_DIR" in message
        assert "data_dir" in message
        assert "msis2data/test.parm" in message

    def test_downloads_missing_file_and_validates_hash(self, monkeypatch, tmp_path):
        import utils.model_data as model_data

        payload = b"upperatmpy data"
        digest = hashlib.sha256(payload).hexdigest()
        monkeypatch.setattr(
            model_data,
            "_load_manifest",
            lambda: {
                "files": [
                    {
                        "model": "msis2",
                        "path": "msis2data/test.parm",
                        "url": "https://example.invalid/test.parm",
                        "sha256": digest,
                        "size": len(payload),
                    }
                ]
            },
        )

        class FakeResponse:
            def __init__(self, data):
                self._data = data
                self._sent = False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self, size):
                if self._sent:
                    return b""
                self._sent = True
                return self._data

        def fake_urlopen(request, timeout):
            assert timeout == 60
            assert request.full_url == "https://example.invalid/test.parm"
            return FakeResponse(payload)

        monkeypatch.setattr(model_data.urllib.request, "urlopen", fake_urlopen)

        root = model_data.ensure_model_data("msis2", data_dir=tmp_path)

        assert root == tmp_path.resolve()
        assert (tmp_path / "msis2data" / "test.parm").read_bytes() == payload
        assert not (tmp_path / "msis2data" / "test.parm.tmp").exists()
