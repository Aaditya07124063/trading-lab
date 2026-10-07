"""S2-MOM-v1 inputs: deterministic dataset builder and loaders with an explicit cutoff.

Reads only data/stage2 (RET-1.1, UNIV-1, ID-1) and its own outputs under data/stage3/s2_mom_v1.
Every reader takes the cutoff as an argument and refuses one later than src.access.RESEARCH_CUTOFF.
Never reads intraday, collector or ORB files.

  research/panel.parquet   daily study returns of every entity in any step's universe (git-ignored)
  research/sessions.csv    market sessions
  research/identity.csv    survivor pool P and delisting class per entity
  research/gap_rows.csv    multi-session gap rows and their no-event flag (R-gap sensitivity only)
  primary/, oos/           calendar.csv and universes.csv of each sample
  manifest.json            provenance, input hashes, output hashes, structural counts
"""

import glob
import hashlib
import json
from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd

from src.access import RESEARCH_CUTOFF
from src.config import BASE_DIR
from src.registry.experiments import environment
from src.stage3 import ladder
from src.stage3.protocol import (DELIST_RETURN, FIRST_T, LAST_T, PROTOCOL_ID, PROTOCOL_SHA256, T_STAR, TOP_N,
                                 UNIV1_SHA256, verify_protocol)

D2 = BASE_DIR / "data" / "stage2"
OUT = BASE_DIR / "data" / "stage3" / "s2_mom_v1"
RET_COLS = ["entity_id", "segment_id", "date", "close", "prev_close", "ret_raw", "event_factor", "other_events",
            "ret_research", "return_status", "research_grade"]


def _cut(cutoff):
    ts = pd.Timestamp(cutoff)
    if ts > pd.Timestamp(RESEARCH_CUTOFF):
        raise ValueError(f"cutoff {ts.date()} is after the research cutoff {RESEARCH_CUTOFF} - refused")
    return ts


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_ret(cutoff, columns=RET_COLS):
    """RET-1.1 rows dated <= cutoff. Each file is checked against ret1_1_manifest.json first."""
    ts = _cut(cutoff)
    man = json.loads((D2 / "returns" / "ret1_1_manifest.json").read_text())
    if man["methodology_version"] != "RET-1.1":
        raise ValueError("returns manifest is not RET-1.1")
    parts = []
    for rel, want in sorted(man["datasets"].items()):
        if _sha(BASE_DIR / rel) != want:
            raise ValueError(f"{rel} does not match the RET-1.1 manifest")
        parts.append(pd.read_parquet(BASE_DIR / rel, columns=columns, filters=[("date", "<=", ts)]))
    r = pd.concat(parts, ignore_index=True)
    if len(r) and r["date"].max() > ts:
        raise ValueError("row after the cutoff - refused")
    return r, man


def load_univ():
    f = D2 / "universe" / "univ1_pit_universe.parquet"
    if _sha(f) != UNIV1_SHA256:
        raise ValueError("UNIV-1 file does not match the frozen SHA-256")
    return pd.read_parquet(f, columns=["selection_date", "segment_at_selection", "status", "rank"])


def identity(ret):
    """seg2ent (segment -> RET-1.1 full-sample entity), survivor pool P (B1.1) and the §22
    delisting class per entity, from ID-1. Raises if ID-1 and RET-1.1 group segments differently."""
    seg = ret[["segment_id", "entity_id"]].drop_duplicates()
    if seg["segment_id"].duplicated().any():
        raise ValueError("a segment belongs to two RET-1.1 entities")
    id_seg = pd.read_csv(D2 / "identity" / "id1_segments.csv", usecols=["segment_id", "entity_id"])
    id_ent = pd.read_csv(D2 / "identity" / "id1_entities.csv", usecols=["entity_id", "end_status", "end_evidence"])
    m = seg.merge(id_seg.rename(columns={"entity_id": "id1_entity"}), on="segment_id", how="left")
    if m["id1_entity"].isna().any():
        raise ValueError("RET-1.1 segment absent from ID-1")
    pair = m[["entity_id", "id1_entity"]].drop_duplicates()
    if pair["entity_id"].duplicated().any() or pair["id1_entity"].duplicated().any():
        raise ValueError("ID-1 and RET-1.1 do not group segments into the same entities")
    e = pair.merge(id_ent.rename(columns={"entity_id": "id1_entity"}), on="id1_entity", how="left")
    if e["end_status"].isna().any():
        raise ValueError("entity without an ID-1 end status")
    e["in_pool"] = e["end_status"] == "ACTIVE_AT_CUTOFF"
    e["delist_class"] = np.where(e["end_evidence"].fillna("").str.contains("Voluntary"), "VOLUNTARY", "OTHER")
    return dict(zip(seg["segment_id"], seg["entity_id"])), e[["entity_id", "in_pool", "delist_class", "end_status"]]


def _universe_frame(univ, cal):
    return pd.concat([u.assign(t=t, key=k) for (k, t), u in univ.items() if t in set(cal["t"])],
                     ignore_index=True)[["t", "key", "entity", "rank"]].sort_values(["t", "key", "rank", "entity"])


