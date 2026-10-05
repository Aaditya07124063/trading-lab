"""Stage 2 raw archive: transient server errors are never recorded; weekends enumerated. No network."""

import io
import urllib.error
from datetime import date

import pytest

import src.stage2.archive as am


class Opener:
    def __init__(self, code):
        self.code = code

    def open(self, req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, self.code, "x", {}, io.BytesIO())


@pytest.fixture
def iso(tmp_path, monkeypatch):
    monkeypatch.setattr(am, "MANIFEST", tmp_path / "m.jsonl")
    monkeypatch.setattr(am, "RAW", tmp_path / "raw")
    monkeypatch.setattr(am, "BASE_DIR", tmp_path)
    return tmp_path


def test_5xx_is_raised_and_not_recorded(iso):
    with pytest.raises(urllib.error.HTTPError):
        am.fetch("http://x/a", "a.zip", "legacy_cm", date(2019, 10, 27), opener=Opener(503), known={})
    assert am.manifest() == {}                                   # a rerun retries it


def test_404_is_recorded_as_no_session(iso):
    rec = am.fetch("http://x/b", "b.zip", "legacy_cm", date(2024, 1, 21), opener=Opener(404), known={})
    assert rec["status"] == 404 and am.manifest()["http://x/b"]["status"] == 404


def test_weekend_days_and_cutoff():
    assert [d.isoformat() for d in am.weekend_days(date(2024, 1, 19), date(2024, 1, 22))] == ["2024-01-20", "2024-01-21"]
    with pytest.raises(ValueError, match="cutoff"):
        am.fetch("http://x/c", "c.zip", "legacy_cm", date(2026, 10, 3), known={})
