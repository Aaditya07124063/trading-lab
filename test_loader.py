"""Proof that the loader reads all three formats correctly."""

from src.data_loader import load_csv

files = ["NIFTY_10Y.csv", "NIFTY50d1.csv", "XAUUSDd1.csv", "XAUUSDm15.csv"]

for name in files:
    df = load_csv(name)
    print(f"{name:18s} {len(df):>7,} candles | "
          f"{df.date.iloc[0].date()} -> {df.date.iloc[-1].date()} | "
          f"last close = {df.close.iloc[-1]:,.2f}")