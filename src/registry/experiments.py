"""Experiment registry (append-only, hash-chained, state machine) + trial log.

registry/experiments.jsonl - one JSON record per experiment, never edited. Changes are appended as
  {"amends": <id>, ...} records; the current view folds them in order. Every field in REQUIRED must
  be present on a new record - use an explicit "n/a"/"unknown" rather than omitting.
registry/trials.jsonl - EVERY backtest run (CLI or web), however casual, so the true number of tests
  is known for multiple-testing accounting.

The registry is the root of trust for "what was registered", so every read validates the whole file
and FAILS CLOSED (RegistryError): unreadable or truncated line, duplicate experiment id, duplicate
record, orphan amendment, broken hash chain, illegal state transition, protected-field replacement.

  history   The first GENESIS_LINES lines (written before the state machine existed, 2026-09-30 to
            2026-10-07) are grandfathered: they are pinned by GENESIS_SHA256 and can never change.
  chain     Every later line carries chain_prev_sha256 = SHA-256 of all bytes before it.
  states    TRANSITIONS below. FINAL may only become SUPERSEDED, INVALID or REQUIRES REVALIDATION.
  protected In a frozen state only `status` may change and `anchors` may gain keys. In every state
            identity fields and recorded hashes (any "...sha256" leaf) are immutable. The only way
            to replace them is an explicit revalidation: REQUIRES REVALIDATION + _revalidation=True.
"""

import fcntl
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path

from src.config import BASE_DIR

EXPERIMENTS = BASE_DIR / "registry" / "experiments.jsonl"
TRIALS = BASE_DIR / "registry" / "trials.jsonl"
REGISTRY_MD = BASE_DIR / "EXPERIMENT_REGISTRY.md"
_CANONICAL = EXPERIMENTS
GENESIS_LINES = 58
GENESIS_SHA256 = "8fae608a52cc41312525ce9cf25da467b2cacb033b8350c064f1244652dd5f9d"

REQUIRED = [
    "research_question", "hypothesis", "null_hypothesis", "strategy", "instrument", "universe",
    "timeframe", "start", "end", "dataset_id", "dataset_sha256", "dataset_stage", "feature_set",
    "parameters", "training_period", "validation_period", "test_period", "oos_status",
    "cost_model", "slippage", "benchmark", "cash_treatment", "dividends", "random_seed",
    "results", "statistical_tests", "limitations", "viewed_before_finalization", "status",
]
LEGACY_STATUSES = {"EXPLORATORY", "DIAGNOSTIC", "REPRODUCED", "REQUIRES REBUILD — TARGET/EXECUTION ALIGNMENT ISSUE",
                   "REQUIRES REBUILD — SURVIVORSHIP BIAS"}
_END = {"SUPERSEDED", "INVALID", "REQUIRES REVALIDATION"}
TRANSITIONS = {
    "PLANNED": {"READY", "INVALID", "SUPERSEDED"},
    "READY": {"EXECUTING", "INVALID", "SUPERSEDED"},
    "EXECUTING": {"REGISTERED", "INVALID"},
    "REGISTERED": {"FINAL"} | _END,
    "FINAL": set(_END),
    "REQUIRES REVALIDATION": {"FINAL", "SUPERSEDED", "INVALID"},      # -> FINAL only with _revalidation=True
    "SUPERSEDED": set(), "INVALID": set(),
    **{s: set(_END) for s in LEGACY_STATUSES},
}
STATUSES = set(TRANSITIONS)
INITIAL_STATUSES = {"PLANNED", "FINAL"} | LEGACY_STATUSES          # READY/EXECUTING/REGISTERED only by transition
MUTABLE_STATES = {"PLANNED", "READY", "EXECUTING", "REGISTERED", "REQUIRES REVALIDATION"}
IDENTITY = {"experiment_id", "executed_at", "protocol_id", "protocol_version", "protocol_file", "protocol_sha256",
            "freeze_commit", "environment"}
ADDITIVE = {"anchors"}                  # the only field a frozen record may still gain keys in
META = ("amends", "amended_at", "reason", "actor", "previous_state", "new_state", "changed_fields", "previous_hashes",
        "new_hashes", "revalidation_required", "chain_prev_sha256")


class RegistryError(ValueError):
    """The registry file is not a valid, untampered history, or a write would make it one. Fail closed."""


