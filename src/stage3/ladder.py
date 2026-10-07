"""S2-MOM-v1 bias ladder A-D and portfolio construction (frozen protocol, Part B and §6-§10, §20-§22).

Pure functions on in-memory frames: no file access, no clock, no randomness (the placebo takes
an explicit seed). Section numbers refer to docs/research/phase3a_momentum_protocol.md.

  step  universe (B1)                      daily return rule
  A     Top200(pool P, T*) for every t     NAIVE  (B1.2)
  B     Top200(pool P, t)                  NAIVE  (B1.3: only the liquidity date changes)
  C     Top200(no pool, t) = UNIV-1 MEMBER NAIVE  + delisting rule §22
  D     as C                               RG     (RET-1.1 research-grade, §20-§21)
Step E is step D net of costs (src/stage3/costs.py).
"""

import copy
import math
from collections import Counter
from types import SimpleNamespace

import numpy as np
import pandas as pd

from src.stage2.returns import JUMP
from src.stage3.protocol import (BREAKPOINT, DELIST_RETURN, FIRST_T, FORMATION_MONTHS, LAST_T, PRIMARY_LAST_T,
                                 SKIP_MONTHS, T_STAR, TOP_N)

STEP_SPECS = {"A": ("A", "NAIVE"), "B": ("B", "NAIVE"), "C": ("C", "NAIVE"), "D": ("C", "RG")}
# B1.5 reverse-order ladder: robustness only, never part of the primary A-E result.
REVERSE_SPECS = {"R_POOL": ("B", "RG"),        # step D with the survivor pool P restored
                 "R_RETURNS": ("C", "NAIVE")}  # step D with the step-A return rule restored
_UNADJ = "RIGHTS|CONSOLIDATION|UNPARSED|NON_EQUITY|SCHEME"     # as src/stage2/returns.py


# ------------------------------------------------------------------ calendar (§8-§9, B2)
def calendar(sessions, first_t=FIRST_T, last_t=LAST_T, primary_last_t=PRIMARY_LAST_T):
    """One row per selection date t: m12 = m(12), m1 = m(1), s_plus, s_pp, holding month, sample."""
    s = pd.DatetimeIndex(sorted(set(pd.to_datetime(list(sessions)))))
    me = pd.Series(s, index=s.to_period("M")).groupby(level=0).max()       # month-end sessions
    rows = []
    for per, t in me.items():
        if not (first_t <= t <= last_t):
            continue
        m12, m1, nxt = (me.get(per - FORMATION_MONTHS), me.get(per - SKIP_MONTHS), me.get(per + 1))
        after_t, after_n = s[s > t], (s[s > nxt] if nxt is not None else s[:0])
        if m12 is None or m1 is None:
            raise ValueError(f"no formation window for selection date {t.date()}")
        rows.append({"t": t, "m12": m12, "m1": m1,
                     "s_plus": after_t[0] if len(after_t) else pd.NaT,
                     "s_pp": after_n[0] if len(after_n) else pd.NaT,
                     "holding_month": str(per + 1), "sample": "PRIMARY" if t <= primary_last_t else "OOS"})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ universes (B1.1-B1.4)
def top200(univ_d, seg2ent, pool=None, n=TOP_N):
    """B1.1 Top200(pool, d). univ_d: UNIV-1 rows of ONE selection date."""
    u = univ_d[univ_d["status"].isin(["MEMBER", "ELIGIBLE_NOT_SELECTED"])]
    ent = u["segment_at_selection"].map(seg2ent)
    if ent.isna().any():
        raise ValueError("UNIV-1 segment without a full-sample entity")
    u = u.assign(entity=ent.to_numpy())
    if pool is not None:
        u = u[u["entity"].isin(pool)]
    return u.sort_values(["rank", "entity"]).drop_duplicates("entity").head(n)[["entity", "rank"]].reset_index(drop=True)


