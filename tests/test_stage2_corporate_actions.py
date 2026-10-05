"""Stage 2 corporate-action evidence layer (CA-2). Synthetic data only."""

import io
import json
import zipfile

import pandas as pd
import pytest

import src.stage2.corporate_actions as ca
from src.stage2.corporate_actions import classify, combined_events, parse_subject, unexplained_jumps, validate


# ------------------------------------------------------------------ parsing

@pytest.mark.parametrize("subject, kind, factor", [
    ("Bonus 1:1", "BONUS", 0.5),
    ("Bonus 1:2", "BONUS", 2 / 3),                     # 1 new for every 2 held
    ("Bonus 3:2", "BONUS", 2 / 5),
    ("Bonus Issue 1 : 1", "BONUS", 0.5),
    ("Div-Rs.4.20 Pr Sh/Bon 1:1", "BONUS", 0.5),
    ("Bonus 1:1 /Dividend- Rs 29 Per Share", "BONUS", 0.5),
    ("Face Value Split (Sub-Division) - From Rs 2 Per Share To Rs 1 Per Share", "SPLIT", 0.5),
    ("Face Value Split From Rs.10/- To Rs.2/-", "SPLIT", 0.2),
    ("FV SPLIT RS.10/- TO RE.1/", "SPLIT", 0.1),
    ("Split-Rs.10tors.2/Div-60%Purpose Revised", "SPLIT", 0.2),
    ("Fv Spl-Rs10tors2/Bon-1:2", "BONUS+SPLIT", 0.2 * 2 / 3),
    ("Bonus 1:1 / Face Value Split From 10/- To Face Value 2/-", "BONUS+SPLIT", 0.1),
])
def test_parse_adjusting_subjects(subject, kind, factor):
    k, f, _ = parse_subject(subject)
    assert k == kind and f == pytest.approx(factor)


@pytest.mark.parametrize("subject, kind", [
    ("Agm/Div Fin-10% + Spl-5%", "DIVIDEND"),          # "spl" = special dividend, not split
    ("Spl Int Div-30%", "DIVIDEND"),
    ("Agm/Spl/Bon-1:1/Div-20%", "UNPARSED_BONUS_SPLIT"),   # split mentioned without a ratio
    ("Agm/Div-20%/Spl Rs10-Rs2", "UNPARSED_BONUS_SPLIT"),
    ("Split Us 64 Into 2 Parts", "UNPARSED_BONUS_SPLIT"),  # "into" is not "to"
    ("Scheme of Arrangement - Bonus Debentures 1:1", "NON_EQUITY_BONUS"),
    ("Sch Of Agmt- Bonus Deb1:1", "NON_EQUITY_BONUS"),
    ("Rights 1:15 @ Premium Rs 1247", "RIGHTS"),
    ("Face Value Consolidation From Rs 1 To Rs 10", "CONSOLIDATION"),
    ("Demerger", "OTHER"),
])
def test_non_adjusting_or_ambiguous_subjects_are_never_adjusted(subject, kind):
    k, f, _ = parse_subject(subject)
    assert k == kind and f is None


# ----------------------------------------------------------- classification

def test_classify():
    assert classify(0.502, 0.5) == "VALIDATED"
    assert classify(0.98, 1 / 1.1) == "INCONCLUSIVE"         # 1:10 bonus: within normal volatility
    assert classify(1.0, 0.5) == "DISCREPANT"                # factor says halve, price did not
    assert classify(0.25, 0.5) == "DISCREPANT"


def test_same_day_records_are_combined():
    ev = pd.DataFrame({"symbol": ["X", "X", "Y"], "ex_date": pd.to_datetime(["2020-01-10"] * 2 + ["2020-01-10"]),
                       "kind": ["SPLIT", "BONUS", "BONUS"], "factor": [0.5, 2 / 3, 0.5],
                       "subject": ["split", "bonus", "bonus"]})
    c = combined_events(ev).set_index("symbol")
    assert c.loc["X", "factor"] == pytest.approx(1 / 3) and c.loc["X", "n_records"] == 2
    assert c.loc["Y", "factor"] == 0.5


# --------------------------------------------------- validation vs prices

