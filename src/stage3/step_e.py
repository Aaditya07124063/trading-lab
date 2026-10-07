"""S2-MOM-v1 step E: costs from the SAVED holdings (frozen §13, Addendum 1, Supplements 1-3).

New code, separate from the registered experiment code (src/stage3/costs.py, ladder.py,
experiment.py), which it does not import and does not change. It reads the holdings saved by the
registered runs and the dated cost schedule; it never recomputes or rewrites a gross return.

Rules applied (Addendum 1, rules 1-6):
  - each portfolio is Rs 1 crore at EVERY rebalance (no compounding);
  - one order per stock per rebalance; order value = |target weight - drifted weight| x Rs 1 crore;
  - target weight = saved begin_weight; drifted weight = the previous month's saved end_weight;
  - every rate is the one in force on the trade date (the entry session s_plus), nothing later;
  - indirect tax on (brokerage + exchange charge + IPFT + SEBI fee) only;
  - a stock whose target is below its drifted weight is sold: the depository charge, tax included
    as billed, is charged once for it, whatever the size of the reduction.
Conventions that follow the registered code (ladder.net_of_costs): the first month of a sample is a
full purchase from cash; nothing is charged for liquidating the last month.

A missing schedule period, a missing rate, a gap between months or a changed schedule file raises.
No cost is ever assumed or set to zero.

Supplement 2 (rulings 8-16) and Supplement 3 (rulings 19-20):
  - slippage S0-S4 (pre-specified cost scenarios): one-way bps on traded value, buys and sells,
    outside the tax base; band from the stock's UNIV-1 rank at the selection date of the rebalance
    where the order trades; above rank 500 or unranked takes the 201-500 rate, flagged as a fallback;
  - join: holdings (t, entity) -> UNIV-1 (selection_date, entity_id), nothing else; a null or
    duplicate key, a missing row or an invalid rank raises before any cost;
  - formation-rank guard (ruling 21): for W and L only, every held stock's UNIV-1 rank must equal
    its saved liquidity_rank, or the run stops before any cost. The benchmark is not a ranked
    selection and is not guarded; its slippage band still comes from the same UNIV-1 lookup;
  - W and the benchmark are costed; L is costed as a HYPOTHETICAL long portfolio;
    hypothetical net WML = gross WML - cost of W - cost of L;
  - H4 (primary sample only, only if H3 is supported) and the break-even x / d.

This module opens no data file and writes nothing. The caller (scripts/run_s2_mom_step_e.py) passes
the saved *_holdings.csv, *_monthly.csv and UNIV-1 key/rank columns as frames.
"""

import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from src.stage3 import stats
from src.stage3.protocol import ALPHA, NOTIONAL_RS, NW_LAG, SLIPPAGE_BPS, UNIV1_SHA256  # noqa: F401 (UNIV-1 pin, re-exported)

ROOT = Path(__file__).resolve().parents[2]
SCHEDULE = ROOT / "config" / "cost_schedules" / "delivery_nse_eq_s2mom_v1_dated.json"
SCHEDULE_SHA256 = "47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f"
PARENTS = {"protocol_sha256": "docs/research/phase3a_momentum_protocol.md",
           "addendum1_sha256": "docs/research/phase3a_momentum_protocol_addendum1_costs.md",
           "supplement1_sha256": "docs/research/phase3a_momentum_protocol_addendum1_supplement1.md"}

AD_VALOREM = ("stt_buy", "stt_sell", "stamp_duty_buy", "exchange_txn", "ipft", "sebi_fee")
COMPONENTS = AD_VALOREM + ("indirect_tax", "brokerage", "dp_charge")
TAX_BASE = ["brokerage", "exchange_txn", "ipft", "sebi_fee"]
SUPPLEMENTS = {   # registered after the schedule was approved, so pinned here and not in the schedule
    "docs/research/phase3a_momentum_protocol_addendum1_supplement2.md": "6c373c5ff0db321cb753fff7a08db078ff29ca2c3f2f0cfbe8c0fb1431e6a888",
    "docs/research/phase3a_momentum_protocol_addendum1_supplement3.md": "682191de462bac3b5d2901995be8d20d355bb4d6146fd87a3f02ed8c6c2580ce"}