def universes(univ, seg2ent, pool, cal, n=TOP_N, t_star=T_STAR):
    """{(key, t): Top200 frame} for universe keys A, B, C."""
    by_date = dict(tuple(univ.groupby("selection_date")))
    if t_star not in by_date:
        raise ValueError("UNIV-1 has no rows at T*")
    fixed = top200(by_date[t_star], seg2ent, pool, n)
    out = {}
    for t in cal["t"]:
        if t not in by_date:
            raise ValueError(f"UNIV-1 has no rows at selection date {t.date()}")
        out[("A", t)] = fixed
        out[("B", t)] = top200(by_date[t], seg2ent, pool, n)
        out[("C", t)] = top200(by_date[t], seg2ent, None, n)
    return out


# ------------------------------------------------------------------ daily study returns (B1.2, §20)
def study_panel(ret):
    """RET-1.1 rows -> one row per (date, entity) with both return rules.
    r_naive (B1.2): close/(prev_close*event_factor)-1 when a parsed factor is present, whatever its
    status; otherwise ret_raw. r_rg (§20): ret_research. cls: OK | SPAN | BAD | FIRST."""
    f, st, raw = ret["event_factor"], ret["return_status"], ret["ret_raw"]
    naive = np.where(f.notna(), ret["close"] / (ret["prev_close"] * f) - 1, raw)
    cls = np.select([st.eq("SPECIAL_SESSION_SPAN"), ret["research_grade"].astype(bool), st.eq("FIRST_OBSERVATION")],
                    ["SPAN", "OK", "FIRST"], "BAD")
    unadj = ret["other_events"].fillna("").str.contains(_UNADJ)
    within = np.abs(np.log1p(raw.where(raw > -1))) <= math.log(JUMP)
    return pd.DataFrame({"date": pd.to_datetime(ret["date"]).to_numpy(), "entity": ret["entity_id"].to_numpy(),
                         "r_naive": naive, "r_rg": ret["ret_research"].to_numpy(), "r_raw": raw.to_numpy(), "cls": cls,
                         "raw_ok": (f.isna() & ~unadj & within.fillna(False)).to_numpy()})


def gap_rows(ret):
    """RET-1.1 MULTI_SESSION_GAP rows with their 'no event on the row' flag (protocol §16 R-gap):
    no parsed bonus/split factor and no unadjustable record (rights, scheme, consolidation, ...)."""
    g = ret[ret["return_status"] == "MULTI_SESSION_GAP"]
    no_event = g["event_factor"].isna() & ~g["other_events"].fillna("").str.contains(_UNADJ)
    return pd.DataFrame({"date": pd.to_datetime(g["date"]).to_numpy(), "entity": g["entity_id"].to_numpy(),
                         "no_event": no_event.to_numpy()})


def wide(panel, entities, sessions, gaps=None):
    """Date x entity matrices used by every step. `sessions`: the market sessions (all of them).
    `gaps`: gap_rows() output, needed only by the R-gap sensitivity treatment."""
    ents, days = pd.Index(sorted(set(entities))), pd.DatetimeIndex(sorted(set(sessions)))
    p = panel[panel["entity"].isin(ents)]
    i, j = days.get_indexer(p["date"]), ents.get_indexer(p["entity"])
    if (i < 0).any():
        raise ValueError("panel row on a date that is not a session")
    first = (p["cls"] == "FIRST").to_numpy()
    if p["r_naive"].isna().to_numpy()[~first].any():
        raise ValueError("missing price in the panel - protocol B1.2 says the run stops")
    shape = (len(days), len(ents))

    def mat(vals, fill, dtype):
        m = np.full(shape, fill, dtype)
        m[i, j] = vals
        return m
    cls = p["cls"].to_numpy()
    w = SimpleNamespace(
        days=days, ents=ents,
        present=mat(True, False, bool),
        ok=mat(cls == "OK", False, bool),
        span=mat(cls == "SPAN", False, bool),
        bad=mat(np.isin(cls, ["BAD", "FIRST"]), False, bool),
        raw_ok=mat(p["raw_ok"].to_numpy(), False, bool),
        factor=mat(~first & ((p["r_naive"] - p["r_raw"]).abs() > 1e-12).to_numpy(), False, bool),   # a parsed factor was applied
        ln=mat(np.where(first, 0.0, np.log1p(p["r_naive"].fillna(0.0))), 0.0, float),
        lr=mat(np.where(cls == "OK", np.log1p(p["r_rg"].fillna(0.0)), 0.0), 0.0, float),
        lraw=mat(np.log1p(p["r_raw"].fillna(0.0)), 0.0, float))
    w.gap_no_event = np.zeros(shape, bool)
    if gaps is not None and len(gaps):
        g = gaps[gaps["entity"].isin(ents) & gaps["date"].isin(days) & gaps["no_event"]]
        w.gap_no_event[days.get_indexer(g["date"]), ents.get_indexer(g["entity"])] = True
        if (w.gap_no_event & ~w.bad).any():
            raise ValueError("a gap row is not classed as non-research-grade in the panel")
    w.cs_ln, w.cs_lr, w.c_bad = w.ln.cumsum(0), w.lr.cumsum(0), w.bad.cumsum(0)
    return w


