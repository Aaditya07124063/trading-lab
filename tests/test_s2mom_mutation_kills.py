"""F-04: tests written to FAIL when a research-critical rule is broken, even if every file hash is valid.

Part 1 is a small hand-built golden world: one holding month, 14 stocks, a handful of non-zero
returns placed exactly on the boundaries the protocol defines. Every expected number below is
written out as arithmetic from the protocol rule (not copied from the code's output).
Parts 2-6 pin statistics, decision labels, runner gates, loader hash checks, Stage 2 rules and
step E rate rules that the 2026-10-07 mutation campaign showed to be untested.
SYNTHETIC DATA ONLY, except where a test says it reads a saved registered artifact (read-only).

Mutation matrix: docs/audit/MUTATION_FINAL_REPORT.md (mutation -> invariant -> test here -> result).
"""

import copy
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import src.stage2.returns as RT
import src.stage2.universe as UM
import src.stage3.protocol as P
from src.intraday.inference import stationary_bootstrap_means
from src.stage2.corporate_actions import classify
from src.stage3 import data, experiment, ladder as L, stats, step_e
from tests import test_stage2_returns as t_ret
from tests import test_stage2_universe as t_univ
from tests.test_s2mom_step_e import S as SCHEDULE, holdings
from tests.test_stage3_infra import inputs, schedule

ROOT = Path(__file__).resolve().parents[1]

# =================================================================== 1. golden ladder world
DAYS = pd.bdate_range("2012-01-02", "2013-04-30")
D = pd.Timestamp
T, M12, M1, S_PLUS, S_PP = D("2013-01-31"), D("2012-01-31"), D("2012-12-31"), D("2013-02-01"), D("2013-03-01")
FORM = D("2012-06-15")                                  # one formation-window day carries each stock's score
SCORE = {"E0": .50, "E1": .40, "E2": .30, "E3": .30, "E4": .20, "E5": .10, "E6": -.10, "E7": -.10, "E8": -.20,
         "E9": -.30, "E10": -.50, "D1": -.60, "V1": .60, "S1": .05}
LAST_ROW = {"D1": D("2013-02-20"), "V1": D("2013-02-20")}        # delisted: no row ever again
# (entity, date) -> (r_naive, r_rg, r_raw, cls). Everything else is a flat 0% research-grade day.
SPECIAL = {
    # ---- traps on the window boundaries: none of these may enter a formation score or a holding return
    ("E5", M12): (5.0, 5.0, 5.0, "OK"),                 # ON m(12): the window starts the session after
    ("E6", D("2013-01-15")): (5.0, 5.0, 5.0, "OK"),     # in the skip month
    ("E4", S_PLUS): (5.0, 5.0, 5.0, "OK"),              # ON the entry session: bought at its close
    ("E3", D("2013-03-04")): (5.0, 5.0, 5.0, "OK"),     # the session AFTER the exit session
    # ---- flagged rows
    ("E5", D("2012-08-10")): (0.0, np.nan, 0.0, "BAD"),             # flagged row inside formation -> not rankable in D
    ("S1", D("2012-09-10")): (3.0, np.nan, 3.0, "SPAN"),            # special-session span: counted by NAIVE, excluded by RG
    ("E0", D("2013-02-15")): (0.10, np.nan, 0.10, "BAD"),           # flagged holding day -> §20(b) neutral fill in D
    ("E1", D("2013-02-25")): (0.02, 0.02, -0.49, "OK"),             # validated 1:1 bonus: raw -49%, adjusted +2%
    # ---- ordinary holding-month returns
    ("E1", D("2013-02-15")): (0.03, 0.03, 0.03, "OK"),
    ("E1", S_PP): (0.06, 0.06, 0.06, "OK"),                         # ON the exit session: must be included
    ("E6", D("2013-02-20")): (0.01, 0.01, 0.01, "OK"),
    ("E7", D("2013-02-20")): (-0.04, -0.04, -0.04, "OK"),
    ("E8", D("2013-02-20")): (0.02, 0.02, 0.02, "OK"),
    ("E10", D("2013-02-20")): (-0.10, -0.10, -0.10, "OK"),
    ("S1", D("2013-02-20")): (0.07, 0.07, 0.07, "OK"),
    ("D1", D("2013-02-18")): (-0.05, -0.05, -0.05, "OK"),
}
UNIVERSE = {"A": ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9"],
            "B": ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E10"],
            "C": ["E0", "E1", "E2", "E3", "S1", "E5", "E6", "E7", "V1", "D1"]}
E1_HOLD = 1.03 * 1.02 * 1.06 - 1                        # three research-grade days, compounded
D1_HOLD = 0.95 * (1 - 0.30) - 1                         # -5%, then the §22 delisting return of -30%


def golden_panel(special=SPECIAL):
    rows = []
    for e, score in SCORE.items():
        for n, d in enumerate(DAYS):
            if d > LAST_ROW.get(e, DAYS[-1]):
                break
            naive, rg, raw, cls = special.get((e, d), (score,) * 3 + ("OK",) if d == FORM else (0.0, 0.0, 0.0, "OK"))
            if n == 0:
                naive, rg, raw, cls = np.nan, np.nan, np.nan, "FIRST"
            rows.append({"date": d, "entity": e, "r_naive": naive, "r_rg": rg, "r_raw": raw, "cls": cls, "raw_ok": cls == "OK"})
    return pd.DataFrame(rows)


