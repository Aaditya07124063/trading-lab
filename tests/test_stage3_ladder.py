"""S2-MOM-v1 ladder A-D, portfolio construction and leakage tests. SYNTHETIC DATA ONLY:
no real return, no file under data/, nothing after the cutoff, no holdout."""

import numpy as np
import pandas as pd
import pytest

from src.stage3 import ladder as L

DAYS = pd.bdate_range("2012-01-02", "2014-06-30")
ME = pd.Series(DAYS, index=DAYS.to_period("M")).groupby(level=0).max()          # month-end sessions


# ------------------------------------------------------------------ synthetic world
def make_panel(returns, cls=None, factor=()):
    """returns: {entity: array aligned to DAYS (nan = no row)}; cls: {(entity, date): class};
    factor: (entity, date) rows that carry a parsed bonus/split factor; raw_ok is False on BAD rows."""
    rows = []
    for e, r in returns.items():
        first = True
        for d, x in zip(DAYS, r):
            if np.isnan(x):
                continue
            c = (cls or {}).get((e, d), "FIRST" if first else "OK")
            rows.append({"date": d, "entity": e, "r_naive": np.nan if first else x,
                         "r_rg": x if c == "OK" else np.nan, "cls": c, "raw_ok": c != "BAD", "status": c,
                         "r_raw": np.nan if first else (x - 0.3 if (e, d) in factor else x)})   # factor: raw != naive
            first = False
    return pd.DataFrame(rows)


def make_world(seed=7, n=30, top=10, dead=4):
    rng = np.random.default_rng(seed)
    ents = [f"E{i:02d}" for i in range(n)]
    rets = {}
    for k, e in enumerate(ents):
        r = rng.normal(0.0005, 0.02, len(DAYS))
        if k >= n - dead:                                    # delisted: rows stop for good
            r[len(DAYS) - 120 - 15 * (k - (n - dead)):] = np.nan
        rets[e] = r
    panel = make_panel(rets)
    alive = panel.groupby("entity")["date"].max()
    urows = []
    for t in ME:
        live = [e for e in ents if not np.isnan(rets[e][DAYS.get_loc(t)])]
        for rank, i in enumerate(rng.permutation(len(live)), 1):
            urows.append({"selection_date": t, "segment_at_selection": live[i], "rank": float(rank),
                          "status": "MEMBER" if rank <= top else "ELIGIBLE_NOT_SELECTED"})
    univ = pd.DataFrame(urows)
    pool = set(alive[alive == DAYS[-1]].index)
    cal = L.calendar(DAYS, ME["2013-01"], ME["2014-04"], ME["2013-08"])
    return {"ents": ents, "panel": panel, "univ": univ, "pool": pool, "cal": cal, "top": top, "seg2ent": {e: e for e in ents}}


def run(wd, panel=None, univ=None, pool=None, days=DAYS, specs=L.STEP_SPECS, **kw):
    u = L.universes(wd["univ"] if univ is None else univ, wd["seg2ent"], wd["pool"] if pool is None else pool,
                    wd["cal"], wd["top"], ME["2014-06"])
    w = L.wide(wd["panel"] if panel is None else panel, wd["ents"], days)
    return L.run_ladder(w, wd["cal"], u, specs, **kw)


def members(hold, steps="ABCD", upto=None):
    return {k: (v["W"], v["L"], v["BM"]) for k, v in hold.items() if k[0] in steps and (upto is None or k[1] <= upto)}


@pytest.fixture(scope="module")
def world():
    return make_world()


# ------------------------------------------------------------------ calendar (§8-§9, B3)
def test_calendar_dates_and_delayed_entry():
    c = L.calendar(DAYS, ME["2013-01"], ME["2013-01"]).iloc[0]
    assert (c.t, c.m12, c.m1) == (pd.Timestamp("2013-01-31"), pd.Timestamp("2012-01-31"), pd.Timestamp("2012-12-31"))
    assert c.s_plus == pd.Timestamp("2013-02-01") and c.s_pp == pd.Timestamp("2013-03-01")   # one session after
    assert c.holding_month == "2013-02"


def test_calendar_matches_the_frozen_sample_sizes():
    c = L.calendar(pd.bdate_range("2011-06-22", "2026-09-30"))          # protocol defaults
    assert len(c) == 170 and (c["sample"] == "PRIMARY").sum() == 114 and (c["sample"] == "OOS").sum() == 56
    assert c["holding_month"].iloc[0] == "2012-07" and c["holding_month"].iloc[-1] == "2026-08"
    assert c.loc[c["sample"] == "PRIMARY", "holding_month"].iloc[-1] == "2021-12"
    assert (c["s_plus"] > c["t"]).all() and (c["m1"] < c["t"]).all()


