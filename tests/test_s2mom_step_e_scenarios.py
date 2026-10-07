"""Step E under Supplements 2 and 3: UNIV-1 rank join and guard, slippage S0-S4, first month, sample
boundary, hypothetical L and net WML, H3 -> H4, break-even, and the runner's input boundary.

Every holding, rank and return here is SYNTHETIC. The runner is only ever run on made-up files in a
temporary directory; the real inputs are hashed, never read."""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest
from scipy.stats import norm

from src.stage3 import stats, step_e
from src.stage3.protocol import NotReady
from src.stage3.step_e import CostScheduleError, band, break_even, cost_ledger, monthly_costs, net_returns, one_sided_test, rank_index
from tests import test_access_boundary as boundary

ROOT = Path(__file__).resolve().parents[1]
S = step_e.load_schedule()
CR = 10_000_000
NAN = float("nan")
RANK = {"A": 1, "B": 200, "C": 3, "D": 4, "E": 5}
_spec = importlib.util.spec_from_file_location("step_e_runner", ROOT / "scripts" / "run_s2_mom_step_e.py")
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)                    # importing defines functions only; nothing runs
runner._real_run = runner.run


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def calendar(first, n=6):
    ts = pd.date_range(first, periods=n + 1, freq="BME")
    sp = [t + pd.offsets.BDay(1) for t in ts]
    return [(ts[i].date().isoformat(), sp[i].date().isoformat(), sp[i + 1].date().isoformat()) for i in range(n)]


def make(first="2013-12-31", sample="PRIMARY", exit_rank=201.0, wml=(0.02, 0.03, 0.025, 0.02, 0.03, 0.025)):
    """Six months. W holds A and B, then swaps B for E at month 2. L (C, D) and the benchmark (A, C, D)
    never trade after the first month. `exit_rank` is B's UNIV-1 rank at the rebalance where it is sold."""
    cal = calendar(first)
    books = {"W": lambda i: {"A": (0.5, 0.6), "B": (0.5, 0.4)} if i < 2 else {"A": (0.5, 0.5), "E": (0.5, 0.5)},
             "L": lambda i: {"C": (0.5, 0.5), "D": (0.5, 0.5)},
             "BM": lambda i: {"A": (0.25, 0.25), "C": (0.25, 0.25), "D": (0.5, 0.5)}}
    h = pd.DataFrame([{"sample": sample, "step": "D", "t": t, "holding_month": sp[:7], "s_plus": sp, "s_pp": spp,
                       "month_status": "OK", "portfolio": p, "entity": e, "liquidity_rank": RANK[e],
                       "begin_weight": b, "end_weight": w}
                      for i, (t, sp, spp) in enumerate(cal) for p, book in books.items() for e, (b, w) in book(i).items()])
    u = pd.DataFrame([{"selection_date": pd.Timestamp(t), "entity_id": e, "rank": float(r)}
                      for t, _, _ in cal for e, r in RANK.items()])
    u.loc[(u["selection_date"] == pd.Timestamp(cal[2][0])) & (u["entity_id"] == "B"), "rank"] = exit_rank
    m = pd.DataFrame({"t": [c[0] for c in cal], "sample": sample, "step": "D", "W": 0.03, "L": 0.01, "BM": 0.02, "WML": list(wml)})
    return h, u, m, cal


def exit_order(exit_rank):
    h, u, _, cal = make(exit_rank=exit_rank)
    led = cost_ledger(h, S, portfolio="W", ranks=rank_index(u))
    return led[(led["t"] == cal[2][0]) & (led["entity"] == "B")].iloc[0]


# ------------------------------------------------------------------ the join and the formation-rank guard
def test_formation_rank_equal_to_saved_liquidity_rank_passes():
    h, u, _, _ = make()
    step_e.check_formation_ranks(h, rank_index(u))
    assert len(cost_ledger(h, S, portfolio="W", ranks=rank_index(u)))


def test_formation_rank_mismatch_is_a_hard_failure_before_any_cost(monkeypatch):
    h, u, _, cal = make()
    monkeypatch.setattr(step_e, "order_cost", lambda *a, **k: pytest.fail("a cost was calculated"))
    wrong = u.copy()
    wrong.loc[(wrong["selection_date"] == pd.Timestamp(cal[4][0])) & (wrong["entity_id"] == "A"), "rank"] = 2.0
    for bad in (wrong, u.assign(rank=NAN)):                                 # a different rank; a held stock with no rank
        with pytest.raises(CostScheduleError, match="differs from the saved liquidity_rank"):
            cost_ledger(h, S, portfolio="W", ranks=rank_index(bad))


