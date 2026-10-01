"""Intraday data collection (Yahoo, free, no key). Safe by construction:
  * every download is stored untouched first: data/raw/yahoo/<dataset>/<ts>.csv
    (checksummed, never overwritten; listed in data/raw/manifest.jsonl);
  * working files only GAIN bars (existing bars always win; overlaps must agree);
  * corrupt / off-grid / mismatching downloads are REJECTED, not merged;
  * every attempt - success, rejection or failure - is appended to
    data/raw/collection_log.jsonl. Nothing is ever deleted.
Targets: research instruments (m15 + h1) and the frozen NIFTY 50 holdout
universe (m15). Never switches provider on failure.

    python3 update_intraday.py              # collect everything
    python3 update_intraday.py --dry-run    # fetch + report, write nothing
    python3 update_intraday.py --only RELIANCE TCS
Exit code 1 if any dataset failed or was rejected."""

import argparse
import json
import sys
from datetime import datetime

import pandas as pd

from src.config import DATA_DIR, YAHOO_SYMBOLS
from src.datasets import file_sha256
from src.data_loader import load_csv
from src.intraday.data import validate
from src.intraday.pipeline import DataConflict, fetch_yahoo, merge_bars, snapshot_raw, write_mt_csv

UNIVERSE_FILE = DATA_DIR / "metadata" / "universe" / "NIFTY50_frozen_20261001.json"
LOG = DATA_DIR / "raw" / "collection_log.jsonl"
TFS = {"m15": 15, "h1": 60}


def targets():
    """(name, yahoo ticker, timeframe, role) - research set first, then holdout universe."""
    out = {}
    for name, ticker in YAHOO_SYMBOLS.items():
        for tf in TFS:
            out[(name, tf)] = (ticker, "research")
    for c in json.load(open(UNIVERSE_FILE))["constituents"]:
        key = (c["symbol"], "m15")
        role = "research+holdout" if key in out else "holdout"
        out[key] = (c["yahoo"], role)
    return [(n, t, tf, role) for (n, tf), (t, role) in out.items()]


def log(rec):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")


def collect_one(name, ticker, tfname, role, run_id, dry):
    tf = TFS[tfname]
    path = DATA_DIR / "india" / f"{name}{tfname}.csv"
    base = {"run_id": run_id, "at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "dataset": path.name, "instrument": name, "ticker": ticker, "role": role,
            "source": "Yahoo Finance via yfinance", "dry_run": dry}
    old = load_csv(path.name) if path.exists() else None
    since = None if old is None else old["date"].max() - pd.Timedelta(days=3)
    try:
        fetched = fetch_yahoo(ticker, tf, since=since)
    except Exception as e:
        return {**base, "status": "FAILED", "error": f"{type(e).__name__}: {e}"[:300]}
    if fetched.empty:
        return {**base, "status": "FAILED", "error": "provider returned no rows"}
    rec = {**base, "rows_fetched": len(fetched), "fetched_range": [str(fetched.date.min()), str(fetched.date.max())]}
    if not dry:
        snap = snapshot_raw(fetched, "yahoo", f"{name}{tfname}")
        rec["raw_snapshot"], rec["raw_sha256"] = snap["file"], snap["sha256"]
    if old is None:
        old = fetched.iloc[0:0]
        rec["new_dataset"] = True
    try:
        merged, rep = merge_bars(old, fetched, tf, name)
    except DataConflict as e:
        return {**rec, "status": "REJECTED", "error": str(e)[:300], "rows_added": 0,
                "rows_rejected": len(fetched)}
    added = merged[~merged["date"].isin(old["date"])]
    v = validate(added, tf, name) if len(added) else {"ok": True, "warnings": [], "incomplete_sessions": []}
    rec.update({"rows_added": rep["added"], "duplicates_overlap": rep["overlap_checked"],
                "rows_rejected": rep["dropped_live_bars"], "gap": rep["gap"],
                "missing_bar_sessions": v.get("incomplete_sessions", []),
                "validation": "PASS" if v["ok"] and not v["warnings"] else ("WARN" if v["ok"] else "FAIL"),
                "validation_warnings": v["warnings"], "range_after": [rep["start"], rep["end"]]})
    if rep["added"] and not dry:
        write_mt_csv(merged, path)
        rec["file_sha256_after"] = file_sha256(path)
    rec["status"] = "OK" if rep["added"] else "OK_NO_NEW_BARS"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="+")
    a = ap.parse_args()
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S")
    bad = 0
    for name, ticker, tfname, role in targets():
        if a.only and name not in a.only:
            continue
        rec = collect_one(name, ticker, tfname, role, run_id, a.dry_run)
        if not a.dry_run:
            log(rec)
        bad += rec["status"] in ("FAILED", "REJECTED")
        extra = rec.get("error") or (f"GAP {rec['gap']}" if rec.get("gap") else "")
        print(f"{rec['status']:15s} {rec['dataset']:20s} +{rec.get('rows_added', 0):5d} "
              f"val={rec.get('validation', '-'):4s} {extra}")
    summary = {"run_id": run_id, "at": datetime.now().astimezone().isoformat(timespec="seconds"),
               "summary": True, "failed_or_rejected": bad, "dry_run": a.dry_run}
    if not a.dry_run:
        log(summary)
    print(f"run {run_id}: {bad} failed/rejected")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