def golden(special=SPECIAL, specs=L.STEP_SPECS, **kw):
    w = L.wide(golden_panel(special), list(SCORE), DAYS)
    cal = L.calendar(DAYS, T, T, T)
    univ = {(k, T): pd.DataFrame({"entity": v, "rank": np.arange(1.0, len(v) + 1)}) for k, v in UNIVERSE.items()}
    delist = np.array([0.0 if e == "V1" else -0.30 for e in w.ents])            # V1 voluntary, everything else OTHER
    monthly, hold = L.run_ladder(w, cal, univ, specs, delist, **kw)
    return monthly.set_index("step"), hold, cal


def test_golden_calendar_is_the_12_1_window_with_delayed_entry_and_exit():
    c = L.calendar(DAYS, T, T, T).iloc[0]
    assert (c.t, c.m12, c.m1, c.s_plus, c.s_pp) == (T, M12, M1, S_PLUS, S_PP) and c.holding_month == "2013-02"


def test_golden_ranking_window_30pct_selection_and_tie_breaks():
    """Invariants 6-8: only (m12, m1] is ranked; k = floor(0.30 n + 0.5); ties by entity ascending."""
    m, hold, _ = golden()
    assert hold[("A", T)]["W"] == ["E0", "E1", "E2"]            # E2 and E3 tie at +30%: E2 first
    assert hold[("A", T)]["L"] == ["E7", "E8", "E9"]            # E6 and E7 tie at -10%: E7 is the worse rank
    assert hold[("A", T)]["order"] == ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9"]   # no boundary trap moved a stock
    assert hold[("B", T)]["W"] == ["E0", "E1", "E2"] and hold[("B", T)]["L"] == ["E7", "E8", "E10"]
    assert hold[("C", T)]["W"] == ["S1", "V1", "E0"] and hold[("C", T)]["L"] == ["E6", "E7", "D1"]   # NAIVE counts the span day: S1 = 1.05*4-1
    assert hold[("D", T)]["W"] == ["V1", "E0", "E1"] and hold[("D", T)]["L"] == ["E6", "E7", "D1"]   # RG: span excluded, S1 = +5%
    assert m["n_rankable"].to_dict() == {"A": 10, "B": 10, "C": 10, "D": 9}                          # E5 flagged in formation: out of D
    assert (m["k"] == 3).all() and (m["n_universe"] == 10).all() and (m["status"] == "OK").all()
    assert hold[("D", T)]["BM"] == ["D1", "E0", "E1", "E2", "E3", "E6", "E7", "S1", "V1"]
    assert hold[("A", T)]["BM"] == sorted(UNIVERSE["A"])


def test_golden_monthly_returns_of_every_step_by_hand():
    """Invariants 1-5, 9-14: equal weights, holding window (s_plus, s_pp], WML = W - L, the step D return
    rule, the benchmark, the A/B/C/D differences, delisting and flagged-day treatment."""
    m, _, _ = golden()
    w_a = (0.10 + E1_HOLD + 0.0) / 3
    l_a = (-0.04 + 0.02 + 0.0) / 3
    assert m.at["A", "W"] == pytest.approx(w_a, abs=1e-12) and m.at["A", "L"] == pytest.approx(l_a, abs=1e-12)
    assert m.at["A", "BM"] == pytest.approx((0.10 + E1_HOLD + 0.01 - 0.04 + 0.02) / 10, abs=1e-12)
    l_b = (-0.04 + 0.02 - 0.10) / 3
    assert m.at["B", "W"] == pytest.approx(w_a, abs=1e-12) and m.at["B", "L"] == pytest.approx(l_b, abs=1e-12)
    w_c = (0.07 + 0.0 + 0.10) / 3                                   # V1 delists voluntarily: 0%
    l_c = (0.01 - 0.04 + D1_HOLD) / 3                               # D1 delists otherwise: -30% on top of -5%
    assert m.at["C", "W"] == pytest.approx(w_c, abs=1e-12) and m.at["C", "L"] == pytest.approx(l_c, abs=1e-12)
    assert m.at["C", "BM"] == pytest.approx((0.10 + E1_HOLD + 0.07 + 0.01 - 0.04 + 0.0 + D1_HOLD) / 10, abs=1e-12)
    e0_fill_w = (0.0 + 0.03) / 2                                    # §20(b): mean of the OTHER W stocks that day (V1, E1)
    w_d = (0.0 + e0_fill_w + E1_HOLD) / 3
    assert m.at["D", "W"] == pytest.approx(w_d, abs=1e-12) and m.at["D", "L"] == pytest.approx(l_c, abs=1e-12)
    e0_fill_bm = 0.03 / 8                                           # in the benchmark the other 8 stocks define the fill
    assert m.at["D", "BM"] == pytest.approx((D1_HOLD + e0_fill_bm + E1_HOLD + 0.01 - 0.04 + 0.07) / 9, abs=1e-12)
    for s, (w_, l_) in {"A": (w_a, l_a), "B": (w_a, l_b), "C": (w_c, l_c), "D": (w_d, l_c)}.items():
        assert m.at[s, "WML"] == pytest.approx(w_ - l_, abs=1e-12)                  # WML = W - L ...
        assert abs(m.at[s, "WML"] - (w_ + l_)) > 1e-3                               # ... and never W + L
    assert len({round(m.at[s, "WML"], 10) for s in "ABCD"}) == 4                    # the four steps really differ
    assert m.at["D", "W_filled_stock_days"] == 1 and m.at["D", "W_delisting_return_applied"] == 1
    assert m.at["C", "L_delisting_return_applied"] == 1 and "L_delisting_return_applied" not in m.columns[m.loc["A"].notna()]