def test_formation_rank_guard_covers_w_and_l_but_not_the_benchmark():
    h, u, _, cal = make()
    assert step_e.RANK_GUARDED == ("W", "L")
    wrong = h.assign(liquidity_rank=h["liquidity_rank"] + 1)                # every saved rank disagrees with UNIV-1
    empty = h.assign(liquidity_rank=NAN)                                    # no saved rank at all
    for bad in (wrong, empty):
        for p in ("W", "L"):
            with pytest.raises(CostScheduleError, match="differs from the saved liquidity_rank"):
                cost_ledger(bad, S, portfolio=p, ranks=rank_index(u))
        bm = cost_ledger(bad, S, portfolio="BM", ranks=rank_index(u))       # benchmark: not guarded (ruling 21) ...
        pd.testing.assert_frame_equal(bm, cost_ledger(h, S, portfolio="BM", ranks=rank_index(u)))
        assert bm["univ1_rank"].tolist() == [RANK[e] for e in bm["entity"]]  # ... its band comes from the UNIV-1 lookup
    low = u.assign(rank=u["rank"].where(u["entity_id"] != "D", 350.0))      # a benchmark stock ranked 350 in UNIV-1
    bm = cost_ledger(wrong, S, portfolio="BM", ranks=rank_index(low))
    assert set(bm[bm["entity"] == "D"]["slippage_band"]) == {"201-500"} and set(bm[bm["entity"] != "D"]["slippage_band"]) == {"1-200"}
    with pytest.raises(CostScheduleError, match="no UNIV-1 row for D"):     # the lookup itself stays strict for the benchmark
        cost_ledger(h, S, portfolio="BM", ranks=rank_index(u[u["entity_id"] != "D"]))
    with pytest.raises(CostScheduleError, match="invalid UNIV-1 rank"):
        cost_ledger(h, S, portfolio="BM", ranks=rank_index(u.assign(rank=u["rank"].where(u["entity_id"] != "D", 0.0))))


def test_duplicate_or_null_univ1_key_is_a_hard_failure():
    _, u, _, _ = make()
    with pytest.raises(CostScheduleError, match="duplicate"):
        rank_index(pd.concat([u, u.iloc[[0]].assign(rank=7.0)]))
    for col in ("selection_date", "entity_id"):
        nulled = u.copy()
        nulled.loc[0, col] = None
        with pytest.raises(CostScheduleError, match="null"):
            rank_index(nulled)


def test_missing_exit_lookup_is_a_hard_failure_with_no_other_date_or_identifier():
    h, u, _, cal = make()
    gone = u[~((u["selection_date"] == pd.Timestamp(cal[2][0])) & (u["entity_id"] == "B"))]   # B has rows at every other date
    with pytest.raises(CostScheduleError, match=f"no UNIV-1 row for B at {cal[2][0]}"):
        cost_ledger(h, S, portfolio="W", ranks=rank_index(gone))


def test_unknown_identifier_is_never_mapped():
    h, u, _, _ = make()
    with pytest.raises(CostScheduleError, match="no UNIV-1 row for A"):
        cost_ledger(h, S, portfolio="W", ranks=rank_index(u.assign(entity_id=u["entity_id"] + "|SEG")))
    assert "segment" not in Path(step_e.__file__).read_text().split('"""', 2)[2]      # segment_at_selection is never a key


@pytest.mark.parametrize("bad", [0.0, -3.0, 1.5])
def test_invalid_rank_is_a_hard_failure(bad):
    with pytest.raises(CostScheduleError, match="invalid UNIV-1 rank"):
        band(bad)
    with pytest.raises(CostScheduleError, match="invalid UNIV-1 rank"):
        exit_order(bad)


# ------------------------------------------------------------------ slippage bands and S0-S4
def test_frozen_scenario_values_are_used_exactly():
    assert step_e.SLIPPAGE_BPS == {"S0": {"1-200": 0, "201-500": 0}, "S1": {"1-200": 5, "201-500": 15},
                                   "S2": {"1-200": 10, "201-500": 30}, "S3": {"1-200": 25, "201-500": 75},
                                   "S4": {"1-200": 50, "201-500": 150}}


