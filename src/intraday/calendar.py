"""ORB v1 session calendar (approved 2026-10-01).

A STANDARD NSE SESSION is a Monday-Friday date that is not listed as a
Capital Market (CM) trading holiday in NSE's holiday master for that year
(stored as docs/evidence/nse_calendar/nse_cm_trading_holidays_<year>.json).
Consequences, by construction:
  * special sessions held on weekends (e.g. Muhurat 2026-11-08, a Sunday;
    weekend budget sessions) are excluded;
  * special sessions held on a listed holiday are excluded;
  * a year without a stored holiday file cannot be counted -> error, never a
    guess. The 2027 file must be stored (with its NSE source) when NSE
    publishes it, before 2027 sessions are counted.
Dates are never added or removed by hand.
"""

import json
from datetime import date, timedelta
from pathlib import Path

from src.config import BASE_DIR

CAL_DIR = BASE_DIR / "docs" / "evidence" / "nse_calendar"


def holidays(year, cal_dir=CAL_DIR):
    f = Path(cal_dir) / f"nse_cm_trading_holidays_{year}.json"
    if not f.exists():
        raise FileNotFoundError(f"NSE CM holiday list for {year} not stored ({f.name}) - "
                                "cannot count sessions in that year")
    from datetime import datetime
    return {datetime.strptime(h["tradingDate"], "%d-%b-%Y").date() for h in json.load(open(f))["holidays"]}


def standard_sessions(start, n, cal_dir=CAL_DIR):
    """The first n standard NSE sessions on or after `start` (ISO string)."""
    d, out, hol = date.fromisoformat(start), [], {}
    while len(out) < n:
        if d.year not in hol:
            hol[d.year] = holidays(d.year, cal_dir)
        if d.weekday() < 5 and d not in hol[d.year]:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


if __name__ == "__main__":
    s = standard_sessions("2026-10-01", 61)                       # rest of 2026 (2027 not yet stored)
    assert s[0] == "2026-10-01" and "2026-10-02" not in s and "2026-11-08" not in s
    print(len(s), s[0], s[-1])
