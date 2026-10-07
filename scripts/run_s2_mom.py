"""S2-MOM-v1 experiment runner (Phase 3B). Fail-closed; enforces the protocol's execution order (B3).

    python3 scripts/run_s2_mom.py checks         # real-data pre-run checks (B2, §25): pass/fail only
    (then: Stage 2 rebuild 150/150, registered in the registry record under provenance.stage2_rebuild)
    python3 scripts/run_s2_mom.py blinded        # §15 blinded precision step (dispersion only)
    python3 scripts/run_s2_mom.py primary        # PRIMARY ONLY: A-D, delta, Newey-West, bootstrap, monthly series,
                                                 # holdings, audit events. No sensitivity, no reverse ladder, no costs.
    python3 scripts/run_s2_mom.py sensitivity    # the six frozen sensitivity variants + the reverse-order ladder, on
                                                 # the primary sample; needs the registered primary run, same code
    python3 scripts/run_s2_mom.py confirmation   # chronological OOS; needs the registered primary run, same code

Refuses to start unless: the protocol file and the registry record carry the frozen SHA-256; every
reviewed decision is recorded; inputs and code match the Stage 3 manifest. Each mode runs once.
Results go to files only - nothing is printed.

Costs: the primary estimand delta = WML_A - WML_D is gross. No mode here runs a cost calculation:
step E and H4 are written as COST-EVIDENCE-PENDING; no cost is ever set to zero.
"""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import BASE_DIR                                              # noqa: E402
from src.registry import experiments                                         # noqa: E402
from src.stage3 import costs, data, experiment                               # noqa: E402
from src.stage3.protocol import PROTOCOL_ID, NotReady, require_ready, verify_protocol   # noqa: E402

OUT = BASE_DIR / "results" / "s2_mom_v1"
CHECKS = BASE_DIR / "data" / "stage3" / "s2_mom_v1" / "checks"
CODE = ("src/stage3/protocol.py", "src/stage3/ladder.py", "src/stage3/data.py", "src/stage3/stats.py",
        "src/stage3/costs.py", "src/stage3/experiment.py", "scripts/run_s2_mom.py")


def code_sha():
    return hashlib.sha256(b"".join((BASE_DIR / f).read_bytes() for f in CODE)).hexdigest()


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / name
    if f.exists():
        raise NotReady(f"{f.relative_to(BASE_DIR)} already exists - each mode runs once")
    f.write_text(json.dumps(obj, indent=1, default=str) + "\n")
    return hashlib.sha256(f.read_bytes()).hexdigest()


def _amend(rec, reason, **prov):
    experiments.amend(PROTOCOL_ID, reason, provenance={**rec["provenance"], **prov})


def _passed(sample):
    f = CHECKS / f"pre_run_checks_{sample.lower()}.json"
    return f.exists() and json.loads(f.read_text()).get("all_passed") is True \
        and json.loads(f.read_text()).get("code_sha256") == code_sha()


def main(mode):
    rec = verify_protocol()
    require_ready(rec)      # costs are NOT a gate: the primary estimand is gross; step E reports itself as pending
    stale = data.verify_provenance()
    if stale:
        raise NotReady(f"inputs or code differ from the Stage 3 manifest (rebuild first): {stale}")
    prov = rec["provenance"]
    if mode == "checks":
        CHECKS.mkdir(parents=True, exist_ok=True)
        for sample in ("PRIMARY", "OOS"):
            res = experiment.pre_run_checks(data.load_inputs(sample))
            res["code_sha256"] = code_sha()
            (CHECKS / f"pre_run_checks_{sample.lower()}.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    elif not (prov.get("stage2_rebuild") or {}).get("checks_passed") == 150:
        raise NotReady("the Stage 2 rebuild (150 of 150 checks, protocol §4 and §25) is not registered as passed")
    elif mode == "blinded":
        if not _passed("PRIMARY"):
            raise NotReady("pre-run checks for the primary sample have not passed with this code")
        res = experiment.blinded(data.load_inputs("PRIMARY"))
        _amend(rec, "blinded precision step generated",
               blinded_precision_artifact_sha256=_write("blinded_precision.json", res), blinded_code_sha256=code_sha())
    elif mode in ("primary", "confirmation"):
        sample = "PRIMARY" if mode == "primary" else "OOS"
        if not _passed(sample):
            raise NotReady(f"pre-run checks for the {sample} sample have not passed with this code")
        f = OUT / "blinded_precision.json"
        if not prov.get("blinded_precision_artifact_sha256") or not f.exists() \
                or _sha(f) != prov["blinded_precision_artifact_sha256"]:
            raise NotReady("the blinded precision artifact is not registered or does not match")
        if mode == "confirmation" and (prov.get("primary_run") or {}).get("code_sha256") != code_sha():
            raise NotReady("no registered primary run with this exact code - confirmation refused")
        res = experiment.analyse(data.load_inputs(sample), costs.load_schedule())
        frames = {k: res.pop(k) for k in ("monthly", "delta", "events", "holdings")}
        frames["events"] = data.with_ret_status(frames["events"])
        sha = _write(f"{mode}_results.json", res)
        files = {f"{mode}_results.json": sha}
        for name, df in frames.items():
            df.to_csv(OUT / f"{mode}_{name}.csv", index=False)       # holdings: turnover, cost, capacity need no second run
            files[f"{mode}_{name}.csv"] = _sha(OUT / f"{mode}_{name}.csv")
        experiments.log_trial("s2_mom_v1", {"mode": mode}, sample, {"results_sha256": sha}, "scripts/run_s2_mom.py")
        _amend(rec, f"{mode} run registered",
               **{("primary_run" if mode == "primary" else "confirmation_run"): {"results_sha256": sha, "code_sha256": code_sha(),
                                                                                  "files_sha256": files}})
    elif mode == "sensitivity":
        run = prov.get("primary_run") or {}
        if run.get("code_sha256") != code_sha():
            raise NotReady("no registered primary run with this exact code - sensitivity refused")
        if any(not (OUT / f).exists() or _sha(OUT / f) != h for f, h in run["files_sha256"].items()):
            raise NotReady("the registered primary result files are missing or changed - sensitivity refused")
        primary = json.loads((OUT / "primary_results.json").read_text())
        inp = data.load_inputs("PRIMARY")
        monthly, _ = experiment.run(inp)        # recomputed, then required to be byte-identical to the registered series
        if hashlib.sha256(monthly.to_csv(index=False).encode()).hexdigest() != run["files_sha256"]["primary_monthly.csv"]:
            raise NotReady("the recomputed primary monthly series differs from the registered file - sensitivity refused")
        res = experiment.sensitivity_analysis(inp, monthly, primary["H1"], costs.load_schedule())
        sha = _write("sensitivity_results.json", res)
        if any(_sha(OUT / f) != h for f, h in run["files_sha256"].items()):
            raise NotReady("a primary result file changed during the sensitivity run - stop and report")
        experiments.log_trial("s2_mom_v1", {"mode": mode, "variants": list(experiment.SENSITIVITY) + list(experiment.ladder.REVERSE_SPECS)},
                              "PRIMARY", {"results_sha256": sha}, "scripts/run_s2_mom.py")
        _amend(rec, "sensitivity run registered", sensitivity_run={"results_sha256": sha, "code_sha256": code_sha()})
    else:
        raise SystemExit(__doc__)
    print(f"{mode}: done")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
