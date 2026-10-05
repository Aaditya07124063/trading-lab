"""Stage 2 identity layer (ID-1). Synthetic data only - no holdout file, nothing after the cutoff."""

import json

import pandas as pd
import pytest

import src.stage2.identity as idm
from src.stage2.identity import end_status, entities, links, resolve_historical, segments

DAYS = pd.bdate_range("2011-05-02", "2011-12-30")       # spans the 2011-06-22 ISIN introduction


def rows(symbol, isin, start, end):
    d = DAYS[(DAYS >= start) & (DAYS <= end)]
    return pd.DataFrame({"date": d, "symbol": symbol,
                         "isin": [isin if x >= pd.Timestamp("2011-06-22") else None for x in d]})


def src(symbol_changes=(), delisted=()):
    sc = pd.DataFrame(list(symbol_changes), columns=["old", "new", "date"])
    sc["date"] = pd.to_datetime(sc["date"])
    dl = pd.DataFrame(list(delisted), columns=["symbol", "date", "type"])
    dl["date"] = pd.to_datetime(dl["date"])
    return {"symbol_changes": sc, "delisted": dl}


NO_CA = pd.DataFrame(columns=["symbol", "ex_date", "kind", "factor", "subject"])


def build(panel, s, ca=NO_CA):
    seg = segments(panel)
    e, f = links(seg, s, ca)
    return seg, e, f, entities(seg, e)


def eid(ent, symbol):
    return set(ent.loc[ent["symbol"] == symbol, "entity_id"])


def test_symbol_change_with_same_isin_links_and_isin_intro():
    p = pd.concat([rows("OLDCO", "INE000A01011", "2011-05-02", "2011-09-30"),
                   rows("NEWCO", "INE000A01011", "2011-10-03", "2011-12-30")])
    seg, e, f, ent = build(p, src([("OLDCO", "NEWCO", "2011-10-03")]))
    assert {"ISIN_SAME", "SYMBOL_CHANGE", "ISIN_INTRO"} <= set(e["evidence"])
    assert len(eid(ent, "OLDCO") | eid(ent, "NEWCO")) == 1


def test_symbol_change_with_conflicting_isins_is_flagged_not_linked():
    p = pd.concat([rows("OLDCO", "INE000A01011", "2011-07-01", "2011-09-30"),
                   rows("NEWCO", "INE999Z01019", "2011-10-03", "2011-12-30")])
    seg, e, f, ent = build(p, src([("OLDCO", "NEWCO", "2011-10-03")]))
    assert "SYMBOL_CHANGE_ISIN_CONFLICT" in set(f["flag"])
    assert eid(ent, "OLDCO") != eid(ent, "NEWCO")


def test_look_alike_symbols_and_names_are_never_linked():
    p = pd.concat([rows("ABC", "INE111A01011", "2011-07-01", "2011-09-30"),
                   rows("ABCLTD", "INE222B01012", "2011-10-03", "2011-12-30")])
    seg, e, f, ent = build(p, src())
    assert e.empty and eid(ent, "ABC") != eid(ent, "ABCLTD")


def test_concurrently_shared_isin_is_flagged_not_linked():
    p = pd.concat([rows("A1", "INE333C01013", "2011-07-01", "2011-10-31"),
                   rows("A2", "INE333C01013", "2011-09-01", "2011-12-30")])
    seg, e, f, ent = build(p, src())
    assert "ISIN_SHARED_CONCURRENTLY" in set(f["flag"]) and eid(ent, "A1") != eid(ent, "A2")


def test_pre_isin_long_gap_splits_and_stays_unlinked():
    p = pd.concat([rows("OLDX", None, "2011-05-02", "2011-05-06"),
                   rows("OLDX", None, "2011-06-13", "2011-06-21"),           # 24-session gap, no ISIN
                   rows("FILLER", "INE000Z01010", "2011-05-02", "2011-12-30")])   # other stocks trade daily
    seg = segments(p)
    oldx = seg[seg["symbol"] == "OLDX"]
    assert len(oldx) == 2 and set(oldx["instrument_type"]) == {"UNKNOWN_NO_ISIN"}
    e, f = links(seg, src(), NO_CA)
    assert not set(oldx["segment_id"]) & (set(e["from_segment"]) | set(e["to_segment"]))


def test_isin_change_needs_ca_evidence_and_accepts_later_symbol_record():
    p = pd.concat([rows("SPLITCO", "INE444D01011", "2011-07-01", "2011-09-12"),
                   rows("SPLITCO", "INE444D01029", "2011-09-13", "2011-11-30"),
                   rows("RENAMED", "INE444D01029", "2011-12-01", "2011-12-30")])
    s = src([("SPLITCO", "RENAMED", "2011-12-01")])
    seg, e, f, ent = build(p, s)                                        # no CA record at all
    assert "ISIN_CHANGE_UNEXPLAINED" in set(f["flag"])
    assert len(eid(ent, "SPLITCO")) == 2                                # old ISIN segment separate
    ca = pd.DataFrame({"symbol": ["RENAMED"], "ex_date": [pd.Timestamp("2011-09-12")], "kind": ["SPLIT"],
                       "factor": [0.2], "subject": ["Face Value Split From Rs.10/- To Rs.2/-"]})
    seg, e, f, ent = build(p, s, ca)                                   # record filed under later symbol
    row = e[e["evidence"] == "ISIN_CHANGE_CA"]
    assert len(row) == 1 and "later symbol RENAMED" in row.iloc[0]["detail"]
    assert len(eid(ent, "SPLITCO") | eid(ent, "RENAMED")) == 1


