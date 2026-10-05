"""Deterministic Stage 2 build + verification (Phase 2.1, B2).

Starts from the archived raw NSE files (data/raw/nse_archive, SHA-256 in
data/stage2/raw_manifest.jsonl) and committed code only. Never reads anything
after RESEARCH_CUTOFF and never touches ORB holdout data.

  1. raw manifest: the Phase 2 records are an unchanged prefix (append-only check)
  2. PANEL-1   rebuilt in memory, every year hash == panel1_manifest.json
  3. CA-2      ca2_event_validation.csv, ca2_unexplained_jumps.csv          == PHASE2_MANIFEST
  4. ID-1      id1_{segments,entities,links,flags}.csv                      == PHASE2_MANIFEST
  5. ID-1 review: id1_later_symbol_ca_resolution.csv, id1_jump_identity_review.csv
  6. UNIV-1    univ1_pit_universe.parquet (frozen; standard sessions)      == 2abf457a...
  7. RET-1     ret1_<year>.parquet == ret1_manifest.json; ret1_* CSVs     == PHASE2_MANIFEST
  8. PANEL-1.1 (adds weekend special sessions + session_type) and the special-session list
  9. RET-1.1   (SPECIAL_SESSION_SPAN, VALIDATED_LARGE_RESIDUAL)
 10. Phase 2.1 committed files and the full raw manifest               == PHASE2_MANIFEST
Steps 1-7 write nothing to the repository: every Phase 2 artifact is regenerated
in a temporary work directory and compared by SHA-256. Steps 8-9 write their
outputs once; on later runs they are rebuilt and compared with the stored hashes
(build-or-verify, never overwritten). Exit status 1 on any mismatch.

    python3 scripts/build_stage2.py
"""

import hashlib
import io
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.access import RESEARCH_CUTOFF                                      # noqa: E402
from src.config import BASE_DIR                                             # noqa: E402
from src.stage2 import panel as pm, returns as rm                           # noqa: E402
from src.stage2.archive import MANIFEST                                     # noqa: E402
from src.stage2.corporate_actions import classify, load_events, unexplained_jumps, validate  # noqa: E402
from src.stage2.identity import end_status, entities, links, load_sources, resolve_historical, segments  # noqa: E402
from src.stage2.universe import build as univ_build, code_version          # noqa: E402

D = BASE_DIR / "data" / "stage2"
VERIFIED_START = "2011-06-22"
PHASE2 = json.loads((D / "PHASE2_MANIFEST.json").read_text())
PHASE2_RAW_LINES = 5844             # raw_manifest.jsonl records at the Phase 2 commit (356a592)
UNIV1_SHA = "2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42"
FAIL = []


def sha(b):
    return hashlib.sha256(b).hexdigest()


def check(name, got, want):
    ok = got == want
    print(f"  {'OK  ' if ok else 'FAIL'} {name}" + ("" if ok else f"  got {got}  want {want}"), flush=True)
    if not ok:
        FAIL.append(name)


def committed(rel, text):
    """Rebuilt CSV text vs the SHA-256 recorded in PHASE2_MANIFEST for a committed file."""
    check(rel, sha(text.encode()), PHASE2["committed_files_sha256"][f"data/stage2/{rel}"])


def rt(df, columns=None):
    """Parquet round trip (the Phase 2 pipeline passed every intermediate through parquet)."""
    b = io.BytesIO()
    df.to_parquet(b)
    b.seek(0)
    return pd.read_parquet(b, columns=columns)


def pq_sha(df):
    b = io.BytesIO()
    df.to_parquet(b, index=False)
    return sha(b.getvalue())


def standard_files():
    return [r for r in pm.raw_files() if date.fromisoformat(r["session"]).weekday() < 5]


# ------------------------------------------------------------------ 1. raw manifest
def step_raw():
    print("1. raw manifest (append-only)")
    lines = MANIFEST.read_bytes().splitlines(keepends=True)
    check("Phase 2 raw records unchanged", sha(b"".join(lines[:PHASE2_RAW_LINES])), PHASE2["raw_archive"]["sha256"])
    recs = [json.loads(l) for l in lines]
    check("no record after the research cutoff", max(r["session"] for r in recs if r["session"]) <= RESEARCH_CUTOFF, True)
    bad = [r["url"] for r in recs if r["status"] == 200 and r.get("sha256") and (BASE_DIR / r["path"]).exists()
           and sha((BASE_DIR / r["path"]).read_bytes()) != r["sha256"]]
    missing = [r["path"] for r in recs if r["status"] == 200 and not (BASE_DIR / r["path"]).exists()]
    check("raw files present", missing, [])
    check("raw file SHA-256 == manifest", bad, [])


