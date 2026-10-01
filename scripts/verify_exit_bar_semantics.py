"""Verify what the end-of-day 15-min bars represent before/after NSE's Closing
Auction Session (CAS, SEBI circular 16 Jan 2026, effective 2026-08-03).

PRE-HOLDOUT DATA ONLY: every intraday row is filtered to Date < 2026-10-01.
Evidence: docs/evidence/cas_2026/ (NSE bhavcopy extracts, SEBI circular, F&O list).

    python3 scripts/verify_exit_bar_semantics.py
"""

import csv
import glob
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "docs" / "evidence" / "cas_2026"
HOLDOUT_START = "2026-10-01"
CAS_START = "2026-08-03"


def universe():
    f = ROOT / "data" / "metadata" / "universe" / "NIFTY50_frozen_20261001.json"
    return [c["symbol"] for c in json.load(open(f))["constituents"]]


def bars(sym):
    d = pd.read_csv(ROOT / "data" / "india" / f"{sym}m15.csv")
    d = d[d.Date < HOLDOUT_START].copy()                 # holdout never read
    d["day"], d["t"] = d.Date.str[:10], d.Date.str[11:]
    return d


def main():
    u = universe()
    fo = {r[1].strip() for r in csv.reader(open(EVID / "nse_fo_mktlots_retrieved_20261001.csv")) if len(r) > 1}
    print(f"1. Frozen constituents with NSE derivatives (CAS-eligible): {sum(s in fo for s in u)}/{len(u)}")

    data = {s: bars(s) for s in u}

    print("\n2. Bar presence per stock-session (mean across stocks)")
    for label, lo, hi in [("pre-CAS ", "2000-01-01", CAS_START), ("post-CAS", CAS_START, HOLDOUT_START)]:
        stats = []
        for d in data.values():
            g = d[(d.day >= lo) & (d.day < hi)].groupby("day").t.apply(set)
            if len(g):
                stats.append((len(g), g.apply(lambda x: "15:00" in x).mean(),
                              g.apply(lambda x: "15:15" in x).mean(), g.apply(len).eq(25).mean()))
        s = pd.DataFrame(stats, columns=["sessions", "has_1500", "has_1515", "all_25_bars"])
        print(f"   {label}: stocks={len(s)} sessions/stock={s.sessions.median():.0f} "
              f"has_1500={s.has_1500.mean():.3f} has_1515={s.has_1515.mean():.3f} "
              f"(min {s.has_1515.min():.3f}) all_25_bars={s.all_25_bars.mean():.3f}")

    print("\n3. Median volume ratio 15:15 bar / 15:00 bar (4 long-history stocks)")
    for sym in ["RELIANCE", "HDFCBANK", "INFY", "TCS"]:
        p = data[sym].pivot_table(index="day", columns="t", values="tick_volume")
        r = p["15:15"] / p["15:00"]
        print(f"   {sym:9s} pre-CAS {r[r.index < CAS_START].median():.2f}   post-CAS {r[r.index >= CAS_START].median():.2f}")

    print("\n4. Yahoo end-of-day bars vs NSE official close (bhavcopy ClsPric)")
    rows = []
    for f in sorted(glob.glob(str(EVID / "bhavcopy_*_nifty50_frozen.csv"))):
        day = pd.Timestamp(Path(f).name.split("_")[1]).strftime("%Y-%m-%d")
        b = pd.read_csv(f).set_index("TckrSymb")
        for s, d in data.items():
            d = d[d.day == day].set_index("t")
            if d.empty or s not in b.index:
                continue
            rows.append(dict(day=day, cas=day >= CAS_START, cls=b.at[s, "ClsPric"], ltp=b.at[s, "LastPric"],
                             c1500=d.close.get("15:00"), c1515=d.close.get("15:15")))
    r = pd.DataFrame(rows)
    bp = lambda a, c: ((a / c - 1) * 1e4).abs()
    r["c1515_bps"], r["c1500_bps"] = bp(r.c1515, r.cls), bp(r.c1500, r.cls)
    for cas, g in r.groupby("cas"):
        print(f"   {'post-CAS' if cas else 'pre-CAS '}: days={g.day.nunique()} stock-days={len(g)} "
              f"has_1515={g.c1515.notna().mean():.2f} "
              f"close(15:15 bar)==official close: {(g.c1515_bps.dropna() < 0.5).mean():.2f}; "
              f"official close==last price: {(g.cls == g.ltp).mean():.2f}; "
              f"|close(15:00 bar) - official close| median {g.c1500_bps.median():.1f} bps, "
              f"p90 {g.c1500_bps.quantile(.9):.1f} bps")


if __name__ == "__main__":
    main()