def test_calendar_refuses_a_missing_formation_window():
    with pytest.raises(ValueError, match="formation"):
        L.calendar(DAYS, ME["2012-06"], ME["2012-06"])


# ------------------------------------------------------------------ universes (B1.1-B1.4)
def test_top200_pool_rank_and_duplicate_rule():
    u = pd.DataFrame({"segment_at_selection": ["s1", "s2", "s3", "s4", "s5"], "rank": [1.0, 2.0, 3.0, 4.0, 5.0],
                      "status": ["MEMBER", "MEMBER", "ELIGIBLE_NOT_SELECTED", "EXCLUDED", "ELIGIBLE_NOT_SELECTED"]})
    seg = {"s1": "X", "s2": "Y", "s3": "X", "s4": "Q", "s5": "Z"}        # s1 and s3 are one entity
    assert L.top200(u, seg, None, 2)["entity"].tolist() == ["X", "Y"]
    assert L.top200(u, seg, {"Y", "Z"}, 2)["entity"].tolist() == ["Y", "Z"]      # pool filter, then rank
    assert L.top200(u, seg, None, 9)["rank"].tolist() == [1.0, 2.0, 5.0]         # duplicate keeps the smaller rank
    with pytest.raises(ValueError):
        L.top200(u, {"s1": "X"}, None, 2)


def test_steps_a_b_c_universe_definitions(world):
    u = L.universes(world["univ"], world["seg2ent"], world["pool"], world["cal"], world["top"], ME["2014-06"])
    ts = list(world["cal"]["t"])
    star = world["univ"][world["univ"]["selection_date"] == ME["2014-06"]]
    fixed = L.top200(star, world["seg2ent"], world["pool"], world["top"])["entity"].tolist()
    for t in ts:
        at_t = world["univ"][world["univ"]["selection_date"] == t]
        assert u[("A", t)]["entity"].tolist() == fixed                               # A: one fixed list, measured at T*
        assert set(u[("A", t)]["entity"]) <= world["pool"] and set(u[("B", t)]["entity"]) <= world["pool"]
        assert u[("B", t)]["entity"].tolist() == L.top200(at_t, world["seg2ent"], world["pool"], world["top"])["entity"].tolist()
        assert set(u[("C", t)]["entity"]) == set(at_t.loc[at_t["status"] == "MEMBER", "segment_at_selection"])
    assert any(set(u[("C", t)]["entity"]) - world["pool"] for t in ts)               # C contains dead names
    assert any(u[("B", t)]["entity"].tolist() != fixed for t in ts)                  # B differs from A by date only


# ------------------------------------------------------------------ return rules (B1.2, §20)
def test_study_panel_naive_and_research_grade_rules():
    ret = pd.DataFrame({
        "date": pd.to_datetime(["2012-01-03"] * 5), "entity_id": list("abcde"),
        "close": [50.0, 101.0, 60.0, 110.0, 99.0], "prev_close": [100.0, 100.0, 100.0, 100.0, 100.0],
        "ret_raw": [-0.5, 0.01, -0.4, 0.10, -0.01], "event_factor": [0.5, np.nan, 0.5, np.nan, np.nan],
        "other_events": [None, None, None, "RIGHTS", "DIVIDEND"],
        "ret_research": [0.0, 0.01, np.nan, np.nan, np.nan],
        "return_status": ["ADJUSTED_VALIDATED", "OK", "EVENT_DISCREPANT", "EVENT_UNADJUSTABLE", "SPECIAL_SESSION_SPAN"],
        "research_grade": [True, True, False, False, False]})
    p = L.study_panel(ret).set_index("entity")
    assert p.loc["a", "r_naive"] == pytest.approx(0.0) and p.loc["c", "r_naive"] == pytest.approx(0.2)  # factor applied, any status
    assert p.loc["d", "r_naive"] == pytest.approx(0.10)                       # rights: not adjusted
    assert p["cls"].tolist() == ["OK", "OK", "BAD", "BAD", "SPAN"]
    assert p["raw_ok"].tolist() == [False, True, False, False, True]


# ------------------------------------------------------------------ ranking (§10)
@pytest.mark.parametrize("n,k", [(10, 3), (5, 2), (4, 1), (200, 60), (1, 0)])
def test_breakpoint_rule(n, k):
    w, l = L.sort_portfolios(pd.Series(np.arange(n, dtype=float), index=[f"e{i:03d}" for i in range(n)]))
    assert len(w) == len(l) == k and not set(w) & set(l)


