"""Stage 2 historical identity / listing layer (Phase 2E). Methodology version ID-1.

SEGMENT = one listing record taken directly from NSE's own daily files: a symbol
with one ISIN (or no ISIN before 2011-06-22, when NSE did not publish it). Before
2011-06-22 a symbol's presence is split into a new segment at any gap longer than
GAP_SPLIT sessions, because without an ISIN nothing proves that a returning
symbol is the same security.

LINKS between segments are made ONLY with explicit evidence:
  ISIN_SAME      same ISIN (official security identifier) under two symbols that
                 never trade on the same day
  SYMBOL_CHANGE  NSE symbolchange.csv old -> new on date D, old segment ending and new
                 segment starting within LINK_WINDOW of D, and (when both have ISINs)
                 identical ISINs
  ISIN_INTRO     the same symbol trading on the last session without an ISIN field and
                 on 2011-06-22, when NSE first published ISINs (a file-format change,
                 not a corporate event)
  ISIN_CHANGE_CA the same symbol changes ISIN between adjacent sessions AND an NSE
                 corporate-action record (split/bonus/consolidation) has its ex-date within
                 LINK_WINDOW, filed under that symbol or under a symbol already proven (by
                 ISIN_SAME / SYMBOL_CHANGE / ISIN_INTRO) to be the same entity
Everything else stays UNLINKED and is flagged. Names, price continuity, look-alike
symbols, price jumps and Yahoo data are never used.
"""

import json

import numpy as np
import pandas as pd

from src.access import RESEARCH_CUTOFF
from src.config import BASE_DIR
from src.stage2.archive import MANIFEST

METHOD_VERSION = "ID-1"
ISIN_INTRO = pd.Timestamp("2011-06-22")
GAP_SPLIT = 20                       # sessions; pre-ISIN segments split at longer gaps
LINK_WINDOW = pd.Timedelta(days=10)
CUT = pd.Timestamp(RESEARCH_CUTOFF)


# ------------------------------------------------------------------ sources

def _latest(name):
    recs = [json.loads(l) for l in MANIFEST.read_text().splitlines() if l.strip()]
    recs = [r for r in recs if r["kind"] == "equities_list" and r["status"] == 200 and r["path"].endswith(name)]
    r = sorted(recs, key=lambda r: r["path"])[-1]
    return BASE_DIR / r["path"], r["sha256"]


def _date(s, fmt=None):
    return pd.to_datetime(s.astype(str).str.strip(), format=fmt or "mixed", dayfirst=True, errors="coerce")


def load_sources():
    """NSE identity/listing snapshots; every row dated after the cutoff is dropped."""
    p, sha = _latest("symbolchange.csv")
    sc = pd.read_csv(p, header=None, names=["company", "old", "new", "date"], skipinitialspace=True, dtype=str)
    sc["date"] = _date(sc["date"], "%d-%b-%Y")
    p2, sha2 = _latest("namechange.csv")
    nc = pd.read_csv(p2, skipinitialspace=True, dtype=str)
    nc.columns = ["symbol", "prev_name", "new_name", "date"]
    nc["date"] = _date(nc["date"])
    p3, sha3 = _latest("delisted.csv")
    dl = pd.read_csv(p3, encoding="latin-1", skipinitialspace=True, usecols=[0, 1, 2, 3], dtype=str)
    dl.columns = ["symbol", "company", "date", "type"]
    dl["date"] = _date(dl["date"])
    p4, sha4 = _latest("EQUITY_L.csv")
    eq = pd.read_csv(p4, skipinitialspace=True, dtype=str)
    eq.columns = [c.strip().lower().replace(" ", "_") for c in eq.columns]
    eq["date"] = _date(eq["date_of_listing"], "%d-%b-%Y")
    out = {}
    for k, df in (("symbol_changes", sc), ("name_changes", nc), ("delisted", dl), ("listed", eq)):
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].str.strip()
        out[k] = df[df["date"].notna() & (df["date"] <= CUT)].reset_index(drop=True)
    out["sha256"] = {"symbolchange": sha, "namechange": sha2, "delisted": sha3, "EQUITY_L": sha4}
    return out


# ----------------------------------------------------------------- segments