def test_delisted_entities_retained_and_one_record_evidences_one_entity():
    p = pd.concat([rows("GONE", None, "2011-05-02", "2011-05-06"),
                   rows("GONE", None, "2011-06-13", "2011-06-21"),             # two unlinked pre-ISIN segments
                   rows("LIVE", "INE555E01015", "2011-05-02", "2011-12-30")])
    seg, e, f, ent = build(p, src())
    es = end_status(ent, src(delisted=[("GONE", "2011-08-01", "Compulsory Delisting")]), p["date"].max())
    gone = es[es["symbols"].apply(lambda s: "GONE" in s)]
    assert len(gone) == 2                                                 # both retained historically
    assert sorted(gone["end_status"]) == ["DELISTED_EVIDENCED", "ENDED_UNEXPLAINED"]
    assert gone.loc[gone["end_status"] == "DELISTED_EVIDENCED", "last"].iloc[0] == pd.Timestamp("2011-06-21")
    assert es.loc[es["symbols"].apply(lambda s: "LIVE" in s), "end_status"].iloc[0] == "ACTIVE_AT_CUTOFF"


def test_resolve_historical_resolves_only_with_evidence():
    p = pd.concat([rows("OLDCO", "INE000A01011", "2011-07-01", "2011-09-30"),
                   rows("NEWCO", "INE000A01011", "2011-10-03", "2011-12-30"),
                   rows("LATECO", "INE777F01017", "2011-11-01", "2011-12-30")])
    seg, e, f, ent = build(p, src([("OLDCO", "NEWCO", "2011-10-03")]))
    st, s = resolve_historical(ent, "NEWCO", "2011-08-15")
    assert st == "RESOLVED" and s["symbol"] == "OLDCO"
    assert resolve_historical(ent, "LATECO", "2011-08-15")[0] == "UNRESOLVED_NO_ENTITY_LISTED_AT_DATE"
    assert resolve_historical(ent, "NOPE", "2011-08-15")[0] == "UNRESOLVED_SYMBOL_NOT_IN_PANEL"


def test_fund_units_are_classified_not_removed():
    p = pd.concat([rows("GOLDETF", "INF204K01JK7", "2011-07-01", "2011-12-30"),
                   rows("CORP", "INE888G01018", "2011-07-01", "2011-12-30")])
    seg = segments(p)
    assert dict(zip(seg["symbol"], seg["instrument_type"])) == {"GOLDETF": "FUND_UNIT", "CORP": "EQUITY"}


def test_cutoff_enforced(tmp_path, monkeypatch):
    bad = pd.DataFrame({"date": [pd.Timestamp("2026-10-01")], "symbol": ["X"], "isin": ["INE1"]})
    with pytest.raises(ValueError, match="cutoff"):
        segments(bad)
    with pytest.raises(ValueError, match="cutoff"):
        resolve_historical(pd.DataFrame(columns=["symbol", "entity_id", "first", "last"]), "X", "2026-10-02")
    d = tmp_path / "lists"
    d.mkdir()
    (d / "x_symbolchange.csv").write_text("A co,OLD,NEW,01-JAN-2020\nB co,OLD2,NEW2,05-OCT-2026\n")
    (d / "x_namechange.csv").write_text("NCH_SYMBOL, NCH_PREV_NAME, NCH_NEW_NAME, NCH_DT\nNEW,a,b,01-JAN-2020\n")
    (d / "x_delisted.csv").write_text("Symbol,Company,Delisted Date,Type\nZ,Z Ltd,02-Oct-26,Voluntary\n")
    (d / "x_EQUITY_L.csv").write_text("SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE\n"
                                      "NEW,New,EQ,01-JAN-2000,1,1,INE1,1\nLATE,Late,EQ,01-OCT-2026,1,1,INE2,1\n")
    man = tmp_path / "manifest.jsonl"
    man.write_text("".join(json.dumps({"kind": "equities_list", "status": 200, "path": f"lists/x_{n}", "sha256": n}) + "\n"
                           for n in ("symbolchange.csv", "namechange.csv", "delisted.csv", "EQUITY_L.csv")))
    monkeypatch.setattr(idm, "MANIFEST", man)
    monkeypatch.setattr(idm, "BASE_DIR", tmp_path)
    s = idm.load_sources()
    assert list(s["symbol_changes"]["new"]) == ["NEW"] and s["delisted"].empty
    assert list(s["listed"]["symbol"]) == ["NEW"]
