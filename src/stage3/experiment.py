"""S2-MOM-v1 analyses on prepared inputs (protocol §2, §14-§15, B1.5, B2, §13, §25).

Pure functions of the inputs: they print nothing and write nothing. The runner
(scripts/run_s2_mom.py) is the only caller on real data and enforces the execution order.
"""

import copy
import hashlib
from collections import Counter

import numpy as np
import pandas as pd

from src.stage3 import costs, ladder, stats
from src.stage3.protocol import (ALPHA, BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, NW_LAG, REFERENCE_THRESHOLD,
                                 SLIPPAGE_BPS)


# §16/§25 sensitivity treatments. Each changes ONE rule of the corrected step D; the primary is untouched.
# Reviewer rulings of 2026-10-05 (sensitivity-only; none of this can reach the primary A-D calculation):
#   R-span is class-based, as §16 states it: EVERY SPECIAL_SESSION_SPAN row takes the raw two-session return.
#     No 1.4x exception is added. (One such row, ZEETELE 2024-01-23, is beyond that bound and stays included.)
#   R-gap "no event on the row" is an IMPLEMENTATION INTERPRETATION, not literal §16 wording:
#     event = a parsed bonus/split factor OR an unadjustable record; a dividend-only record is not an event.
#     The 1.4x bound is not applied to R-gap, because the frozen sentence does not name it.
SENSITIVITY = {
    "R_SPAN": {"span_raw": True},              # special-session spans use the raw two-session return
    "R_GAP": {"gap_raw": True},                # multi-session gaps with no event use the raw gap return
    "R_MISS_RAW": {"miss": "RAW"},             # a flagged holding day takes the stock's own raw return
    "R_MISS_ZERO": {"miss": "ZERO"},           # ... or zero
    "R_DELIST_ZERO": {"delist": "ZERO"},       # delisting return 0% for all
    "R_DELIST_MINUS100": {"delist": "MINUS100"},   # -100% for all non-voluntary delistings
}
RANKABLE_MIN, RANKABLE_MEAN, FILL_SHARE_MAX = 100, 150, 0.05      # §25 "not reliable" thresholds
PENDING = "COST-EVIDENCE-PENDING"
SENSITIVITY_PENDING = "SENSITIVITY-PENDING"


def run(inp, specs=ladder.STEP_SPECS, score_fn=None, w=None, cal=None, delist_ret=None, miss="FILL"):
    return ladder.run_ladder(inp.w if w is None else w, inp.cal if cal is None else cal, inp.univ, specs,
                             inp.delist_ret if delist_ret is None else delist_ret, score_fn, inp.data_end, miss)


def holdings_frame(inp, monthly, hold):
    """Everything needed later for turnover, cost and capacity without a second run: one row per
    (step, month, portfolio, stock) with its formation rank, begin weight and end weight."""
    cal = inp.cal.set_index("t")
    status = monthly.set_index(["step", "t"])["status"]
    rows = []
    for (step, t), h in hold.items():
        liq = inp.univ[(ladder.STEP_SPECS.get(step, ladder.REVERSE_SPECS.get(step))[0], t)].set_index("entity")["rank"]
        order = {e: n for n, e in enumerate(h["order"], 1)}
        for p in ("W", "L", "BM"):
            end = h.get(p + "_end", {})
            for e in h[p]:
                rows.append({"sample": inp.sample, "step": step, "t": t, "holding_month": cal.at[t, "holding_month"],
                             "s_plus": cal.at[t, "s_plus"], "s_pp": cal.at[t, "s_pp"], "month_status": status[(step, t)],
                             "portfolio": p, "entity": e, "formation_rank": order[e], "n_rankable": len(order),
                             "liquidity_rank": liq[e], "begin_weight": 1.0 / len(h[p]), "end_weight": end.get(e, np.nan)})
    return pd.DataFrame(rows).sort_values(["step", "t", "portfolio", "formation_rank"]).reset_index(drop=True)


def events(inp, hold):
    """Audit trail of every fill, booked gap return and delisting return, with the RET-1.1 status."""
    ev = pd.DataFrame([e for h in hold.values() for e in h["events"]],
                      columns=["t", "step", "portfolio", "kind", "entity", "date"])
    status = getattr(inp, "status", None)
    ev["ret1_1_status"] = None if status is None else [status.get((e, d)) for e, d in zip(ev["entity"], ev["date"])]
    return ev


