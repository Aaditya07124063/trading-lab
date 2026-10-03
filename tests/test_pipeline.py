"""Intraday data pipeline: add, never rewrite; refuse anything suspicious."""

import pandas as pd
import pytest

from src.data_loader import load_csv
from src.intraday.pipeline import DataConflict, merge_bars, write_mt_csv
from tests.test_intraday import day

AFTER_CLOSE = pd.Timestamp("2030-01-01 18:00")


def bars(*dates, base=100.0):
    return pd.DataFrame([r for d in dates for r in day(d, base=base)])


def test_adds_only_new_bars_and_existing_wins():
    old = bars("2026-01-05", "2026-01-06")
    new = bars("2026-01-06", "2026-01-07")
    new.loc[new.date.dt.date == pd.Timestamp("2026-01-06").date(), "close"] += 0.1  # tiny diff
    merged, rep = merge_bars(old, new, 15, "X", now=AFTER_CLOSE)
    assert rep["added"] == 25 and rep["overlap_checked"] == 25
    assert len(merged) == 75 and merged["date"].is_unique and merged["date"].is_monotonic_increasing
    pd.testing.assert_frame_equal(merged.iloc[:50], old)          # history untouched


def test_fills_missing_bars_of_a_partial_stored_day():
    old = bars("2026-01-05").iloc[:10]
    merged, rep = merge_bars(old, bars("2026-01-05"), 15, "X", now=AFTER_CLOSE)
    assert rep["added"] == 15 and len(merged) == 25


def test_refuses_wrong_instrument_on_overlap():
    with pytest.raises(DataConflict, match="disagree"):
        merge_bars(bars("2026-01-05"), bars("2026-01-05", base=250), 15, "X", now=AFTER_CLOSE)


def test_refuses_implausible_jump_across_gap_and_reports_real_gaps():
    with pytest.raises(DataConflict, match="jump"):
        merge_bars(bars("2026-01-05"), bars("2026-02-05", base=200), 15, "X", now=AFTER_CLOSE)
    _, rep = merge_bars(bars("2026-01-05"), bars("2026-02-05", base=105), 15, "X", now=AFTER_CLOSE)
    assert rep["gap"] == ("2026-01-05 15:15:00", "2026-02-05 09:15:00")


def test_refuses_corrupt_incoming_data():
    new = bars("2026-01-06")
    with pytest.raises(DataConflict, match="duplicate"):
        merge_bars(bars("2026-01-05"), pd.concat([new, new.iloc[[1]]]), 15, "X", now=AFTER_CLOSE)
    bad = new.copy(); bad.loc[3, "low"] = 500
    with pytest.raises(DataConflict, match="OHLC"):
        merge_bars(bars("2026-01-05"), bad, 15, "X", now=AFTER_CLOSE)


def test_refuses_mixing_session_grids():
    shifted = bars("2026-01-06").assign(date=lambda d: d.date - pd.Timedelta(minutes=15))
    with pytest.raises(DataConflict, match="grid"):
        merge_bars(bars("2026-01-05"), shifted, 15, "X", now=AFTER_CLOSE)


def test_drops_todays_bars_while_market_open():
    _, rep = merge_bars(bars("2026-01-05"), bars("2026-01-06"), 15, "X",
                        now=pd.Timestamp("2026-01-06 11:00"))
    assert rep["added"] == 0 and rep["dropped_live_bars"] == 25


def test_write_roundtrip_with_backup(tmp_path, monkeypatch):
    import src.data_loader as dl
    monkeypatch.setattr(dl, "DATA_DIR", tmp_path)
    p = tmp_path / "XYZm15.csv"
    df = bars("2026-01-05")
    write_mt_csv(df, p)
    write_mt_csv(df, p)
    assert len(list((tmp_path / "backups").glob("XYZm15.csv.*.bak"))) == 1
    back = load_csv("XYZm15.csv")
    pd.testing.assert_frame_equal(back, df, check_dtype=False)


def test_raw_snapshot_is_immutable_and_manifested(tmp_path, monkeypatch):
    import json
    import src.config as cfg
    from src.intraday.pipeline import snapshot_raw
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path)
    rec = snapshot_raw(bars("2026-01-05"), "yahoo", "XYZm15", retrieved_at="20260105T180000")
    assert (tmp_path / "raw" / "yahoo" / "XYZm15" / "20260105T180000.csv").exists()
    assert json.loads((tmp_path / "raw" / "manifest.jsonl").read_text())["sha256"] == rec["sha256"]
    with pytest.raises(FileExistsError):
        snapshot_raw(bars("2026-01-05"), "yahoo", "XYZm15", retrieved_at="20260105T180000")


def test_holdout_is_locked_by_default(tmp_path, monkeypatch):
    import src.intraday.data as d
    df = bars("2026-09-30", "2026-10-01")
    monkeypatch.setattr(d, "load_csv", lambda f, sort=True, coerce=False: df)
    loaded, _ = d.load_intraday("XYZm15.csv")
    assert loaded["date"].max() < pd.Timestamp("2026-10-01")
    proto = tmp_path / "p.md"
    proto.write_text("**Status:** DRAFT")
    monkeypatch.setattr("src.config.BASE_DIR", tmp_path)
    with pytest.raises(d.HoldoutLocked):
        d.load_intraday("XYZm15.csv", holdout_protocol="p.md")
    proto.write_text("**Status:** FROZEN")          # Phase 1: FROZEN alone is NOT enough
    with pytest.raises(d.HoldoutLocked, match="authorization"):
        d.load_intraday("XYZm15.csv", holdout_protocol="p.md")
