"""Stage 2 PIT universe (UNIV-1) - adversarial tests on SYNTHETIC data (no holdout, no post-cutoff)."""

from pathlib import Path

import pandas as pd
import pytest

import src.stage2.universe as um
from src.stage2.identity import links, segments
from src.stage2.universe import build, selection_dates

SESS = pd.bdate_range("2011-06-22", "2012-06-29")
NO_CA = pd.DataFrame(columns=["symbol", "ex_date", "kind", "factor", "subject"])


def stock(symbol, isin, start=SESS[0], end=SESS[-1], value=1e7, extra=None):
    d = SESS[(SESS >= pd.Timestamp(start)) & (SESS <= pd.Timestamp(end))]
    df = pd.DataFrame({"date": d, "symbol": symbol, "isin": isin, "series": "EQ", "value": float(value)})
    for day, v in (extra or {}).items():
        df.loc[df["date"] == pd.Timestamp(day), "value"] = v
    return df


def run(panel, changes=(), top_n=2):
    sc = pd.DataFrame(list(changes), columns=["old", "new", "date"])
    sc["date"] = pd.to_datetime(sc["date"])
    seg = segments(panel[["date", "symbol", "isin"]])
    lk, _ = links(seg, {"symbol_changes": sc, "delisted": pd.DataFrame(columns=["symbol", "date", "type"])}, NO_CA)
    return build(panel, seg, lk, top_n=top_n)


BASE = [stock("AAA", "INE000A01011", value=3e7), stock("BBB", "INE000B01012", value=2e7),
        stock("CCC", "INE000C01013", value=1e7)]


def test_decision_on_t_identical_with_full_or_truncated_data():
    """Covers future delisting, future volume and future listings in one invariant."""
    full = pd.concat(BASE + [stock("AAA2", "INE000D01014", start="2012-03-01", value=9e9)])
    u_full = run(full)
    for t in selection_dates(full["date"])[:-1]:
        u_t = run(full[full["date"] <= t])
        a = u_full[u_full["selection_date"] == t].drop(columns="evidence_links").reset_index(drop=True)
        b = u_t[u_t["selection_date"] == t].drop(columns="evidence_links").reset_index(drop=True)
        pd.testing.assert_frame_equal(a, b)


def test_future_delisting_does_not_remove_prior_membership():
    p = pd.concat([stock("AAA", "INE000A01011", end="2012-01-31", value=9e7)] + BASE[1:])
    u = run(p)
    aaa = u[u["symbol_at_selection"] == "AAA"]
    assert (aaa[aaa["selection_date"] <= "2012-01-31"]["status"] == "MEMBER").all() and len(aaa) >= 4
    assert not len(u[(u["entity_id"].str.startswith("AAA")) & (u["selection_date"] > "2012-04-30")])


def test_future_high_volume_cannot_raise_past_liquidity():
    calm = pd.concat(BASE)
    spiky = pd.concat([stock("CCC", "INE000C01013", value=1e7,
                             extra={d: 1e12 for d in SESS[SESS >= "2012-04-02"]})] + BASE[:2])
    t = pd.Timestamp("2012-03-30")
    a = run(calm).query("selection_date == @t").set_index("entity_id")["liquidity_median_value"]
    b = run(spiky).query("selection_date == @t").set_index("entity_id")["liquidity_median_value"]
    pd.testing.assert_series_equal(a.sort_index(), b.sort_index())


def test_post_cutoff_row_refused():
    p = pd.concat(BASE + [pd.DataFrame({"date": [pd.Timestamp("2026-10-01")], "symbol": ["AAA"],
                                        "isin": ["INE000A01011"], "series": ["EQ"], "value": [1.0]})])
    with pytest.raises(ValueError, match="cutoff"):
        build(p, pd.DataFrame(columns=["segment_id", "first"]), pd.DataFrame(columns=["from_segment", "to_segment", "evidence"]))
    assert max(selection_dates(pd.bdate_range("2026-01-01", "2026-12-31"))) <= pd.Timestamp("2026-09-30")


