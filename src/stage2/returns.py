"""Stage 2 price series and daily return methodology (Phase 2G). Methodology version RET-1.

Scope: UNIV-1 verified period, EQ rows 2011-06-22 .. 2026-09-30. Raw NSE fields are copied
unchanged; nothing is repaired. No Yahoo data. No total returns (dividends are NOT included).

ENTITY      2E segments joined by all 2E evidence links; entity_id = earliest segment of the
            component (same convention as UNIV-1; UNIV-1 rows join exactly via segment_id).
RETURN ROW  each EQ row with a previous EQ row of the same entity:
            ret_raw = close_t / close_prev - 1                      (always reported)
            event factor f = product of 2D-parsed bonus/split factors of NSE records filed under
            any symbol of the entity with prev_date < ex_date <= t
            ret_adj = close_t / (close_prev * f) - 1  ONLY when that event VALIDATES (2D rule)
RETURN STATUS (first that applies)
  FIRST_OBSERVATION        no previous row (listing / start of verified period / new entity)
  MISSING_PRICE            close_t or close_prev missing / non-positive
  MULTI_SESSION_GAP        previous row is not the previous market session (suspension/other series)
  EVENT_DISCREPANT / EVENT_INCONCLUSIVE   bonus/split record whose price check does not validate
  EVENT_UNADJUSTABLE       record that changes the share count but has no supported factor:
                           rights, scheme/demerger/amalgamation/capital reduction, consolidation,
                           unparsed or non-equity bonus/split
  UNEXPLAINED_JUMP         |log(ratio)| > log 1.4 with no validated event (ratio = adjusted if an event
                           validated, else raw)
  ADJUSTED_VALIDATED       validated bonus/split, factor applied              (research-grade)
  OK                       none of the above                                  (research-grade)
DIVIDEND ex-dates are flagged (`dividend_exdate`) but do not change status: returns are PRICE returns.
`research_grade` = status in {OK, ADJUSTED_VALIDATED}; ret_research = ret_adj if adjusted else ret_raw
for research-grade rows, NaN otherwise.
"""

import math
import re

import numpy as np
import pandas as pd

from src.access import RESEARCH_CUTOFF
from src.stage2.corporate_actions import classify, combined_events

METHOD_VERSION = "RET-1"
VERIFIED_START = pd.Timestamp("2011-06-22")
CUT = pd.Timestamp(RESEARCH_CUTOFF)
JUMP = 1.4
_UNADJ = re.compile(r"demerg|scheme|arrangement|amalgam|capital\s+red|reduction", re.I)


def entity_map(segs, links):
    """segment_id -> entity_id (earliest segment of the evidence component)."""
    parent = {s: s for s in segs["segment_id"]}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in zip(links["from_segment"], links["to_segment"]):
        if a in parent and b in parent:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
    root = pd.Series({s: find(s) for s in parent})
    first = segs.set_index("segment_id")["first"]
    order = pd.DataFrame({"seg": root.index, "root": root.values, "first": first.reindex(root.index).values})
    earliest = order.sort_values(["first", "seg"]).groupby("root")["seg"].first()
    return root.map(earliest)


def _events_on_rows(rows, ev, ent_syms):
    """Attach events (symbol, ex_date, ...) to the entity row t with prev_date < ex_date <= date."""
    if ev.empty:
        return pd.DataFrame(columns=["row", *ev.columns])
    e = ev.merge(ent_syms, on="symbol")
    e["ex_date"] = pd.to_datetime(e["ex_date"]).astype("datetime64[ns]")
    e = e.sort_values("ex_date")
    r = rows[["entity_id", "date", "prev_date"]].reset_index().rename(columns={"index": "row"})
    r["date"] = r["date"].astype("datetime64[ns]")
    r = r.sort_values("date")
    m = pd.merge_asof(e, r, left_on="ex_date", right_on="date", by="entity_id", direction="forward")
    m = m[m["row"].notna() & (m["prev_date"] < m["ex_date"])]
    m["row"] = m["row"].astype(int)
    return m