def segments(panel):
    """panel: date, symbol, isin (EQ rows). -> one row per listing segment."""
    if panel["date"].max() > CUT:
        raise ValueError("panel contains dates after the research cutoff - refused")
    sess = pd.Index(sorted(panel["date"].unique()))
    pos = pd.Series(np.arange(len(sess)), index=sess)
    p = panel[["date", "symbol", "isin"]].copy()
    p["isin"] = p["isin"].astype("string").fillna("")
    p["pos"] = pos.reindex(p["date"]).to_numpy()
    p = p.sort_values(["symbol", "isin", "pos"])
    gap = p.groupby(["symbol", "isin"])["pos"].diff()
    new = gap.isna() | ((p["isin"] == "") & (gap > GAP_SPLIT + 1))
    p["part"] = new.groupby([p["symbol"], p["isin"]]).cumsum()
    g = p.groupby(["symbol", "isin", "part"])
    seg = g.agg(first=("date", "min"), last=("date", "max"), n_sessions=("date", "size"),
                first_pos=("pos", "min"), last_pos=("pos", "max")).reset_index()
    seg["max_gap_sessions"] = g["pos"].apply(lambda s: int(s.diff().max() - 1) if len(s) > 1 else 0).to_numpy()
    seg["segment_id"] = seg["symbol"] + "|" + seg["isin"].replace("", "NOISIN") + "|" + seg["part"].astype(str)
    seg["instrument_type"] = np.where(seg["isin"].str.startswith("INF"), "FUND_UNIT",
                              np.where(seg["isin"].str.startswith("INE"), "EQUITY",
                              np.where(seg["isin"] == "", "UNKNOWN_NO_ISIN", "OTHER_ISIN")))
    return seg.drop(columns="part")


# -------------------------------------------------------------------- links

def links(seg, sources, ca_events):
    """Evidence-backed edges between segments + flags for what could not be linked."""
    edges, flags = [], []
    s = seg.set_index("segment_id")
    # ISIN_SAME
    isn = seg[seg["isin"] != ""]
    for isin, grp in isn.groupby("isin"):
        if grp["symbol"].nunique() < 2:
            continue
        grp = grp.sort_values("first")
        rows = list(grp.itertuples())
        for a, b in zip(rows, rows[1:]):
            if a.symbol == b.symbol:
                continue
            if b.first_pos <= a.last_pos:
                flags.append({"segment_id": b.segment_id, "flag": "ISIN_SHARED_CONCURRENTLY", "detail": a.segment_id})
            else:
                edges.append((a.segment_id, b.segment_id, "ISIN_SAME", isin))
    # SYMBOL_CHANGE (NSE file)
    by_sym = {k: v for k, v in seg.groupby("symbol")}
    for r in sources["symbol_changes"].itertuples():
        olds, news = by_sym.get(r.old), by_sym.get(r.new)
        if olds is None or news is None:
            continue
        o = olds[(olds["last"] < r.date) & (olds["last"] >= r.date - LINK_WINDOW)]
        n = news[(news["first"] >= r.date - LINK_WINDOW) & (news["first"] <= r.date + LINK_WINDOW)]
        for a in o.itertuples():
            for b in n.itertuples():
                if a.isin and b.isin and a.isin != b.isin:
                    flags.append({"segment_id": b.segment_id, "flag": "SYMBOL_CHANGE_ISIN_CONFLICT",
                                  "detail": f"{r.old}->{r.new} {r.date.date()} {a.isin}!={b.isin}"})
                else:
                    edges.append((a.segment_id, b.segment_id, "SYMBOL_CHANGE", f"{r.old}->{r.new} {r.date.date()}"))
    # ISIN_INTRO
    pre = seg[(seg["isin"] == "") & (seg["last"] < ISIN_INTRO)]
    first_isin_session = seg.loc[seg["first"] >= ISIN_INTRO, "first"].min()
    post = seg[(seg["isin"] != "") & (seg["first"] == first_isin_session)]
    last_pre_pos = s.loc[s["last"] < ISIN_INTRO, "last_pos"].max()
    pre_last = pre[pre["last_pos"] == last_pre_pos]
    m = pre_last.merge(post, on="symbol", suffixes=("_a", "_b"))
    for r in m.itertuples():
        edges.append((r.segment_id_a, r.segment_id_b, "ISIN_INTRO", f"{r.symbol} -> {r.isin_b}"))
    # ISIN_CHANGE_CA (same symbol, adjacent ISIN segments). NSE often files old corporate actions
    # under the company's LATER symbol, so the record may be filed under any symbol already proven
    # (by the links above) to belong to the same entity - never under a merely similar symbol.
    base = pd.DataFrame(edges, columns=["from_segment", "to_segment", "evidence", "detail"])
    ent0 = entities(seg, base).set_index("segment_id")["entity_id"]
    ent_syms = seg.assign(entity_id=seg["segment_id"].map(ent0)).groupby("entity_id")["symbol"].agg(set)
    adj = ca_events[ca_events["factor"].notna() | ca_events["kind"].isin(["CONSOLIDATION", "UNPARSED_BONUS_SPLIT"])]
    adj = adj.assign(ex_date=pd.to_datetime(adj["ex_date"]))
    for sym, grp in isn.groupby("symbol"):
        if grp["isin"].nunique() < 2:
            continue
        rows = list(grp.sort_values("first").itertuples())
        for a, b in zip(rows, rows[1:]):
            if a.isin == b.isin or b.first_pos - a.last_pos > 5:
                continue
            syms = ent_syms.get(ent0[b.segment_id], {sym}) | {sym}
            hit = adj[adj["symbol"].isin(syms) & ((adj["ex_date"] - b.first).abs() <= LINK_WINDOW)]
            if len(hit):
                h = hit.iloc[0]
                via = "" if h["symbol"] == sym else f" [record filed under later symbol {h['symbol']}]"
                edges.append((a.segment_id, b.segment_id, "ISIN_CHANGE_CA", f"{h['subject'].strip()}{via}"))
            else:
                flags.append({"segment_id": b.segment_id, "flag": "ISIN_CHANGE_UNEXPLAINED",
                              "detail": f"{a.isin}->{b.isin} at {b.first.date()}"})
    e = pd.DataFrame(edges, columns=["from_segment", "to_segment", "evidence", "detail"]).drop_duplicates()
    return e, pd.DataFrame(flags, columns=["segment_id", "flag", "detail"])


