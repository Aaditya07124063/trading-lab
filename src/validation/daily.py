"""Daily data validation. FLAGS ONLY - it never removes a row.
An extreme move can be real; exclusion requires a reviewed entry in
data/metadata/exclusions.csv with evidence (see src/datasets.py)."""

import json

import numpy as np
import pandas as pd

from src.config import DATA_DIR

INSTRUMENTS = json.load(open(DATA_DIR / "metadata" / "instruments.json"))

RULES = {
    "V01": "duplicate date",
    "V02": "date out of order",
    "V03": "missing OHLC value",
    "V04": "OHLC inconsistent (high/low do not bound open/close)",
    "V05": "non-positive price",
    "V06": "placeholder bar: O=H=L=C and zero volume in a series that normally has volume",
    "V07": "spike-and-revert: |move| > 30% that fully reverses next bar",
    "V08": "level-shift block: jump > 40% reversed within 20 bars (adjustment-boundary pattern)",
    "V09": "weekend date",
    "V10": "row before the instrument's listing date",
    "V11": "extreme move |return| > 20% (informational - often genuine)",
}


def instrument_of(filename):
    for key in sorted(INSTRUMENTS, key=len, reverse=True):
        if filename.upper().startswith(key):
            return key
    return None


def validate_daily(df, filename):
    """df: raw rows in file order (load_csv(..., sort=False)).
    Returns a DataFrame of flags: rule, date_start, date_end, rows, detail."""
    flags = []

    def flag(rule, d0, d1, rows, detail=""):
        flags.append({"rule": rule, "description": RULES[rule], "date_start": str(pd.Timestamp(d0).date()),
                      "date_end": str(pd.Timestamp(d1).date()), "rows": int(rows), "detail": detail})

    for d in df.loc[df["date"].duplicated(), "date"]:
        flag("V01", d, d, 1)
    for i in np.where(df["date"].diff() < pd.Timedelta(0))[0]:
        flag("V02", df["date"].iloc[i], df["date"].iloc[i], 1)
    px = ["open", "high", "low", "close"]
    for d in df.loc[df[px].isna().any(axis=1), "date"]:
        flag("V03", d, d, 1)
    bad = (df["high"] < df[["open", "close"]].max(axis=1)) | (df["low"] > df[["open", "close"]].min(axis=1))
    for d in df.loc[bad, "date"]:
        flag("V04", d, d, 1)
    for d in df.loc[(df[px] <= 0).any(axis=1), "date"]:
        flag("V05", d, d, 1)
    if (df["volume"] > 0).mean() > 0.5:
        ph = (df["open"] == df["high"]) & (df["high"] == df["low"]) & (df["low"] == df["close"]) & (df["volume"] == 0)
        for _, r in df[ph].iterrows():
            flag("V06", r["date"], r["date"], 1, f"price {r['close']}")
    for d in df.loc[df["date"].dt.dayofweek >= 5, "date"]:
        flag("V09", d, d, 1)
    inst = INSTRUMENTS.get(instrument_of(filename) or "", {})
    if inst.get("listing_date"):
        pre = df[df["date"] < pd.Timestamp(inst["listing_date"])]
        if len(pre):
            flag("V10", pre["date"].min(), pre["date"].max(), len(pre),
                 f"listing date {inst['listing_date']}")

    s = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
    lr = np.log(s["close"] / s["close"].shift(1))
    for i in range(1, len(s) - 1):
        if abs(lr[i]) > np.log(1.3) and abs(lr[i] + lr[i + 1]) < 0.1 and np.sign(lr[i + 1]) == -np.sign(lr[i]):
            flag("V07", s["date"][i], s["date"][i], 1,
                 f"close {s['close'][i - 1]} -> {s['close'][i]} -> {s['close'][i + 1]}")
    jumps = np.where(lr.abs() > np.log(1.4))[0]
    for a in jumps:
        for b in jumps:
            if 1 < b - a <= 20 and np.sign(lr[b]) == -np.sign(lr[a]) and abs(lr[a] + lr[b]) < 0.15:
                flag("V08", s["date"][a], s["date"][b - 1], b - a,
                     f"jump {lr[a]:+.2f} log at {s['date'][a].date()}, reversal {lr[b]:+.2f} at {s['date'][b].date()}")
    for i in np.where(lr.abs() > np.log(1.2))[0]:
        flag("V11", s["date"][i], s["date"][i], 1, f"log return {lr[i]:+.3f}")
    return pd.DataFrame(flags, columns=["rule", "description", "date_start", "date_end", "rows", "detail"])