# ------------------------------------------------------------------ 2. PANEL-1
def step_panel1():
    print("2. PANEL-1 (standard sessions)")
    want = {e["year"]: e for e in json.loads((D / "panel" / "panel1_manifest.json").read_text())["files"]}
    files, ca, full = standard_files(), [], []
    for y in sorted(want):
        df, _ = pm.build_year(y, files)
        check(f"panel1_{y}.parquet", pq_sha(df), want[y]["sha256"])
        check(f"panel1_{y} qa", pm.qa(df) | pm.qa_conflicts(df), want[y]["qa"])
        ca.append(df[["date", "symbol", "isin", "open", "close", "prevclose"]])
        full.append(df[df["date"] >= VERIFIED_START])
    ca = pd.concat(ca, ignore_index=True)
    full = pd.concat(full, ignore_index=True)
    return ca, full


# ------------------------------------------------------------------ 3. CA-2
def step_ca2(ca):
    print("3. CA-2 validation outputs")
    p = rt(ca)
    ev = load_events()
    v = validate(ev, p)
    vcsv = v.to_csv(index=False)
    committed("validation/ca2_event_validation.csv", vcsv)
    j = unexplained_jumps(p, ev)
    u = j[~j.explained].copy()
    q = p.sort_values(["symbol", "date"])
    q["prev_date"] = q.groupby("symbol").date.shift(1)
    sess = pd.Index(sorted(p.date.unique()))
    pos = pd.Series(range(len(sess)), index=sess)
    u = u.merge(q[["symbol", "date", "prev_date", "isin"]], on=["symbol", "date"], how="left", suffixes=("", "_q"))
    u["gap"] = pos.reindex(u.date).values - pos.reindex(u.prev_date).values
    isin = u["isin_q"] if "isin_q" in u else u["isin"]
    u["cause"] = ["GAP>1 session (absent from EQ)" if g > 1 else ("FUND/ETF unit (ISIN INF)" if str(i).startswith("INF") else
                  ("COMPANY (ISIN INE)" if str(i).startswith("INE") else "NO ISIN (pre-2011-06-22)")) for g, i in zip(u.gap, isin)]
    jcsv = u.to_csv(index=False)
    committed("validation/ca2_unexplained_jumps.csv", jcsv)
    print(f"  events {len(v)} {dict(Counter(v.status))} | unexplained jumps {len(u)}")
    return ev, vcsv, jcsv


# ------------------------------------------------------------------ 4. ID-1
def step_identity(ca, ev):
    print("4. ID-1 identity outputs")
    b = io.BytesIO()
    ca.to_parquet(b)
    b.seek(0)
    p = pd.read_parquet(b, columns=["date", "symbol", "isin"])
    src = load_sources()
    seg = segments(p)
    e, f = links(seg, src, ev)
    ent = entities(seg, e)
    es = end_status(ent, src, p.date.max())
    seg, ent, es = rt(seg), rt(ent), rt(es)
    ecsv, fcsv = e.to_csv(index=False), f.to_csv(index=False)
    committed("identity/id1_segments.csv", ent.to_csv(index=False))
    committed("identity/id1_entities.csv", es.assign(symbols=lambda d: d.symbols.map("|".join),
                                                     isins=lambda d: d.isins.map("|".join)).to_csv(index=False))
    committed("identity/id1_links.csv", ecsv)
    committed("identity/id1_flags.csv", fcsv)
    print(f"  segments {len(seg)} | links {len(e)} | entities {len(es)}")
    return seg, ent, pd.read_csv(io.StringIO(ecsv)), pd.read_csv(io.StringIO(fcsv))


