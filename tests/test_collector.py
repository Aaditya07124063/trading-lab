"""Collector: failures and rejections are recorded, never silently skipped,
and existing files are never altered."""

import pandas as pd

import update_intraday as ui
from tests.test_intraday import day


def bars(*dates, base=100.0):
    return pd.DataFrame([r for d in dates for r in day(d, base=base)])


def setup(tmp_path, monkeypatch, fetch):
    import src.config as cfg
    import src.data_loader as dl
    (tmp_path / "india").mkdir()
    monkeypatch.setattr(ui, "DATA_DIR", tmp_path)
    monkeypatch.setattr(dl, "DATA_DIR", tmp_path)
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ui, "fetch_yahoo", fetch)


def test_provider_failure_is_recorded(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("yahoo down")
    setup(tmp_path, monkeypatch, boom)
    r = ui.collect_one("XYZ", "XYZ.NS", "m15", "holdout", "run", dry=False)
    assert r["status"] == "FAILED" and "yahoo down" in r["error"]


def test_mismatching_download_is_rejected_and_file_untouched(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, lambda *a, **k: bars("2026-01-05", "2026-01-06", base=300))
    from src.intraday.pipeline import write_mt_csv
    path = tmp_path / "india" / "XYZm15.csv"
    write_mt_csv(bars("2026-01-05"), path)
    before = path.read_bytes()
    r = ui.collect_one("XYZ", "XYZ.NS", "m15", "holdout", "run", dry=False)
    assert r["status"] == "REJECTED" and r["rows_added"] == 0
    assert path.read_bytes() == before
    assert (tmp_path / "raw" / "yahoo" / "XYZm15").exists()          # raw snapshot still kept


def test_good_download_appends_and_logs_counts(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, lambda *a, **k: bars("2026-01-05", "2026-01-06"))
    from src.intraday.pipeline import write_mt_csv
    write_mt_csv(bars("2026-01-05"), tmp_path / "india" / "XYZm15.csv")
    r = ui.collect_one("XYZ", "XYZ.NS", "m15", "holdout", "run", dry=False)
    assert (r["status"], r["rows_added"], r["duplicates_overlap"]) == ("OK", 25, 25)
    assert r["file_sha256_after"] and r["raw_sha256"]