def test_ties_break_by_entity_ascending():
    w, l = L.sort_portfolios(pd.Series([1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], index=list("dcbaefghij")))
    assert w == ["a", "b", "c"] and l == ["h", "i", "j"]


# ------------------------------------------------------------------ hand-checked month (§7-§10)
T = pd.Timestamp("2013-01-31")
CAL1 = L.calendar(DAYS, T, T)


def tiny(spec, cls=None, univ_keys="ABC", factor=()):
    """spec: {entity: {date-or-slice: return}} over a zero baseline. One selection date (2013-01-31)."""
    rets = {}
    for e, changes in spec.items():
        r = pd.Series(0.0, index=DAYS)
        for k, v in changes.items():
            r.loc[k] = v
        rets[e] = r.to_numpy()
    w = L.wide(make_panel(rets, cls, factor), list(spec), DAYS)
    u = {(k, T): pd.DataFrame({"entity": sorted(spec), "rank": np.arange(1.0, len(spec) + 1)}) for k in univ_keys}
    return w, u


def test_formation_is_12_1_and_holding_starts_one_session_late():
    w, u = tiny({
        "X": {slice("2012-02-01", "2012-12-31"): 0.001, "2012-01-31": -0.5, slice("2013-01-01", "2013-01-31"): -0.05,
              "2013-02-01": 0.5, "2013-02-04": 0.02, "2013-03-01": 0.01, "2013-03-04": 0.9},
        "Y": {slice("2012-02-01", "2012-12-31"): -0.001, slice("2013-01-01", "2013-01-31"): 0.05},
        "Z1": {}, "Z2": {"2012-06-01": 0.0001}})
    m, h = L.run_ladder(w, CAL1, u, {"C": L.STEP_SPECS["C"]})
    r = m.iloc[0]
    assert h[("C", T)]["W"] == ["X"] and h[("C", T)]["L"] == ["Y"]      # ranks on 2012-02..12 only (not m12 day, not skip month)
    assert r["n_rankable"] == 4 and r["k"] == 1
    assert r["W"] == pytest.approx(1.02 * 1.01 - 1)                     # s_plus return excluded, s_pp included, later excluded
    assert r["L"] == pytest.approx(0.0) and r["WML"] == pytest.approx(r["W"] - r["L"])
    assert r["BM"] == pytest.approx((1.02 * 1.01 - 1) / 4)              # equal weight of all rankable stocks


def test_rankable_needs_a_price_on_m12_and_m1():
    w, u = tiny({"X": {slice("2012-02-01", "2012-12-31"): 0.001}, "Y": {"2012-01-31": np.nan},
                 "Z": {"2012-12-31": np.nan}, "Q": {}, "R": {}})
    m, h = L.run_ladder(w, CAL1, u, {"C": L.STEP_SPECS["C"]})
    assert sorted(h[("C", T)]["BM"]) == ["Q", "R", "X"] and m.iloc[0]["n_universe"] == 5


# ------------------------------------------------------------------ step D rules (§20-§21)
def test_step_d_excludes_flagged_formation_rows_but_not_span_days():
    bad, span = pd.Timestamp("2012-06-01"), pd.Timestamp("2012-09-03")
    spec = {e: {slice("2012-02-01", "2012-12-31"): x} for e, x in zip("VWXYZ", (0.002, 0.001, 0.0, -0.001, -0.002))}
    spec["V"][bad] = 0.30                                                # an unresolved jump on V
    cls = {("V", bad): "BAD", **{(e, span): "SPAN" for e in "VWXYZ"}}
    for e in "VWXYZ":
        spec[e][span] = 0.25                                             # market-wide two-session move
    w, u = tiny(spec, cls)
    m, h = L.run_ladder(w, CAL1, u, {"C": L.STEP_SPECS["C"], "D": L.STEP_SPECS["D"]})
    assert "V" in h[("C", T)]["BM"] and "V" not in h[("D", T)]["BM"]     # flagged row: unrankable only in D
    assert len(h[("D", T)]["BM"]) == 4                                   # the SPAN day did not exclude anyone
    assert h[("C", T)]["W"] == ["V", "W"] and h[("D", T)]["W"] == ["W"]