def test_golden_delta_is_wml_a_minus_wml_d_in_percent():
    m, _, cal = golden()
    d = L.paired_delta(m.reset_index(), cal)
    want = ((0.10 + E1_HOLD) / 3 - (-0.02) / 3) - ((0.015 + E1_HOLD) / 3 - (0.01 - 0.04 + D1_HOLD) / 3)
    assert d["paired"].all() and d["delta"].iloc[0] == pytest.approx(want * 100, abs=1e-10)
    assert d["delta"].iloc[0] < 0                                   # sign: here the corrected step D shows MORE momentum than A


@pytest.mark.parametrize("key, value, what", [
    (("E1", S_PP), (0.0, 0.0, 0.0, "OK"), "exit-session return (holding window is inclusive of s_pp)"),
    (("E1", D("2013-02-25")), (0.02, 0.02, 0.02, "OK"), None),              # control: raw == adjusted changes nothing
    (("E0", D("2013-02-15")), (0.10, 0.10, 0.10, "OK"), "flagged day treated as research-grade"),
    (("E4", S_PLUS), (0.0, 0.0, 0.0, "OK"), None),                          # control: the entry-session return is never used
    (("E3", D("2013-03-04")), (0.0, 0.0, 0.0, "OK"), None),                 # control: nor is anything after the exit
    (("E6", D("2013-01-15")), (0.0, 0.0, 0.0, "OK"), None),                 # control: nor the skip month
    (("E5", M12), (0.0, 0.0, 0.0, "OK"), None),                             # control: nor the m(12) session itself
])
def test_golden_sensitivity_of_step_d_to_each_boundary(key, value, what):
    """Changing a return that the protocol says is used must move step D; one it says is unused must not."""
    base, _, _ = golden()
    alt, _, _ = golden({**SPECIAL, key: value})
    moved = not np.allclose(base.loc["D", ["W", "L", "BM"]].astype(float), alt.loc["D", ["W", "L", "BM"]].astype(float), atol=1e-12)
    assert moved == (what is not None), what or f"{key} must not influence step D"


def test_golden_step_d_uses_research_returns_never_raw():
    """Invariant 4. E1's bonus day: raw -49%, research-grade +2%. Step D must book +2%."""
    m, hold, _ = golden()
    assert hold[("D", T)]["W_end"]["E1"] * 3 * (1 + m.at["D", "W"]) == pytest.approx(1 + E1_HOLD, abs=1e-12)
    raw_e1 = 1.03 * (1 - 0.49) * 1.06 - 1
    assert abs(m.at["D", "W"] - (0.0 + 0.015 + raw_e1) / 3) > 0.1
    w = L.wide(golden_panel(), list(SCORE), DAYS)
    j, i = w.ents.get_loc("S1"), w.days.get_loc(D("2012-09-10"))
    assert w.lr[i, j] == 0.0 and w.ln[i, j] == pytest.approx(math.log(4.0)) and w.span[i, j] and not w.ok[i, j]
    j, i = w.ents.get_loc("E0"), w.days.get_loc(D("2013-02-15"))
    assert w.lr[i, j] == 0.0 and w.bad[i, j] and not w.ok[i, j]                    # a flagged row contributes no RG return


def test_golden_delisting_rule_only_from_step_c_and_by_class():
    """Invariant 13: -30% (other) / 0% (voluntary) in C and D; in A/B a vanished stock is simply carried."""
    specs = {"A_with_C_universe": ("A", "NAIVE")}
    univ_swap = dict(UNIVERSE)
    try:
        UNIVERSE["A"] = UNIVERSE["C"]
        m, _, _ = golden(specs=specs)
    finally:
        UNIVERSE.update(univ_swap)
    assert m.at["A_with_C_universe", "L"] == pytest.approx((0.01 - 0.04 + (0.95 - 1)) / 3, abs=1e-12)   # no delisting return
    assert P.DELIST_RETURN == {"VOLUNTARY": 0.0, "OTHER": -0.30}


def test_missing_price_in_the_panel_stops_the_run():
    """Invariant 14 / protocol B1.2: a missing price is never skipped or filled."""
    bad = golden_panel()
    bad.loc[(bad["entity"] == "E2") & (bad["date"] == D("2012-07-02")), "r_naive"] = np.nan
    with pytest.raises(ValueError, match="missing price in the panel"):
        L.wide(bad, list(SCORE), DAYS)
    L.wide(golden_panel(), list(SCORE), DAYS)                       # FIRST rows may be NaN


