"""Stage 2 point-in-time (PIT) equity universe (Phase 2F). Methodology version UNIV-1.

Verified era: sessions 2011-06-22 (first NSE file with ISINs) .. 2026-09-30 (research cutoff).
Older data is preserved but is NOT part of the verified universe (docs/stage2/data/universe_20261005.md).

SELECTION DATES  last market session of each calendar month whose trailing WINDOW sessions all
                 lie in the verified era: 2011-09-30 .. 2026-09-30 (181 dates). Membership chosen
                 on date t is meant to apply from the next session until the next selection date.
IDENTITY AT t    2E segments joined ONLY by 2E evidence links already effective on t (a link is
                 effective from the first session of its later segment). entity_id = id of the
                 entity's EARLIEST segment, so the id never reveals a future symbol/ISIN.
CANDIDATE        an entity with an EQ row on t (its symbol/ISIN that day = symbol/ISIN_at_selection).
EXCLUSIONS (first that applies, recorded as `reason`):
  NOT_TRADED_ON_SELECTION_DATE  no EQ row on t (suspended / other series / ended)
  FUND_UNIT                     ISIN on t starts with INF (ETF / mutual-fund unit)
  NON_EQUITY_ISIN               ISIN on t neither INE nor INF (e.g. IN9 partly paid)
  INSUFFICIENT_HISTORY          fewer than MIN_VALID valid sessions in the trailing window
                                (new listings, long suspensions, missing traded value)
LIQUIDITY        median over the WINDOW market sessions ending t (inclusive) of the entity's
                 daily traded value (NSE TOTTRDVAL / TtlTrfVal, Rs); sessions with no EQ row or a
                 missing / non-positive value count as 0. Valid session = EQ row with value > 0.
SELECTION        eligible entities ranked by liquidity (desc), ties by entity_id (asc);
                 MEMBER if rank <= TOP_N, else ELIGIBLE_NOT_SELECTED.
Nothing after t is used for the decision on t; a later delisting never alters earlier rows.
"""

import hashlib
import subprocess

import numpy as np
import pandas as pd

from src.access import RESEARCH_CUTOFF
from src.config import BASE_DIR

METHOD_VERSION = "UNIV-1"
VERIFIED_START = pd.Timestamp("2011-06-22")
CUT = pd.Timestamp(RESEARCH_CUTOFF)
WINDOW = 63
MIN_VALID = 50
TOP_N = 200


def selection_dates(sessions):
    s = pd.Series(sorted(pd.to_datetime(pd.Index(sessions).unique())))
    s = s[(s >= VERIFIED_START) & (s <= CUT)].reset_index(drop=True)
    if len(s) < WINDOW:
        return []
    month_end = s.groupby(s.dt.to_period("M")).max()
    return [d for d in month_end if d >= s.iloc[WINDOW - 1]]