def build(out=OUT):
    """Build (or, if the files exist, rebuild and compare byte for byte) the Stage 3 inputs."""
    verify_protocol()
    out.mkdir(parents=True, exist_ok=True)
    ret, ret_man = load_ret(RESEARCH_CUTOFF)
    sessions = pd.DatetimeIndex(sorted(ret["date"].unique()))
    cal = ladder.calendar(sessions)
    univ = load_univ()
    seg2ent, ident = identity(ret)
    pool = set(ident.loc[ident["in_pool"], "entity_id"])
    u = ladder.universes(univ, seg2ent, pool, cal)

    # structural checks against the frozen protocol - any failure stops the build
    assert sessions[-1] == T_STAR, "last session is not T*"
    assert len(cal) == 170 and cal["t"].iloc[0] == FIRST_T and cal["t"].iloc[-1] == LAST_T, "calendar != protocol §9"
    assert (cal["sample"] == "PRIMARY").sum() == 114 and (cal["sample"] == "OOS").sum() == 56, "sample sizes != B3"
    assert cal[["s_plus", "s_pp"]].notna().all().all(), "holding window without sessions"
    members = univ[univ["status"] == "MEMBER"].assign(entity=lambda d: d["segment_at_selection"].map(seg2ent))
    by = members.groupby("selection_date")["entity"].agg(set)
    assert set(u[("A", cal["t"].iloc[0])]["entity"]) == by[T_STAR] and len(by[T_STAR]) == TOP_N, "step A list != B1.2"
    for t in cal["t"]:
        assert set(u[("C", t)]["entity"]) == by[t] and len(by[t]) == TOP_N, f"step C != UNIV-1 MEMBER at {t.date()}"
        assert len(u[("B", t)]) == TOP_N, f"step B has fewer than {TOP_N} survivors at {t.date()}"

    ents = sorted(set().union(*(set(x["entity"]) for x in u.values())))
    panel = ladder.study_panel(ret[ret["entity_id"].isin(ents)]).sort_values(["entity", "date"]).reset_index(drop=True)
    ident = ident[ident["entity_id"].isin(ents)].sort_values("entity_id").reset_index(drop=True)
    w = ladder.wide(panel, ents, sessions)
    pos = {d: n for n, d in enumerate(w.days)}
    miss_exit = bad_hold = 0                                   # data-quality counts only (no returns)
    for c in cal.itertuples():
        j = w.ents.get_indexer(u[("C", c.t)]["entity"])
        miss_exit += int((~w.present[pos[c.s_pp], j]).sum())
        bad_hold += int(w.bad[pos[c.s_plus] + 1:pos[c.s_pp] + 1][:, j].sum())

    gaps = ladder.gap_rows(ret[ret["entity_id"].isin(ents)]).sort_values(["entity", "date"]).reset_index(drop=True)
    files = {"research/panel.parquet": panel, "research/sessions.csv": pd.DataFrame({"date": sessions}),
             "research/identity.csv": ident, "research/gap_rows.csv": gaps}
    for name in ("PRIMARY", "OOS"):
        c = cal[cal["sample"] == name]
        files[f"{name.lower()}/calendar.csv"] = c
        files[f"{name.lower()}/universes.csv"] = _universe_frame(u, c)
    hashes, identical = {}, True
    for rel, df in files.items():
        f = out / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(f.suffix + ".tmp")
        df.to_parquet(tmp, index=False) if rel.endswith(".parquet") else df.to_csv(tmp, index=False)
        hashes[rel] = _sha(tmp)
        if f.exists() and _sha(f) != hashes[rel]:
            identical = False
            tmp.unlink()
            raise ValueError(f"{rel}: rebuild differs from the stored file - not overwritten")
        tmp.replace(f)
    content = {
        "protocol_id": PROTOCOL_ID, "protocol_sha256": PROTOCOL_SHA256, "cutoff": RESEARCH_CUTOFF,
        "versions": {"returns": "RET-1.1", "universe": "UNIV-1", "identity": "ID-1"},
        "inputs_sha256": {"univ1": UNIV1_SHA256, "ret1_1_manifest": _sha(D2 / "returns" / "ret1_1_manifest.json"),
                          "ret1_1_datasets": ret_man["datasets"],
                          "id1_segments": _sha(D2 / "identity" / "id1_segments.csv"),
                          "id1_entities": _sha(D2 / "identity" / "id1_entities.csv")},
        "outputs_sha256": hashes,
        "samples": {n: {"months": int((cal["sample"] == n).sum()),
                        "first_t": str(cal.loc[cal["sample"] == n, "t"].min().date()),
                        "last_t": str(cal.loc[cal["sample"] == n, "t"].max().date()),
                        "protocol_exit_session": str(cal.loc[cal["sample"] == n, "s_pp"].max().date())}
                    for n in ("PRIMARY", "OOS")},
        "structural_counts": {"sessions": len(sessions), "entities_in_any_universe": len(ents),
                              "survivor_pool_entities_in_any_universe": int(ident["in_pool"].sum()),
                              "panel_rows": len(panel), "panel_rows_by_class": panel["cls"].value_counts().to_dict(),
                              "gap_rows": len(gaps), "gap_rows_without_event": int(gaps["no_event"].sum()),
                              "step_c_member_months_without_exit_price": miss_exit,
                              "step_c_non_research_grade_stock_days_in_holding": bad_hold},
        "code_sha256": {f: _sha(BASE_DIR / f) for f in ("src/stage3/ladder.py", "src/stage3/data.py",
                                                         "src/stage3/protocol.py")},
    }
    man = out / "manifest.json"
    if man.exists():                    # stored data may gain files; an existing file or input may never change
        old = json.loads(man.read_text())["content"]
        changed = [k for k, v in old["outputs_sha256"].items() if hashes.get(k) != v]
        changed += [k for k, v in old["inputs_sha256"].items() if json.loads(json.dumps(content))["inputs_sha256"].get(k) != v]
        if changed or old["protocol_sha256"] != PROTOCOL_SHA256:
            raise ValueError(f"stored Stage 3 data or inputs changed - not overwritten: {changed}")
    if not man.exists() or json.loads(man.read_text())["content"] != json.loads(json.dumps(content)):
        man.write_text(json.dumps({"content": content, "build": {"built_at": datetime.now().isoformat(timespec="seconds"),
                                                                   "environment": environment()}}, indent=1) + "\n")
    return content, identical


