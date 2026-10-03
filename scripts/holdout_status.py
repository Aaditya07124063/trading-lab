"""ORB v1 holdout OPERATIONAL status (tier O, src/access.py) - STRUCTURE ONLY.

Reads which bars exist, whether rows are well-formed (frozen rules §5.3-5.4) and
the collector's own log. Computes NO prices, signals, trades, returns, P&L,
Sharpe, p-values or any other outcome. Output keys are fixed (STATUS_FIELDS);
tests/test_access_boundary.py enforces the field list and the allowed imports.

    PYTHONPATH=. python3 scripts/holdout_status.py
"""

import json
from collections import Counter

import pandas as pd

from src.config import BASE_DIR, HOLDOUT_START
from src.data_loader import load_csv
from src.intraday.calendar import CAL_DIR, standard_sessions
from src.intraday.data import split_defective
from src.intraday.engine import EngineConfig, tradable_sessions
from src.intraday.portfolio import frozen_universe

N = 250
PROTOCOL = BASE_DIR / "docs" / "protocols" / "ORB_v1.md"
LOG = BASE_DIR / "data" / "raw" / "collection_log.jsonl"
STATUS_FIELDS = (
    "protocol_status", "holdout_start", "sessions_collected", "sessions_required",
    "sessions_remaining", "collected_through", "latest_successful_collection",
    "latest_run", "latest_run_failed_or_rejected", "stale", "data_health",
    "universe_files_present", "untradable_stock_sessions", "untradable_by_reason",
    "calendar_2027_stored", "sessions_countable_with_stored_calendars",
    "ready_for_final_evaluation", "performance_computed",
)


def _known_sessions():
    known = []
    for n in range(1, N + 1):
        try:
            known = standard_sessions(HOLDOUT_START, n)
        except FileNotFoundError:               # next year's NSE list not stored yet
            break
    return known


def _runs():
    if not LOG.exists():
        return []
    return [r for r in map(json.loads, filter(str.strip, LOG.read_text().splitlines()))
            if r.get("summary") and not r.get("dry_run")]


def build_status(now=None):
    now = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)
    known = _known_sessions()
    present, frames = {}, {}
    for s in frozen_universe():
        try:
            raw = load_csv(f"{s}m15.csv", sort=False, coerce=True)
        except FileNotFoundError:
            present[s] = False
            continue
        present[s] = True
        frames[s] = raw[raw["date"] >= pd.Timestamp(HOLDOUT_START)]

    last = max((f["date"].max() for f in frames.values() if len(f)), default=pd.NaT)
    through = str(last.date()) if pd.notna(last) else None
    collected = [x for x in known if through and x <= through]

    reasons = Counter()
    for s, raw in frames.items():
        keep, bad, _ = split_defective(raw, 15)
        df = keep.assign(session=keep["date"].dt.date, time=keep["date"].dt.strftime("%H:%M"))
        ok, miss = tradable_sessions(df, EngineConfig()) if len(df) else (set(), [])
        ok, miss = {str(x) for x in ok}, dict(miss)
        for x in collected:
            if x not in ok:
                reasons["malformed data" if x in bad else "missing bars" if x in miss else "no data"] += 1
    reasons["no data file"] += sum(not v for v in present.values()) * len(collected)
    reasons = {k: v for k, v in reasons.items() if v}

    runs = _runs()
    ok_runs = [r for r in runs if r.get("failed_or_rejected") == 0]
    # stale = a standard session whose evening collection (22:30 IST) is due is not collected
    due = [x for x in known if pd.Timestamp(f"{x} 22:30") <= now]
    stale = bool(due) and (through is None or through < due[-1])
    failed = runs[-1].get("failed_or_rejected") if runs else None
    health = "STALE" if stale else ("DEGRADED" if failed else "OK")
    ready = len(collected) == N and not stale

    out = {
        "protocol_status": "FROZEN" if "**Status:** FROZEN" in PROTOCOL.read_text() else "NOT FROZEN",
        "holdout_start": HOLDOUT_START,
        "sessions_collected": len(collected), "sessions_required": N,
        "sessions_remaining": N - len(collected), "collected_through": through,
        "latest_successful_collection": ok_runs[-1]["at"] if ok_runs else None,
        "latest_run": runs[-1]["at"] if runs else None,
        "latest_run_failed_or_rejected": failed,
        "stale": stale, "data_health": health,
        "universe_files_present": f"{sum(present.values())} / {len(present)}",
        "untradable_stock_sessions": sum(reasons.values()), "untradable_by_reason": reasons,
        "calendar_2027_stored": (CAL_DIR / "nse_cm_trading_holidays_2027.json").exists(),
        "sessions_countable_with_stored_calendars": len(known),
        "ready_for_final_evaluation": "READY FOR EXPLICIT FINAL EVALUATION" if ready else "NOT READY",
        "performance_computed": False,
    }
    assert tuple(out) == STATUS_FIELDS
    return out


if __name__ == "__main__":
    print(json.dumps(build_status(), indent=2))
