"""Stage 2 normalised panel (PANEL-1) data quality. Synthetic data only."""

import io
import json
import zipfile

import pandas as pd
import pytest

import src.stage2.panel as pm
from src.stage2.panel import calendar_check, qa, qa_conflicts

LEGACY_HDR = "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN\n"


def frame(rows):
    return pd.DataFrame(rows, columns=["date", "symbol", "isin", "series", "open", "high", "low", "close",
                                       "last", "prevclose", "volume", "value", "trades"])


def test_qa_counts_each_problem_without_removing_rows():
    d = pd.Timestamp("2020-01-02")
    df = frame([(d, "A", "INE1", "EQ", 10, 11, 9, 10, 10, 10, 100, 1000, 5),
                (d, "A", "INE1", "EQ", 10, 11, 9, 10, 10, 10, 100, 1000, 5),        # duplicate
                (d, "B", "INE2", "EQ", 10, 9, 9, 10, 10, 10, 100, 1000, 5),         # high < open
                (d, "C", "INE3", "EQ", 0, 1, 0, 1, 1, 1, -5, -1, 5),                 # <=0 price, bad vol/value
                (d, "D", None, "EQ", None, 1, 1, 1, 1, 1, None, 1, 5)])              # missing price/vol/isin
    before = df.copy()
    q = qa(df)
    assert q == {"rows": 5, "duplicate_symbol_date": 1, "impossible_ohlc": 1, "non_positive_price": 1,
                 "missing_price": 1, "negative_or_missing_volume": 2, "negative_value": 1, "missing_isin_rows": 1}
    pd.testing.assert_frame_equal(df, before)


def test_identity_conflicts():
    d = pd.Timestamp("2020-01-02")
    df = frame([(d, "A", "INE1", "EQ", 1, 1, 1, 1, 1, 1, 1, 1, 1), (d, "B", "INE1", "EQ", 1, 1, 1, 1, 1, 1, 1, 1, 1),
                (d, "C", "INE3", "EQ", 1, 1, 1, 1, 1, 1, 1, 1, 1), (d, "C", "INE4", "EQ", 1, 1, 1, 1, 1, 1, 1, 1, 1)])
    assert qa_conflicts(df) == {"isin_on_two_symbols_same_day": 1, "symbol_with_two_isins_same_day": 1}


def test_calendar_check_detects_unattempted_days_and_holiday_mismatch():
    recs = [{"kind": "legacy_cm", "status": 200, "session": "2020-01-06"},
            {"kind": "legacy_cm", "status": 404, "session": "2020-01-07"},
            {"kind": "udiff_cm", "status": 404, "session": "2020-01-07"},          # same day, other format
            {"kind": "legacy_cm", "status": 200, "session": "2020-01-09"}]
    c = calendar_check(recs, "2020-01-06", "2020-01-10", holidays={pd.Timestamp("2020-01-09").date()})
    assert c["sessions"] == 2 and c["non_trading_weekdays_404"] == 1
    assert c["never_attempted"] == ["2020-01-08", "2020-01-10"]
    assert c["404_not_in_holiday_list"] == ["2020-01-07"] and c["holiday_with_file"] == ["2020-01-09"]


def _zip(text):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("f.csv", text)
    return b.getvalue()


def test_overlap_days_are_compared_field_by_field(tmp_path, monkeypatch):
    leg = LEGACY_HDR + "A,EQ,10,11,9,10,10,9.5,100,1000,01-MAR-2024,5,INE1\n"
    udf = ("TradDt,FinInstrmTp,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,LastPric,PrvsClsgPric,"
           "TtlTradgVol,TtlTrfVal,TtlNbOfTxsExctd,ISIN\n2024-03-01,STK,A,EQ,10,11,9,10.5,10,9.5,100,1000,5,INE1\n")
    (tmp_path / "l.zip").write_bytes(_zip(leg))
    (tmp_path / "u.zip").write_bytes(_zip(udf))
    files = [{"kind": "legacy_cm", "status": 200, "session": "2024-03-01", "path": "l.zip", "sha256": "L"},
             {"kind": "udiff_cm", "status": 200, "session": "2024-03-01", "path": "u.zip", "sha256": "U"}]
    monkeypatch.setattr(pm, "BASE_DIR", tmp_path)
    df, ov = pm.build_year(2024, files)
    assert list(df["source"]) == ["udiff_cm"] and df["close"].iloc[0] == 10.5      # UDiFF used from 2024
    assert ov[0]["field_mismatches"]["close"] == 1 and ov[0]["field_mismatches"]["open"] == 0


def test_dataset_never_overwritten(tmp_path, monkeypatch):
    (tmp_path / "l.zip").write_bytes(_zip(LEGACY_HDR + "A,EQ,10,11,9,10,10,9.5,100,1000,02-JAN-2020,5,INE1\n"))
    monkeypatch.setattr(pm, "BASE_DIR", tmp_path)
    monkeypatch.setattr(pm, "raw_files", lambda: [{"kind": "legacy_cm", "status": 200, "session": "2020-01-02",
                                                    "path": "l.zip", "sha256": "L"}])
    entries, _ = pm.build_dataset("out", years=[2020])
    assert entries[0]["qa"]["rows"] == 1
    with pytest.raises(FileExistsError):
        pm.build_dataset("out", years=[2020])


def test_post_cutoff_session_refused_by_builder(tmp_path, monkeypatch):
    (tmp_path / "x.zip").write_bytes(_zip(LEGACY_HDR + "A,EQ,1,1,1,1,1,1,1,1,01-OCT-2026,1,INE1\n"))
    monkeypatch.setattr(pm, "BASE_DIR", tmp_path)
    with pytest.raises(ValueError, match="cutoff"):
        pm.build_year(2026, [{"kind": "legacy_cm", "status": 200, "session": "2026-10-01", "path": "x.zip", "sha256": "x"}])