@pytest.mark.parametrize("exit_rank,want_band,fallback,bps", [
    (150.0, "1-200", False, (0, 5, 10, 25, 50)),
    (200.0, "1-200", False, (0, 5, 10, 25, 50)),
    (201.0, "201-500", False, (0, 15, 30, 75, 150)),
    (500.0, "201-500", False, (0, 15, 30, 75, 150)),
    (501.0, "201-500", True, (0, 15, 30, 75, 150)),           # above 500: fallback
    (NAN, "201-500", True, (0, 15, 30, 75, 150)),             # row present, no rank: fallback
])
def test_exit_order_uses_the_rank_at_the_exit_rebalance(exit_rank, want_band, fallback, bps):
    o = exit_order(exit_rank)                                  # B was HELD at rank 200; it is sold at `exit_rank`
    assert (o["side"], o["target_weight"], o["slippage_band"], bool(o["band_fallback"])) == ("SELL", 0.0, want_band, fallback)
    assert o["order_value_rs"] == pytest.approx(0.4 * CR)
    for s, b in zip(("S0", "S1", "S2", "S3", "S4"), bps):
        assert o[f"slippage_{s}_rs"] == pytest.approx(0.4 * CR * b / 1e4)
        assert o[f"cost_fraction_{s}"] == pytest.approx((o["total_cost_rs"] + 0.4 * CR * b / 1e4) / CR)


def test_slippage_applies_to_buys_and_sells_and_is_never_taxed():
    h, u, _, _ = make()
    plain, led = cost_ledger(h, S, portfolio="W"), cost_ledger(h, S, portfolio="W", ranks=rank_index(u))
    assert {"BUY", "SELL"} <= set(led["side"]) and (led["slippage_S1_rs"] > 0).all()
    pd.testing.assert_frame_equal(led[plain.columns], plain)                # class 1 costs and tax are unchanged
    assert (led["cost_fraction_S0"] == led["cost_fraction"]).all() and (led["slippage_S0_rs"] == 0).all()
    for a, b in zip(("S0", "S1", "S2", "S3"), ("S1", "S2", "S3", "S4")):
        assert (led[f"cost_fraction_{b}"] > led[f"cost_fraction_{a}"]).all()


def test_monthly_costs_count_the_low_band_and_the_fallback():
    for rank, low, fb in ((150.0, 0.0, 0), (201.0, 0.4, 0), (NAN, 0.4, 1)):
        h, u, _, cal = make(exit_rank=rank)
        mc = monthly_costs(cost_ledger(h, S, portfolio="W", ranks=rank_index(u))).set_index("t")
        assert mc.loc[cal[2][0], "traded_fraction_201_500"] == pytest.approx(low) and mc.loc[cal[2][0], "n_fallback"] == fb
        assert mc.loc[cal[2][0], "traded_fraction_fallback"] == pytest.approx(0.4 * fb)
        assert mc["traded_fraction_201_500"].sum() == pytest.approx(low)


# ------------------------------------------------------------------ first month and sample boundary
def test_first_month_is_a_full_purchase_from_cash_with_slippage():
    h, u, _, cal = make()
    for p in step_e.PORTFOLIOS:
        led = cost_ledger(h, S, portfolio=p, ranks=rank_index(u))
        first = led[led["t"] == cal[0][0]]
        held = h[(h["portfolio"] == p) & (h["t"] == cal[0][0])]
        assert (first["side"] == "BUY").all() and (first["drift_weight"] == 0).all() and len(first) == len(held)
        assert sorted(first["order_value_rs"]) == pytest.approx(sorted(held["begin_weight"] * CR))
        assert first["weight_change"].sum() == pytest.approx(1.0)           # the whole Rs 1 crore
        assert first["slippage_S4_rs"].sum() == pytest.approx(CR * 50 / 1e4) and (first["stamp_duty_rs"] > 0).all()
        assert (first["dp_charge_rs"] == 0).all()


def test_no_terminal_liquidation():
    h, u, _, cal = make()
    for p in step_e.PORTFOLIOS:
        led = cost_ledger(h, S, portfolio=p, ranks=rank_index(u))
        assert led["trade_date"].max() <= cal[-1][1] and cal[-1][2] not in set(led["trade_date"])
        assert not ((led["t"] == cal[-1][0]) & (led["target_weight"] == 0)).any()
        longer = cost_ledger(h[h["t"] != cal[-1][0]], S, portfolio=p, ranks=rank_index(u))      # one month fewer:
        pd.testing.assert_frame_equal(led[led["t"] != cal[-1][0]].reset_index(drop=True), longer)  # no sale appears at its end


def test_each_sample_starts_from_cash_independently():
    h, u, _, _ = make()
    h2, u2, _, cal2 = make(first="2022-01-31", sample="OOS")
    led = cost_ledger(h2, S, portfolio="W", ranks=rank_index(u2))
    assert (led[led["t"] == cal2[0][0]]["side"] == "BUY").all() and led[led["t"] == cal2[0][0]]["weight_change"].sum() == pytest.approx(1.0)
    with pytest.raises(CostScheduleError, match="mix samples"):
        cost_ledger(pd.concat([h, h2]), S, portfolio="W", ranks=rank_index(pd.concat([u, u2])))