def treated(w, span_raw=False, gap_raw=False):
    """Sensitivity treatments of protocol §16/§20, as a modified COPY of the matrices. The primary
    matrices are never altered.
      span_raw (R-span): special-session span rows use the raw two-session return.
      gap_raw  (R-gap):  multi-session gap rows with no event on the row use the raw gap return."""
    t = copy.copy(w)
    use = np.zeros(w.ok.shape, bool)
    if span_raw:
        use |= w.span
    if gap_raw:
        use |= w.gap_no_event
    t.ok, t.span, t.bad = w.ok | use, w.span & ~use, w.bad & ~use
    t.lr = np.where(use, w.lraw, w.lr)
    t.cs_lr, t.c_bad = t.lr.cumsum(0), t.bad.cumsum(0)
    t.treated_rows = int(use.sum())
    return t


# ------------------------------------------------------------------ ranking (§10, B1.1)
def ranking(scores):
    """Entities from best to worst: descending score, ties by entity ascending."""
    return pd.DataFrame({"entity": scores.index, "s": scores.to_numpy()}).sort_values(
        ["s", "entity"], ascending=[False, True], kind="mergesort")["entity"].tolist()


def sort_portfolios(scores, breakpoint=BREAKPOINT):
    """k = floor(0.30*n + 0.5); descending score, ties by entity ascending. -> (W, L)."""
    names = ranking(scores)
    k = int(math.floor(breakpoint * len(names) + 0.5))
    return names[:k], (names[len(names) - k:] if k else [])


def random_scores(seed):
    """Placebo ranking: seeded random scores that ignore the formation return."""
    def fn(t, step, form):
        rng = np.random.default_rng([seed, pd.Timestamp(t).toordinal(), sum(map(ord, step))])
        return pd.Series(rng.random(len(form)), index=sorted(form.index))
    return fn