def environment():
    def git(*a):
        try:
            return subprocess.check_output(["git", *a], cwd=BASE_DIR, text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    pkgs = {}
    for p in ("pandas", "numpy", "scipy", "pyarrow", "scikit-learn", "yfinance", "fastapi"):
        try:
            pkgs[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            pkgs[p] = "not installed"
    head, dirty = git("rev-parse", "HEAD"), git("status", "--porcelain", "--", "src", "*.py")
    return {"git_commit": head or "git unavailable", "git_dirty": bool(dirty) if dirty is not None else "git unavailable",
            "python": platform.python_version(), "platform": platform.platform(), "machine": platform.machine(),
            "packages": pkgs}


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _tool():
    return os.path.basename(sys.argv[0] or "") or "interactive"


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def _leaves(obj, path=()):
    """Every (path, value) leaf of nested dicts/lists."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _leaves(v, path + (k,))
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from _leaves(v, path + (n,))
    else:
        yield path, obj


def _at(obj, path):
    for k in path:
        try:
            obj = obj[k]
        except (KeyError, IndexError, TypeError):
            return _MISSING
    return obj


_MISSING = object()


def _no_duplicate_keys(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise RegistryError(f"duplicate key in a registry line: {sorted(k for k in keys if keys.count(k) > 1)}")
    return dict(pairs)


def _changes(rec):
    return {k: v for k, v in rec.items() if k not in META}


def _check_amendment(exp, rec):
    """Raise unless `rec` is a legal amendment of the folded experiment `exp`. Used on write AND on read."""
    eid, changes = rec.get("amends"), _changes(rec)
    missing = [k for k in META if k not in rec]
    if missing:
        raise RegistryError(f"amendment of {eid} lacks {missing}")
    if not isinstance(rec["reason"], str) or not rec["reason"].strip():
        raise RegistryError(f"amendment of {eid} has an empty reason")
    if not isinstance(rec["actor"], str) or not rec["actor"].strip():
        raise RegistryError(f"amendment of {eid} has no actor")
    prev, new, reval = exp["status"], changes.get("status", exp["status"]), rec["revalidation_required"]
    if rec["previous_state"] != prev or rec["new_state"] != new:
        raise RegistryError(f"amendment of {eid} misstates the state: recorded {rec['previous_state']!r} -> "
                            f"{rec['new_state']!r}, actual {prev!r} -> {new!r}")
    if new not in STATUSES:
        raise RegistryError(f"unknown status {new!r}")
    if new != prev and new not in TRANSITIONS[prev]:
        raise RegistryError(f"illegal transition {prev} -> {new} for {eid} (allowed: {sorted(TRANSITIONS[prev]) or 'none'})")
    if type(reval) is not bool:
        raise RegistryError("revalidation_required must be true or false")
    protected_ok = reval and prev == "REQUIRES REVALIDATION"
    if (prev, new) == ("REQUIRES REVALIDATION", "FINAL") and not reval:
        raise RegistryError(f"{eid}: REQUIRES REVALIDATION -> FINAL needs an explicit revalidation")
    if new == "REQUIRES REVALIDATION" and new != prev and not reval:
        raise RegistryError(f"{eid}: a move to REQUIRES REVALIDATION must record revalidation_required = true")
    if reval and not (protected_ok or new == "REQUIRES REVALIDATION"):
        raise RegistryError(f"{eid}: revalidation is only possible in state REQUIRES REVALIDATION (now {prev})")
    for k, v in changes.items():
        old = exp.get(k, _MISSING)
        if k == "status" or k == "history":
            if k == "history":
                raise RegistryError("'history' is derived and cannot be amended")
            continue
        if k in ADDITIVE:
            if not isinstance(v, dict) or any(_at(v, p) != x for p, x in _leaves({} if old is _MISSING else old)):
                raise RegistryError(f"{eid}: {k} may only gain keys - an existing entry was changed or removed")
            continue
        if prev not in MUTABLE_STATES:
            raise RegistryError(f"{eid} is {prev}: protected field {k!r} is immutable "
                                f"(only status and new anchors may be appended)")
        if protected_ok or old is _MISSING:
            continue
        if k in IDENTITY and old != v:
            raise RegistryError(f"{eid}: {k} cannot be replaced without explicit revalidation")
        for path, x in _leaves(old):
            if x is not None and any("sha256" in str(p) for p in (k, *path)) and _at(v, path) != x:
                raise RegistryError(f"{eid}: recorded hash {k}{list(path)} cannot be replaced or removed without "
                                    f"explicit revalidation")
    if rec["changed_fields"] != sorted(changes):
        raise RegistryError(f"amendment of {eid}: changed_fields does not list the changed fields")
    if rec["previous_hashes"] != {k: (_sha(exp[k]) if k in exp else None) for k in sorted(changes)} \
            or rec["new_hashes"] != {k: _sha(v) for k, v in sorted(changes.items())}:
        raise RegistryError(f"amendment of {eid}: previous/new hashes do not match the fields")


def _check_record(rec):
    missing = [k for k in REQUIRED if k not in rec]
    if missing:
        raise RegistryError(f"experiment record missing fields: {missing}")
    if rec["status"] not in STATUSES:
        raise RegistryError(f"unknown status {rec['status']!r}")
    if rec["status"] not in INITIAL_STATUSES:
        raise RegistryError(f"a new experiment cannot start in state {rec['status']!r}")
    if not rec.get("experiment_id") or not isinstance(rec["experiment_id"], str):
        raise RegistryError("experiment record without an experiment_id")


def _fold(exp, rec):
    changes = _changes(rec)
    exp.setdefault("history", []).append({k: rec[k] for k in ("amended_at", "reason", "actor") if k in rec} |
                                         {k: exp.get(k) for k in changes})
    exp.update(changes)


def _parse(raw, genesis):
    """bytes of a registry file -> ({id: folded experiment}, sha256 of the file). Validates everything."""
    n0, sha0 = genesis
    if raw and not raw.endswith(b"\n"):
        raise RegistryError("registry ends in a truncated line (interrupted write?) - refusing to read it")
    lines = raw.split(b"\n")[:-1]
    if n0 and (len(lines) < n0 or hashlib.sha256(b"".join(x + b"\n" for x in lines[:n0])).hexdigest() != sha0):
        raise RegistryError(f"the first {n0} registry lines (registered history) are missing or were rewritten")
    out, seen, h = {}, set(), hashlib.sha256()
    for n, line in enumerate(lines):
        before = h.hexdigest()
        h.update(line + b"\n")
        try:
            rec = json.loads(line, object_pairs_hook=_no_duplicate_keys)
        except ValueError as e:
            raise RegistryError(f"registry line {n + 1} is unreadable: {e}") from None
        if not isinstance(rec, dict):
            raise RegistryError(f"registry line {n + 1} is not a record")
        if line in seen:
            raise RegistryError(f"registry line {n + 1} duplicates an earlier record")
        seen.add(line)
        if n >= n0 and rec.get("chain_prev_sha256") != before:
            raise RegistryError(f"hash chain broken at registry line {n + 1} (a line was edited, inserted or removed)")
        if "amends" in rec:
            if "experiment_id" in rec:
                raise RegistryError(f"registry line {n + 1} is both a record and an amendment")
            if rec["amends"] not in out:
                raise RegistryError(f"registry line {n + 1} amends unknown experiment {rec['amends']!r}")
            if n >= n0:
                _check_amendment(out[rec["amends"]], rec)
            _fold(out[rec["amends"]], rec)
        else:
            if rec.get("experiment_id") in out:
                raise RegistryError(f"duplicate experiment id {rec['experiment_id']!r} at registry line {n + 1}")
            if n >= n0:
                _check_record(rec)
            elif "experiment_id" not in rec:
                raise RegistryError(f"registry line {n + 1} has no experiment_id")
            out[rec["experiment_id"]] = dict(rec)
    return out, h.hexdigest()


def _genesis(path):
    return (GENESIS_LINES, GENESIS_SHA256) if Path(path) == _CANONICAL else (0, None)


def load(path=None, genesis=None):
    """Validated current view of a registry file. `genesis` = (lines, sha256) of a grandfathered prefix."""
    path = Path(path or EXPERIMENTS)
    genesis = genesis or _genesis(path)
    if not path.exists():
        if genesis[0]:
            raise RegistryError(f"{path.name} is missing")
        return {}
    return _parse(path.read_bytes(), genesis)[0]


def current():
    """Experiments with amendments folded in; keeps an amendment history. Raises RegistryError if invalid."""
    return load()


def head_sha256(path=None):
    """SHA-256 of the validated registry file (the value a release pins)."""
    path = Path(path or EXPERIMENTS)
    return _parse(path.read_bytes(), _genesis(path))[1]


def _append(path, build):
    """Lock, validate the whole file, build the new line from the validated state, append, fsync."""
    path.parent.mkdir(exist_ok=True)
    with open(path, "a+b") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0)
        state, head = _parse(fh.read(), _genesis(path))
        rec = build(state)
        rec["chain_prev_sha256"] = head
        line = json.dumps(rec, default=str)
        rec = json.loads(line)
        (_check_amendment(state[rec["amends"]], rec) if "amends" in rec else _check_record(rec))
        fh.write(line.encode() + b"\n")
        fh.flush()
        os.fsync(fh.fileno())
    return rec


def _next_id(prefix, state):
    today = datetime.now().strftime("%Y%m%d")
    return f"{prefix}-{today}-{sum(1 for k in state if k.startswith(f'{prefix}-{today}')) + 1:03d}"


def record(entry, prefix="EXP", env=None):
    def build(state):
        rec = {"experiment_id": entry.get("experiment_id") or _next_id(prefix, state),
               "executed_at": entry.get("executed_at") or _now(),
               **{k: v for k, v in entry.items() if k not in ("experiment_id", "executed_at")},
               "environment": env or entry.get("environment") or environment()}
        if rec["experiment_id"] in state:
            raise RegistryError(f"{rec['experiment_id']} already registered - append an amendment instead")
        return rec
    return _append(EXPERIMENTS, build)


def amend(experiment_id, reason, _actor=None, _revalidation=False, **changes):
    """Append an amendment. Refused unless the state machine and the protection rules allow it."""
    bad = [k for k in changes if k in META or k == "experiment_id"]
    if bad:
        raise RegistryError(f"reserved field(s) cannot be amended: {bad}")

    def build(state):
        if experiment_id not in state:
            raise KeyError(experiment_id)
        exp, new = state[experiment_id], json.loads(json.dumps(changes, default=str))
        return {"amends": experiment_id, "amended_at": _now(), "reason": reason, "actor": _actor or _tool(),
                "previous_state": exp["status"], "new_state": new.get("status", exp["status"]),
                "changed_fields": sorted(new), "previous_hashes": {k: (_sha(exp[k]) if k in exp else None) for k in sorted(new)},
                "new_hashes": {k: _sha(v) for k, v in sorted(new.items())},
                "revalidation_required": bool(_revalidation) or (new.get("status") == "REQUIRES REVALIDATION"
                                                                 and exp["status"] != "REQUIRES REVALIDATION"),
                **new}
    return _append(EXPERIMENTS, build)


def anchor(experiment_id, reason, _actor=None, **entries):
    """Add new keys to `anchors` (hashes that tie other artifacts to the registry). Existing anchors never change."""
    old = current()[experiment_id].get("anchors") or {}
    clash = sorted(set(old) & set(entries))
    if clash:
        raise RegistryError(f"{experiment_id}: anchor(s) already recorded and immutable: {clash}")
    return amend(experiment_id, reason, _actor=_actor, anchors={**old, **entries})


def _read_jsonl(path):
    if not path.exists():
        return []
    raw = path.read_text()
    if raw and not raw.endswith("\n"):
        raise RegistryError(f"{path.name} ends in a truncated line")
    try:
        return [json.loads(line) for line in raw.splitlines()]
    except ValueError as e:
        raise RegistryError(f"{path.name} has an unreadable line: {e}") from None


def log_trial(kind, params, dataset, headline, source):
    """Record every run. TRADING_LAB_NO_TRIAL_LOG suppresses logging ONLY inside pytest; anywhere else
    the variable is an error, so a real run can never proceed without its trial record (F-11)."""
    if os.environ.get("TRADING_LAB_NO_TRIAL_LOG"):
        if "pytest" in sys.modules:
            return None
        raise RegistryError("TRADING_LAB_NO_TRIAL_LOG is set outside the test suite - unset it; every run must be logged")
    rec = {"at": _now(), "kind": kind, "source": source, "params": params, "dataset": dataset, "headline": headline}
    TRIALS.parent.mkdir(exist_ok=True)
    with open(TRIALS, "a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.write(json.dumps(rec, default=str) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return rec


def trial_count(kind=None):
    return sum(1 for t in _read_jsonl(TRIALS) if kind is None or t["kind"] == kind)


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
    tmp = REGISTRY_MD.with_suffix(".md.tmp")
    tmp.write_text("\n".join(lines))
    os.replace(tmp, REGISTRY_MD)


if __name__ == "__main__":
    write_md()
    print(f"{len(current())} experiments -> {REGISTRY_MD.name}")