# ------------------------------------------------------------------ net returns, hypothetical L and WML
def costed(**kw):
    h, u, m, cal = make(**kw)
    ledger = pd.concat([cost_ledger(h, S, portfolio=p, ranks=rank_index(u)) for p in step_e.PORTFOLIOS], ignore_index=True)
    return net_returns(m, monthly_costs(ledger), h), ledger, m, cal


def test_net_returns_copy_gross_and_deduct_the_cost_of_each_scenario():
    net, ledger, m, cal = costed()
    assert net["gross_W"].tolist() == m["W"].tolist() and net["gross_WML"].tolist() == m["WML"].tolist()
    for s in step_e.SLIPPAGE_BPS:
        for p, col in (("W", "W"), ("BM", "BM"), ("L", "hypothetical_{}_L")):
            cost = ledger[ledger["portfolio"] == p].groupby("t")[f"cost_fraction_{s}"].sum().reindex(net["t"]).fillna(0.0).tolist()
            c, n = (col.format("cost"), col.format("net")) if "{}" in col else (f"cost_{col}", f"net_{col}")
            assert net[f"{c}_{s}"].tolist() == pytest.approx(cost)
            assert net[f"{n}_{s}"].tolist() == pytest.approx((m[p] - pd.Series(cost)).tolist())
        assert net[f"net_excess_W_over_BM_{s}"].tolist() == pytest.approx((net[f"net_W_{s}"] - net[f"net_BM_{s}"]).tolist())
    assert net["hypothetical_cost_L_S0"].tolist()[1:] == [0.0] * 5        # L never trades again: no order, no cost
    assert net["traded_fraction_W"].tolist() == pytest.approx([1.0, 0.2, 1.0, 0, 0, 0])
    assert net["one_way_turnover_W"].tolist() == pytest.approx((net["traded_fraction_W"] / 2).tolist())
    assert not [c for c in net.columns if "L" in c.split("_") and c.startswith(("cost", "net"))]   # L cost/net: hypothetical only
    assert {"traded_fraction_L", "one_way_turnover_L"} <= set(net.columns)                        # L turnover: §23, as ruled


def test_hypothetical_net_wml_deducts_the_costs_of_both_legs():
    net, _, m, _ = costed()
    for s in step_e.SLIPPAGE_BPS:
        w, l = net[f"cost_W_{s}"], net[f"hypothetical_cost_L_{s}"]
        assert net[f"hypothetical_net_WML_{s}"].tolist() == pytest.approx((m["WML"] - w - l).tolist())
        assert net[f"hypothetical_net_WML_{s}"].iloc[0] < m["WML"].iloc[0] - w.iloc[0]          # L's cost LOWERS it
        naive = net[f"net_W_{s}"] - net[f"hypothetical_net_L_{s}"]                              # the withdrawn formula
        assert naive.iloc[0] - net[f"hypothetical_net_WML_{s}"].iloc[0] == pytest.approx(
            (m["W"] - m["L"] - m["WML"]).iloc[0] + 2 * l.iloc[0])
    assert l.iloc[0] > 0


def test_net_returns_refuse_months_that_do_not_match():
    h, u, m, cal = make()
    costs = monthly_costs(pd.concat([cost_ledger(h, S, portfolio=p, ranks=rank_index(u)) for p in step_e.PORTFOLIOS]))
    for bad in (m[m["t"] != cal[3][0]], pd.concat([m, m.iloc[[0]]]), m.assign(W=[NAN] + [0.03] * 5)):
        with pytest.raises(CostScheduleError, match="do not match one to one"):
            net_returns(bad, costs, h)
    with pytest.raises(CostScheduleError):
        net_returns(m, costs[costs["portfolio"] != "L"], h)
    with pytest.raises(CostScheduleError):                                  # a portfolio without one of the months
        net_returns(m, costs, h[~((h["portfolio"] == "L") & (h["t"] == cal[5][0]))])


# ------------------------------------------------------------------ H3 -> H4 and break-even
def test_one_sided_test_is_the_registered_newey_west_test():
    x = [0.02, -0.01, 0.03, 0.01, 0.0, 0.02, -0.005, 0.015]
    r, ref = one_sided_test(x, 4), stats.mean_test([v * 100 for v in x], 4)
    assert (r["t"], r["mean_pct"], r["lag"]) == (ref["t"], ref["mean"], 4)
    assert r["p_one_sided"] == pytest.approx(norm.sf(ref["t"])) == pytest.approx(ref["p_two_sided"] / 2)
    assert one_sided_test([-v for v in x], 4)["supported"] is False and step_e.NW_LAG == {"PRIMARY": 4, "OOS": 3, "POOLED": 4}