# ------------------------------------------------------------------ holding (B1.1, §20(b), §22)
def _hold(w, j, a, b, rule, delist_on, consumed, delist_ret, miss="FILL"):
    """Position values at the exit for stocks j bought with equal value at session a, sold at b.
    Returns (values, counts, events); an event is (kind, entity position, session position).

    §20(b), step D: a held stock is never removed. On a day when its row is not research-grade its
    return is the simple mean of the same-day research-grade returns of the other stocks in the
    portfolio (reviewer interpretation 2026-10-05: equal-weighted portfolios -> arithmetic mean).
    §22, steps C and D, applied literally: no price at the exit session -> carried at the last
    price; trades again later -> the realised gap return (last price to the next traded price) is
    booked in this month and never counted again; never trades again in the research data -> the
    delisting return (0% voluntary, -30% otherwise).
    `miss`: "FILL" is the frozen primary rule. "RAW" and "ZERO" are the R-miss sensitivity
    treatments (§16): the flagged day takes the stock's own raw return, or zero."""
    if miss not in ("FILL", "RAW", "ZERO"):
        raise ValueError(f"unknown missing-day treatment {miss!r}")
    v, cnt, events = np.ones(len(j)), Counter(), []
    skip = np.zeros((b - a, len(j)), bool)
    for q, e in enumerate(j):
        for r in consumed:
            if r[0] == e and a < r[1] <= b:
                skip[r[1] - a - 1, q] = True
    if rule == "NAIVE":
        v = np.exp(np.where(skip, 0.0, w.ln[a + 1:b + 1][:, j]).sum(0))
    else:
        for n, i in enumerate(range(a + 1, b + 1)):
            ok, bad = w.ok[i, j] & ~skip[n], w.bad[i, j] & ~skip[n]
            r = np.expm1(w.lr[i, j])
            cnt["span_stock_days"] += int(w.span[i, j].sum())
            if bad.any() and miss == "FILL":
                f = r[ok].mean() if ok.any() else 0.0           # no other stock traded: nothing to average
                cnt["filled_stock_days"] += int(bad.sum())
                cnt["fill_without_other_stocks"] += 0 if ok.any() else int(bad.sum())
                events += [("NEUTRAL_FILL" if ok.any() else "NEUTRAL_FILL_NO_OTHER_STOCKS", j[q], i)
                           for q in np.flatnonzero(bad)]
                v[bad] *= 1 + f
            elif bad.any():                                     # R-miss sensitivity only
                cnt["flagged_stock_days_" + miss.lower()] += int(bad.sum())
                if miss == "RAW":
                    v[bad] *= np.exp(w.lraw[i, j][bad])
            v[ok] *= 1 + r[ok]
    if delist_on:                                              # §22: no price at the exit session
        for q in np.flatnonzero(~w.present[b, j]):
            e, later = j[q], np.flatnonzero(w.present[b + 1:, j[q]])
            if len(later):
                i = b + 1 + int(later[0])
                if rule == "RG" and w.factor[i, e]:
                    raise ValueError("a corporate-action factor sits on a §22 resumption row - the realised gap "
                                     "return is not defined by the frozen protocol; stop and report")
                v[q] *= math.exp(w.ln[i, e] if rule == "NAIVE" else w.lraw[i, e])
                consumed.add((e, i))                           # never counted again in a later month
                cnt["exit_gap_booked"] += 1
                cnt["exit_gap_booked_on_flagged_row"] += int(not w.raw_ok[i, e])
                events.append(("EXIT_GAP_BOOKED" if w.raw_ok[i, e] else "EXIT_GAP_BOOKED_FLAGGED_ROW", e, i))
            else:                                              # never trades again in the research data
                v[q] *= 1 + delist_ret[e]
                cnt["delisting_return_applied"] += 1
                events.append(("DELISTING_RETURN", e, b))
    return v, cnt, events


