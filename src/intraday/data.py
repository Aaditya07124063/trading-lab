"""Intraday data: load, infer timeframe, and validate - loudly.
Timestamps are bar START times in IST (09:15 = the first NSE bar).
Validation never repairs data silently; it returns a report of problems."""

import re

import pandas as pd

from src.data_loader import load_csv

SESSION_OPEN = "09:15"
SESSION_CLOSE = "15:30"
TF_MINUTES = {"m15": 15, "m30": 30, "h1": 60, "h4": 240}


def timeframe_of(filename):
    m = re.search(r"(m15|m30|h1|h4)\.csv$", filename)
    if not m:
        raise ValueError(f"{filename}: not an intraday file (need m15/m30/h1/h4)")
    return TF_MINUTES[m.group(1)]


def symbol_of(filename):
    return re.sub(r"(m15|m30|h1|h4|d1)?\.csv$", "", filename)


def expected_times(tf, open_=SESSION_OPEN, close=SESSION_CLOSE):
    """Bar start times of a full NSE session on a tf-minute grid."""
    t = pd.Timestamp(f"2000-01-01 {open_}")
    end = pd.Timestamp(f"2000-01-01 {close}")
    out = []
    while t < end:
        out.append(t.strftime("%H:%M"))
        t += pd.Timedelta(minutes=tf)
    return out


def validate(df, tf, symbol=""):
    """df in raw file order. Returns dict: ok, errors (block research),
    warnings (limit trust), and the available range."""
    errors, warnings = [], []
    n = len(df)
    if n == 0:
        return {"ok": False, "errors": ["empty dataset"], "warnings": [], "symbol": symbol}

    if df[["open", "high", "low", "close"]].isna().any().any():
        errors.append("missing OHLC values")
    if df["date"].isna().any():
        errors.append("unparseable timestamps")
    dup = df["date"].duplicated().sum()
    if dup:
        errors.append(f"{dup} duplicate timestamps")
    backwards = (df["date"].diff() < pd.Timedelta(0)).sum()
    if backwards:
        errors.append(f"{backwards} out-of-order timestamps")

    bad_ohlc = ((df["high"] < df[["open", "close", "low"]].max(axis=1)) |
                (df["low"] > df[["open", "close", "high"]].min(axis=1)) |
                (df[["open", "high", "low", "close"]] <= 0).any(axis=1)).sum()
    if bad_ohlc:
        errors.append(f"{bad_ohlc} bars with impossible OHLC (high<low, <=0, ...)")

    weekend = sorted({str(d) for d in df.loc[df["date"].dt.dayofweek >= 5, "date"].dt.date})
    if weekend:   # NSE holds rare special sessions (e.g. Budget Saturday 2025-02-01)
        warnings.append(f"weekend sessions {', '.join(weekend)} - verify they were real "
                        "special NSE sessions")

    grid = expected_times(tf)
    times = df["date"].dt.strftime("%H:%M")
    off = ~times.isin(grid)
    if off.any():
        sample = sorted(times[off].unique())[:3]
        warnings.append(f"{off.sum()} bars off the {SESSION_OPEN} {tf}-min session grid "
                        f"(e.g. {', '.join(sample)}) - session alignment is wrong")

    days = df.assign(d=df["date"].dt.date, t=times)
    incomplete = []
    for d, g in days.groupby("d"):
        missing = set(grid) - set(g["t"])
        if missing:
            incomplete.append((str(d), len(missing)))
    if incomplete:
        warnings.append(f"{len(incomplete)} of {days['d'].nunique()} sessions have missing bars "
                        f"(e.g. {incomplete[0][0]} missing {incomplete[0][1]})")

    if (df["volume"] == 0).all():
        warnings.append("volume is zero on every bar - volume/VWAP features unusable")

    sessions = days["d"].nunique()
    return {
        "ok": not errors, "errors": errors, "warnings": warnings, "symbol": symbol,
        "timeframe_min": tf, "bars": n, "sessions": sessions,
        "start": str(df["date"].min()), "end": str(df["date"].max()),
        "incomplete_sessions": [d for d, _ in incomplete],
    }


def load_intraday(filename):
    """Load + validate. Returns (clean sorted df with 'session' column, report).
    Raises on hard errors so corrupted data can never reach a backtest."""
    tf = timeframe_of(filename)
    raw = load_csv(filename, sort=False)
    report = validate(raw, tf, symbol_of(filename))
    if not report["ok"]:
        raise ValueError(f"{filename} failed validation: {report['errors']}")
    df = raw.sort_values("date").reset_index(drop=True)
    df["session"] = df["date"].dt.date
    df["time"] = df["date"].dt.strftime("%H:%M")
    return df, report