PORTFOLIOS = ("W", "L", "BM")                       # L is costed as a hypothetical long portfolio (ruling 14)
RANK_GUARDED = ("W", "L")                           # ruling 21: the formation-rank guard is not applied to the benchmark
BAND_TOP, BAND_LOW = "1-200", "201-500"
H3_REGISTERED = {"PRIMARY": True, "OOS": False}     # Supplement 2 §6, from the registered step D results
NO_BREAK_EVEN = "no break-even: W does not trade more than benchmark."
FAILS_S0 = "does not pass S0."
COST_COLUMNS = ["stt_rs", "stamp_duty_rs", "exchange_txn_rs", "ipft_rs", "sebi_fee_rs", "brokerage_rs",
                "indirect_tax_rs", "dp_charge_rs"]


class CostScheduleError(Exception):
    """The schedule cannot give a rate, or the holdings cannot be costed under the frozen rules."""


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _day(x):
    return x if isinstance(x, dt.date) and not isinstance(x, dt.datetime) else pd.Timestamp(x).date()


def validate(schedule):
    """Every component present, every period with a rate, periods contiguous over the sample, and
    the conventions this module implements. Raises CostScheduleError otherwise."""
    comps, conv = schedule["components"], schedule["conventions"]
    if set(comps) != set(COMPONENTS):
        raise CostScheduleError(f"components differ: {sorted(set(comps) ^ set(COMPONENTS))}")
    if (conv["indirect_tax_base"] != TAX_BASE or conv["notional_rs_per_portfolio"] != NOTIONAL_RS
            or conv["orders_per_stock_per_rebalance"] != 1 or conv["compounding"] is not False):
        raise CostScheduleError("schedule conventions differ from the ones this module implements")
    lo, hi = _day(schedule["sample"]["from"]), _day(schedule["sample"]["to"])
    for name, periods in comps.items():
        if not periods or _day(periods[0]["from"]) != lo or _day(periods[-1]["to"]) != hi:
            raise CostScheduleError(f"{name}: periods do not span {lo}..{hi}")
        for i, p in enumerate(periods):
            v = p.get("billed_rs" if name == "dp_charge" else "rate")
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v != v or v < 0:
                raise CostScheduleError(f"{name} {p.get('from')}: missing or invalid rate")
            if name == "brokerage" and not isinstance(p.get("cap_rs_per_order"), (int, float)):
                raise CostScheduleError(f"brokerage {p.get('from')}: missing cap")
            if i and _day(p["from"]) != _day(periods[i - 1]["to"]) + dt.timedelta(days=1):
                raise CostScheduleError(f"{name}: gap or overlap at {p['from']}")
    return schedule


def load_schedule(path=SCHEDULE, expected_sha256=SCHEDULE_SHA256, root=ROOT):
    """The approved schedule, byte-checked against its approved hash and its parent documents."""
    if _sha(path) != expected_sha256:
        raise CostScheduleError(f"{path} is not the approved schedule (SHA-256 differs)")
    schedule = validate(json.loads(Path(path).read_text()))
    for key, rel in PARENTS.items():
        if _sha(Path(root) / rel) != schedule["parents"][key]:
            raise CostScheduleError(f"{rel} differs from the hash recorded in the schedule")
    for rel, sha in SUPPLEMENTS.items():
        if _sha(Path(root) / rel) != sha:
            raise CostScheduleError(f"{rel} differs from its registered hash")
    return schedule


def rank_index(univ):
    """{(selection_date, entity_id): rank} from UNIV-1 key and rank columns. A null or duplicate key raises."""
    key = ["selection_date", "entity_id"]
    if univ[key].isna().any().any():
        raise CostScheduleError("UNIV-1 has a null selection_date or entity_id")
    if univ.duplicated(key).any():
        raise CostScheduleError("UNIV-1 has a duplicate (selection_date, entity_id) key")
    return dict(zip(zip(pd.to_datetime(univ["selection_date"]), univ["entity_id"]), univ["rank"].astype(float)))


def rank_at(ranks, t, entity):
    """UNIV-1 rank of `entity` at selection date `t`; NaN if its row carries no rank. A missing row
    raises: it is never replaced by another identifier or another date (ruling 20)."""
    try:
        return ranks[(pd.Timestamp(t), entity)]
    except KeyError:
        raise CostScheduleError(f"no UNIV-1 row for {entity} at {pd.Timestamp(t).date()}") from None


def check_formation_ranks(holdings, ranks):
    """Every held stock: UNIV-1 rank at its selection date == its saved liquidity_rank. Else raises."""
    for t, e, saved in zip(holdings["t"], holdings["entity"], holdings["liquidity_rank"]):
        if rank_at(ranks, t, e) != saved:                       # NaN on either side also fails
            raise CostScheduleError(f"{e} at {pd.Timestamp(t).date()}: UNIV-1 rank differs from the saved liquidity_rank")


