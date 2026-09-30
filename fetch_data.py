"""The lab feeds itself: downloads fresh Indian market data from Yahoo
straight into data/india/. Run me anytime to refresh everything.
Add any stock to SYMBOLS and run again."""

import pandas as pd
import yfinance as yf

from src.config import DATA_DIR, YAHOO_SYMBOLS

OUT = DATA_DIR / "india"

SYMBOLS = YAHOO_SYMBOLS      # add more in src/config.py

for name, ticker in SYMBOLS.items():
    df = yf.Ticker(ticker).history(period="max", interval="1d", auto_adjust=False)
    if df is None or df.empty:
        print(f"{name}: nothing returned, skipped")
        continue
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)

    out = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    out.columns = ["open", "high", "low", "close", "tick_volume"]
    out = out.dropna(subset=["open", "close"]).round(2)
    out["tick_volume"] = out["tick_volume"].fillna(0).astype("int64")
    out.index = out.index.strftime("%Y-%m-%d")
    out.index.name = "Date"

    out.to_csv(OUT / f"{name}d1.csv")
    print(f"{name}d1.csv  {len(out):,} candles  (up to {out.index[-1]})")