def test_no_rankable_stock_and_no_row_behaviour():
    """Invariant 10: a universe with nothing to rank is recorded with its reason, never as a zero return."""
    w = L.wide(golden_panel(), list(SCORE), DAYS)
    cal = L.calendar(DAYS, T, T, T)
    univ = {(k, T): pd.DataFrame({"entity": ["E0"], "rank": [1.0]}) for k in "ABC"}
    m, _ = L.run_ladder(w, cal, univ, L.STEP_SPECS)
    assert (m["status"] == "NO_RANKABLE_STOCKS").all() and "WML" not in m.columns
    d = L.paired_delta(m, cal)
    assert not d["paired"].any() and d["delta"].isna().all() and d["reason"].iloc[0] == "A:NO_RANKABLE_STOCKS D:NO_RANKABLE_STOCKS"
    with pytest.raises(ValueError, match="missing from the panel"):
        L.run_ladder(w, cal, {(k, T): pd.DataFrame({"entity": ["NOPE"], "rank": [1.0]}) for k in "ABC"}, L.STEP_SPECS)


# =================================================================== 2. statistics (§15)
def nw_by_hand(x, lag):
    n, mean = len(x), sum(x) / len(x)
    d = [v - mean for v in x]
    lrv = sum(v * v for v in d) / n
    for k in range(1, lag + 1):
        lrv += 2 * (1 - k / (lag + 1)) * sum(d[i] * d[i - k] for i in range(k, n)) / n
    return mean, math.sqrt(lrv / n)


@pytest.mark.parametrize("lag", [0, 1, 3, 4])
def test_newey_west_test_by_hand_is_two_sided_and_lag_sensitive(lag):
    """Invariants 15-16: Bartlett weights, division by n, two-sided normal p-value."""
    x = [0.8, -0.3, 1.1, 0.2, -0.9, 1.4, 0.5, -0.1, 0.7, 0.9, -0.4, 0.6]
    mean, se = nw_by_hand(x, lag)
    r = stats.mean_test(x, lag)
    assert r["mean"] == pytest.approx(mean, abs=1e-14) and r["se_nw"] == pytest.approx(se, abs=1e-14) and r["lag"] == lag
    assert r["p_two_sided"] == pytest.approx(math.erfc(abs(mean / se) / math.sqrt(2)), abs=1e-14)      # = 2 * (1 - Phi(|t|))
    assert stats.mean_test([-v for v in x], lag)["p_two_sided"] == pytest.approx(r["p_two_sided"], abs=1e-14)   # direction-free
    assert r["ci90"][0] == pytest.approx(mean - 1.6448536269514722 * se, abs=1e-12)
    if lag:
        assert stats.mean_test(x, lag)["se_nw"] != stats.mean_test(x, lag - 1)["se_nw"]


def test_frozen_lags_equal_the_protocol_formula_for_the_registered_sample_sizes():
    for sample, n in (("PRIMARY", 114), ("OOS", 56)):
        assert P.NW_LAG[sample] == math.floor(4 * (n / 100) ** (2 / 9))
    for mode, n in (("primary", 114), ("confirmation", 56)):                       # saved registered artifact, read-only
        h1 = json.loads((ROOT / f"results/s2_mom_v1/{mode}_results.json").read_text())["H1"]
        assert h1["n"] == n and h1["lag"] == math.floor(4 * (n / 100) ** (2 / 9)) and h1["distribution"] == "NORMAL"


def test_bootstrap_p_value_counts_both_tails():
    """Invariant 17: p = (1 + #{|mean* - xbar| >= |xbar|}) / (B + 1). A one-tailed count would be about half."""
    x = np.random.default_rng(3).normal(0.15, 1.0, 90)
    r = stats.bootstrap_test(x, 11, 4000)
    dev = stationary_bootstrap_means(x, r["block_length"], 4000, 11) - x.mean()
    upper, lower = int((dev >= abs(x.mean())).sum()), int((dev <= -abs(x.mean())).sum())
    assert upper > 20 and lower > 20                                # both tails are populated in this example
    assert r["p_two_sided"] == (1 + upper + lower) / 4001
    assert r["p_two_sided"] > 1.5 * (1 + upper) / 4001              # clearly not the one-tailed value
    assert stats.bootstrap_test(-x, 11, 4000)["B"] == 4000


def test_bootstrap_seed_and_configuration_are_the_registered_ones():
    """Invariant 18. Constants, and the saved registered artifacts (read-only) that carry them."""
    assert P.BOOTSTRAP_SEED == 20261005 and P.BOOTSTRAP_RESAMPLES == 10_000 and P.RESOLVED_DECISIONS["bootstrap_seed"] == 20261005
    for mode in ("primary", "confirmation"):
        b = json.loads((ROOT / f"results/s2_mom_v1/{mode}_results.json").read_text())["H1_bootstrap"]
        assert (b["B"], b["seed"]) == (10_000, 20261005) and b["block_length"] >= 1
    x = np.random.default_rng(1).normal(0, 1, 60)
    assert stats.bootstrap_test(x, 1, 500) != stats.bootstrap_test(x, 2, 500)       # the seed matters
    assert stats.bootstrap_test(x, 1, 500) == stats.bootstrap_test(x, 1, 500)       # and fixes the result