def build(panel, segs, links, events):
    """panel: EQ rows (date, symbol, isin, series, open, high, low, close, last, prevclose,
    volume, value[, source_sha256]); segs/links: 2E; events: 2D load_events() output."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    if p["date"].max() > CUT:
        raise ValueError("panel contains dates after the research cutoff - refused")
    p = p[(p["date"] >= VERIFIED_START) & (p["series"] == "EQ")]
    p["isin"] = p["isin"].astype("string").fillna("")
    p["segment_id"] = p["symbol"] + "|" + p["isin"].replace("", "NOISIN") + "|1"
    emap = entity_map(segs, links)
    p["entity_id"] = p["segment_id"].map(emap).fillna(p["segment_id"])
    sessions = pd.Index(sorted(p["date"].unique()))
    p["pos"] = sessions.get_indexer(p["date"])
    p = p.sort_values(["entity_id", "date"]).reset_index(drop=True)
    g = p.groupby("entity_id")
    p["prev_date"] = g["date"].shift(1)
    p["prev_close"] = g["close"].shift(1)
    p["prev_symbol"] = g["symbol"].shift(1)
    p["gap_sessions"] = p["pos"] - g["pos"].shift(1) - 1
    p["identity_transition"] = p["prev_symbol"].notna() & (p["segment_id"] != g["segment_id"].shift(1))
    p["ret_raw"] = p["close"] / p["prev_close"] - 1

    ent_syms = p[["entity_id", "symbol"]].drop_duplicates()
    ent_syms = pd.concat([ent_syms, segs.assign(entity_id=segs["segment_id"].map(emap))[["entity_id", "symbol"]]]).drop_duplicates()
    adj = combined_events(events)
    m = _events_on_rows(p, adj[["symbol", "ex_date", "factor", "kind", "subject"]], ent_syms)
    f = m.groupby("row")["factor"].prod()
    p["event_factor"] = f.reindex(p.index).astype(float)
    p["event_kind"] = m.groupby("row")["kind"].agg("+".join).reindex(p.index)
    p["event_subject"] = m.groupby("row")["subject"].agg(" | ".join).reindex(p.index)

    other = events[events["factor"].isna()].copy()
    other["flag"] = np.where(other["kind"] == "DIVIDEND", "DIVIDEND",
                    np.where(other["kind"].isin(["RIGHTS", "CONSOLIDATION", "UNPARSED_BONUS_SPLIT", "NON_EQUITY_BONUS"]),
                             other["kind"], np.where(other["subject"].str.contains(_UNADJ), "SCHEME_DEMERGER", None)))
    other = other[other["flag"].notna()]
    mo = _events_on_rows(p, other[["symbol", "ex_date", "flag", "subject"]], ent_syms)
    flags = mo.groupby("row")["flag"].agg(lambda s: "+".join(sorted(set(s))))
    p["other_events"] = flags.reindex(p.index)
    p["dividend_exdate"] = p["other_events"].fillna("").str.contains("DIVIDEND")
    unadj = p["other_events"].fillna("").str.contains("RIGHTS|CONSOLIDATION|UNPARSED|NON_EQUITY|SCHEME")

    ev_status = pd.Series(None, index=p.index, dtype=object)
    has = p["event_factor"].notna() & (p["prev_close"] > 0) & (p["close"] > 0)
    ev_status[has] = [classify(r, fac) for r, fac in zip((p["close"] / p["prev_close"])[has], p.loc[has, "event_factor"])]
    p["event_status"] = ev_status
    validated = p["event_status"] == "VALIDATED"
    p["ret_adj"] = np.where(validated, p["close"] / (p["prev_close"] * p["event_factor"]) - 1, np.nan)
    ratio = np.where(validated, p["ret_adj"] + 1, p["ret_raw"] + 1).astype(float)
    jump = np.abs(np.log(np.where(ratio > 0, ratio, np.nan))) > math.log(JUMP)

    conds = [p["prev_date"].isna(),
             ~((p["close"] > 0) & (p["prev_close"] > 0)),
             p["gap_sessions"] > 0,
             p["event_status"] == "DISCREPANT",
             p["event_status"] == "INCONCLUSIVE",
             unadj,
             jump,
             validated]
    names = ["FIRST_OBSERVATION", "MISSING_PRICE", "MULTI_SESSION_GAP", "EVENT_DISCREPANT", "EVENT_INCONCLUSIVE",
             "EVENT_UNADJUSTABLE", "UNEXPLAINED_JUMP", "ADJUSTED_VALIDATED"]
    p["return_status"] = np.select(conds, names, default="OK")
    p["research_grade"] = p["return_status"].isin(["OK", "ADJUSTED_VALIDATED"])
    p["ret_research"] = np.where(p["research_grade"], np.where(validated, p["ret_adj"], p["ret_raw"]), np.nan)
    p["methodology"] = METHOD_VERSION
    keep = ["entity_id", "segment_id", "symbol", "isin", "series", "date", "open", "high", "low", "close", "last",
            "prevclose", "volume", "value", "prev_date", "prev_close", "gap_sessions", "identity_transition",
            "ret_raw", "event_factor", "event_kind", "event_status", "event_subject", "other_events",
            "dividend_exdate", "ret_adj", "return_status", "research_grade", "ret_research", "methodology"]
    if "source_sha256" in p:
        keep.insert(14, "source_sha256")
    return p[keep]


def entity_quality(r):
    """Per entity: rows, research-grade share, and counts of unresolved discontinuities."""
    bad = ["EVENT_DISCREPANT", "EVENT_INCONCLUSIVE", "EVENT_UNADJUSTABLE", "UNEXPLAINED_JUMP"]
    q = r.groupby("entity_id").agg(rows=("date", "size"), first=("date", "min"), last=("date", "max"),
                                   research_grade=("research_grade", "sum"),
                                   unresolved=("return_status", lambda s: int(s.isin(bad).sum())),
                                   gaps=("return_status", lambda s: int((s == "MULTI_SESSION_GAP").sum())),
                                   adjusted=("return_status", lambda s: int((s == "ADJUSTED_VALIDATED").sum())),
                                   symbols=("symbol", lambda s: "|".join(dict.fromkeys(s))))
    q["quality"] = np.where(q["unresolved"] > 0, "HAS_UNRESOLVED_DISCONTINUITY", "NO_UNRESOLVED_DISCONTINUITY")
    return q.reset_index()