def entities(seg, edges):
    """Union-find over evidence edges -> entity_id per segment (smallest segment_id)."""
    parent = {k: k for k in seg["segment_id"]}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in zip(edges["from_segment"], edges["to_segment"]):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    out = seg.copy()
    out["entity_id"] = out["segment_id"].map(find)
    return out


def end_status(ent, sources, last_session):
    """Per entity: ACTIVE_AT_CUTOFF; DELISTED_EVIDENCED - an NSE delisted.csv row for one of its
    symbols, assigned to the ONE entity carrying that symbol whose last session is the latest
    on/before the delisting date (one record never evidences several entities);
    or ENDED_UNEXPLAINED."""
    g = ent.groupby("entity_id").agg(symbols=("symbol", lambda s: sorted(set(s))), first=("first", "min"),
                                     last=("last", "max"), isins=("isin", lambda s: sorted(set(s) - {""})),
                                     instrument_type=("instrument_type", lambda s: "FUND_UNIT" if "FUND_UNIT" in set(s)
                                                      else ("EQUITY" if "EQUITY" in set(s) else sorted(set(s))[0])),
                                     n_segments=("segment_id", "size")).reset_index()
    ex = g[["entity_id", "symbols", "last"]].explode("symbols").rename(columns={"symbols": "symbol"})
    evidence = {}
    for d in sources["delisted"].itertuples():
        c = ex[(ex["symbol"] == d.symbol) & (ex["last"] <= d.date)]
        if len(c):
            eid = c.sort_values("last").iloc[-1]["entity_id"]
            evidence.setdefault(eid, f"{d.symbol} {d.date.date()} {d.type}")
    g["end_status"] = np.where(g["last"] >= last_session, "ACTIVE_AT_CUTOFF",
                               np.where(g["entity_id"].isin(list(evidence)), "DELISTED_EVIDENCED", "ENDED_UNEXPLAINED"))
    g["end_evidence"] = g["entity_id"].map(evidence)
    g.loc[g["end_status"] == "ACTIVE_AT_CUTOFF", "end_evidence"] = None
    return g


def resolve_historical(ent, symbol, when):
    """For a record filed under `symbol` (often a LATER symbol) at date `when`: the segment of the
    same evidenced entity that was listed at `when`. Returns (status, segment_row_or_None).
    RESOLVED only if exactly one entity carrying `symbol` spans `when` and one of its segments
    is listed at `when`; otherwise UNRESOLVED_* (never guessed)."""
    when = pd.Timestamp(when)
    if when > CUT:
        raise ValueError("date after the research cutoff - refused")
    cand = ent[ent["entity_id"].isin(ent.loc[ent["symbol"] == symbol, "entity_id"])]
    if cand.empty:
        return "UNRESOLVED_SYMBOL_NOT_IN_PANEL", None
    spans = cand.groupby("entity_id").agg(first=("first", "min"), last=("last", "max"))
    hit = spans[(spans["first"] <= when) & (spans["last"] >= when)]
    if len(hit) != 1:
        return ("UNRESOLVED_NO_ENTITY_LISTED_AT_DATE" if hit.empty else "UNRESOLVED_AMBIGUOUS"), None
    segs = cand[(cand["entity_id"] == hit.index[0]) & (cand["first"] <= when) & (cand["last"] >= when)]
    if len(segs) != 1:
        # `when` may fall on a non-session day between two adjacent segments: take the one listed before
        prior = cand[(cand["entity_id"] == hit.index[0]) & (cand["first"] <= when)].sort_values("last")
        if prior.empty:
            return "UNRESOLVED_NO_SEGMENT_AT_DATE", None
        return "RESOLVED", prior.iloc[-1]
    return "RESOLVED", segs.iloc[0]