def run_ladder(w, cal, univ, specs, delist_ret=None, score_fn=None, data_end=None, miss="FILL"):
    """Monthly W, L, WML and benchmark returns (fractions) for each step in `specs`.
    Returns (monthly frame, holdings). A month that cannot be computed is kept with its reason.
    `w` must run to the research cutoff for §22 ('never trades again') to be decided.
    `data_end`: a holding month whose exit session is later than this is NOT computed."""
    pos = {d: n for n, d in enumerate(w.days)}
    delist_ret = np.full(len(w.ents), DELIST_RETURN["OTHER"]) if delist_ret is None else delist_ret
    consumed = {(s, p): set() for s in specs for p in ("W", "L", "BM")}
    rows, hold = [], {}
    for c in cal.itertuples():
        a12, a1, sp, spp = (pos.get(x, -1) for x in (c.m12, c.m1, c.s_plus, c.s_pp))
        for step, (ukey, rule) in specs.items():
            rec = {"t": c.t, "holding_month": c.holding_month, "sample": c.sample, "step": step, "status": "OK"}
            rows.append(rec)
            if a12 < 0 or a1 < 0:
                rec["status"] = "NO_FORMATION_DATA"
                continue
            ents = univ[(ukey, c.t)]["entity"].to_numpy()
            j = w.ents.get_indexer(ents)
            if (j < 0).any():
                raise ValueError("universe entity missing from the panel matrices")
            ok = w.present[a12, j] & w.present[a1, j]
            if rule == "RG":
                ok &= (w.c_bad[a1, j] - w.c_bad[a12, j]) == 0
            cs = w.cs_lr if rule == "RG" else w.cs_ln
            form = pd.Series(np.expm1(cs[a1, j] - cs[a12, j])[ok], index=ents[ok])
            scores = form if score_fn is None else score_fn(c.t, step, form)
            wl = sort_portfolios(scores)
            members = {"W": wl[0], "L": wl[1], "BM": sorted(form.index)}
            rec.update(n_universe=len(ents), n_rankable=len(form), k=len(wl[0]), holding_sessions=max(spp - sp, 0))
            hold[(step, c.t)] = h = {p: list(m) for p, m in members.items()}
            h["events"], h["order"] = [], ranking(scores)
            if not len(wl[0]):
                rec["status"] = "NO_RANKABLE_STOCKS"
                continue
            if sp < 0 or spp < 0 or (data_end is not None and c.s_pp > data_end):
                rec["status"] = "NO_HOLDING_DATA"
                continue
            for p, m in members.items():
                v, cnt, ev = _hold(w, w.ents.get_indexer(m), sp, spp, rule, ukey == "C", consumed[(step, p)], delist_ret, miss)
                rec[p] = float(v.mean() - 1)
                h[p + "_end"] = dict(zip(m, (v / v.sum()).tolist()))
                h["events"] += [{"t": c.t, "step": step, "portfolio": p, "kind": k, "entity": w.ents[e], "date": w.days[i]}
                                for k, e, i in ev]
                rec.update({f"{p}_{k}": n for k, n in cnt.items()})
            rec["WML"] = rec["W"] - rec["L"]
    return pd.DataFrame(rows), hold


# ------------------------------------------------------------------ primary estimand (§2)
def paired_delta(monthly, cal):
    """delta(t) = WML_A(t) - WML_D(t), percent per month, one row per calendar month.
    A month enters only when BOTH steps are computable; otherwise it is kept with the reason."""
    wml = monthly.pivot(index="t", columns="step", values="WML") if "WML" in monthly else pd.DataFrame()
    st = monthly.pivot(index="t", columns="step", values="status")
    out = cal[["t", "holding_month", "sample"]].copy()
    none = pd.Series(dtype=object)
    sa, sd = out["t"].map(st.get("A", none)).fillna("NOT_RUN"), out["t"].map(st.get("D", none)).fillna("NOT_RUN")
    both = (sa == "OK") & (sd == "OK")
    out["delta"] = np.where(both, (out["t"].map(wml.get("A", pd.Series(dtype=float)))
                                   - out["t"].map(wml.get("D", pd.Series(dtype=float)))) * 100, np.nan)
    out["paired"] = both
    out["reason"] = np.where(both, "", "A:" + sa + " D:" + sd)
    return out


# ------------------------------------------------------------------ step E (§13, §23)
def net_of_costs(monthly, hold, step, portfolio, schedule, scenario, band="1-200"):
    """Gross and net monthly return of one portfolio, with turnover. Costs are deducted at the
    rebalance session (= entry of the month). Raises if cost evidence is missing."""
    from src.stage3.costs import rebalance, rebalance_cost
    m = monthly[(monthly["step"] == step) & (monthly["status"] == "OK")].sort_values("t")
    rows, prev_t, order = [], None, list(monthly["t"].drop_duplicates().sort_values())
    for r in m.itertuples():
        h = hold[(step, r.t)]
        consecutive = prev_t is not None and order.index(r.t) == order.index(prev_t) + 1
        drift = hold[(step, prev_t)][portfolio + "_end"] if consecutive else {}
        trade = rebalance({e: 1.0 / len(h[portfolio]) for e in h[portfolio]}, drift)
        cost = rebalance_cost(trade, schedule, scenario, band)
        rows.append({"t": r.t, "gross": getattr(r, portfolio), "cost": cost, "net": getattr(r, portfolio) - cost,
                     "turnover_one_way": trade["turnover_one_way"], "traded": trade["bought"] + trade["sold"]})
        prev_t = r.t
    return pd.DataFrame(rows)