# ------------------------------------------------------------------ 5. ID-1 review outputs
def step_identity_review(ca, ent, e, f, ev, vcsv, jcsv):
    print("5. ID-1 review outputs")
    v = pd.read_csv(io.StringIO(vcsv), parse_dates=["ex_date"])
    nb = v[v.status == "NO_PRICES:NO_SESSION_BEFORE_EX"].copy()
    p = rt(ca, columns=["date", "symbol", "close"])
    res = []
    for r in nb.itertuples():
        st, s = resolve_historical(ent, r.symbol, r.ex_date - pd.Timedelta(days=1))
        row = {"symbol": r.symbol, "ex_date": r.ex_date, "factor": r.factor, "resolution": st}
        if s is not None:
            row["historical_symbol"] = s["symbol"]
            row["entity_id"] = s["entity_id"]
            eseg = ent[ent.entity_id == s["entity_id"]]
            ids = set(eseg.segment_id)
            evd = e[e.from_segment.isin(ids) | e.to_segment.isin(ids)]
            row["evidence"] = ";".join(sorted(set(evd.evidence)))
            q = p[p.symbol.isin(set(eseg.symbol))].sort_values("date")
            bf = q[q.date < r.ex_date]
            af = q[(q.date >= r.ex_date) & (q.date <= r.ex_date + pd.Timedelta(days=10))]
            if len(bf) and len(af):
                raw = af.iloc[0].close / bf.iloc[-1].close
                row["raw_ratio"] = raw
                row["ca_status_after_identity"] = classify(raw, r.factor)
            else:
                row["ca_status_after_identity"] = "NO_PRICES"
        res.append(row)
    committed("validation/id1_later_symbol_ca_resolution.csv", pd.DataFrame(res).to_csv(index=False))

    j = pd.read_csv(io.StringIO(jcsv), parse_dates=["date"])
    j = j[j.cause == "COMPANY (ISIN INE)"]
    adj = ev[ev.factor.notna() | ev.kind.isin(["CONSOLIDATION", "UNPARSED_BONUS_SPLIT", "RIGHTS"])]
    m = j.merge(ev[["symbol", "ex_date"]], on="symbol", how="left")
    m["near"] = (m.ex_date - m.date).abs() <= pd.Timedelta(days=10)
    has = m.groupby(["symbol", "date"]).near.any().reset_index()
    j = j.merge(has, on=["symbol", "date"])
    base = j[~j.near].copy()
    newseg = dict(zip(zip(ent.symbol, ent["first"]), ent.segment_id))
    linked = set(e[e.evidence == "ISIN_CHANGE_CA"].to_segment)
    unexpl = set(f[f.flag == "ISIN_CHANGE_UNEXPLAINED"].segment_id)
    syms_by_ent = ent.groupby("entity_id").symbol.agg(set)

    def entity_at(sym, d):
        c = ent[(ent.symbol == sym) & (ent["first"] <= d) & (ent["last"] >= d)]
        return c.entity_id.iloc[0] if len(c) == 1 else None
    out = []
    for r in base.itertuples():
        sid = newseg.get((r.symbol, r.date))
        if sid in linked:
            cat = "ISIN change at jump, linked to an NSE CA record filed under a later symbol"
        elif sid in unexpl:
            cat = "ISIN change at jump (identity event evidenced) - no NSE CA record; factor unknown"
        else:
            eid = entity_at(r.symbol, r.date)
            other = (syms_by_ent.get(eid, set()) - {r.symbol}) if eid else set()
            o = adj[adj.symbol.isin(other) & ((adj.ex_date - r.date).abs() <= pd.Timedelta(days=10))]
            cat = ("NSE CA record exists under the entity's other (later/earlier) symbol: " + ",".join(sorted(set(o.kind)))
                   if len(o) else "no identity/listing evidence - remains flagged")
        out.append({"symbol": r.symbol, "date": r.date, "ratio": r.ratio, "identity_category": cat})
    committed("validation/id1_jump_identity_review.csv", pd.DataFrame(out).to_csv(index=False))


# ------------------------------------------------------------------ 6. UNIV-1 (frozen)
def step_univ1(full, seg, e):
    print("6. UNIV-1 (frozen; standard sessions)")
    p = rt(full[["date", "symbol", "isin", "series", "value", "source_sha256"]])
    u = rt(univ_build(p, seg, e))
    h = pq_sha(u)
    check("univ1_pit_universe.parquet == frozen SHA-256", h, UNIV1_SHA)
    check("univ1_pit_universe.parquet == committed file", h, sha((D / "universe" / "univ1_pit_universe.parquet").read_bytes()))
    m = u[u.status == "MEMBER"]
    print(f"  rows {len(u)} | selection dates {u.selection_date.nunique()} | distinct members {m.entity_id.nunique()}")
    return u