def test_h4_and_break_even_only_in_the_primary_sample_with_h3_supported():
    net, _, _, _ = costed()
    r = step_e.summarise("PRIMARY", net)
    assert r["H3"]["supported"] and r["H3"]["lag"] == 4
    assert r["H4"] == one_sided_test(net["net_excess_W_over_BM_S0"], 4)
    x, d = net["net_excess_W_over_BM_S0"].mean(), (net["traded_fraction_W"] - net["traded_fraction_BM"]).mean()
    assert d == pytest.approx(1.2 / 6)                                      # the first month (1 - 1) adds nothing
    assert r["break_even"]["break_even_one_way_cost_bps"] == pytest.approx(x / d * 1e4) and r["break_even"]["status"] == "OK"
    assert set(r["scenarios"]) == {"S0", "S1", "S2", "S3", "S4"}
    assert r["scenarios"]["S0"]["net_W"] > r["scenarios"]["S4"]["net_W"]
    oos, _, _, _ = costed(first="2022-01-31", sample="OOS", wml=(0.01, -0.01, 0.01, -0.01, 0.01, -0.01))
    c = step_e.summarise("OOS", oos)
    assert c["H3"]["supported"] is False and c["H3"]["lag"] == 3
    assert c["H4"]["status"].startswith("NOT RUN") and c["break_even"]["status"].startswith("NOT RUN")
    assert "t" not in c["H4"] and "break_even_one_way_cost_bps" not in c["break_even"]
    assert set(c["scenarios"]) == set(r["scenarios"])                       # S0-S4 are still reported for confirmation


def test_h3_that_differs_from_the_registered_decision_is_refused():
    net, _, _, _ = costed(wml=(0.01, -0.01, 0.01, -0.01, 0.01, -0.01))
    with pytest.raises(CostScheduleError, match="registered decision"):
        step_e.summarise("PRIMARY", net)
    oos, _, _, _ = costed(first="2022-01-31", sample="OOS")
    with pytest.raises(CostScheduleError, match="registered decision"):
        step_e.summarise("OOS", oos)


def test_break_even_and_its_undefined_cases():
    assert break_even(0.001, 0.2)["break_even_one_way_cost_bps"] == pytest.approx(50.0)
    for x, d, text in ((0.001, 0.0, step_e.NO_BREAK_EVEN), (0.001, -0.1, step_e.NO_BREAK_EVEN), (0.0, 0.2, step_e.FAILS_S0),
                       (-0.001, 0.2, step_e.FAILS_S0), (-0.001, -0.1, step_e.NO_BREAK_EVEN + " " + step_e.FAILS_S0)):
        r = break_even(x, d)
        assert r["break_even_one_way_cost_bps"] is None and r["status"] == text
    assert step_e.NO_BREAK_EVEN == "no break-even: W does not trade more than benchmark." and step_e.FAILS_S0 == "does not pass S0."
    with pytest.raises(CostScheduleError):
        break_even(NAN, 0.2)


# ------------------------------------------------------------------ documents
def test_supplements_2_and_3_are_pinned_and_checked(tmp_path):
    for rel, want in step_e.SUPPLEMENTS.items():
        assert sha(ROOT / rel) == want
    for rel in [*step_e.PARENTS.values(), *step_e.SUPPLEMENTS]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes((ROOT / rel).read_bytes())
    step_e.load_schedule(root=tmp_path)
    (tmp_path / list(step_e.SUPPLEMENTS)[1]).write_text("edited")
    with pytest.raises(CostScheduleError, match="differs from its registered hash"):
        step_e.load_schedule(root=tmp_path)


# ------------------------------------------------------------------ the runner (synthetic files in a temp directory)
@pytest.fixture
def sandbox(tmp_path):
    hp, up, mp, _ = make()
    ho, uo, mo, _ = make(first="2022-01-31", sample="OOS", wml=(0.01, -0.01, 0.01, -0.01, 0.01, -0.01))
    files = {k: tmp_path / rel for k, (rel, _) in runner.INPUTS.items()}
    for f in files.values():
        f.parent.mkdir(parents=True, exist_ok=True)
    extra = hp.assign(step="C", liquidity_rank=999)                         # other ladder steps are in the file, never costed
    pd.concat([hp, extra]).to_csv(files["primary_holdings"], index=False)
    pd.concat([mp, mp.assign(step="C", W=9.0)]).to_csv(files["primary_monthly"], index=False)
    ho.to_csv(files["confirmation_holdings"], index=False)
    mo.to_csv(files["confirmation_monthly"], index=False)
    pd.concat([up, uo]).assign(segment_at_selection="x", liquidity_median_value=1.0).to_parquet(files["univ1"])
    inputs = {k: (rel, sha(tmp_path / rel)) for k, (rel, _) in runner.INPUTS.items()}
    return tmp_path, inputs, tmp_path / "out"