def test_step_d_span_day_is_left_out_of_holding_returns():
    span = pd.Timestamp("2013-02-11")
    spec = {e: {slice("2012-02-01", "2012-12-31"): x, span: 0.10, "2013-02-12": 0.01}
            for e, x in zip("VWXYZ", (0.002, 0.001, 0.0, -0.001, -0.002))}
    w, u = tiny(spec, {(e, span): "SPAN" for e in "VWXYZ"})
    m, _ = L.run_ladder(w, CAL1, u, {"C": L.STEP_SPECS["C"], "D": L.STEP_SPECS["D"]})
    m = m.set_index("step")
    assert m.loc["D", "BM"] == pytest.approx(0.01) and m.loc["C", "BM"] == pytest.approx(1.1 * 1.01 - 1)
    assert m.loc["D", "BM_span_stock_days"] == 5


def test_step_d_neutral_fill_is_the_simple_mean_and_keeps_the_stock():
    day1, day2 = pd.Timestamp("2013-02-04"), pd.Timestamp("2013-02-05")
    spec = {"A1": {slice("2012-02-01", "2012-12-31"): 0.003, day1: 1.0, day2: 0.2},
            "A2": {slice("2012-02-01", "2012-12-31"): 0.002, day2: 0.1},
            "A3": {slice("2012-02-01", "2012-12-31"): 0.001, day2: -0.9},
            **{f"B{i}": {slice("2012-02-01", "2012-12-31"): -0.001 * i} for i in range(1, 8)}}
    w, u = tiny(spec, {("A3", day2): "BAD"})
    m, h = L.run_ladder(w, CAL1, u, {"D": L.STEP_SPECS["D"]})
    assert h[("D", T)]["W"] == ["A1", "A2", "A3"]                         # the flagged stock stays a member
    fill = (0.2 + 0.1) / 2                                               # simple mean: NOT value-weighted (0.1667), NOT zero
    assert m.iloc[0]["W"] == pytest.approx((2 * 1.2 + 1.1 + (1 + fill)) / 3 - 1)
    assert m.iloc[0]["W"] != pytest.approx((2 * 1.2 + 1.1 + 1 + (2 * 0.2 + 0.1) / 3) / 3 - 1)
    assert m.iloc[0]["W_filled_stock_days"] == 1 and set(h[("D", T)]["W_end"]) == {"A1", "A2", "A3"}
    ev = [e for e in h[("D", T)]["events"] if e["portfolio"] == "W"]
    assert ev == [{"t": T, "step": "D", "portfolio": "W", "kind": "NEUTRAL_FILL", "entity": "A3", "date": day2}]


def test_step_d_fill_when_no_other_stock_has_a_return_is_recorded():
    day = pd.Timestamp("2013-02-05")
    spec = {**{f"A{i}": {slice("2012-02-01", "2012-12-31"): 0.004 - 0.001 * i, day: 0.5} for i in range(1, 4)},
            **{f"B{i}": {slice("2012-02-01", "2012-12-31"): -0.001 * i} for i in range(1, 8)}}
    w, u = tiny(spec, {(f"A{i}", day): "BAD" for i in range(1, 4)})
    m, h = L.run_ladder(w, CAL1, u, {"D": L.STEP_SPECS["D"]})
    assert m.iloc[0]["W"] == pytest.approx(0.0) and m.iloc[0]["W_fill_without_other_stocks"] == 3
    assert {e["kind"] for e in h[("D", T)]["events"] if e["portfolio"] == "W"} == {"NEUTRAL_FILL_NO_OTHER_STOCKS"}


