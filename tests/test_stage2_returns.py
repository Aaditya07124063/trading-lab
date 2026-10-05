"""Stage 2 price/return methodology (RET-1). Synthetic data only - no holdout, nothing after the cutoff."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import src.stage2.returns as rm
from src.stage2.identity import links, segments
from src.stage2.returns import build

SESS = pd.bdate_range("2012-01-02", "2012-03-30")
NO_SC = {"symbol_changes": pd.DataFrame(columns=["old", "new", "date"]),
         "delisted": pd.DataFrame(columns=["symbol", "date", "type"])}


def stock(symbol, isin, closes, start="2012-01-02"):
    d = SESS[SESS >= pd.Timestamp(start)][:len(closes)]
    c = np.asarray(closes, float)
    return pd.DataFrame({"date": d, "symbol": symbol, "isin": isin, "series": "EQ", "open": c, "high": c,
                         "low": c, "close": c, "last": c, "prevclose": np.r_[np.nan, c[:-1]],
                         "volume": 100.0, "value": 1e6})


def events(*rows):
    e = pd.DataFrame(rows, columns=["symbol", "ex_date", "kind", "factor", "subject"])
    e["ex_date"] = pd.to_datetime(e["ex_date"])
    return e


NOEV = events()


def run(panel, ev=NOEV, sc=None):
    seg = segments(panel[["date", "symbol", "isin"]])
    src = NO_SC if sc is None else {**NO_SC, "symbol_changes": sc}
    lk, _ = links(seg, src, ev.assign(factor=ev["factor"]) if len(ev) else ev)
    return build(panel, seg, lk, ev)


def row(r, symbol, day):
    return r[(r["symbol"] == symbol) & (r["date"] == pd.Timestamp(day))].iloc[0]


def test_raw_prices_never_mutated():
    p = stock("AAA", "INE000A01011", [100, 101, 50.6, 51])
    before = p.copy()
    r = run(p, events(("AAA", SESS[2], "BONUS", 0.5, "Bonus 1:1")))
    pd.testing.assert_frame_equal(p, before)
    cols = ["open", "high", "low", "close", "last", "prevclose", "volume", "value"]
    pd.testing.assert_frame_equal(r[cols].reset_index(drop=True), p[cols].reset_index(drop=True))


def test_no_yahoo_anywhere_in_methodology():
    src = Path(rm.__file__).read_text().lower()
    assert "yfinance" not in src and "adj close" not in src and "auto_adjust" not in src


def test_no_adjustment_without_evidence():
    r = run(stock("AAA", "INE000A01011", [100, 101, 50.5, 51]))
    x = row(r, "AAA", SESS[2])
    assert x["return_status"] == "UNEXPLAINED_JUMP" and not x["research_grade"]
    assert np.isnan(x["ret_adj"]) and np.isnan(x["ret_research"]) and x["ret_raw"] == pytest.approx(-0.5, abs=0.01)


def test_validated_bonus_is_adjusted():
    r = run(stock("AAA", "INE000A01011", [100, 101, 50.6, 51]), events(("AAA", SESS[2], "BONUS", 0.5, "Bonus 1:1")))
    x = row(r, "AAA", SESS[2])
    assert x["return_status"] == "ADJUSTED_VALIDATED" and x["research_grade"]
    assert x["ret_research"] == pytest.approx(50.6 / (101 * 0.5) - 1)


@pytest.mark.parametrize("closes, ev, status", [
    ([100, 101, 99.0, 99], ("BONUS", 10 / 11, "Bonus 1:10"), "EVENT_INCONCLUSIVE"),
    ([100, 101, 100.5, 100], ("BONUS", 0.5, "Bonus 1:1"), "EVENT_DISCREPANT"),
    ([100, 101, 90.0, 91], ("RIGHTS", np.nan, "Rights 1:5 @ Premium Rs 50"), "EVENT_UNADJUSTABLE"),
    ([100, 101, 60.0, 61], ("OTHER", np.nan, "Demerger"), "EVENT_UNADJUSTABLE"),
    ([100, 101, 60.0, 61], ("UNPARSED_BONUS_SPLIT", np.nan, "Split Us 64 Into 2 Parts"), "EVENT_UNADJUSTABLE"),
])
def test_unresolved_events_stay_unresolved(closes, ev, status):
    r = run(stock("AAA", "INE000A01011", closes), events(("AAA", SESS[2], *ev)))
    x = row(r, "AAA", SESS[2])
    assert x["return_status"] == status and not x["research_grade"] and np.isnan(x["ret_research"])
    assert np.isnan(x["ret_adj"])                     # no adjustment is ever produced without validation


def test_dividend_flagged_but_price_return_kept():
    r = run(stock("AAA", "INE000A01011", [100, 101, 99, 99]), events(("AAA", SESS[2], "DIVIDEND", np.nan, "Dividend - Rs 2")))
    x = row(r, "AAA", SESS[2])
    assert x["return_status"] == "OK" and x["dividend_exdate"] and x["ret_research"] == pytest.approx(99 / 101 - 1)


def test_identity_transition_and_record_under_later_symbol():
    p = pd.concat([stock("OLDCO", "INE000B01012", [100, 101, 102]),
                   stock("NEWCO", "INE000B01012", [51.2, 52], start=SESS[3])])
    sc = pd.DataFrame({"old": ["OLDCO"], "new": ["NEWCO"], "date": [SESS[3]]})
    r = run(p, events(("NEWCO", SESS[3], "SPLIT", 0.5, "Face Value Split From Rs 10 To Rs 5")), sc)
    x = row(r, "NEWCO", SESS[3])
    assert x["identity_transition"] and x["entity_id"].startswith("OLDCO")
    assert x["return_status"] == "ADJUSTED_VALIDATED" and x["ret_research"] == pytest.approx(51.2 / 51 - 1)


def test_unexplained_isin_change_starts_a_new_entity():
    p = pd.concat([stock("CHG", "INE000C01013", [100, 101, 102]),
                   stock("CHG", "INE000C01021", [20.5, 21], start=SESS[3])])
    r = run(p)
    x = row(r, "CHG", SESS[3])
    assert x["return_status"] == "FIRST_OBSERVATION" and r["entity_id"].nunique() == 2


def test_delisting_and_relisting_gap():
    a = stock("REL", "INE000D01014", [100, 101, 102])
    b = stock("REL", "INE000D01014", [104, 105], start=SESS[20])        # same ISIN returns after a gap
    r = run(pd.concat([a, b, stock("OTHER", "INE000E01015", list(range(100, 160)))]))
    x = row(r, "REL", SESS[20])
    assert x["return_status"] == "MULTI_SESSION_GAP" and not x["research_grade"] and x["gap_sessions"] == 17
    assert r[r["symbol"] == "REL"]["date"].max() == SESS[21]             # nothing after its last row


def test_missing_price():
    p = stock("AAA", "INE000A01011", [100, 101, 102])
    p.loc[p.index[1], "close"] = np.nan
    r = run(p)
    assert set(r[r["symbol"] == "AAA"]["return_status"].iloc[1:]) == {"MISSING_PRICE"}


def test_cutoff_and_verified_start():
    p = stock("AAA", "INE000A01011", [100, 101])
    late = p.assign(date=pd.to_datetime(["2026-09-30", "2026-10-01"]))
    with pytest.raises(ValueError, match="cutoff"):
        build(late, pd.DataFrame(columns=["segment_id", "symbol", "first"]),
              pd.DataFrame(columns=["from_segment", "to_segment", "evidence"]), NOEV)
    early = p.assign(date=pd.to_datetime(["2011-06-21", "2011-06-22"]))
    seg = segments(early[["date", "symbol", "isin"]])
    r = build(early, seg, pd.DataFrame(columns=["from_segment", "to_segment", "evidence"]), NOEV)
    assert r["date"].min() == pd.Timestamp("2011-06-22")


# ------------------------------------------------------------- RET-1.1 (Phase 2.1)

def run11(panel, ev=NOEV, special=()):
    seg = segments(panel[["date", "symbol", "isin"]])
    lk, _ = links(seg, NO_SC, ev)
    return build(panel, seg, lk, ev, special_sessions=pd.to_datetime(list(special)), large_residual=rm.LARGE_RESIDUAL)


def test_validated_adjustment_with_large_residual_is_flagged_not_research_grade():
    # bonus 1:1 validates (raw 0.56 vs factor 0.5) but leaves an adjusted move of +12% > 10%
    p = stock("AAA", "INE000A01011", [100, 100, 56.0, 56])
    ev = events(("AAA", SESS[2], "BONUS", 0.5, "Bonus 1:1"))
    x = row(run11(p, ev), "AAA", SESS[2])
    assert x["return_status"] == "VALIDATED_LARGE_RESIDUAL" and not x["research_grade"]
    assert x["ret_adj"] == pytest.approx(0.12) and np.isnan(x["ret_research"]) and x["close"] == 56.0
    assert row(run(p, ev), "AAA", SESS[2])["return_status"] == "ADJUSTED_VALIDATED"          # RET-1 unchanged
    small = row(run11(stock("AAA", "INE000A01011", [100, 100, 52.0, 52]), ev), "AAA", SESS[2])   # +4%: clean
    assert small["return_status"] == "ADJUSTED_VALIDATED" and small["research_grade"]


def test_return_spanning_a_special_session_is_flagged():
    p = stock("AAA", "INE000A01011", [100, 101, 102, 103, 104, 105, 106])      # Mon 2012-01-02 ...
    sat = pd.Timestamp("2012-01-07")                                             # special Saturday session
    r = run11(p, special=[sat])
    x = row(r, "AAA", "2012-01-09")                                              # Fri -> Mon spans Saturday
    assert x["return_status"] == "SPECIAL_SESSION_SPAN" and not x["research_grade"] and x["spans_special_session"]
    assert r.loc[r["date"] != pd.Timestamp("2012-01-09"), "return_status"].isin(["OK", "FIRST_OBSERVATION"]).all()
    assert (r["date"] != sat).all()                                              # never a return endpoint
    assert row(run(p), "AAA", "2012-01-09")["return_status"] == "OK"             # RET-1 unchanged
    assert "spans_special_session" not in run(p).columns and set(run(p)["methodology"]) == {"RET-1"}
    assert set(r["methodology"]) == {"RET-1.1"}