# ------------------------------------------------------------------ 7. RET-1
def step_ret1(full, seg, e, ev, u):
    print("7. RET-1")
    want = json.loads((D / "returns" / "ret1_manifest.json").read_text())
    r = rt(rm.build(rt(full), seg, e, ev))
    for y, g in r.groupby(r.date.dt.year):
        check(f"ret1_{y}.parquet", pq_sha(g), want["datasets"][f"data/stage2/datasets/ret1/ret1_{y}.parquet"])
    check("ret1 status counts", r.return_status.value_counts().to_dict(), want["stats"]["status_counts"])
    committed("returns/ret1_entity_quality.csv", rt(rm.entity_quality(r)).to_csv(index=False))
    bad = r[r.return_status.isin(["EVENT_DISCREPANT", "EVENT_INCONCLUSIVE", "EVENT_UNADJUSTABLE", "UNEXPLAINED_JUMP"])]
    bcsv = bad[["entity_id", "symbol", "date", "prev_close", "close", "ret_raw", "event_kind", "event_status",
                "other_events", "return_status", "event_subject"]].to_csv(index=False)
    committed("returns/ret1_unresolved_discontinuities.csv", bcsv)
    m = u[u.status == "MEMBER"]
    seg2ent = r[["segment_id", "entity_id"]].drop_duplicates("segment_id").set_index("segment_id").entity_id
    mem = set(m.segment_at_selection.map(seg2ent))
    b = pd.read_csv(io.StringIO(bcsv), parse_dates=["date"])
    b = b[b.entity_id.isin(mem)]
    lst = b.groupby("entity_id").agg(symbols=("symbol", lambda s: "|".join(dict.fromkeys(s))), n_unresolved=("date", "size"),
                                     first=("date", "min"), last=("date", "max"),
                                     statuses=("return_status", lambda s: "+".join(sorted(set(s))))).reset_index()
    committed("returns/ret1_member_entities_with_unresolved_discontinuities.csv", lst.to_csv(index=False))


# ------------------------------------------------------------------ build-or-verify helpers (Phase 2.1)
def write_or_verify(path, blob):
    """New Phase 2.1 artifact: write once; if it exists, the rebuild must be byte-identical."""
    path = Path(path)
    if path.exists():
        check(f"{path.relative_to(BASE_DIR)} (rebuild identical)", sha(blob), sha(path.read_bytes()))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
        print(f"  wrote {path.relative_to(BASE_DIR)}")
    return sha(blob)


def pq_bytes(df):
    b = io.BytesIO()
    df.to_parquet(b, index=False)
    return b.getvalue()


