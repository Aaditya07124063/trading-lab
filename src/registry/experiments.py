"""Experiment registry (append-only) + trial log.

registry/experiments.jsonl - one JSON record per experiment, never edited.
  Status changes are appended as {"amends": <id>, ...} records; the current
  view folds them in order. Every field in REQUIRED must be present - use an
  explicit "n/a"/"unknown" rather than omitting.
registry/trials.jsonl - EVERY backtest run (CLI or web), however casual, so
  the true number of tests is known for multiple-testing accounting.
"""

import json
import os
import platform
import subprocess
from datetime import datetime
from importlib import metadata

from src.config import BASE_DIR

EXPERIMENTS = BASE_DIR / "registry" / "experiments.jsonl"
TRIALS = BASE_DIR / "registry" / "trials.jsonl"
REGISTRY_MD = BASE_DIR / "EXPERIMENT_REGISTRY.md"

REQUIRED = [
    "research_question", "hypothesis", "null_hypothesis", "strategy", "instrument", "universe",
    "timeframe", "start", "end", "dataset_id", "dataset_sha256", "dataset_stage", "feature_set",
    "parameters", "training_period", "validation_period", "test_period", "oos_status",
    "cost_model", "slippage", "benchmark", "cash_treatment", "dividends", "random_seed",
    "results", "statistical_tests", "limitations", "viewed_before_finalization", "status",
]
STATUSES = {
    "PLANNED", "EXPLORATORY", "DIAGNOSTIC", "REPRODUCED", "FINAL",
    "REQUIRES REVALIDATION", "REQUIRES REBUILD — TARGET/EXECUTION ALIGNMENT ISSUE",
    "REQUIRES REBUILD — SURVIVORSHIP BIAS", "SUPERSEDED", "INVALID",
}


def environment():
    def git(*a):
        try:
            return subprocess.check_output(["git", *a], cwd=BASE_DIR, text=True,
                                           stderr=subprocess.DEVNULL).strip()
        except Exception:
            return "unknown"
    pkgs = {}
    for p in ("pandas", "numpy", "scikit-learn", "yfinance", "fastapi"):
        try:
            pkgs[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            pkgs[p] = "not installed"
    return {"git_commit": git("rev-parse", "HEAD"),
            "git_dirty": bool(git("status", "--porcelain", "--", "src", "*.py")),
            "python": platform.python_version(), "packages": pkgs}


def _read(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _next_id(prefix):
    today = datetime.now().strftime("%Y%m%d")
    n = sum(1 for r in _read(EXPERIMENTS) if r.get("experiment_id", "").startswith(f"{prefix}-{today}"))
    return f"{prefix}-{today}-{n + 1:03d}"


def record(entry, prefix="EXP", env=None):
    missing = [k for k in REQUIRED if k not in entry]
    if missing:
        raise ValueError(f"experiment record missing fields: {missing}")
    if entry["status"] not in STATUSES:
        raise ValueError(f"unknown status {entry['status']!r}")
    rec = {"experiment_id": entry.get("experiment_id") or _next_id(prefix),
           "executed_at": entry.get("executed_at") or datetime.now().isoformat(timespec="seconds"),
           **{k: v for k, v in entry.items() if k not in ("experiment_id", "executed_at")},
           "environment": env or entry.get("environment") or environment()}
    if any(r.get("experiment_id") == rec["experiment_id"] for r in _read(EXPERIMENTS)):
        raise ValueError(f"{rec['experiment_id']} already registered - append an amendment instead")
    EXPERIMENTS.parent.mkdir(exist_ok=True)
    with open(EXPERIMENTS, "a") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return rec


def amend(experiment_id, reason, **changes):
    if "status" in changes and changes["status"] not in STATUSES:
        raise ValueError(f"unknown status {changes['status']!r}")
    if not any(r.get("experiment_id") == experiment_id for r in _read(EXPERIMENTS)):
        raise KeyError(experiment_id)
    rec = {"amends": experiment_id, "amended_at": datetime.now().isoformat(timespec="seconds"),
           "reason": reason, **changes}
    with open(EXPERIMENTS, "a") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return rec


def current():
    """Experiments with amendments folded in; keeps an amendment history."""
    out = {}
    for r in _read(EXPERIMENTS):
        if "amends" in r:
            e = out[r["amends"]]
            e.setdefault("history", []).append({k: r[k] for k in ("amended_at", "reason")} |
                                               {k: e.get(k) for k in r if k not in ("amends", "amended_at", "reason")})
            e.update({k: v for k, v in r.items() if k not in ("amends", "amended_at", "reason")})
        else:
            out[r["experiment_id"]] = dict(r)
    return out


def log_trial(kind, params, dataset, headline, source):
    """Record every run. Disabled under tests via TRADING_LAB_NO_TRIAL_LOG."""
    if os.environ.get("TRADING_LAB_NO_TRIAL_LOG"):
        return None
    rec = {"at": datetime.now().isoformat(timespec="seconds"), "kind": kind, "source": source,
           "params": params, "dataset": dataset, "headline": headline}
    TRIALS.parent.mkdir(exist_ok=True)
    with open(TRIALS, "a") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return rec


def trial_count(kind=None):
    return sum(1 for t in _read(TRIALS) if kind is None or t["kind"] == kind)


def write_md():
    exps = current()
    lines = ["# Experiment registry", "",
             "_Generated from `registry/experiments.jsonl` (append-only) by "
             "`python3 -m src.registry.experiments` - do not edit by hand._", "",
             f"Registered experiments: {len(exps)} · logged trials (every run, incl. casual): "
             f"{trial_count()} (trials log started 2026-09-30; earlier casual runs were not logged).", "",
             "| ID | status | strategy | data | period | OOS status | viewed before final | headline |",
             "|---|---|---|---|---|---|---|---|"]
    for e in exps.values():
        r = e["results"]
        head = r.get("headline", "") if isinstance(r, dict) else str(r)
        lines.append(f"| {e['experiment_id']} | **{e['status']}** | {e['strategy']} | `{e['dataset_id']}` "
                     f"| {e['start']} → {e['end']} | {e['oos_status']} | {e['viewed_before_finalization']} | {head} |")
    lines += ["", "## Details", ""]
    for e in exps.values():
        lines.append(f"### {e['experiment_id']} — {e['strategy']}")
        lines.append("")
        for k in ("research_question", "hypothesis", "null_hypothesis", "dataset_stage", "parameters",
                  "cost_model", "slippage", "benchmark", "cash_treatment", "dividends",
                  "statistical_tests", "limitations"):
            lines.append(f"- **{k}:** {e[k]}")
        env = e.get("environment", {})
        lines.append(f"- **code:** `{env.get('git_commit', 'unknown')[:10]}`"
                     f"{' (dirty)' if env.get('git_dirty') else ''} · python {env.get('python', '?')}")
        for h in e.get("history", []):
            lines.append(f"- **amended {h['amended_at']}:** {h['reason']}")
        lines.append("")
    REGISTRY_MD.write_text("\n".join(lines))


if __name__ == "__main__":
    write_md()
    print(f"{len(current())} experiments -> {REGISTRY_MD.name}")
