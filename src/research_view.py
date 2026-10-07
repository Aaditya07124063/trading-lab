"""Read-only view of the registered research for the web UI (GET /api/research).

A presentation layer: it reads the registries and the saved result JSON files and re-hashes the
registered artifacts. It computes no return, cost or statistic, runs no experiment and writes nothing.
"""

import hashlib
import json

from src.access import RESEARCH_CUTOFF
from src.config import BASE_DIR, HOLDOUT_START
from src.registry import experiments

S2, S2_DIR, STEP_E_DIR = "S2-MOM-v1", "results/s2_mom_v1", "results/s2_mom_v1_step_e"
ORB_PROTOCOL = "docs/protocols/ORB_v1.md"
EXP_FIELDS = ("experiment_id", "status", "strategy", "research_question", "hypothesis", "universe", "instrument", "timeframe",
              "start", "end", "dataset_id", "dataset_stage", "cost_model", "benchmark", "oos_status", "test_period",
              "limitations", "viewed_before_finalization", "executed_at", "protocol_id", "protocol_version",
              "protocol_file", "frozen_on")
ORB_DEV_FIELDS = ("purpose", "holdout_start", "window", "sessions", "universe_n", "primary_scenario", "trades",
                  "primary_inference_bps", "reporting_label_on_dev_sample", "gross_mean_bps", "benchmark_A_mean_net_bps")


def _sha(rel):
    p = BASE_DIR / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def _json(rel):
    p = BASE_DIR / rel
    return json.loads(p.read_text()) if p.is_file() else None


def _verify(folder, files):
    """Do the saved files still match their registered SHA-256?"""
    bad = [f for f, sha in (files or {}).items() if _sha(f"{folder}/{f}") != sha]
    return {"registered": bool(files), "files": len(files or {}), "verified": bool(files) and not bad, "mismatch": bad}


def _headline(e):
    r = e.get("results")
    return r.get("headline", "") if isinstance(r, dict) else str(r or "")


def _ladder(res):
    return {step: {p: {k: v.get(k) for k in ("n", "mean_pct", "t_nw", "p_two_sided")}
                   for p, v in row.items() if isinstance(v, dict) and "mean_pct" in v}
            for step, row in (res or {}).get("ladder", {}).items()}


def _s2(e):
    prov = e.get("provenance") or {}
    primary, conf = _json(f"{S2_DIR}/primary_results.json"), _json(f"{S2_DIR}/confirmation_results.json")
    sens, step_e = _json(f"{S2_DIR}/sensitivity_results.json"), _json(f"{STEP_E_DIR}/step_e_results.json")
    run = lambda k: prov.get(k) or {}
    runs = {"blinded": _verify(S2_DIR, {"blinded_precision.json": prov.get("blinded_precision_artifact_sha256")}
                               if prov.get("blinded_precision_artifact_sha256") else {}),
            "primary": _verify(S2_DIR, run("primary_run").get("files_sha256")),
            "sensitivity": _verify(S2_DIR, {"sensitivity_results.json": run("sensitivity_run").get("results_sha256")}
                                   if run("sensitivity_run") else {}),
            "confirmation": _verify(S2_DIR, run("confirmation_run").get("files_sha256")),
            "step_e": _verify(STEP_E_DIR, run("step_e_run").get("files_sha256"))}
    docs = [{"id": "Frozen protocol", "file": e.get("protocol_file"), "sha256": e.get("protocol_sha256")},
            *({"id": a["id"], "file": a["file"], "sha256": a["sha256"]} for a in e.get("addenda", []))]
    for d in docs:
        d["verified"] = _sha(d["file"]) == d["sha256"]
    block = lambda res: res and {"H1": res.get("H1"), "ladder": _ladder(res), "reliability": res.get("reliability")}
    return {"registry_status": e.get("status"), "registry_oos_status": e.get("oos_status"),
            "research_question": e.get("research_question"), "primary_estimand": e.get("primary_estimand"),
            "hypothesis": e.get("hypothesis"), "protocol_version": e.get("protocol_version"), "frozen_on": e.get("frozen_on"),
            "freeze_commit": e.get("freeze_commit"), "primary_sample": e.get("primary_sample"), "oos_sample": e.get("oos_sample"),
            "universe": e.get("universe"), "documents": docs, "runs": runs,
            "code_sha256": run("primary_run").get("code_sha256"), "step_e_code_sha256": run("step_e_run").get("code_sha256"),
            "primary": block(primary), "confirmation": block(conf),
            "sensitivity_reliability": (sens or {}).get("reliability"),
            "step_e": step_e and {"statement": step_e.get("statement"), "samples": step_e.get("samples")}}


def _orb(cur):
    p = BASE_DIR / ORB_PROTOCOL
    text = p.read_text() if p.is_file() else ""
    status = next((ln.split("**Status:**")[1].strip() for ln in text.splitlines() if "**Status:**" in ln), "unknown")
    recs = [e for k, e in cur.items() if k.startswith("ORBV1")]
    dev = _json("results/orb_v1_dev/summary.json") or {}
    return {"protocol_file": ORB_PROTOCOL, "protocol_status": status, "protocol_sha256": _sha(ORB_PROTOCOL), "protocol_text": text,
            "holdout_start": HOLDOUT_START, "final_evaluation_registered": any(e.get("status") == "FINAL" for e in recs),
            "records": [{**{k: e.get(k) for k in EXP_FIELDS}, "headline": _headline(e)} for e in recs],
            "dev_sample": {k: dev.get(k) for k in ORB_DEV_FIELDS}}


def snapshot():
    cur = experiments.current()
    data = _json("registry/datasets.json") or []
    return {"research_cutoff": RESEARCH_CUTOFF, "holdout_start": HOLDOUT_START, "logged_trials": experiments.trial_count(),
            "experiments": [{**{k: e.get(k) for k in EXP_FIELDS}, "headline": _headline(e), "amendments": len(e.get("history", []))}
                            for e in cur.values()],
            "s2_mom": _s2(cur[S2]) if S2 in cur else None,
            "orb": _orb(cur),
            "datasets": [{k: d.get(k) for k in ("dataset_id", "file", "frequency", "instrument", "rows", "start", "end",
                                                "provider", "validation_status")} for d in data]}
