"""Grow the intraday history safely. Every download is first stored untouched
in data/raw/yahoo/<dataset>/<timestamp>.csv (checksummed, never overwritten);
the working file only ever gains NEW bars. (Yahoo, free, no key). Run after 15:45 IST,
ideally every few weeks - Yahoo only keeps ~60 days of 15-min bars, so
anything not captured in time is gone.
    python3 update_intraday.py            # m15 + h1, all symbols
    python3 update_intraday.py --dry-run  # report only, write nothing"""

import argparse

from src.config import DATA_DIR, YAHOO_SYMBOLS
from src.data_loader import load_csv
from src.intraday.pipeline import DataConflict, fetch_yahoo, merge_bars, snapshot_raw, write_mt_csv

TFS = {"m15": 15, "h1": 60}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tf", nargs="+", default=list(TFS), choices=list(TFS))
    ap.add_argument("--symbols", nargs="+", default=list(YAHOO_SYMBOLS))
    args = ap.parse_args()

    for sym in args.symbols:
        for tfname in args.tf:
            fname = f"{sym}{tfname}.csv"
            path = DATA_DIR / "india" / fname
            old = load_csv(fname) if path.exists() else fetch_yahoo("", 15).iloc[0:0]
            fetched = fetch_yahoo(YAHOO_SYMBOLS[sym], TFS[tfname])
            if not args.dry_run:
                snap = snapshot_raw(fetched, "yahoo", f"{sym}{tfname}")
                print(f"raw snapshot {snap['file']} sha256 {snap['sha256'][:12]}")
            try:
                merged, rep = merge_bars(old, fetched, TFS[tfname], sym)
            except DataConflict as e:
                print(f"REFUSED  {fname}: {e}")
                continue
            gap = f"  GAP {rep['gap'][0]} -> {rep['gap'][1]} (bars lost)" if rep["gap"] else ""
            print(f"{'DRY ' if args.dry_run else ''}{fname:18s} +{rep['added']:5d} bars "
                  f"(overlap checked {rep['overlap_checked']}) | {rep['start'][:10]} -> "
                  f"{rep['end'][:10]}{gap}")
            if rep["added"] and not args.dry_run:
                write_mt_csv(merged, path)
