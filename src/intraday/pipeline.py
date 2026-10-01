"""Safe intraday data updates: ADD new bars, never rewrite history.

merge_bars() is pure and refuses (raises DataConflict) when:
  * incoming data fails validation (dupes, disorder, bad OHLC, NaN);
  * incoming bars sit on a different session grid than the file;
  * an overlapping bar disagrees with the stored one (> tolerance) -
    wrong instrument, or adjusted vs unadjusted prices;
  * there is no overlap and the price jump across the gap is implausible.
Existing bars always win; only NEW timestamps are added. Today's session
is dropped while the market may still be open (bars can still change)."""

import shutil
from datetime import datetime

import pandas as pd

from src.intraday.data import expected_times, validate

TOLERANCE = 0.002          # 0.2% max disagreement on overlapping bars
MAX_GAP_JUMP = 0.25        # >25% close-to-open jump across a data gap = suspicious


class DataConflict(Exception):
    pass


def merge_bars(old, new, tf, symbol, now=None):
    now = now or pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)   # NSE clock, not the Mac's
    rep = validate(new, tf, symbol)
    if not rep["ok"]:
        raise DataConflict(f"{symbol}: incoming data invalid: {rep['errors']}")

    grid = set(expected_times(tf))
    for label, d in (("stored", old), ("incoming", new)):
        off = ~d["date"].dt.strftime("%H:%M").isin(grid)
        if off.any():
            raise DataConflict(f"{symbol}: {label} bars are not on the 09:15 {tf}-min grid - "
                               f"({int(off.sum())} off-grid bars) - mixing grids would corrupt the file; not merging")

    live = (new["date"].dt.date == now.date()) & (now.strftime("%H:%M") < "15:45")
    new = new[~live]

    both = old.merge(new, on="date", suffixes=("_old", "_new"))
    if len(both):
        diff = ((both["close_new"] / both["close_old"]) - 1).abs()
        if (diff > TOLERANCE).any():
            raise DataConflict(f"{symbol}: {int((diff > TOLERANCE).sum())} of {len(both)} "
                               f"overlapping bars disagree by >{TOLERANCE:.1%} - wrong "
                               "instrument or adjusted prices; not merging")
    elif len(old) and len(new):
        jump = abs(new["open"].iloc[0] / old["close"].iloc[-1] - 1)
        if jump > MAX_GAP_JUMP:
            raise DataConflict(f"{symbol}: no overlap and a {jump:.0%} jump across the gap - "
                               "cannot confirm it is the same instrument")

    added = new[~new["date"].isin(old["date"])]
    merged = pd.concat([old, added]).sort_values("date").reset_index(drop=True)
    gap = None
    if len(old) and len(added) and not len(both):
        gap = (str(old["date"].max()), str(added["date"].min()))
    return merged, {"symbol": symbol, "added": len(added), "overlap_checked": len(both),
                    "gap": gap, "dropped_live_bars": int(live.sum()),
                    "start": str(merged["date"].min()), "end": str(merged["date"].max())}


def snapshot_raw(df, provider, dataset, retrieved_at=None):
    """Store one retrieval exactly as fetched - immutable, checksummed,
    listed in data/raw/manifest.jsonl. Never overwritten."""
    import hashlib
    import json
    from src.config import DATA_DIR
    retrieved_at = retrieved_at or datetime.now().strftime("%Y%m%dT%H%M%S")
    folder = DATA_DIR / "raw" / provider / dataset
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{retrieved_at}.csv"
    if path.exists():
        raise FileExistsError(f"raw snapshot {path} already exists - refusing to overwrite")
    df.to_csv(path, index=False)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    rec = {"file": str(path.relative_to(DATA_DIR.parent)), "provider": provider, "dataset": dataset,
           "retrieved_at": retrieved_at, "sha256": sha, "rows": len(df),
           "start": str(df["date"].min()) if len(df) else None,
           "end": str(df["date"].max()) if len(df) else None}
    with open(DATA_DIR / "raw" / "manifest.jsonl", "a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def write_mt_csv(df, path):
    """Write in the file's original MetaTrader dialect, atomically, after a backup."""
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backups = path.parent / "backups"
        backups.mkdir(exist_ok=True)
        shutil.copy2(path, backups / f"{path.name}.{stamp}.bak")
    out = df[["date", "open", "high", "low", "close", "volume"]].copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d %H:%M")
    out.columns = ["Date", "open", "high", "low", "close", "tick_volume"]
    tmp = path.with_suffix(".tmp")
    out.to_csv(tmp, index=False)
    tmp.replace(path)


MAX_LOOKBACK_DAYS = {15: 59, 60: 729}     # Yahoo's intraday history limits


def fetch_yahoo(ticker, tf, since=None):
    """Free Yahoo intraday (no key). since=None -> as far back as Yahoo allows;
    otherwise from `since` (capped at Yahoo's limit). Raises on transport errors."""
    import yfinance as yf
    interval = {15: "15m", 60: "60m"}[tf]
    today = pd.Timestamp.now(tz="Asia/Kolkata").normalize().tz_localize(None)
    earliest = today - pd.Timedelta(days=MAX_LOOKBACK_DAYS[tf])
    start = earliest if since is None else max(pd.Timestamp(since).normalize(), earliest)
    h = yf.Ticker(ticker).history(start=start.strftime("%Y-%m-%d"),
                                  end=(today + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                                  interval=interval, auto_adjust=False, raise_errors=True)
    if h is None or h.empty:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    idx = h.index.tz_convert("Asia/Kolkata").tz_localize(None) if h.index.tz else h.index
    df = pd.DataFrame({"date": idx, "open": h["Open"].values, "high": h["High"].values,
                       "low": h["Low"].values, "close": h["Close"].values,
                       "volume": h["Volume"].fillna(0).astype("int64").values})
    return df.dropna(subset=["open", "high", "low", "close"]).round(2).reset_index(drop=True)
