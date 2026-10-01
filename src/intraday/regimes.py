"""ORB v1 regime labels - EXPLORATORY / DESCRIPTIVE only (approved framing).

Market regimes from the NIFTY 50 index DAILY closes, known before the session:
  vol regime(t)   = HIGH if vol20(t) > median of all vol20 values up to and
                    including t (expanding), else LOW; vol20(t) = sample sd of
                    the 20 daily close-to-close returns ending on session t-1
  trend regime(t) = UP if close(t-1) / close(t-21) - 1 > 0, else DOWN
Nothing from session t or later enters the label for session t.
"""

import numpy as np
import pandas as pd


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