def _components(segment_ids, links, t):
    """Union-find over links effective on or before t. -> {segment_id: pit_entity_id}."""
    eff = links[links["effective"] <= t]
    parent = {s: s for s in segment_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in zip(eff["from_segment"], eff["to_segment"]):
        if a in parent and b in parent:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
    return {s: find(s) for s in segment_ids}


def build(panel, segs, links, top_n=TOP_N):
    """panel: date, symbol, isin, series, value (EQ rows, <= cutoff). segs/links: 2E outputs
    (segment_id, symbol, isin, first) and (from_segment, to_segment, evidence).
    Returns one row per (selection_date, entity) seen in the trailing window."""
    if pd.to_datetime(panel["date"]).max() > CUT:
        raise ValueError("panel contains dates after the research cutoff - refused")
    p = panel[pd.to_datetime(panel["date"]) >= VERIFIED_START].copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p[p["series"] == "EQ"]
    p["isin"] = p["isin"].astype("string").fillna("")
    p["segment_id"] = p["symbol"] + "|" + p["isin"].replace("", "NOISIN") + "|1"
    first = segs.set_index("segment_id")["first"]
    lk = links.copy()
    lk["effective"] = lk["to_segment"].map(first)
    lk = lk.dropna(subset=["effective"])
    by_seg = {}
    for a, b, ev, eff in zip(lk["from_segment"], lk["to_segment"], lk["evidence"], lk["effective"]):
        by_seg.setdefault(a, []).append((eff, ev))
        by_seg.setdefault(b, []).append((eff, ev))
    sessions = pd.Index(sorted(p["date"].unique()))
    out = []
    for t in selection_dates(sessions):
        i = sessions.get_loc(t)
        win = sessions[i - WINDOW + 1:i + 1]
        w = p[p["date"].isin(win)]
        known = sorted(set(w["segment_id"]) | set(segs.loc[segs["first"] <= t, "segment_id"]))
        comp = _components(known, lk, t)
        # entity id = earliest segment of the PIT component (never a future listing)
        seg_first = first.reindex(known)
        root_first = pd.DataFrame({"seg": known, "root": [comp[s] for s in known],
                                   "first": seg_first.to_numpy()}).sort_values(["first", "seg"])
        earliest = root_first.groupby("root")["seg"].first()
        w = w.assign(entity_id=w["segment_id"].map(comp).map(earliest))
        val = w["value"].where(w["value"] > 0)
        daily = w.assign(v=val).groupby(["entity_id", "date"])["v"].sum(min_count=1)
        mat = daily.unstack("date").reindex(columns=win)
        valid = mat.notna().sum(axis=1)
        liq = mat.fillna(0.0).median(axis=1)
        today = w[w["date"] == t].drop_duplicates("entity_id").set_index("entity_id")
        for e in mat.index:
            row = {"selection_date": t, "entity_id": e, "valid_sessions": int(valid[e]),
                   "liquidity_median_value": float(liq[e])}
            if e in today.index:
                r = today.loc[e]
                row |= {"symbol_at_selection": r["symbol"], "isin_at_selection": r["isin"] or None,
                        "series": r["series"], "segment_at_selection": r["segment_id"],
                        "source_sha256": r.get("source_sha256")}
                isin = r["isin"]
                reason = ("FUND_UNIT" if isin.startswith("INF") else
                          "NON_EQUITY_ISIN" if not isin.startswith("INE") else
                          "INSUFFICIENT_HISTORY" if valid[e] < MIN_VALID else None)
            else:
                reason = "NOT_TRADED_ON_SELECTION_DATE"
            row["reason"] = reason
            out.append(row)
    u = pd.DataFrame(out)
    el = u["reason"].isna()
    u.loc[el, "rank"] = (u[el].sort_values(["selection_date", "liquidity_median_value", "entity_id"],
                                          ascending=[True, False, True])
                         .groupby("selection_date").cumcount() + 1)
    u["status"] = np.where(~el, "EXCLUDED", np.where(u["rank"] <= top_n, "MEMBER", "ELIGIBLE_NOT_SELECTED"))
    u["reason"] = u["reason"].fillna(pd.Series(np.where(u["status"] == "MEMBER", "TOP_N_LIQUIDITY", "BELOW_TOP_N"),
                                               index=u.index))
    u["evidence_links"] = [";".join(sorted({ev for eff, ev in by_seg.get(s, []) if eff <= d})) or None
                           if isinstance(s, str) else None
                           for s, d in zip(u.get("segment_at_selection", []), u["selection_date"])]
    return u.sort_values(["selection_date", "status", "rank", "entity_id"]).reset_index(drop=True)


def code_version(files=("src/stage2/universe.py", "src/stage2/identity.py", "src/stage2/panel.py",
                        "src/stage2/corporate_actions.py", "src/stage2/archive.py")):
    head = subprocess.run(["git", "-C", str(BASE_DIR), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {"git_head": head,
            "files_sha256": {f: hashlib.sha256((BASE_DIR / f).read_bytes()).hexdigest() for f in files}}