# ------------------------------------------------------------------ delisting (§22)
def test_delisting_rule_applies_from_step_c_only_and_never_double_counts():
    gone, back = pd.Timestamp("2013-02-15"), pd.Timestamp("2013-03-20")
    cal = L.calendar(DAYS, T, ME["2013-02"])
    base = {slice("2012-02-01", "2013-01-31"): 0.002}
    spec = {"DEAD": {**base, slice(gone, DAYS[-1]): np.nan},
            "HALT": {**base, slice(gone, back - pd.Timedelta(days=1)): np.nan, back: -0.5},
            "LIVE": {**base}, **{f"B{i}": {slice("2012-02-01", "2013-01-31"): -0.001 * i} for i in range(1, 8)}}
    rets = {}
    for e, ch in spec.items():
        r = pd.Series(0.0, index=DAYS)
        for k, v in ch.items():
            r.loc[k] = v
        rets[e] = r.to_numpy()
    w = L.wide(make_panel(rets), list(spec), DAYS)
    u = {(k, t): pd.DataFrame({"entity": sorted(spec), "rank": np.arange(1.0, 11)}) for k in "ABC" for t in cal["t"]}
    dr = np.where(w.ents == "DEAD", 0.0, -0.30)                          # DEAD = voluntary delisting -> 0%
    m, h = L.run_ladder(w, cal, u, {"C": L.STEP_SPECS["C"], "A": L.STEP_SPECS["A"]}, delist_ret=dr)
    c, a = m[m.step == "C"].set_index("t"), m[m.step == "A"].set_index("t")
    assert c.loc[T, "W"] == pytest.approx((1.0 + 0.5 + 1.0) / 3 - 1)    # HALT's -50% booked in the month of the missed exit
    assert c.loc[T, "W_exit_gap_booked"] == 1 and c.loc[T, "W_delisting_return_applied"] == 1
    assert a.loc[T, "W"] == pytest.approx(0.0)                           # A/B: no delisting rule (B1.2)
    assert c.loc[ME["2013-02"], "W"] == pytest.approx(0.0)               # the booked row is not counted again
    assert a.loc[ME["2013-02"], "W"] == pytest.approx((1.0 + 0.5 + 1.0) / 3 - 1)
    m2, _ = L.run_ladder(w, cal, u, {"C": L.STEP_SPECS["C"]}, delist_ret=np.full(len(w.ents), -0.30))
    assert m2.set_index("t").loc[T, "W"] == pytest.approx((0.7 + 0.5 + 1.0) / 3 - 1)   # non-voluntary: -30%
    kinds = {(e["entity"], e["kind"]) for e in h[("C", T)]["events"] if e["portfolio"] == "W"}
    assert kinds == {("HALT", "EXIT_GAP_BOOKED"), ("DEAD", "DELISTING_RETURN")}       # audit trail


BACK = pd.Timestamp("2013-03-20")


def _halt_world(cls=None, factor=(), later=None):
    """HALT stops trading on 2013-02-15, has no price at the exit session and resumes on BACK at -50%.
    later: return written on EVERY row after the exit session; later_keep: leave the BACK row alone."""
    spec = {"HALT": {slice("2012-02-01", "2013-01-31"): 0.002, slice("2013-02-15", BACK - pd.Timedelta(days=1)): np.nan, BACK: -0.5},
            **{f"B{i}": {slice("2012-02-01", "2013-01-31"): -0.001 * i} for i in range(1, 10)}}
    if later is not None:
        value, keep_resumption = later
        for e in spec:
            for d in DAYS[DAYS > CAL1["s_pp"].iloc[0]]:
                if e == "HALT" and (d < BACK or (keep_resumption and d == BACK)):
                    continue
                spec[e][d] = value
    return tiny(spec, cls, factor=factor)


CD = {"C": L.STEP_SPECS["C"], "D": L.STEP_SPECS["D"]}


def test_section_22_is_applied_literally_in_step_d_as_in_step_c():
    w, u = _halt_world({("HALT", BACK): "BAD"})                          # gap row: not research-grade
    m, h = L.run_ladder(w, CAL1, u, CD)
    m = m.set_index("step")
    for step in "CD":                                                    # realised gap return booked in both
        assert m.loc[step, "W"] == pytest.approx((0.5 + 1 + 1) / 3 - 1) and m.loc[step, "W_exit_gap_booked"] == 1
    assert m.loc["D", "W_exit_gap_booked_on_flagged_row"] == 1          # counted for the audit trail, still booked
    assert [e["kind"] for e in h[("D", T)]["events"] if e["portfolio"] == "W"] == ["EXIT_GAP_BOOKED_FLAGGED_ROW"]


def test_section_22_stops_if_a_factor_sits_on_the_resumption_row_in_step_d():
    w, u = _halt_world(factor={("HALT", BACK)})
    L.run_ladder(w, CAL1, u, {"C": L.STEP_SPECS["C"]})                   # step C: B1.2 rule, no stop
    with pytest.raises(ValueError, match="resumption row"):
        L.run_ladder(w, CAL1, u, {"D": L.STEP_SPECS["D"]})


def test_only_the_section_22_row_can_reach_past_the_exit_session():
    cols = ["step", "W", "L", "WML", "BM"]
    run_cd = lambda world: L.run_ladder(world[0], CAL1, world[1], CD)[0]
    base = run_cd(_halt_world())
    unrelated, with_22_row = run_cd(_halt_world(later=(0.75, True))), run_cd(_halt_world(later=(0.75, False)))
    pd.testing.assert_frame_equal(unrelated[cols], base[cols])           # unrelated future prices: no effect
    assert not with_22_row[cols].equals(base[cols])                      # the §22 row: the one permitted channel


