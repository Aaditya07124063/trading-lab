"""Intraday data: load, infer timeframe, and validate - loudly.
Timestamps are bar START times in IST (09:15 = the first NSE bar).
Validation never repairs data silently; it returns a report of problems."""

import re

import pandas as pd

from src.config import HOLDOUT_START
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


def validate(df, tf, symbol="", session_grid=True):
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
    if session_grid and off.any():
        sample = sorted(times[off].unique())[:3]
        warnings.append(f"{off.sum()} bars off the {SESSION_OPEN} {tf}-min session grid "
                        f"(e.g. {', '.join(sample)}) - session alignment is wrong")

    days = df.assign(d=df["date"].dt.date, t=times)
    incomplete = []
    for d, g in days.groupby("d") if session_grid else []:
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


class HoldoutLocked(Exception):
    pass


def split_defective(raw, tf):
    """ORB v1 rule (approved 2026-10-01): malformed data makes ONLY the affected
    stock-session untradable. raw = rows in FILE order. Returns (rows of
    unaffected sessions, {session: [reasons]}, n rows with unparseable
    timestamps). Nothing is repaired; the source file is never touched.
    Defects: unparseable timestamp (row has no session; counted), missing
    OHLC, impossible OHLC, duplicate timestamp, out-of-order timestamp,
    bar off the session grid."""
    d = raw.copy()
    bad_time = d["date"].isna()
    d = d[~bad_time]
    sess = d["date"].dt.date.astype(str)
    reasons = {}

    def flag(mask, why):
        for s in sorted(set(sess[mask])):
            reasons.setdefault(s, []).append(why)

    px = d[["open", "high", "low", "close"]]
    flag(px.isna().any(axis=1), "missing OHLC")
    flag((d["high"] < px.max(axis=1)) | (d["low"] > px.min(axis=1)) | (px <= 0).any(axis=1),
         "impossible OHLC")
    flag(d["date"].duplicated(keep=False), "duplicate timestamp")
    flag(d["date"] < d["date"].cummax().shift(1), "out-of-order timestamp")
    flag(~d["date"].dt.strftime("%H:%M").isin(expected_times(tf)), "bar off the session grid")
    keep = d[~sess.isin(reasons)]
    return keep, reasons, int(bad_time.sum())


def load_intraday(filename, holdout_protocol=None, session_errors=False):
    """Load + validate. Returns (clean sorted df with 'session' column, report).
    Raises on hard errors so corrupted data can never reach a backtest - or,
    with session_errors=True (ORB v1), removes ONLY the affected sessions from
    the returned frame and lists them with reasons in report["defective_sessions"].
    Bars on/after HOLDOUT_START are dropped unless `holdout_protocol` names a
    protocol file whose status line reads FROZEN."""
    tf = timeframe_of(filename)
    raw = load_csv(filename, sort=False, coerce=session_errors)
    if holdout_protocol is None:
        raw = raw[raw["date"] < pd.Timestamp(HOLDOUT_START)]
    else:
        from src.config import BASE_DIR
        text = (BASE_DIR / holdout_protocol).read_text()
        if "**Status:** FROZEN" not in text:
            raise HoldoutLocked(f"{holdout_protocol} is not FROZEN - holdout stays locked")
    if session_errors:                     # ORB v1: isolate defects per stock-session
        raw, defects, n_bad_time = split_defective(raw, tf)
    report = validate(raw, tf, symbol_of(filename))
    if session_errors:
        report |= {"defective_sessions": defects, "unparseable_timestamp_rows": n_bad_time}
    elif not report["ok"]:
        raise ValueError(f"{filename} failed validation: {report['errors']}")
    df = raw.sort_values("date").reset_index(drop=True)
    df["session"] = df["date"].dt.date
    df["time"] = df["date"].dt.strftime("%H:%M")
    return df, report