# =================================================================== 3. decision labels (§27, §14)
def h1_label(p, lo, hi, alpha=0.05, thr=0.10):
    """Frozen §27 table as implemented and registered (independent restatement)."""
    if p < alpha:
        return "MATERIAL" if (lo > thr or hi < -thr) else "DETECTED_SIZE_UNCERTAIN"
    return "IMMATERIAL" if (-thr < lo and hi < thr) else "INCONCLUSIVE"


def analyse_with(monkeypatch, **forced):
    """experiment.analyse on the synthetic world with chosen p / interval for the tests it runs."""
    real, calls = stats.mean_test, []

    def fake(x, lag):
        r = real(x, lag)
        calls.append(r)
        if len(calls) == 1 or "all" in forced:
            r.update({k: v for k, v in forced.items() if k != "all"})
        return r
    monkeypatch.setattr(experiment.stats, "mean_test", fake)
    return experiment.analyse(inputs(), schedule())


@pytest.mark.parametrize("p, ci, label", [
    (0.01, (0.20, 0.50), "MATERIAL"), (0.01, (-0.50, -0.20), "MATERIAL"),
    (0.01, (0.05, 0.50), "DETECTED_SIZE_UNCERTAIN"), (0.01, (-0.50, 0.05), "DETECTED_SIZE_UNCERTAIN"),
    (0.01, (-0.05, 0.05), "DETECTED_SIZE_UNCERTAIN"),          # F-22: significant but inside +/-0.10 - as registered
    (0.049999, (0.11, 0.12), "MATERIAL"), (0.05, (0.11, 0.12), "INCONCLUSIVE"),     # alpha is strict
    (0.50, (-0.05, 0.05), "IMMATERIAL"), (0.50, (-0.10, 0.05), "INCONCLUSIVE"), (0.50, (-0.05, 0.10), "INCONCLUSIVE"),
    (0.50, (-0.30, 0.05), "INCONCLUSIVE"), (0.50, (0.20, 0.50), "INCONCLUSIVE"),
])
def test_h1_decision_table(monkeypatch, p, ci, label):
    """Mutation 'H1 decision threshold flipped'. All four labels, both directions, both boundaries."""
    r = analyse_with(monkeypatch, p_two_sided=p, ci90=ci)
    assert r["H1"]["decision"] == label == h1_label(p, *ci)


def test_registered_h1_labels_follow_from_the_registered_numbers():
    """Read-only on saved artifacts: the label must be the one the saved p-value and interval imply."""
    want = {"primary": "INCONCLUSIVE", "confirmation": "MATERIAL"}
    for mode, label in want.items():
        h1 = json.loads((ROOT / f"results/s2_mom_v1/{mode}_results.json").read_text())["H1"]
        assert h1["decision"] == label == h1_label(h1["p_two_sided"], *h1["ci90"])
        assert h1["p_two_sided"] == pytest.approx(math.erfc(abs(h1["mean"] / h1["se_nw"]) / math.sqrt(2)), abs=1e-12)
        assert h1["ci90"][0] == pytest.approx(h1["mean"] - 1.6448536269514722 * h1["se_nw"], abs=1e-10)


@pytest.mark.parametrize("p_two, detected", [(0.08, True), (0.0999, True), (0.10, False), (0.12, False)])
def test_economic_conclusions_are_one_sided_at_5_percent(monkeypatch, p_two, detected):
    """Mutation 'economic conclusion uses two-sided p': H3-type flags use p_two_sided / 2 < alpha AND mean > 0."""
    r = analyse_with(monkeypatch, p_two_sided=p_two, all=True)
    seen = set()
    for step, t in r["ladder"].items():
        mean_wml = t["WML"]["mean_pct"]
        assert t["economic_conclusion"]["momentum_detected"] == (mean_wml > 0 and detected), step
        m = r["monthly"][r["monthly"]["step"] == step]
        assert t["economic_conclusion"]["winners_beat_universe"] == ((m["W"] - m["BM"]).mean() > 0 and detected), step
        seen.add(mean_wml > 0)
        seen.add((m["W"] - m["BM"]).mean() > 0)
    assert True in seen, "the synthetic world must contain a positive mean, or this test proves nothing"