# ------------------------------------------------------------------ sensitivity treatments (§16, §20)
def _five(extra=None, cls=None, gaps=None):
    spec = {e: {slice("2012-02-01", "2012-12-31"): x} for e, x in zip("VWXYZ", (0.002, 0.001, 0.0, -0.001, -0.002))}
    for e, ch in (extra or {}).items():
        spec[e].update(ch)
    rets = {}
    for e, changes in spec.items():
        r = pd.Series(0.0, index=DAYS)
        for k, v in changes.items():
            r.loc[k] = v
        rets[e] = r.to_numpy()
    w = L.wide(make_panel(rets, cls), list(spec), DAYS, gaps)
    return w, {(k, T): pd.DataFrame({"entity": sorted(spec), "rank": np.arange(1.0, 6.0)}) for k in "ABC"}


D_ONLY = {"D": L.STEP_SPECS["D"]}


def test_r_span_uses_the_raw_two_session_return_and_leaves_the_primary_alone():
    span = pd.Timestamp("2013-02-11")
    w, u = _five({e: {span: 0.10, "2013-02-12": 0.01} for e in "VWXYZ"}, {(e, span): "SPAN" for e in "VWXYZ"})
    before = {k: v.copy() for k, v in vars(w).items() if isinstance(v, np.ndarray)}
    t = L.treated(w, span_raw=True)
    assert all((getattr(w, k) == v).all() for k, v in before.items())            # the primary matrices are untouched
    assert t.treated_rows == 5 and not t.span.any() and w.span.sum() == 5
    primary = L.run_ladder(w, CAL1, u, D_ONLY)[0].iloc[0]
    treated = L.run_ladder(t, CAL1, u, D_ONLY)[0].iloc[0]
    assert primary["BM"] == pytest.approx(0.01) and treated["BM"] == pytest.approx(1.1 * 1.01 - 1)
    assert L.run_ladder(w, CAL1, u, D_ONLY)[0].iloc[0]["BM"] == pytest.approx(0.01)   # primary still the primary


def test_r_gap_uses_the_raw_gap_return_only_when_no_event_is_on_the_row():
    g1, g2 = pd.Timestamp("2012-06-04"), pd.Timestamp("2012-06-05")
    extra = {"V": {"2012-06-01": np.nan, g1: 0.05}, "W": {"2012-06-04": np.nan, g2: 0.05}}
    cls = {("V", g1): "BAD", ("W", g2): "BAD"}                                   # both are multi-session gap rows
    gaps = pd.DataFrame({"date": [g1, g2], "entity": ["V", "W"], "no_event": [True, False]})   # W's row carries an event
    w, u = _five(extra, cls, gaps)
    assert L.run_ladder(w, CAL1, u, D_ONLY)[1][("D", T)]["BM"] == ["X", "Y", "Z"]          # primary: both unrankable
    t = L.treated(w, gap_raw=True)
    assert t.treated_rows == 1
    assert L.run_ladder(t, CAL1, u, D_ONLY)[1][("D", T)]["BM"] == ["V", "X", "Y", "Z"]     # only the no-event gap is restored
    assert L.run_ladder(L.treated(w), CAL1, u, D_ONLY)[1] == L.run_ladder(w, CAL1, u, D_ONLY)[1]   # no treatment = primary
    with pytest.raises(ValueError, match="gap row"):
        L.wide(make_panel({"V": np.zeros(len(DAYS))}), ["V"], DAYS, pd.DataFrame({"date": [g1], "entity": ["V"], "no_event": [True]}))


@pytest.mark.parametrize("miss,a3", [("FILL", 1 + (0.2 + 0.1) / 2), ("RAW", 0.1), ("ZERO", 1.0)])
def test_r_miss_treatments_of_a_flagged_holding_day(miss, a3):
    day1, day2 = pd.Timestamp("2013-02-04"), pd.Timestamp("2013-02-05")
    spec = {"A1": {slice("2012-02-01", "2012-12-31"): 0.003, day1: 1.0, day2: 0.2},
            "A2": {slice("2012-02-01", "2012-12-31"): 0.002, day2: 0.1},
            "A3": {slice("2012-02-01", "2012-12-31"): 0.001, day2: -0.9},
            **{f"B{i}": {slice("2012-02-01", "2012-12-31"): -0.001 * i} for i in range(1, 8)}}
    w, u = tiny(spec, {("A3", day2): "BAD"})
    m, h = L.run_ladder(w, CAL1, u, D_ONLY, miss=miss)
    assert h[("D", T)]["W"] == ["A1", "A2", "A3"]                              # membership never changes
    assert m.iloc[0]["W"] == pytest.approx((2 * 1.2 + 1.1 + a3) / 3 - 1)
    assert m.iloc[0].get("W_filled_stock_days", 0) == (1 if miss == "FILL" else 0)
    if miss == "FILL":
        pd.testing.assert_frame_equal(m, L.run_ladder(w, CAL1, u, D_ONLY)[0])   # FILL is the default = the primary
    with pytest.raises(ValueError, match="missing-day"):
        L.run_ladder(w, CAL1, u, D_ONLY, miss="GUESS")