# ------------------------------------------------------------------ real-data pre-run checks (B2, §25)
def _members(hold, upto):
    return {k: (v["W"], v["L"], v["BM"]) for k, v in hold.items() if k[1] <= upto}


def _perturbed(w, i, seed):
    """A copy of the matrices in which everything AFTER session i is scrambled: returns, flags."""
    rng, p = np.random.default_rng(seed), copy.copy(w)
    for name in ("ln", "lr", "lraw"):
        m = getattr(w, name).copy()
        m[i + 1:] = rng.normal(0.0, 0.2, m[i + 1:].shape) * w.present[i + 1:]
        setattr(p, name, m)
    flip = (rng.random(w.ok[i + 1:].shape) < 0.2) & w.present[i + 1:]
    p.ok, p.bad = w.ok.copy(), w.bad.copy()
    p.ok[i + 1:] &= ~flip
    p.bad[i + 1:] |= flip
    p.cs_ln, p.cs_lr, p.c_bad = p.ln.cumsum(0), p.lr.cumsum(0), p.bad.cumsum(0)
    return p


def _truncated(w, i):
    """The matrices with every session after i removed."""
    t = copy.copy(w)
    t.days = w.days[:i + 1]
    for name in ("present", "ok", "span", "bad", "raw_ok", "factor", "ln", "lr", "lraw", "cs_ln", "cs_lr", "c_bad"):
        setattr(t, name, getattr(w, name)[:i + 1])
    return t