def band(rank):
    """(slippage band, is_fallback) for the UNIV-1 rank at the rebalance where the order trades.
    Above 500 or unranked: the 201-500 band, as a labelled assumption (ruling 11)."""
    if rank != rank:
        return BAND_LOW, True
    if rank < 1 or rank != int(rank):
        raise CostScheduleError(f"invalid UNIV-1 rank {rank}")
    return (BAND_TOP, False) if rank <= 200 else (BAND_LOW, rank > 500)


def period(schedule, component, day):
    """The one period of `component` in force on `day`. Uses that date only; raises if none."""
    d = _day(day)
    hits = [p for p in schedule["components"][component] if _day(p["from"]) <= d <= _day(p["to"])]
    if len(hits) != 1:
        raise CostScheduleError(f"{component}: {len(hits)} schedule periods for {d}; no cost is calculated")
    return hits[0]


def periods_on(schedule, day):
    """The period of every component in force on `day`."""
    return {c: period(schedule, c, day) for c in COMPONENTS}


def order_cost(schedule, trade_date, weight_change, notional=NOTIONAL_RS, p=None):
    """Every class 1 cost of ONE order, in rupees, with the schedule period behind each.
    weight_change = target weight - drifted weight; positive is a buy, negative a sale.
    `p` may carry periods_on(schedule, trade_date) to avoid looking them up for every order."""
    if weight_change == 0 or weight_change != weight_change:
        raise CostScheduleError("no order exists for a zero or undefined weight change")
    p = p or periods_on(schedule, trade_date)
    buy = weight_change > 0
    value = abs(weight_change) * notional
    c = {"stt_rs": value * p["stt_buy" if buy else "stt_sell"]["rate"],
         "stamp_duty_rs": value * p["stamp_duty_buy"]["rate"] if buy else 0.0,
         "exchange_txn_rs": value * p["exchange_txn"]["rate"],
         "ipft_rs": value * p["ipft"]["rate"],
         "sebi_fee_rs": value * p["sebi_fee"]["rate"],
         "brokerage_rs": min(value * p["brokerage"]["rate"], p["brokerage"]["cap_rs_per_order"])}
    c["tax_base_rs"] = sum(c[k + "_rs"] for k in TAX_BASE)
    c["indirect_tax_rate"] = p["indirect_tax"]["rate"]
    c["indirect_tax_rs"] = c["tax_base_rs"] * p["indirect_tax"]["rate"]
    c["dp_charge_rs"] = 0.0 if buy else float(p["dp_charge"]["billed_rs"])      # tax already inside; never taxed again
    unused = ("stt_sell", "dp_charge") if buy else ("stt_buy", "stamp_duty_buy")
    used = [k for k in COMPONENTS if k not in unused]
    return {"side": "BUY" if buy else "SELL", "order_value_rs": value, **c,
            "total_cost_rs": sum(c[k] for k in COST_COLUMNS),
            "assumptions": ";".join(f"{k}:{p[k]['basis']}" for k in used if p[k]["assumption"]),
            **{f"{k}_period_from": p[k]["from"] if k in used else "" for k in COMPONENTS}}      # "" = not charged on this side