# ------------------------------------------------------------------ primary estimand (§2)
def test_paired_delta_keeps_unpaired_months_with_a_reason(world):
    m, _ = run(world)
    d = L.paired_delta(m, world["cal"])
    assert len(d) == len(world["cal"]) and d["paired"].all()
    wml = m.pivot(index="t", columns="step", values="WML")
    assert np.allclose(d["delta"], (wml["A"] - wml["D"]).to_numpy() * 100)
    broken = m.copy()
    row = (broken["step"] == "D") & (broken["t"] == world["cal"]["t"].iloc[3])
    broken.loc[row, "status"] = "NO_HOLDING_DATA"
    d2 = L.paired_delta(broken, world["cal"])
    assert len(d2) == len(world["cal"]) and d2["paired"].sum() == len(d) - 1      # not silently dropped
    assert np.isnan(d2["delta"].iloc[3]) and d2["reason"].iloc[3] == "A:OK D:NO_HOLDING_DATA"
    assert L.paired_delta(m[m["step"] != "A"], world["cal"])["paired"].sum() == 0


def test_month_after_the_data_end_is_recorded_not_computed(world):
    end = world["cal"]["s_pp"].iloc[5]
    m, _ = run(world, data_end=end)
    st = m[m.step == "D"].set_index("t")["status"]
    assert (st.iloc[:6] == "OK").all() and (st.iloc[6:] == "NO_HOLDING_DATA").all()


def test_deterministic(world):
    a, b = run(world), run(make_world())
    pd.testing.assert_frame_equal(a[0], b[0])
    assert a[1] == b[1]


# ------------------------------------------------------------------ leakage tests (§19, B2)
def test_a_perturbation_of_future_information_changes_no_past_portfolio(world):
    cut = world["cal"]["t"].iloc[8]
    base = members(run(world)[1], "BCD", cut)
    p = world["panel"].copy()
    fut = p["date"] > cut
    p.loc[fut, ["r_naive", "r_rg", "r_raw"]] = p.loc[fut, ["r_naive", "r_rg", "r_raw"]] * -3 + 0.5
    p.loc[fut & (p["cls"] == "OK") & (p.index % 3 == 0), "cls"] = "BAD"
    u = world["univ"].copy()
    late = (u["selection_date"] > cut) & (u["selection_date"] < ME["2014-06"])
    u.loc[late, "rank"] = u.loc[late].groupby("selection_date")["rank"].transform(lambda s: s[::-1].to_numpy())
    u.loc[late, "status"] = np.where(u.loc[late, "rank"] <= world["top"], "MEMBER", "ELIGIBLE_NOT_SELECTED")
    assert members(run(world, panel=p, univ=u)[1], "BCD", cut) == base


def test_b_truncation_after_the_selection_date_changes_nothing(world):
    cut = world["cal"]["t"].iloc[8]
    base = members(run(world)[1], "CD", cut)
    p = world["panel"][world["panel"]["date"] <= cut]
    u = world["univ"][(world["univ"]["selection_date"] <= cut) | (world["univ"]["selection_date"] == ME["2014-06"])]
    cal = world["cal"][world["cal"]["t"] <= cut]
    m, h = run({**world, "cal": cal}, panel=p, univ=u, days=DAYS[DAYS <= cut])
    assert members(h, "CD", cut) == base
    assert m.loc[(m.t == cut) & (m.step == "D"), "status"].item() == "NO_HOLDING_DATA"   # outcome unknown at t


def test_c_random_ranking_placebo_runs_and_ignores_momentum(world):
    real = run(world)[1]
    m, h = run(world, score_fn=L.random_scores(11))
    assert (m["status"] == "OK").all() and m["WML"].notna().all()
    assert h == run(world, score_fn=L.random_scores(11))[1]                    # seeded: reproducible
    assert h != run(world, score_fn=L.random_scores(12))[1]
    keys = [k for k in real if k[0] == "D"]
    assert sum(real[k]["W"] != h[k]["W"] for k in keys) > len(keys) // 2       # not the momentum ranking
    assert all(real[k]["BM"] == h[k]["BM"] for k in keys)                      # same rankable stocks