@pytest.fixture
def reads(monkeypatch):
    seen = []
    for fn in ("read_csv", "read_parquet"):
        real = getattr(pd, fn)
        monkeypatch.setattr(runner.pd, fn, lambda p, *a, _real=real, **k: (seen.append(Path(p)), _real(p, *a, **k))[1])
    return seen


def test_runner_end_to_end_on_synthetic_files(sandbox, reads):
    root, inputs, out = sandbox
    before = {rel: sha(root / rel) for rel, _ in inputs.values()}
    files = runner.run(root=root, inputs=inputs, out=out)
    assert sorted(files) == ["confirmation_step_e_ledger.csv", "confirmation_step_e_monthly.csv", "primary_step_e_ledger.csv",
                             "primary_step_e_monthly.csv", "step_e_results.json"]
    assert sorted(reads) == sorted(root / rel for rel, _ in inputs.values())               # exactly the five, once each
    assert before == {rel: sha(root / rel) for rel, _ in inputs.values()}                  # inputs untouched
    assert sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()) == sorted(
        [*before, *(f"out/{f}" for f in files)])                                           # nothing written anywhere else
    res = json.loads((out / "step_e_results.json").read_text())
    assert res["inputs_sha256"] == dict(inputs.values()) and "HYPOTHETICAL" in res["statement"] and "pre-specified" in res["statement"]
    p, c = res["samples"]["primary"], res["samples"]["confirmation"]
    assert p["sample"] == "PRIMARY" and p["months"] == 6 and "t" in p["H4"] and p["break_even"]["status"] == "OK"
    assert c["sample"] == "OOS" and c["H4"]["status"].startswith("NOT RUN") and c["break_even"]["status"].startswith("NOT RUN")
    assert {(o["portfolio"], o["band"]) for o in p["orders_by_band"]} == {("W", "1-200"), ("W", "201-500"), ("L", "1-200"), ("BM", "1-200")}
    led = pd.read_csv(out / "primary_step_e_ledger.csv")
    assert set(led["step"]) == {"D"} and set(led["portfolio"]) == {"W", "L", "BM"} and 999 not in set(led["univ1_rank"])
    monthly = pd.read_csv(out / "primary_step_e_monthly.csv")
    assert monthly["gross_W"].tolist() == [0.03] * 6
    assert all("hypothetical" in col for col in monthly.columns if "WML" in col and "gross" not in col)


def test_runner_refuses_an_input_whose_hash_differs_before_any_read(sandbox, reads):
    root, inputs, out = sandbox
    for key in inputs:
        f = root / inputs[key][0]
        original = f.read_bytes()
        f.write_bytes(original + b"\n")
        with pytest.raises(NotReady, match="does not match its registered SHA-256"):
            runner.run(root=root, inputs=inputs, out=out)
        f.write_bytes(original)
        assert reads == [] and not out.exists()


def test_runner_never_overwrites_existing_output(sandbox, reads):
    root, inputs, out = sandbox
    out.mkdir()
    (out / "step_e_results.json").write_text("protected")
    with pytest.raises(NotReady, match="already exists"):
        runner.run(root=root, inputs=inputs, out=out)
    assert (out / "step_e_results.json").read_text() == "protected" and reads == [] and len(list(out.iterdir())) == 1
    out2 = root / "out2"
    first = runner.run(root=root, inputs=inputs, out=out2)
    with pytest.raises(NotReady, match="already exists"):                   # a second run is refused as well
        runner.run(root=root, inputs=inputs, out=out2)
    assert first == {p.name: sha(p) for p in out2.iterdir()}


def test_runner_does_not_guard_benchmark_ranks_but_guards_w_and_l(sandbox):
    root, inputs, out = sandbox
    f = root / inputs["primary_holdings"][0]
    h = pd.read_csv(f)
    h.loc[h["portfolio"] == "BM", "liquidity_rank"] = NAN                   # benchmark rows carry no usable saved rank
    h.to_csv(f, index=False)
    fixed = {**inputs, "primary_holdings": (inputs["primary_holdings"][0], sha(f))}
    assert "step_e_results.json" in runner.run(root=root, inputs=fixed, out=out)
    h.loc[(h["portfolio"] == "L") & (h["step"] == "D"), "liquidity_rank"] = NAN
    h.to_csv(f, index=False)
    with pytest.raises(CostScheduleError, match="differs from the saved liquidity_rank"):
        runner.run(root=root, inputs={**inputs, "primary_holdings": (inputs["primary_holdings"][0], sha(f))}, out=root / "out_l")
    assert not (root / "out_l").exists()