# =================================================================== 4. runner gates (protocol B3, §25)
@pytest.fixture
def runner(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("run_s2_mom_kill", ROOT / "scripts" / "run_s2_mom.py")
    r = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r)
    monkeypatch.setattr(r, "OUT", tmp_path / "results")
    monkeypatch.setattr(r, "CHECKS", tmp_path / "checks")
    code = r.code_sha()                                         # hash of the real code files, then sandbox the paths
    monkeypatch.setattr(r, "code_sha", lambda: code)
    monkeypatch.setattr(r, "BASE_DIR", tmp_path)
    (tmp_path / "results").mkdir()
    (tmp_path / "checks").mkdir()
    for s in ("primary", "oos"):
        (tmp_path / "checks" / f"pre_run_checks_{s}.json").write_text(json.dumps({"all_passed": True, "code_sha256": r.code_sha()}))
    blind = tmp_path / "results" / "blinded_precision.json"
    blind.write_text('{"blinded": true}\n')
    r.rec = {"protocol_sha256": P.PROTOCOL_SHA256, "pending_decisions": {}, "decisions": dict(P.RESOLVED_DECISIONS),
             "provenance": {"stage2_rebuild": {"checks_passed": 150}, "blinded_precision_artifact_sha256": r._sha(blind),
                            "primary_run": {"code_sha256": r.code_sha(), "files_sha256": {}}}}
    r.calls = []
    monkeypatch.setattr(r, "verify_protocol", lambda: r.rec)
    monkeypatch.setattr(r, "require_ready", lambda rec, need_costs=False: rec["decisions"])
    monkeypatch.setattr(r.data, "verify_provenance", lambda: [])
    monkeypatch.setattr(r.experiments, "amend", lambda *a, **k: r.calls.append(("amend", a, k)))
    monkeypatch.setattr(r.experiments, "log_trial", lambda *a, **k: r.calls.append(("log_trial", a, k)))

    class Reached(Exception):
        """Every gate passed and the runner asked for data."""
    r.Reached = Reached

    def reached(*a, **k):
        raise Reached
    monkeypatch.setattr(r.data, "load_inputs", reached)
    return r


def test_all_gates_open_reaches_the_data_only_then(runner):
    for mode in ("primary", "confirmation"):
        with pytest.raises(runner.Reached):
            runner.main(mode)
    assert runner.calls == []


@pytest.mark.parametrize("primary_run", [None, {}, {"code_sha256": "0" * 64}, {"code_sha256": None}, {"results_sha256": "x"}])
def test_confirmation_requires_a_registered_primary_run_with_the_same_code(runner, primary_run):
    """Invariants 20-21, protocol §25 stop rule. Mutation 'confirmation without same-code primary'."""
    runner.rec["provenance"]["primary_run"] = primary_run
    with pytest.raises(P.NotReady, match="confirmation refused"):
        runner.main("confirmation")
    with pytest.raises(runner.Reached):                         # the primary mode itself does not need a primary run
        runner.main("primary")
    assert runner.calls == [] and sorted(p.name for p in runner.OUT.iterdir()) == ["blinded_precision.json"]


@pytest.mark.parametrize("attack", ["edit", "delete", "unregister"])
def test_blinded_artifact_must_exist_and_match_its_registered_hash(runner, attack):
    """Mutation 'blinded artifact gate off'."""
    f = runner.OUT / "blinded_precision.json"
    if attack == "edit":
        f.write_text('{"blinded": false}\n')
    elif attack == "delete":
        f.unlink()
    else:
        runner.rec["provenance"]["blinded_precision_artifact_sha256"] = None
    for mode in ("primary", "confirmation"):
        with pytest.raises(P.NotReady, match="blinded precision artifact"):
            runner.main(mode)
    assert runner.calls == []


def test_each_mode_runs_once_an_existing_output_is_never_overwritten(runner, monkeypatch):
    """Mutation 'runner overwrite guard off'."""
    f = runner.OUT / "primary_results.json"
    assert len(runner._write("primary_results.json", {"a": 1})) == 64
    before = f.read_bytes()
    with pytest.raises(P.NotReady, match="already exists - each mode runs once"):
        runner._write("primary_results.json", {"a": 2})
    assert f.read_bytes() == before
    monkeypatch.setattr(runner.data, "load_inputs", lambda s: "inputs")
    monkeypatch.setattr(runner.experiment, "blinded", lambda inp: {"new": True})
    with pytest.raises(P.NotReady, match="already exists"):     # a second blinded run: refused, not registered
        runner.main("blinded")
    assert runner.calls == [] and json.loads((runner.OUT / "blinded_precision.json").read_text()) == {"blinded": True}


def test_pre_run_checks_must_have_passed_with_this_code_for_the_right_sample(runner):
    (runner.CHECKS / "pre_run_checks_oos.json").write_text(json.dumps({"all_passed": False, "code_sha256": runner.code_sha()}))
    with pytest.raises(P.NotReady, match="pre-run checks for the OOS sample"):
        runner.main("confirmation")
    with pytest.raises(runner.Reached):
        runner.main("primary")


# =================================================================== 5. loader hash checks (frozen src/stage3/data.py)
def test_load_inputs_refuses_a_stage3_file_that_differs_from_the_manifest(tmp_path):
    """Mutation 'stage3 input hash check off'. The check must fire before any file is parsed."""
    good = tmp_path / "primary" / "calendar.csv"
    good.parent.mkdir()
    good.write_text("t\n")
    (tmp_path / "manifest.json").write_text(json.dumps({"content": {"outputs_sha256": {"primary/calendar.csv": "0" * 64}}}))
    with pytest.raises(ValueError, match="primary/calendar.csv does not match the Stage 3 manifest"):
        data.load_inputs("PRIMARY", out=tmp_path)