def _panel(symbol, closes, start="2020-01-06", prevclose=None):
    d = pd.bdate_range(start, periods=len(closes))
    pc = prevclose or [None] + closes[:-1]
    return pd.DataFrame({"date": d, "symbol": symbol, "close": closes, "prevclose": pc})


def _ev(symbol, ex, factor, kind="BONUS"):
    return pd.DataFrame({"symbol": [symbol], "ex_date": [pd.Timestamp(ex)], "kind": [kind],
                         "factor": [factor], "subject": [kind]})


def test_validate_bonus_and_prevclose_convention():
    p = _panel("A", [100.0, 101.0, 50.4, 50.6])                        # ex-date = 3rd session
    v = validate(_ev("A", "2020-01-08", 0.5), p).iloc[0]
    assert v.status == "VALIDATED" and v.prevclose_convention == "UNADJUSTED"
    assert v.raw_ratio == pytest.approx(50.4 / 101.0)
    p2 = _panel("A", [100.0, 101.0, 50.4], prevclose=[None, 100.0, 50.5])  # NSE base adjusted
    assert validate(_ev("A", "2020-01-08", 0.5), p2).iloc[0].prevclose_convention == "ADJUSTED"


def test_validate_flags_but_never_changes_prices():
    p = _panel("A", [100.0, 101.0, 100.5, 100.7])                      # no visible halving
    before = p.copy()
    v = validate(_ev("A", "2020-01-08", 0.5), p).iloc[0]
    assert v.status == "DISCREPANT"
    pd.testing.assert_frame_equal(p, before)


def test_validate_no_price_reasons_and_pre_2006_excluded():
    p = _panel("A", [100.0, 101.0])
    ev = pd.concat([_ev("A", "2020-01-02", 0.5),        # before first session
                    _ev("A", "2020-03-02", 0.5),        # nothing within 10 days after
                    _ev("ZZ", "2020-01-08", 0.5),       # symbol absent
                    _ev("A", "2005-06-01", 0.5)])       # pre-2006: not validated/adjusted
    s = set(validate(ev, p).status)
    assert s == {"NO_PRICES:NO_SESSION_BEFORE_EX", "NO_PRICES:NO_SESSION_AFTER_EX",
                 "NO_PRICES:SYMBOL_NOT_IN_PANEL"}


def test_unexplained_jumps():
    p = pd.concat([_panel("A", [100.0, 101.0, 50.0, 50.0]), _panel("B", [100.0, 100.0, 30.0, 30.0])])
    j = unexplained_jumps(p, _ev("A", "2020-01-08", 0.5)).set_index("symbol")
    assert bool(j.loc["A", "explained"]) and not bool(j.loc["B", "explained"])


# ------------------------------------------------ cutoff / source handling

def test_load_events_drops_post_cutoff_and_non_eq(tmp_path, monkeypatch):
    raw = tmp_path / "ca.json"
    raw.write_text(json.dumps([
        {"symbol": "A", "series": "EQ", "isin": "INE1", "comp": "A", "subject": "Bonus 1:1", "exDate": "10-Jan-2020",
         "recDate": "-", "faceVal": "10"},
        {"symbol": "A", "series": "EQ", "isin": "INE1", "comp": "A", "subject": "Bonus 1:1", "exDate": "05-Oct-2026",
         "recDate": "-", "faceVal": "10"},
        {"symbol": "B", "series": "GS", "isin": "INE2", "comp": "B", "subject": "Bonus 1:1", "exDate": "10-Jan-2020",
         "recDate": "-", "faceVal": "10"}]))
    man = tmp_path / "manifest.jsonl"
    man.write_text(json.dumps({"kind": "corp_actions", "status": 200, "path": "ca.json", "sha256": "x"}) + "\n")
    monkeypatch.setattr(ca, "MANIFEST", man)
    monkeypatch.setattr(ca, "BASE_DIR", tmp_path)
    ev = ca.load_events()
    assert list(ev.symbol) == ["A"] and ev.ex_date.max() <= pd.Timestamp("2026-09-30")


def test_panel_parser_refuses_post_cutoff_session():
    from src.stage2.panel import parse
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x.csv", "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP\n"
                            "A,EQ,1,1,1,1,1,1,1,1,01-OCT-2026\n")
    with pytest.raises(ValueError, match="cutoff"):
        parse(buf.getvalue(), "legacy_cm", "2026-10-01")
