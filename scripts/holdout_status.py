"""ORB v1 holdout COLLECTION status - DATA STRUCTURE ONLY.

Reads only which bars exist and whether rows are well-formed (frozen rules
§5.3-5.4). Computes NO prices, signals, trades, returns or any performance.
Safe to run any time during holdout preservation.

    PYTHONPATH=. python3 scripts/holdout_status.py
"""

import json

import pandas as pd

from src.config import HOLDOUT_START
from src.data_loader import load_csv
from src.intraday.calendar import CAL_DIR, standard_sessions
from src.intraday.data import split_defective
from src.intraday.engine import EngineConfig, tradable_sessions
from src.intraday.portfolio import frozen_universe

N = 250
known, d = [], None
for n in range(1, N + 1):
    try:
        known = standard_sessions(HOLDOUT_START, n)
    except FileNotFoundError as e:                 # next year's NSE list not stored yet
        d = str(e)
        break

files, frames = {}, {}
for s in frozen_universe():
    try:
        raw = load_csv(f"{s}m15.csv", sort=False, coerce=True)
    except FileNotFoundError:
        files[s] = False
        continue
    files[s] = True
    frames[s] = raw[raw["date"] >= pd.Timestamp(HOLDOUT_START)]

last = max((f["date"].max() for f in frames.values() if len(f)), default=pd.NaT)
through = str(last.date()) if pd.notna(last) else None
collected = [x for x in known if through and x <= through]

untradable = []
for s, raw in frames.items():
    keep, bad, _ = split_defective(raw, 15)
    df = keep.assign(session=keep["date"].dt.date, time=keep["date"].dt.strftime("%H:%M"))
    ok, miss = tradable_sessions(df, EngineConfig()) if len(df) else (set(), [])
    ok, miss = {str(x) for x in ok}, dict(miss)
    for x in collected:
        if x not in ok:
            why = ("malformed data: " + "; ".join(bad[x]) if x in bad else
                   "missing bars: " + " ".join(miss[x]) if x in miss else "no data")
            untradable.append({"session": x, "symbol": s, "reason": why})
for s in (s for s, ok in files.items() if not ok):
    untradable += [{"session": x, "symbol": s, "reason": "no data file"} for x in collected]

print(json.dumps({
    "standard_holdout_sessions_collected": f"{len(collected)} / {N}",
    "collected_through": through,
    "sessions_countable_with_stored_calendars": len(known),
    "calendar_note": d,
    "nse_2027_holiday_list_stored": (CAL_DIR / "nse_cm_trading_holidays_2027.json").exists(),
    "universe_files_present": f"{sum(files.values())} / {len(files)}",
    "untradable_stock_sessions": len(untradable),
    "untradable": untradable,
    "performance_computed": False,
}, indent=2))