@pytest.fixture
def registry(monkeypatch):
    """Recorders in place of the real registry: no test ever writes registry/ or the trials log."""
    calls = []
    monkeypatch.setattr(runner, "verify_protocol", lambda: {"provenance": {"primary_run": "kept"}})
    for name in ("amend", "log_trial", "write_md"):
        monkeypatch.setattr(runner.experiments, name, lambda *a, _n=name, **k: calls.append((_n, a, k)))
    return calls


def test_registration_only_after_a_complete_successful_run(sandbox, registry, monkeypatch):
    root, inputs, out = sandbox
    for failure in (NotReady("refused"), CostScheduleError("failed"), KeyboardInterrupt()):
        monkeypatch.setattr(runner, "run", lambda e=failure: (_ for _ in ()).throw(e))
        with pytest.raises(type(failure)):
            runner.main()
        assert registry == []                                               # refused, failed, interrupted: nothing registered
    monkeypatch.setattr(runner, "run", lambda: runner.__dict__["_real_run"](root=root, inputs=inputs, out=out))
    runner.main()
    assert [c[0] for c in registry] == ["amend", "log_trial", "write_md"]
    files = {p.name: sha(p) for p in out.iterdir()}                         # registered hashes = the finished files
    run = registry[0][2]["provenance"]["step_e_run"]
    assert run["files_sha256"] == files and run["results_sha256"] == files["step_e_results.json"] and run["code_sha256"] == runner.code_sha()
    assert registry[0][2]["provenance"]["primary_run"] == "kept" and registry[1][1][3] == {"results_sha256": files["step_e_results.json"]}


def test_a_run_that_fails_while_writing_leaves_no_final_directory_and_is_not_rerun(sandbox, registry, monkeypatch):
    root, inputs, out = sandbox
    real, n = pd.DataFrame.to_csv, []

    def failing(self, *a, **k):
        n.append(1)
        if len(n) == 3:
            raise OSError("disk full")
        return real(self, *a, **k)
    monkeypatch.setattr(pd.DataFrame, "to_csv", failing)
    monkeypatch.setattr(runner, "run", lambda: runner.__dict__["_real_run"](root=root, inputs=inputs, out=out))
    with pytest.raises(OSError):
        runner.main()
    monkeypatch.setattr(pd.DataFrame, "to_csv", real)
    assert registry == [] and not out.exists() and (root / "out.partial").is_dir()
    left = {q.name: sha(q) for q in (root / "out.partial").iterdir()}
    with pytest.raises(NotReady, match="already exists"):                   # the partial output is never overwritten or deleted
        runner.main()
    assert registry == [] and not out.exists() and left == {q.name: sha(q) for q in (root / "out.partial").iterdir()}


def test_runner_writes_nothing_when_a_rank_or_identifier_is_invalid(sandbox):
    root, inputs, out = sandbox
    u = pd.read_parquet(root / inputs["univ1"][0])
    for bad in (u.assign(rank=u["rank"] + 1),                                # formation rank mismatch
                u[u["entity_id"] != "A"],                                    # a held stock with no UNIV-1 row
                pd.concat([u, u.iloc[[0]]]),                                 # duplicate key
                u.assign(entity_id=u["entity_id"].where(u["entity_id"] != "E"))):   # null key
        bad.to_parquet(root / inputs["univ1"][0])
        fixed = {**inputs, "univ1": (inputs["univ1"][0], sha(root / inputs["univ1"][0]))}
        with pytest.raises(CostScheduleError):
            runner.run(root=root, inputs=fixed, out=out)
        assert not out.exists()


def test_runner_refuses_files_of_the_wrong_sample(sandbox):
    root, inputs, out = sandbox
    swapped = {**inputs, "primary_holdings": inputs["confirmation_holdings"], "confirmation_holdings": inputs["primary_holdings"]}
    with pytest.raises(NotReady, match="do not hold"):
        runner.run(root=root, inputs=swapped, out=out)
    assert not out.exists()


# ------------------------------------------------------------------ the input boundary (static; real files are hashed only)
def test_runner_inputs_are_exactly_the_five_registered_in_supplement_3():
    supp3 = (ROOT / "docs/research/phase3a_momentum_protocol_addendum1_supplement3.md").read_text()
    assert len(runner.INPUTS) == 5
    for rel, want in runner.INPUTS.values():
        assert f"`{rel}` | `{want}`" in supp3 and sha(ROOT / rel) == want
    assert runner.INPUTS["univ1"][1] == step_e.UNIV1_SHA256


