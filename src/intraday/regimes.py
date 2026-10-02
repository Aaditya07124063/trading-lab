"""ORB v1 regime labels - EXPLORATORY / DESCRIPTIVE only (approved framing).

Market regimes from the NIFTY 50 index DAILY closes, known before the session:
  vol regime(t)   = HIGH if vol20(t) > median of all vol20 values up to and
                    including t (expanding), else LOW; vol20(t) = sample sd of
                    the 20 daily close-to-close returns ending on session t-1
  trend regime(t) = UP if close(t-1) / close(t-21) - 1 > 0, else DOWN
Nothing from session t or later enters the label for session t.
"""

import csv
import hashlib
import io
import urllib.request

import numpy as np
import pandas as pd

from src.config import BASE_DIR


def regime_labels(daily_close):
    """daily_close: Series indexed by date (sorted). Returns DataFrame with
    vol20, vol_regime, trend20, trend_regime for every date."""
    c = daily_close.sort_index().astype(float)
    r = c.pct_change()
    vol20 = r.rolling(20).std().shift(1)                  # returns up to t-1 only
    med = vol20.expanding().median()
    trend20 = (c.shift(1) / c.shift(21) - 1)
    out = pd.DataFrame({"vol20": vol20, "trend20": trend20})
    out["vol_regime"] = np.where(vol20.isna(), None, np.where(vol20 > med, "HIGH", "LOW"))
    out["trend_regime"] = np.where(trend20.isna(), None, np.where(trend20 > 0, "UP", "DOWN"))
    return out


# ---------------- official NSE NIFTY 50 daily close (approved regime source)

HISTORY = BASE_DIR / "docs" / "evidence" / "nse_index" / "nifty50_official_close_2026.csv"
RAW = BASE_DIR / "data" / "raw" / "nse_index"
URL = "https://nsearchives.nseindia.com/content/indices/ind_close_all_{d}.csv"


def official_close(session):
    """(close, sha256) of NIFTY 50 from NSE's ind_close_all_DDMMYYYY.csv (cached raw)."""
    name = f"ind_close_all_{session[8:10]}{session[5:7]}{session[:4]}.csv"
    f = RAW / name
    if not f.exists():
        req = urllib.request.Request(URL.format(d=name[14:22]), headers={"User-Agent": "Mozilla/5.0"})
        blob = urllib.request.urlopen(req, timeout=30).read()
        RAW.mkdir(parents=True, exist_ok=True)
        f.write_bytes(blob)
    blob = f.read_bytes()
    row = [r for r in csv.reader(io.StringIO(blob.decode())) if r and r[0].strip().lower() == "nifty 50"]
    return float(row[0][5]), hashlib.sha256(blob).hexdigest()


def official_closes(sessions):
    """Stored pre-holdout history (2026-01-01..2026-09-30 standard sessions) plus
    the official close of every later session in `sessions`. Any unavailable
    file raises -> caller reports regimes as NOT RUN (no substitute source)."""
    hist = pd.read_csv(HISTORY)
    s = pd.Series(hist["close"].to_numpy(), index=pd.to_datetime(hist["date"]))
    later = [x for x in sessions if x > hist["date"].iloc[-1]]
    sha = {}
    for x in later:
        s.loc[pd.Timestamp(x)], sha[x] = official_close(x)
    return s.sort_index(), sha