def cost_ledger(holdings, schedule, step="D", portfolio="W", notional=NOTIONAL_RS, ranks=None):
    """One row per order: (rebalance, stock) with a non-zero weight change, in a fixed order.
    `holdings` is a saved *_holdings.csv frame; it is read, never changed.
    With `ranks` (rank_index of UNIV-1) every order also gets its slippage band and its cost under
    S0-S4; for W and L the formation-rank guard runs first, before any cost (ruling 21)."""
    h = holdings[(holdings["step"] == step) & (holdings["portfolio"] == portfolio)]
    if h.empty:
        raise CostScheduleError(f"no saved holdings for step {step}, portfolio {portfolio}")
    if h["sample"].nunique() != 1 or (h["month_status"] != "OK").any() or h[["begin_weight", "end_weight"]].isna().any().any():
        raise CostScheduleError("holdings mix samples, or hold a month that is not OK, or lack a weight")
    if ranks is not None and portfolio in RANK_GUARDED:
        check_formation_ranks(h, ranks)
    rows, drift, prev_exit = [], {}, None
    for t in sorted(h["t"].unique()):
        g = h[h["t"] == t]
        s_plus, s_pp = g["s_plus"].iloc[0], g["s_pp"].iloc[0]
        if prev_exit is not None and prev_exit != s_plus:
            raise CostScheduleError(f"holding months are not consecutive at {t}; the frozen rules do not cost a gap")
        if g["entity"].duplicated().any():
            raise CostScheduleError(f"duplicate stock at {t}")
        target, p = dict(zip(g["entity"], g["begin_weight"])), periods_on(schedule, s_plus)
        for e in sorted(set(target) | set(drift)):
            d = target.get(e, 0.0) - drift.get(e, 0.0)
            if d == 0:
                continue                                                    # no change, no order, no charge
            slip = {}
            if ranks is not None:                                       # rank at THIS rebalance, exits included
                r = rank_at(ranks, t, e)
                slip = dict(zip(("slippage_band", "band_fallback"), band(r)), univ1_rank=r)
            rows.append({"sample": g["sample"].iloc[0], "step": step, "portfolio": portfolio, "t": t,
                         "holding_month": g["holding_month"].iloc[0], "trade_date": s_plus, "entity": e,
                         "drift_weight": drift.get(e, 0.0), "target_weight": target.get(e, 0.0), "weight_change": d,
                         "notional_rs": notional, **order_cost(schedule, s_plus, d, notional, p), **slip})
        drift, prev_exit = dict(zip(g["entity"], g["end_weight"])), s_pp
    out = pd.DataFrame(rows)
    out["cost_fraction"] = out["total_cost_rs"] / notional
    if ranks is not None:
        for s, bps in SLIPPAGE_BPS.items():                             # slippage is never taxed
            out[f"slippage_{s}_rs"] = out["order_value_rs"] * out["slippage_band"].map(bps) / 1e4
            out[f"cost_fraction_{s}"] = (out["total_cost_rs"] + out[f"slippage_{s}_rs"]) / notional
    return out


def monthly_costs(ledger):
    """Class 1 cost of each rebalance as a fraction of the Rs 1 crore portfolio, with its parts."""
    by = ["sample", "step", "portfolio", "t", "holding_month", "trade_date"]
    g = ledger.groupby(by, sort=True)
    scen = [c for c in ledger.columns if c.startswith(("slippage_S", "cost_fraction_S"))]
    out = g[COST_COLUMNS + ["total_cost_rs", "cost_fraction"] + scen].sum()
    out["n_orders"], out["n_sold"] = g.size(), g["side"].agg(lambda s: int((s == "SELL").sum()))
    out["traded_fraction"] = g["weight_change"].agg(lambda s: float(s.abs().sum()))
    if scen:                                                            # how much trades outside the 1-200 band
        w = ledger["weight_change"].abs()
        out["traded_fraction_201_500"] = w.where(ledger["slippage_band"] == BAND_LOW, 0.0).groupby([ledger[c] for c in by]).sum()
        out["traded_fraction_fallback"] = w.where(ledger["band_fallback"], 0.0).groupby([ledger[c] for c in by]).sum()
        out["n_fallback"] = ledger["band_fallback"].groupby([ledger[c] for c in by]).sum()
    return out.reset_index()


def net_of_class1(monthly, costs, portfolio):
    """Gross and net-of-class-1 return per month (slippage scenario S0). `monthly` is a saved
    *_monthly.csv frame; the gross column is copied from it unchanged."""
    c = costs[costs["portfolio"] == portfolio]
    m = monthly[monthly["step"].isin(c["step"].unique())][["step", "t", portfolio]].rename(columns={portfolio: "gross"})
    out = m.merge(c[["step", "t", "cost_fraction"]], on=["step", "t"], how="inner", validate="one_to_one")
    if len(out) != len(c):
        raise CostScheduleError("a costed month has no saved gross return")
    out["net_S0"] = out["gross"] - out["cost_fraction"]
    return out