def load_inputs(sample, out=OUT):
    """Inputs of one sample ('PRIMARY' or 'OOS'). Every stored file is verified against the
    manifest. Holding months end at the protocol exit sessions (data_end). The matrices run to the
    research cutoff T* because frozen §22 decides 'trades again later' / 'never trades again' from
    all research data; nothing after T* can be read."""
    verify_protocol()
    man = json.loads((out / "manifest.json").read_text())["content"]
    for rel, want in man["outputs_sha256"].items():
        if _sha(out / rel) != want:
            raise ValueError(f"{rel} does not match the Stage 3 manifest")
    cal = pd.read_csv(out / sample.lower() / "calendar.csv", parse_dates=["t", "m12", "m1", "s_plus", "s_pp"])
    uf = pd.read_csv(out / sample.lower() / "universes.csv", parse_dates=["t"])
    ident = pd.read_csv(out / "research" / "identity.csv")
    sessions = pd.read_csv(out / "research" / "sessions.csv", parse_dates=["date"])["date"]
    data_end, cutoff = cal["s_pp"].max(), _cut(T_STAR)
    if data_end > cutoff:
        raise ValueError("a protocol exit session lies after the research cutoff - refused")
    panel = pd.read_parquet(out / "research" / "panel.parquet", filters=[("date", "<=", cutoff)])
    if panel["date"].max() > cutoff or sessions.max() > cutoff:
        raise ValueError("row after the research cutoff - refused")
    gaps = pd.read_csv(out / "research" / "gap_rows.csv", parse_dates=["date"])
    w = ladder.wide(panel, ident["entity_id"], sessions, gaps[gaps["date"] <= cutoff])
    kind = ident.set_index("entity_id")["delist_class"].reindex(w.ents)
    return SimpleNamespace(sample=sample, cal=cal, w=w, data_end=data_end, cutoff=cutoff, manifest=man,
                           univ={(k, t): g[["entity", "rank"]].reset_index(drop=True) for (k, t), g in uf.groupby(["key", "t"])},
                           delist_ret=kind.map(DELIST_RETURN).to_numpy())


def with_ret_status(events):
    """Add the RET-1.1 return_status of each audit event's row (the reason code)."""
    ret, _ = load_ret(T_STAR, ["entity_id", "date", "return_status"])
    return events.drop(columns="ret1_1_status").merge(
        ret.rename(columns={"entity_id": "entity", "return_status": "ret1_1_status"}), on=["entity", "date"], how="left")


def verify_provenance(out=OUT):
    """Stage 2 inputs and Stage 3 code still match the hashes recorded when the inputs were built."""
    man = json.loads((out / "manifest.json").read_text())["content"]
    now = {"univ1": _sha(D2 / "universe" / "univ1_pit_universe.parquet"),
           "ret1_1_manifest": _sha(D2 / "returns" / "ret1_1_manifest.json"),
           "id1_segments": _sha(D2 / "identity" / "id1_segments.csv"),
           "id1_entities": _sha(D2 / "identity" / "id1_entities.csv")}
    bad = [k for k, v in now.items() if man["inputs_sha256"][k] != v]
    bad += [f for f, v in man["code_sha256"].items() if _sha(BASE_DIR / f) != v]
    bad += [] if man["protocol_sha256"] == PROTOCOL_SHA256 and man["inputs_sha256"]["univ1"] == UNIV1_SHA256 else ["protocol/univ1"]
    return bad