def test_etf_never_enters_equity_universe():
    u = run(pd.concat(BASE + [stock("GOLDETF", "INF204K01JK7", value=9e12)]))
    etf = u[u["symbol_at_selection"] == "GOLDETF"]
    assert set(etf["status"]) == {"EXCLUDED"} and set(etf["reason"]) == {"FUND_UNIT"}


def test_future_symbol_not_used_before_its_effective_date():
    p = pd.concat([stock("OLDNAME", "INE000E01015", end="2012-02-14", value=9e7),
                   stock("NEWNAME", "INE000E01015", start="2012-02-15", value=9e7)] + BASE[1:])
    u = run(p, changes=[("OLDNAME", "NEWNAME", "2012-02-15")])
    before = u[(u["selection_date"] < "2012-02-15") & u["symbol_at_selection"].isin(["OLDNAME", "NEWNAME"])]
    after = u[(u["selection_date"] > "2012-02-15") & u["symbol_at_selection"].isin(["OLDNAME", "NEWNAME"])]
    assert set(before["symbol_at_selection"]) == {"OLDNAME"} and set(after["symbol_at_selection"]) == {"NEWNAME"}
    assert set(before["entity_id"]) == set(after["entity_id"]) == {"OLDNAME|INE000E01015|1"}
    assert not u["entity_id"].str.contains("NEWNAME").any()          # id never reveals the later symbol


def test_insufficient_history_then_eligible():
    u = run(pd.concat(BASE + [stock("NEWLIST", "INE000F01016", start="2012-01-16", value=9e9)]))
    n = u[u["symbol_at_selection"] == "NEWLIST"].set_index("selection_date")
    assert n.loc["2012-01-31", "reason"] == "INSUFFICIENT_HISTORY" and n.loc["2012-01-31", "valid_sessions"] < 50
    assert n.loc["2012-03-30", "status"] == "MEMBER" and n.loc["2012-03-30", "valid_sessions"] >= 50


def test_suspension_missing_value_and_not_traded_on_date():
    sus = stock("SUSP", "INE000G01017", value=9e9)
    sus = sus[~sus["date"].between("2012-02-01", "2012-02-29")]           # suspended all of Feb
    sus.loc[sus["date"].between("2012-01-02", "2012-01-31"), "value"] = float("nan")   # missing value
    u = run(pd.concat(BASE + [sus])).set_index(["symbol_at_selection", "selection_date"], drop=False)
    rows = u[u["entity_id"].str.startswith("SUSP")].set_index("selection_date")
    assert rows.loc["2012-02-29", "reason"] == "NOT_TRADED_ON_SELECTION_DATE"
    assert rows.loc["2012-03-30", "reason"] == "INSUFFICIENT_HISTORY"   # Jan missing + Feb suspended
    assert rows.loc["2011-12-30", "status"] == "MEMBER"


def test_ties_are_deterministic_and_top_n_respected():
    p = pd.concat([stock("ZZZ", "INE000H01018", value=5e7), stock("AAB", "INE000I01019", value=5e7)] + BASE)
    u = run(p, top_n=2)
    m = u[u["status"] == "MEMBER"]
    assert (m.groupby("selection_date").size() == 2).all()
    assert set(m["symbol_at_selection"]) == {"AAB", "ZZZ"}             # tie -> entity_id order, both above AAA


def test_no_current_nifty50_membership_can_leak():
    import ast
    src = Path(um.__file__).read_text()
    mods = {n.module for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom)}
    assert mods <= {"src.access", "src.config"}                      # no portfolio / frozen-universe import
    for name in ("frozen_universe", "NIFTY50_frozen", "ind_nifty50list", "NIFTY"):
        assert name not in src
    u = run(pd.concat(BASE))
    assert set(u["symbol_at_selection"].dropna()) <= {"AAA", "BBB", "CCC"}    # only what the panel shows
