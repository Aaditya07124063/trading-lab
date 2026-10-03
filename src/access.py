"""Central data-access boundary (Phase 1, approved 2026-10-03).

Three tiers (docs/architecture/holdout_ops_design.md):
  W  writer       - the collector (update_intraday.py, src/intraday/pipeline.py)
                    reads/writes raw files through src.data_loader.load_csv.
                    NOT routed through this module, so collection is never blocked.
  O  operational  - status / integrity checks: raw structure only, fixed output
                    fields (scripts/holdout_status.py).
  R  research     - Stage 2, ML, features, dashboard, ordinary backtests: MUST use
                    the research_* loaders below, which drop every row dated after
                    RESEARCH_CUTOFF. tests/test_access_boundary.py scans the code
                    base and fails if a research-tier file reads market data any
                    other way.
The ORB v1 final evaluation is the only consumer of holdout rows, and only through
holdout_authorized() + final_evaluation_unused(). The authorization artifact is a
research-control record, not a secret.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

from src.config import BASE_DIR, HOLDOUT_START
from src.data_loader import load_csv

RESEARCH_CUTOFF = "2026-09-30"                         # last research-visible date (inclusive)
AUTH_NAME = "ORB_v1_holdout_authorization.md"
AUTH_LINE = "AUTHORIZE: ORB v1 final holdout evaluation"
ORB_V1_STRATEGY = "ORB 30m on 15m bars, long/short, exit 15:00 bar OPEN (X2)"
assert pd.Timestamp(RESEARCH_CUTOFF) + pd.Timedelta(days=1) == pd.Timestamp(HOLDOUT_START)


class HoldoutLocked(Exception):
    """Holdout rows requested without a valid authorization."""


# ------------------------------------------------------------- research tier

def research_frame(df, col="date"):
    """Drop every row whose timestamp is after RESEARCH_CUTOFF."""
    return df[df[col] < pd.Timestamp(HOLDOUT_START)].reset_index(drop=True)


def research_load_csv(filename, **kw):
    return research_frame(load_csv(filename, **kw))


def research_load_clean(filename):
    from src.datasets import load_clean
    df, report = load_clean(filename)
    return research_frame(df), report


# ------------------------------------------------- ORB v1 final evaluation

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def holdout_authorized(protocol_path):
    """Raise HoldoutLocked unless ALL hold: protocol FROZEN; authorization artifact
    (same directory, AUTH_NAME) exists, is tracked by git and unmodified at HEAD,
    contains AUTH_LINE, 'protocol_sha256: <sha256 of the protocol file>',
    'sessions: 250', a non-empty 'authorized_by:' and 'date:'. Returns the fields."""
    protocol = Path(protocol_path)
    if "**Status:** FROZEN" not in protocol.read_text():
        raise HoldoutLocked(f"{protocol.name} is not FROZEN - holdout stays locked")
    auth = protocol.parent / AUTH_NAME
    if not auth.exists():
        raise HoldoutLocked(f"no authorization artifact {auth.name} - holdout stays locked")
    repo = _git(protocol.parent, "rev-parse", "--show-toplevel").stdout.strip()
    if not repo or _git(repo, "ls-files", "--error-unmatch", str(auth)).returncode != 0:
        raise HoldoutLocked(f"{auth.name} is not committed (untracked)")
    if _git(repo, "diff", "--quiet", "HEAD", "--", str(auth)).returncode != 0:
        raise HoldoutLocked(f"{auth.name} has uncommitted modifications")
    lines = [l.strip() for l in auth.read_text().splitlines()]
    fields = dict(l.split(":", 1) for l in lines if ":" in l and not l.startswith(AUTH_LINE))
    fields = {k.strip(): v.strip() for k, v in fields.items()}
    if AUTH_LINE not in lines:
        raise HoldoutLocked(f"{auth.name} lacks the line '{AUTH_LINE}'")
    want = hashlib.sha256(protocol.read_bytes()).hexdigest()
    if fields.get("protocol_sha256") != want:
        raise HoldoutLocked(f"{auth.name} protocol_sha256 does not match {protocol.name} ({want})")
    if fields.get("sessions") != "250":
        raise HoldoutLocked(f"{auth.name} must state 'sessions: 250'")
    if not fields.get("authorized_by") or not fields.get("date"):
        raise HoldoutLocked(f"{auth.name} must state authorized_by and date")
    return fields


def final_evaluation_unused(results_dir=None, experiments_file=None):
    """Single-use guard: refuse if any holdout result directory exists or a FINAL
    ORB v1 experiment is already registered."""
    results_dir = Path(results_dir or BASE_DIR / "results" / "orb_v1_holdout")
    experiments_file = Path(experiments_file or BASE_DIR / "registry" / "experiments.jsonl")
    if results_dir.exists() and any(results_dir.iterdir()):
        raise HoldoutLocked(f"{results_dir} already contains an evaluation - single use")
    status = {}
    if experiments_file.exists():
        for line in experiments_file.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "amends" in r:
                if "status" in r:
                    status[r["amends"]] = (status.get(r["amends"], (None,))[0], r["status"])
            else:
                status[r["experiment_id"]] = (r.get("strategy"), r.get("status"))
    if any(s == ORB_V1_STRATEGY and st == "FINAL" for s, st in status.values()):
        raise HoldoutLocked("a FINAL ORB v1 experiment is already registered - single use")