def test_runner_reads_no_other_file_and_no_raw_market_data():
    src = (ROOT / "scripts/run_s2_mom_step_e.py").read_text()
    tree = ast.parse(src)
    calls = [getattr(n.func, "attr", getattr(n.func, "id", None)) for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert calls.count("read_csv") == 2 and calls.count("read_parquet") == 1
    assert not {"open", "read_excel", "read_json", "read_table", "load_csv", "load_clean", "load_ret", "load_univ", "glob", "rglob"} & set(calls)
    paths = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and n.value.endswith((".csv", ".parquet")) and "/" in n.value}
    assert paths == {rel for rel, _ in runner.INPUTS.values()}
    code = src.split('"""', 2)[2]                                            # the code, without its docstring
    for banned in ("data/raw", "data/india", "ret1", "id1_", "stage2/datasets", "build_stage", "stage3.data", "stage3.ladder",
                   "stage3.experiment", "stage3.costs", "src.stage2"):
        assert banned not in code, banned
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert imports == {"pathlib", "src.config", "src.registry", "src.stage3", "src.stage3.protocol"}
    assert 'sys.argv[1:] != ["execute"]' in src                              # never runs on import or without the word


def test_one_access_boundary_entry_for_step_e():
    entries = [k for k in boundary.RAW_ACCESS_ALLOWED if "step_e" in k]
    assert entries == ["scripts/run_s2_mom_step_e.py"] and "src/stage3/step_e.py" not in boundary.RAW_ACCESS_ALLOWED
    module = ast.parse(Path(step_e.__file__).read_text())
    assert not [n for n in ast.walk(module) if isinstance(n, ast.Call)
                and getattr(n.func, "attr", getattr(n.func, "id", None)) in ("read_csv", "read_parquet", "to_csv", "to_parquet")]


STEP_E_OUTPUTS = {   # the single registered execution of 2026-10-06; NEVER update
    "primary_step_e_ledger.csv": "75d0fbb0ae2eedda5970836d66c6961f6203e0c3d4bf63134421371dc3397352",
    "primary_step_e_monthly.csv": "3ec30ebdd256234c61bd82292dc01b3acbf582e94eec7f558f06f715b8b3dfd7",
    "confirmation_step_e_ledger.csv": "547c7be5adfc82d6fc62b7517b698c14199032d8041a34b84de61ea9a5ac1037",
    "confirmation_step_e_monthly.csv": "f43b4a4d9d9898a45ff2d46fa3e0381b1386ec35f4a8e3d92de898d5a2f10638",
    "step_e_results.json": "675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0",
}


def test_registered_step_e_outputs_are_intact_and_outside_the_registered_results():
    """Post-execution integrity. The files are hashed only; nothing is recomputed."""
    out, registered_dir = ROOT / "results" / "s2_mom_v1_step_e", ROOT / "results" / "s2_mom_v1"
    assert runner.OUT == out and out.is_dir()
    assert {p.name: sha(p) for p in out.iterdir()} == STEP_E_OUTPUTS                 # exactly the five files, unchanged
    records = [json.loads(line) for line in (ROOT / "registry" / "experiments.jsonl").read_text().splitlines()]
    runs = [r["provenance"]["step_e_run"] for r in records if "step_e_run" in (r.get("provenance") or {})]
    assert runs and all(r == runs[0] for r in runs)                                  # one execution, never re-registered differently
    assert runs[0]["files_sha256"] == STEP_E_OUTPUTS and runs[0]["results_sha256"] == STEP_E_OUTPUTS["step_e_results.json"]
    trials = [json.loads(line) for line in (ROOT / "registry" / "trials.jsonl").read_text().splitlines()]
    assert [t["headline"] for t in trials if t["source"] == "scripts/run_s2_mom_step_e.py"] == [
        {"results_sha256": STEP_E_OUTPUTS["step_e_results.json"]}]                   # exactly one logged run
    before = {}                                                                      # results/s2_mom_v1: the 12 registered files only
    for r in records:
        prov = r.get("provenance") or {}
        for run in ("primary_run", "confirmation_run"):
            before.update((prov.get(run) or {}).get("files_sha256") or {})
    listed = sorted(p.name for p in registered_dir.iterdir())
    assert listed == sorted([*before, "blinded_precision.json", "sensitivity_results.json"]) and len(listed) == 12
    assert not [n for n in listed if "step_e" in n]
    assert sorted(p.name for p in (ROOT / "results").iterdir() if "step_e" in p.name) == ["s2_mom_v1_step_e"]   # no .partial, no copy