def manifest_json(obj):
    return (json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n").encode()


# ------------------------------------------------------------------ 8. PANEL-1.1
def step_panel11():
    print("8. PANEL-1.1 (standard + weekend special sessions)")
    recs = [json.loads(l) for l in MANIFEST.read_text().splitlines() if l.strip()]
    files, entries, specials = pm.raw_files(), [], []
    for y in range(2005, 2027):
        df, _ = pm.build_year(y, files, include_special=True)
        if df.empty:
            continue
        f = D / "datasets" / "panel1_1" / f"panel1_1_{y}.parquet"
        h = write_or_verify(f, pq_bytes(df))
        std = df[df.session_type == "STANDARD"].drop(columns="session_type")
        check(f"panel1_1_{y} standard rows == PANEL-1", pq_sha(std),
              {e["year"]: e["sha256"] for e in json.loads((D / "panel" / "panel1_manifest.json").read_text())["files"]}[y])
        entries.append({"file": str(f.relative_to(BASE_DIR)), "sha256": h, "year": y,
                        "sessions": int(df["date"].nunique()),
                        "special_sessions": int(df.loc[df.session_type != "STANDARD", "date"].nunique()),
                        "rows": len(df), "special_rows": int((df.session_type != "STANDARD").sum()),
                        "qa": pm.qa(df) | pm.qa_conflicts(df)})
        sd = sorted(df.loc[df.session_type != "STANDARD", "date"].unique())
        sess = sorted(df["date"].unique())
        for d in sd:
            s = df[df.date == d].set_index("symbol")
            prev_std = max((x for x in sess if x < d and x.weekday() < 5), default=None)
            nxt = min((x for x in sess if x > d and x.weekday() < 5), default=None)
            row = {"date": d.date(), "weekday": d.day_name(), "session_type": "SPECIAL_WEEKEND",
                   "source": s.source.iloc[0], "source_sha256": s.source_sha256.iloc[0], "eq_rows": len(s),
                   "prev_standard_session": prev_std.date() if prev_std is not None else None,
                   "next_standard_session": nxt.date() if nxt is not None else None}
            if nxt is not None:                       # evidence: next session's PREVCLOSE is the special close
                n = df[df.date == nxt].set_index("symbol")
                c = n.index.intersection(s.index)
                row["next_prevclose_eq_special_close"] = round(float((n.loc[c, "prevclose"] == s.loc[c, "close"]).mean()), 4)
                if prev_std is not None:
                    pv = df[df.date == prev_std].set_index("symbol")
                    c2 = c.intersection(pv.index)
                    row["next_prevclose_eq_prev_standard_close"] = round(float((n.loc[c2, "prevclose"] == pv.loc[c2, "close"]).mean()), 4)
            specials.append(row)
    sp = pd.DataFrame(specials)
    write_or_verify(D / "panel" / "special_sessions.csv", sp.to_csv(index=False).encode())
    cal = pm.calendar_check(recs, "2005-01-01", RESEARCH_CUTOFF, weekends=True)
    check("every weekend day 2005..cutoff attempted", cal["never_attempted"], [])
    man = {"methodology_version": "PANEL-1.1", "cutoff": RESEARCH_CUTOFF,
           "definition": "PANEL-1 + weekend (Saturday/Sunday) special sessions; session_type STANDARD | SPECIAL_WEEKEND; "
                         "rows with session_type == STANDARD are byte-identical to PANEL-1",
           "files": entries, "special_sessions": len(sp), "weekend_calendar_2005_to_cutoff": cal,
           "code_sha256": code_version(files=("src/stage2/panel.py", "src/stage2/archive.py"))["files_sha256"]}
    write_or_verify(D / "panel" / "panel1_1_manifest.json", manifest_json(man))
    print(f"  special sessions: {len(sp)}")
    return sp


# ------------------------------------------------------------------ 9. RET-1.1
def step_ret11(full, seg, e, ev, u, sp):
    print("9. RET-1.1 (special-session spans, large-residual flag)")
    r = rm.build(rt(full), seg, e, ev, special_sessions=pd.to_datetime(sp["date"]), large_residual=rm.LARGE_RESIDUAL)
    files = {}
    for y, g in r.groupby(r.date.dt.year):
        f = D / "datasets" / "ret1_1" / f"ret1_1_{y}.parquet"
        files[str(f.relative_to(BASE_DIR))] = write_or_verify(f, pq_bytes(g))
    big = r[r.return_status == "VALIDATED_LARGE_RESIDUAL"]
    write_or_verify(D / "returns" / "ret1_1_large_residuals.csv",
                    big[["entity_id", "symbol", "date", "prev_close", "close", "ret_raw", "event_factor", "event_kind",
                         "ret_adj", "event_subject"]].to_csv(index=False).encode())
    write_or_verify(D / "returns" / "ret1_1_entity_quality.csv", rm.entity_quality(r).to_csv(index=False).encode())
    m = u[u.status == "MEMBER"]
    span = r[r.spans_special_session]
    man = {"methodology_version": rm.METHOD_VERSION_1_1, "cutoff": RESEARCH_CUTOFF, "verified_start": VERIFIED_START,
           "parameters": {"jump": rm.JUMP, "large_residual": rm.LARGE_RESIDUAL,
                          "special_sessions": "data/stage2/panel/special_sessions.csv (never return endpoints)"},
           "datasets": files,
           "stats": {"rows": len(r), "entities": int(r.entity_id.nunique()),
                     "status_counts": r.return_status.value_counts().to_dict(),
                     "research_grade_rows": int(r.research_grade.sum()),
                     "rows_spanning_a_special_session": len(span),
                     "spanning_rows_by_status": span.return_status.value_counts().to_dict(),
                     "validated_large_residual_rows": len(big),
                     "univ1_members_unchanged_sha256": UNIV1_SHA, "univ1_member_rows": len(m)},
           "code_sha256": code_version(files=("src/stage2/returns.py", "src/stage2/corporate_actions.py",
                                              "src/stage2/identity.py", "src/stage2/panel.py"))["files_sha256"]}
    write_or_verify(D / "returns" / "ret1_1_manifest.json", manifest_json(man))
    print(f"  {man['stats']['status_counts']}")


# ------------------------------------------------------------------ 10. Phase 2.1 records
def step_phase21():
    print("10. Phase 2.1 files == PHASE2_MANIFEST")
    p21 = PHASE2["phase2_1"]
    check("raw manifest (Phase 2 + weekend records)", sha(MANIFEST.read_bytes()), p21["raw_manifest_sha256"])
    for rel, want in p21["committed_files_sha256"].items():
        check(rel, sha((BASE_DIR / rel).read_bytes()), want)


def main():
    step_raw()
    ca, full = step_panel1()
    ev, vcsv, jcsv = step_ca2(ca)
    seg, ent, e, f = step_identity(ca, ev)
    step_identity_review(ca, ent, e, f, ev, vcsv, jcsv)
    del ca
    u = step_univ1(full, seg, e)
    step_ret1(full, seg, e, ev, u)
    sp = step_panel11()
    step_ret11(full, seg, e, ev, u, sp)
    step_phase21()
    print("\nRESULT:", "ALL CHECKS PASSED" if not FAIL else f"{len(FAIL)} FAILED: {FAIL}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