def test_load_univ_and_load_ret_refuse_files_that_differ_from_their_frozen_hashes(tmp_path, monkeypatch):
    """Mutations 'UNIV-1 hash check off' and 'RET-1.1 hash check off'."""
    monkeypatch.setattr(data, "D2", tmp_path / "data" / "stage2")
    monkeypatch.setattr(data, "BASE_DIR", tmp_path)
    for rel in ("data/stage2/universe/univ1_pit_universe.parquet", "data/stage2/datasets/ret1_1/ret1_1_2011.parquet"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(b"not the registered file")
    with pytest.raises(ValueError, match="UNIV-1 file does not match the frozen SHA-256"):
        data.load_univ()
    (tmp_path / "data/stage2/returns").mkdir(parents=True)
    man = tmp_path / "data/stage2/returns/ret1_1_manifest.json"
    man.write_text(json.dumps({"methodology_version": "RET-1.1", "datasets": {"data/stage2/datasets/ret1_1/ret1_1_2011.parquet": "0" * 64}}))
    with pytest.raises(ValueError, match="does not match the RET-1.1 manifest"):
        data.load_ret(P.T_STAR)
    man.write_text(json.dumps({"methodology_version": "RET-1", "datasets": {}}))
    with pytest.raises(ValueError, match="not RET-1.1"):
        data.load_ret(P.T_STAR)


# =================================================================== 6. Stage 2 rules (UNIV-1, RET-1.1, CA validation)
def test_univ1_liquidity_window_is_63_sessions_and_needs_50_valid_ones():
    """Mutations 'liquidity window 63->64' and 'min valid 50->49'."""
    assert (UM.WINDOW, UM.MIN_VALID, UM.TOP_N) == (63, 50, 200)
    sess = t_univ.SESS
    t = UM.selection_dates(sess)[-1]
    i = sess.get_loc(t)
    old = t_univ.stock("OLD", "INE000A01011", value=3e7)
    exact50 = t_univ.stock("N50", "INE000B01012", start=sess[i - 49], value=2e7)        # 50 valid sessions ending t
    only49 = t_univ.stock("N49", "INE000C01013", start=sess[i - 48], value=2e7)         # 49
    u = t_univ.run(pd.concat([old, exact50, only49]), top_n=5)
    at = u[u["selection_date"] == t].set_index("symbol_at_selection")
    assert at.at["OLD", "valid_sessions"] == 63                                          # the window, not 64
    assert (at.at["N50", "valid_sessions"], at.at["N50", "status"]) == (50, "MEMBER")
    assert (at.at["N49", "valid_sessions"], at.at["N49", "reason"]) == (49, "INSUFFICIENT_HISTORY")
    assert UM.selection_dates(sess)[0] >= sess[62] and UM.selection_dates(sess[:62]) == []


def test_univ1_liquidity_is_the_median_not_the_mean():
    """Mutation 'liquidity mean instead of median': a few huge days must not move the measure."""
    sess = t_univ.SESS
    t = UM.selection_dates(sess)[-1]
    spikes = {d: 1e12 for d in sess[sess <= t][-5:]}
    u = t_univ.run(pd.concat([t_univ.stock("SPK", "INE000A01011", value=1e7, extra=spikes),
                              t_univ.stock("CALM", "INE000B01012", value=2e7)]), top_n=5)
    at = u[u["selection_date"] == t].set_index("symbol_at_selection")
    assert at.at["SPK", "liquidity_median_value"] == 1e7 and at.at["CALM", "rank"] == 1 and at.at["SPK", "rank"] == 2


def test_ret1_jump_threshold_is_40_percent():
    """Mutation 'jump threshold 1.4->1.5': a 45% move with no event is an unexplained jump."""
    assert RT.JUMP == 1.4
    r = t_ret.run(t_ret.stock("AAA", "INE000A01011", [100, 145, 146, 203, 204]))
    day = lambda n: t_ret.row(r, "AAA", t_ret.SESS[n])
    assert day(1)["return_status"] == "UNEXPLAINED_JUMP" and not day(1)["research_grade"] and np.isnan(day(1)["ret_research"])
    assert day(3)["return_status"] == "OK"                      # 203/146 = 1.39: inside the bound, research-grade
    assert day(2)["return_status"] == "OK"


def test_ret1_event_is_attached_to_the_first_row_on_or_after_its_ex_date():
    """Mutation 'event attached to row before ex-date': ex-date on a Saturday belongs to Monday's row."""
    sat = pd.Timestamp("2012-01-14")
    assert sat not in t_ret.SESS and sat.dayofweek == 5
    r = t_ret.run(t_ret.stock("AAA", "INE000A01011", [100] * 10 + [50.5] + [51] * 5),
                  t_ret.events(("AAA", sat, "BONUS", 0.5, "Bonus 1:1")))
    fri, mon = t_ret.row(r, "AAA", "2012-01-13"), t_ret.row(r, "AAA", "2012-01-16")
    assert np.isnan(fri["event_factor"]) and fri["return_status"] == "OK"
    assert mon["event_factor"] == 0.5 and mon["return_status"] == "ADJUSTED_VALIDATED"
    assert mon["ret_research"] == pytest.approx(50.5 / (100 * 0.5) - 1)


@pytest.mark.parametrize("raw, factor, verdict", [
    (0.505, 0.5, "VALIDATED"), (0.35, 0.5, "DISCREPANT"), (0.70, 0.5, "DISCREPANT"), (0.61, 0.5, "VALIDATED"),
    (0.63, 0.5, "DISCREPANT"), (1.0, 0.5, "DISCREPANT"), (0.9, 0.9, "INCONCLUSIVE"), (0.5, 0.81, "INCONCLUSIVE"),
])
def test_corporate_action_validation_band_is_25_percent(raw, factor, verdict):
    """Mutation 'validation band 1.25->2.0': adjusted move must be within 25% AND smaller than the raw move."""
    assert classify(raw, factor) == verdict


# =================================================================== 7. step E rates (Addendum 1)
def test_step_e_rates_are_the_ones_in_force_on_the_entry_session_not_the_exit():
    """Invariant 19. Mutation 'rate date = exit not entry': brokerage went to zero on 2015-12-01."""
    h = holdings([("2015-10-30", "2015-11-30", "2015-12-31", {"A": (1.0, 1.0)})])
    row = step_e.cost_ledger(h, SCHEDULE).iloc[0]
    assert row["trade_date"] == "2015-11-30" and row["brokerage_period_from"] == "2012-07-02"
    assert row["brokerage_rs"] == pytest.approx(min(1e7 * 0.001, step_e.period(SCHEDULE, "brokerage", "2015-11-30")["cap_rs_per_order"]))
    assert row["brokerage_rs"] > 0 and row["indirect_tax_rate"] == 0.145
    after = step_e.cost_ledger(holdings([("2015-11-30", "2015-12-01", "2016-01-01", {"A": (1.0, 1.0)})]), SCHEDULE).iloc[0]
    assert after["brokerage_rs"] == 0.0 and after["total_cost_rs"] < row["total_cost_rs"]


def test_step_e_buy_and_sell_use_their_own_stt_rate():
    """Mutation 'STT sell uses buy rate' - equivalent on the real schedule (both 0.1%), so tested on a
    copy in which the two rates differ."""
    s = copy.deepcopy(SCHEDULE)
    assert s["components"]["stt_buy"][0]["rate"] == s["components"]["stt_sell"][0]["rate"] == 0.001
    s["components"]["stt_buy"][0]["rate"], s["components"]["stt_sell"][0]["rate"] = 0.002, 0.005
    assert step_e.order_cost(s, "2014-01-02", 0.01)["stt_rs"] == pytest.approx(1e5 * 0.002)
    assert step_e.order_cost(s, "2014-01-02", -0.01)["stt_rs"] == pytest.approx(1e5 * 0.005)


def test_step_e_net_is_gross_minus_cost_and_gross_is_copied_unchanged_in_the_registered_files():
    """Read-only on saved registered artifacts: the arithmetic identity must hold in every month."""
    for mode in ("primary", "confirmation"):
        e = pd.read_csv(ROOT / f"results/s2_mom_v1_step_e/{mode}_step_e_monthly.csv")
        g = pd.read_csv(ROOT / f"results/s2_mom_v1/{mode}_monthly.csv")
        g = g[g["step"] == "D"].reset_index(drop=True)
        assert (e["gross_W"] == g["W"]).all() and (e["gross_WML"] == g["WML"]).all() and len(e) == len(g)
        for s in P.SLIPPAGE_BPS:
            assert np.allclose(e[f"net_W_{s}"], e["gross_W"] - e[f"cost_W_{s}"], atol=1e-15, rtol=0)
            assert np.allclose(e[f"hypothetical_net_WML_{s}"], e["gross_WML"] - e[f"cost_W_{s}"] - e[f"hypothetical_cost_L_{s}"], atol=1e-15, rtol=0)
            assert (e[f"cost_W_{s}"] > 0).all() and (e[f"cost_BM_{s}"] > 0).all()   # F-17: no month costed at zero
        assert (e["cost_W_S0"] < e["cost_W_S1"]).all() and (e["cost_W_S3"] < e["cost_W_S4"]).all()


# =================================================================== 8. registered ladder files obey the definitions
def test_registered_monthly_files_satisfy_wml_and_delta_identities():
    """Read-only. A wrong WML or delta sign in a saved file would pass every hash test; not this one."""
    for mode, n in (("primary", 114), ("confirmation", 56)):
        m = pd.read_csv(ROOT / f"results/s2_mom_v1/{mode}_monthly.csv")
        d = pd.read_csv(ROOT / f"results/s2_mom_v1/{mode}_delta.csv")
        assert len(m) == 4 * n and (m["status"] == "OK").all() and d["paired"].all() and len(d) == n
        assert np.allclose(m["WML"], m["W"] - m["L"], atol=1e-15, rtol=0)
        wml = m.pivot(index="t", columns="step", values="WML")
        assert np.allclose(d.set_index("t")["delta"], (wml["A"] - wml["D"]) * 100, atol=1e-12, rtol=0)
        assert (m["k"] == np.floor(0.30 * m["n_rankable"] + 0.5)).all() and (m["n_universe"] == 200).all()
        h1 = json.loads((ROOT / f"results/s2_mom_v1/{mode}_results.json").read_text())["H1"]
        assert h1["mean"] == pytest.approx(d["delta"].mean(), abs=1e-12)
        mean, se = nw_by_hand(list(d["delta"]), h1["lag"])
        assert h1["se_nw"] == pytest.approx(se, abs=1e-12) and h1["mean"] == pytest.approx(mean, abs=1e-12)