def net_returns(monthly, costs, holdings, step="D"):
    """One row per holding month: gross (copied, never recomputed), cost and net return of W, L and the
    benchmark under S0-S4, traded value and one-way turnover. `costs` holds monthly_costs of the
    three portfolios; `holdings` is the frame they were costed from and fixes which months exist.
    Everything about L, and the net WML, is hypothetical (ruling 14)."""
    m = monthly[monthly["step"] == step].set_index("t")[["W", "L", "BM", "WML"]]
    cols = [f"cost_fraction_{s}" for s in SLIPPAGE_BPS] + ["traded_fraction"]
    c = costs[costs["step"] == step].pivot(index="t", columns="portfolio", values=cols)
    held = holdings[holdings["step"] == step].groupby("portfolio")["t"].agg(set)
    if (m.index.duplicated().any() or m.isna().any().any() or set(held.index) != set(PORTFOLIOS)
            or any(months != set(m.index) for months in held) or not set(c.index) <= set(m.index)
            or set(c.columns.get_level_values(1)) != set(PORTFOLIOS)):
        raise CostScheduleError("costed months and saved gross returns do not match one to one")
    c = c.reindex(m.index).fillna(0.0)                                  # a rebalance with no order costs nothing
    out = m.add_prefix("gross_")
    name = {"W": "{}_W", "BM": "{}_BM", "L": "hypothetical_{}_L"}
    for s in SLIPPAGE_BPS:
        for p in PORTFOLIOS:
            out[name[p].format("cost") + f"_{s}"] = c[(f"cost_fraction_{s}", p)]
            out[name[p].format("net") + f"_{s}"] = m[p] - c[(f"cost_fraction_{s}", p)]
        out[f"hypothetical_net_WML_{s}"] = m["WML"] - c[(f"cost_fraction_{s}", "W")] - c[(f"cost_fraction_{s}", "L")]
        out[f"net_excess_W_over_BM_{s}"] = out[f"net_W_{s}"] - out[f"net_BM_{s}"]
    for p in PORTFOLIOS:
        out[f"traded_fraction_{p}"] = c[("traded_fraction", p)]
        out[f"one_way_turnover_{p}"] = c[("traded_fraction", p)] / 2    # frozen §23
    return out.reset_index()


def one_sided_test(x, lag):
    """H: mean > 0. Newey-West standard error, standard normal reference (frozen §15, as registered).
    `x` is a monthly series as a fraction; reported in percent per month."""
    r = stats.mean_test(np.asarray(x, dtype=float) * 100, lag)
    p = float(norm.sf(r["t"]))
    return {"n": r["n"], "mean_pct": r["mean"], "se_nw_pct": r["se_nw"], "t": r["t"], "lag": lag,
            "p_one_sided": p, "alpha": ALPHA, "supported": bool(r["mean"] > 0 and p < ALPHA)}


def break_even(x, d):
    """Ruling 12: x / d in bps, or the fixed text of each undefined case. No value is manufactured."""
    if x != x or d != d:
        raise CostScheduleError("break-even inputs are undefined")
    why = [text for bad, text in ((d <= 0, NO_BREAK_EVEN), (x <= 0, FAILS_S0)) if bad]
    return {"x_mean_net_excess_S0": x, "d_mean_traded_value_W_minus_BM": d,
            "break_even_one_way_cost_bps": None if why else x / d * 1e4, "status": " ".join(why) or "OK"}


def summarise(sample, net):
    """Means per scenario, turnover, H3, and - primary sample with H3 supported only - H4 and the
    break-even. `net` is net_returns of one sample."""
    h3 = one_sided_test(net["gross_WML"], NW_LAG[sample])
    if h3["supported"] != H3_REGISTERED[sample]:
        raise CostScheduleError(f"H3 for {sample} differs from the registered decision recorded in Supplement 2")
    mean = lambda col: float(net[col].mean())
    out = {"sample": sample, "months": len(net), "H3": h3,
           "gross_mean": {k: mean(f"gross_{k}") for k in ("W", "L", "BM", "WML")},
           "scenarios": {s: {"slippage_bps": SLIPPAGE_BPS[s],
                             **{k: mean(f"{k}_{s}") for k in ("cost_W", "cost_BM", "hypothetical_cost_L", "net_W", "net_BM",
                                                              "hypothetical_net_L", "hypothetical_net_WML",
                                                              "net_excess_W_over_BM")}} for s in SLIPPAGE_BPS},
           "mean_one_way_turnover": {p: mean(f"one_way_turnover_{p}") for p in PORTFOLIOS}}
    if sample == "PRIMARY" and h3["supported"]:
        out["H4"] = one_sided_test(net["net_excess_W_over_BM_S0"], NW_LAG["PRIMARY"])
        out["break_even"] = break_even(mean("net_excess_W_over_BM_S0"),
                                       float((net["traded_fraction_W"] - net["traded_fraction_BM"]).mean()))
    else:
        out["H4"] = out["break_even"] = {"status": "NOT RUN: H3 is not supported in this sample (frozen §17, ruling 13)"}
    return out