def test_d_huge_future_traded_value_changes_no_past_liquidity_rank(world):
    cut = world["cal"]["t"].iloc[8]
    u = world["univ"].copy()
    late = (u["selection_date"] > cut) & (u["selection_date"] < ME["2014-06"])
    u.loc[late, "rank"] = u.loc[late].groupby("selection_date")["rank"].transform(lambda s: s[::-1].to_numpy())
    u.loc[late, "status"] = np.where(u.loc[late, "rank"] <= world["top"], "MEMBER", "ELIGIBLE_NOT_SELECTED")
    a, b = run(world)[1], run(world, univ=u)[1]
    assert members(a, "BCD", cut) == members(b, "BCD", cut)
    assert members(a, "BCD") != members(b, "BCD")                              # the injection did bite later


def test_e_future_delisting_information_cannot_change_pit_membership(world):
    smaller = set(sorted(world["pool"])[5:])                                   # "we now know 5 more names die"
    a, b = run(world)[1], run(world, pool=smaller)[1]
    assert members(a, "CD") == members(b, "CD")                                # PIT steps: untouched
    assert members(a, "AB") != members(b, "AB")                                # survivor steps: change, by definition


def test_f_impossible_future_returns_change_no_signal_or_past_membership(world):
    cut = world["cal"]["t"].iloc[8]
    p = world["panel"].copy()
    fut = p["date"] > world["cal"].loc[world["cal"]["t"] == cut, "m1"].item()  # everything after the formation window
    p.loc[fut & p["r_naive"].notna(), ["r_naive", "r_rg", "r_raw"]] = 9.0
    a, b = run(world)[1], run(world, panel=p)[1]
    assert members(a, "ABCD", cut) == members(b, "ABCD", cut)


def test_a_and_d_share_one_month_structure_so_delta_is_paired(world):
    m, h = run(world)
    cols = ["t", "holding_month", "sample"]
    a, d = (m[m["step"] == s].reset_index(drop=True) for s in "AD")
    pd.testing.assert_frame_equal(a[cols], d[cols])                              # same months, same order
    pd.testing.assert_frame_equal(a[cols], world["cal"][cols].reset_index(drop=True))   # exactly the calendar
    assert (a["status"] == "OK").all() and (d["status"] == "OK").all()
    assert (a["k"] == np.floor(0.30 * a["n_rankable"] + 0.5)).all() and (d["k"] == np.floor(0.30 * d["n_rankable"] + 0.5)).all()
    for t in world["cal"]["t"]:                                                  # one selection date -> both steps
        assert len(h[("A", t)]["W"]) == len(h[("A", t)]["L"]) and len(h[("D", t)]["W"]) == len(h[("D", t)]["L"])
    assert len(L.paired_delta(m, world["cal"])) == len(world["cal"])


def test_prices_after_the_exit_session_cannot_change_a_month_with_an_exit_price(world):
    """No future information inside a holding period. Covers every stock-month that HAS a price on
    its exit session. (A missed exit is governed by frozen §22 - see the delisting tests.)"""
    row = world["cal"].iloc[8]
    base = run(world)[0]
    p = world["panel"].copy()
    later = (p["date"] > row.s_pp) & p["r_naive"].notna()
    p.loc[later, ["r_naive", "r_rg", "r_raw"]] = -0.99                            # absurd later prices
    p.loc[later & (p.index % 2 == 0), "cls"] = "BAD"
    after = run(world, panel=p)[0]
    cols = ["t", "step", "status", "W", "L", "WML", "BM", "k", "n_rankable"]
    upto = lambda m: m.loc[m["t"] <= row.t, cols].reset_index(drop=True)
    pd.testing.assert_frame_equal(upto(base), upto(after))
    assert not base.loc[base["t"] > row.t, "WML"].reset_index(drop=True).equals(
        after.loc[after["t"] > row.t, "WML"].reset_index(drop=True))             # the perturbation was real


def test_reverse_order_specs_are_separate_and_as_defined(world):
    assert set(L.REVERSE_SPECS) & set(L.STEP_SPECS) == set()
    m, h = run(world, specs={**L.STEP_SPECS, **L.REVERSE_SPECS})
    base = run(world)[0]
    pd.testing.assert_frame_equal(m[m["step"].isin(list("ABCD"))].reset_index(drop=True).dropna(axis=1, how="all"),
                                  base.dropna(axis=1, how="all"))                  # primary ladder unchanged by it
    t = world["cal"]["t"].iloc[2]
    assert h[("R_RETURNS", t)]["W"] == h[("C", t)]["W"]                          # D with the step-A return rule
    assert set(h[("R_POOL", t)]["BM"]) <= world["pool"]                          # D with the survivor pool