def pre_run_checks(inp, n_dates=5):
    """Checks that must pass on the REAL pipeline before any result (protocol B2, §25).
    Reports pass/fail and counts only. It contains no return, mean or test of a momentum
    portfolio; the only statistic is the p-value of the random-ranking placebo."""
    lag, cal, w = NW_LAG[inp.sample], inp.cal, inp.w
    pos = {d: n for n, d in enumerate(w.days)}
    monthly, hold = run(inp)
    out = {"sample": inp.sample, "months_in_calendar": len(cal)}

    d = ladder.paired_delta(monthly, cal)                                   # A/D pairing
    out["pairing"] = {"paired_months": int(d["paired"].sum()), "unpaired": dict(Counter(d.loc[~d["paired"], "reason"])),
                      "pass": bool(d["paired"].all())}

    out["boundary"] = {"last_session_in_matrices": str(w.days.max().date()), "research_cutoff": str(inp.cutoff.date()),
                       "last_exit_session": str(inp.data_end.date()),
                       "pass": bool(w.days.max() <= inp.cutoff and inp.data_end <= inp.cutoff
                                    and (cal["s_plus"] > cal["t"]).all() and (cal["m1"] < cal["t"]).all())}

    dates = [cal["t"].iloc[k] for k in np.linspace(0, len(cal) - 1, n_dates + 2).astype(int)[1:-1]]
    pert, trunc = [], []
    for k, t in enumerate(dates):
        base, sub = _members(hold, t), cal[cal["t"] <= t]
        pert.append(_members(run(inp, w=_perturbed(w, pos[t], BOOTSTRAP_SEED + k), cal=sub)[1], t) == base)
        trunc.append(_members(run(inp, w=_truncated(w, pos[t]), cal=sub)[1], t) == base)
    out["perturbation"] = {"dates": [str(t.date()) for t in dates], "pass": bool(all(pert))}
    out["truncation"] = {"dates": [str(t.date()) for t in dates], "pass": bool(all(trunc))}

    pm, ph = run(inp, score_fn=ladder.random_scores(BOOTSTRAP_SEED))        # random-ranking placebo
    ok = pm[(pm["step"] == "D") & (pm["status"] == "OK")]
    p = stats.mean_test(ok["WML"].to_numpy() * 100, lag)["p_two_sided"]
    keys = [k for k in hold if k[0] == "D"]
    out["placebo"] = {"seed": BOOTSTRAP_SEED, "months": len(ok), "p_two_sided_of_random_wml": round(p, 4),
                      "months_ranked_differently_from_momentum": int(sum(hold[k]["W"] != ph[k]["W"] for k in keys)),
                      "same_rankable_stocks": bool(all(hold[k]["BM"] == ph[k]["BM"] for k in keys)),
                      "pass": bool(p > ALPHA and all(hold[k]["BM"] == ph[k]["BM"] for k in keys)
                                   and sum(hold[k]["W"] != ph[k]["W"] for k in keys) > len(keys) // 2)}

    dq = monthly[monthly["step"] == "D"]
    out["data_quality_counts"] = {"rankable_min": int(dq["n_rankable"].min()), "rankable_mean": float(dq["n_rankable"].mean()),
                                  "events_by_kind_and_step": {f"{s}:{k}": int(n) for (s, k), n in
                                                              events(inp, hold).groupby(["step", "kind"]).size().items()}}
    out["all_passed"] = all(out[k]["pass"] for k in ("pairing", "boundary", "perturbation", "truncation", "placebo"))
    return out


# ------------------------------------------------------------------ blinded precision step (§15)
def blinded(inp):
    """Dispersion and counts of delta only. No mean, no test."""
    monthly, _ = run(inp)
    d = ladder.paired_delta(monthly, inp.cal)
    x = d.loc[d["paired"], "delta"].to_numpy()
    counts = monthly.filter(regex="_(stock_days|booked|applied|stocks|row)$").fillna(0).sum().astype(int)
    return {"sample": inp.sample, "months_in_calendar": len(d), "paired_months": int(d["paired"].sum()),
            "unpaired_months": Counter(d.loc[~d["paired"], "reason"]),
            "rankable_min_by_step": monthly.groupby("step")["n_rankable"].min().to_dict(),
            "data_quality_counts": counts.to_dict(),
            "delta_series_sha256": hashlib.sha256(np.round(x, 12).tobytes()).hexdigest(),
            **stats.blinded_precision(x, NW_LAG[inp.sample], REFERENCE_THRESHOLD)}


# ------------------------------------------------------------------ primary analysis (§2, §14, §27, §13)
def _describe(x, lag):
    """§14 metrics of one monthly series (fractions)."""
    x = np.asarray(x, float)
    wealth = np.cumprod(1 + x)
    t = stats.mean_test(x, lag)
    return {"n": len(x), "mean_pct": x.mean() * 100, "sd_pct": x.std(ddof=1) * 100,
            "mean_over_sd": x.mean() / x.std(ddof=1), "t_nw": t["t"], "p_two_sided": t["p_two_sided"],
            "max_drawdown_pct": float((wealth / np.maximum.accumulate(wealth) - 1).min() * 100),
            "share_positive": float((x > 0).mean())}


def _delist(inp, mode):
    if mode == "ZERO":
        return np.zeros(len(inp.delist_ret))
    if mode == "MINUS100":
        return np.where(inp.delist_ret != 0, -1.0, 0.0)          # voluntary delistings stay at 0%
    raise ValueError(f"unknown delisting treatment {mode!r}")


def sensitivity(inp, monthly, h1, schedule):
    """§25: does H1, H3 or H4 change sign or significance under R-span, R-gap, R-miss, R-delist?
    Step A is not touched by any of these rules, so each treatment reruns step D only and pairs it
    with the primary step A. H4 needs costs; without archived evidence it is marked pending."""
    lag, cal = NW_LAG[inp.sample], inp.cal
    ok = monthly[monthly["status"] == "OK"]
    wml_a = ok[ok["step"] == "A"].set_index("t")["WML"]
    base_d = ok[ok["step"] == "D"].set_index("t")["WML"]
    one_sided = lambda x: (float(np.mean(x)) > 0, bool(np.mean(x) > 0 and stats.mean_test(x, lag)["p_two_sided"] / 2 < ALPHA))
    two_sided = lambda t: (t["mean"] > 0, bool(t["p_two_sided"] < ALPHA))
    base_h1, base_h3 = two_sided(h1), one_sided(base_d.to_numpy())
    costs_ready = not costs.missing_evidence(schedule)
    out = {}
    for name, t in SENSITIVITY.items():
        w = ladder.treated(inp.w, t.get("span_raw", False), t.get("gap_raw", False)) if ("span_raw" in t or "gap_raw" in t) else inp.w
        m, _ = run(inp, {"D": ladder.STEP_SPECS["D"]}, w=w, delist_ret=_delist(inp, t["delist"]) if "delist" in t else None,
                   miss=t.get("miss", "FILL"))
        d = m[m["status"] == "OK"].set_index("t")["WML"]
        both = wml_a.index.intersection(d.index)
        test = stats.mean_test(((wml_a[both] - d[both]) * 100).to_numpy(), lag)
        h3 = one_sided(d.to_numpy())
        out[name] = {"treatment": t, "paired_months": len(both), "unpaired_months": len(cal) - len(both),
                     "rows_treated": getattr(w, "treated_rows", None), "H1": test,
                     "H1_sign_changed": two_sided(test)[0] != base_h1[0], "H1_significance_changed": two_sided(test)[1] != base_h1[1],
                     "H3_sign_changed": h3[0] != base_h3[0], "H3_significance_changed": h3[1] != base_h3[1],
                     "H4": "not computed here" if costs_ready else PENDING}
    return out


def fill_shares(d):
    """Share of stock-days filled under §20(b), for W and for L SEPARATELY (each has k stocks per month)."""
    days = (d["k"] * d["holding_sessions"]).sum()
    return {p: float(d.get(f"{p}_filled_stock_days", pd.Series(0, index=d.index)).fillna(0).sum() / days) for p in ("W", "L")}


def reliability(monthly, sens=None):
    """§25 'not reliable' labels: fixed thresholds applied to counts and to the sensitivity flags.
    sens=None (primary mode): the sensitivity criterion is PENDING until the sensitivity mode runs;
    `not_reliable` is then True if a count criterion already fails, otherwise None (not yet known).
    §25: "more than 5% of stock-days in W or L filled under §20(b)" - W and L are tested separately
    (reviewer ruling 2026-10-05); the label fails if either is above 5%; exactly 5% does not fail."""
    d = monthly[(monthly["step"] == "D") & (monthly["status"] == "OK")]
    share = fill_shares(d)
    counts = {"rankable_below_minimum": bool(d["n_rankable"].min() < RANKABLE_MIN or d["n_rankable"].mean() < RANKABLE_MEAN),
              "filled_share_above_5pct": bool(share["W"] > FILL_SHARE_MAX or share["L"] > FILL_SHARE_MAX)}
    facts = {"rankable_min": int(d["n_rankable"].min()), "rankable_mean": float(d["n_rankable"].mean()),
             "filled_share_of_W_stock_days": share["W"], "filled_share_of_L_stock_days": share["L"]}
    if sens is None:
        return {**counts, "changes_under_sensitivity": SENSITIVITY_PENDING, **facts,
                "not_reliable": True if any(counts.values()) else None,
                "status": "PARTIAL - the sensitivity criterion of §25 is pending (sensitivity mode not run)"}
    flips = sorted(k for k, v in sens.items() if any(v[f] for f in ("H1_sign_changed", "H1_significance_changed",
                                                                    "H3_sign_changed", "H3_significance_changed")))
    labels = {**counts, "changes_under_sensitivity": bool(flips)}
    return {**labels, **facts, "sensitivity_treatments_that_change_H1_or_H3": flips,
            "H4_under_sensitivity": PENDING if any(v["H4"] == PENDING for v in sens.values()) else "not computed here",
            "not_reliable": any(labels.values()), "status": "COMPLETE except H4 (cost evidence)"}


def step_e(monthly, hold, schedule, lag):
    """Step E (§13): step D net of costs under S0-S4, with break-even. Without archived cost
    evidence nothing is computed and nothing is assumed: the block is marked pending."""
    gaps = costs.missing_evidence(schedule)
    if gaps:
        return {"status": PENDING, "missing_cost_evidence": gaps,
                "note": "step E, H4 and every cost-dependent conclusion wait for archived evidence; no cost was set to zero"}
    net = {"status": "COMPUTED", "assumptions_under_frozen_section_13": costs.assumptions(schedule)}
    for sc in SLIPPAGE_BPS:
        nw, nb = (ladder.net_of_costs(monthly, hold, "D", p, schedule, sc) for p in ("W", "BM"))
        ex = nw["net"] - nb["net"]
        net[sc] = {"W_net": _describe(nw["net"], lag), "BM_net": _describe(nb["net"], lag),
                   "excess_net": _describe(ex, lag), "turnover_W": float(nw["turnover_one_way"].mean()),
                   "turnover_BM": float(nb["turnover_one_way"].mean())}
        if sc == "S0":
            be = costs.breakeven_one_way(ex.mean(), nw["traded"].mean(), nb["traded"].mean())
            net["breakeven_one_way_bps"] = None if be is None else be * 1e4
    return net


def analyse(inp, schedule):
    """PRIMARY analysis of one sample, and nothing else: H1 on the gross estimand delta (Newey-West
    and bootstrap), the gross ladder A-D, step differences, the count-based §25 labels, and the
    monthly series, holdings and audit events. It runs NO sensitivity treatment, NO reverse-order
    ladder and NO cost calculation: step E is written as pending. Called only by the runner."""
    lag = NW_LAG[inp.sample]
    monthly, hold = run(inp)
    d = ladder.paired_delta(monthly, inp.cal)
    x = d.loc[d["paired"], "delta"].to_numpy()
    h1 = stats.mean_test(x, lag)
    lo, hi = h1["ci90"]
    h1["decision"] = ("MATERIAL" if h1["p_two_sided"] < ALPHA and (lo > REFERENCE_THRESHOLD or hi < -REFERENCE_THRESHOLD)
                      else "DETECTED_SIZE_UNCERTAIN" if h1["p_two_sided"] < ALPHA
                      else "IMMATERIAL" if -REFERENCE_THRESHOLD < lo and hi < REFERENCE_THRESHOLD else "INCONCLUSIVE")
    ok = monthly[monthly["status"] == "OK"]
    table = {s: {p: _describe(g[p], lag) for p in ("W", "L", "WML", "BM")} for s, g in ok.groupby("step")}
    for s, g in ok.groupby("step"):
        table[s]["economic_conclusion"] = {
            "momentum_detected": bool(g["WML"].mean() > 0 and table[s]["WML"]["p_two_sided"] / 2 < ALPHA),
            "winners_beat_universe": bool((g["W"] - g["BM"]).mean() > 0
                                          and stats.mean_test(g["W"] - g["BM"], lag)["p_two_sided"] / 2 < ALPHA)}
    wml = ok.pivot(index="t", columns="step", values="WML").dropna()
    steps = {f"{a}-{b}": stats.mean_test((wml[a] - wml[b]) * 100, lag) for a, b in (("A", "B"), ("B", "C"), ("C", "D"))}
    return {"sample": inp.sample, "H1": h1, "H1_bootstrap": stats.bootstrap_test(x, BOOTSTRAP_SEED, BOOTSTRAP_RESAMPLES),
            "unpaired_months": d.loc[~d["paired"], ["holding_month", "reason"]].to_dict("records"),
            "ladder": table, "step_differences_pct": steps,
            "step_E": {"status": PENDING, "missing_cost_evidence": costs.missing_evidence(schedule),
                       "note": "no cost calculation is part of this mode; step E and H4 are run separately"},
            "sensitivity": SENSITIVITY_PENDING, "reverse_ladder": SENSITIVITY_PENDING,
            "reliability": reliability(monthly),
            "monthly": monthly, "delta": d, "events": events(inp, hold), "holdings": holdings_frame(inp, monthly, hold)}


def sensitivity_analysis(inp, monthly, h1, schedule):
    """SENSITIVITY mode: the six frozen §16/§25 treatments, the reverse-order ladder (B1.5) and the
    completed §25 labels. `h1` is the REGISTERED primary test, read from the result file; `monthly`
    is the primary series, which the runner recomputes and requires to be byte-identical to the
    registered file before calling this. Nothing here writes to or alters the primary result."""
    sens = sensitivity(inp, monthly, h1, schedule)
    return {"sample": inp.sample, "sensitivity": sens, "reliability": reliability(monthly, sens),
            "reverse_ladder": reverse_ladder(inp)}


def reverse_ladder(inp):
    """B1.5 reverse-order ladder (robustness only; separate from the primary A-E result)."""
    lag = NW_LAG[inp.sample]
    monthly, _ = run(inp, {**{"D": ladder.STEP_SPECS["D"]}, **ladder.REVERSE_SPECS})
    wml = monthly[monthly["status"] == "OK"].pivot(index="t", columns="step", values="WML").dropna()
    return {k: stats.mean_test((wml[k] - wml["D"]) * 100, lag) for k in ladder.REVERSE_SPECS}
