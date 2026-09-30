"""Reads any of our CSV files and returns one clean table:
columns = date, open, high, low, close, volume (oldest first)."""

import pandas as pd
from src.config import DATA_DIR


def find_file(filename):
    """Search data/ and its subfolders for the file."""
    matches = list(DATA_DIR.rglob(filename))
    if not matches:
        raise FileNotFoundError(f"{filename} not found anywhere inside {DATA_DIR}")
    return matches[0]


def load_csv(filename, sort=True):
    """sort=False keeps the file's raw row order (for data validation)."""
    path = find_file(filename)

    # Peek at the first line to detect which format this is
    first_line = open(path).readline()

    if first_line.startswith("Price,"):
        # Format A: Yahoo multi-header file (NIFTY_10Y.csv)
        df = pd.read_csv(path, skiprows=[1, 2])
        df = df.rename(columns={"Price": "date"})
        df.columns = [c.lower() for c in df.columns]

    elif "tick_volume" in first_line:
        # Format B: MetaTrader-style file (your gold + india CSVs)
        df = pd.read_csv(path)
        df = df.rename(columns={"Date": "date", "tick_volume": "volume"})

        if "XAUUSD" in filename.upper():
            # gold prices are stored x100 (172497 means $1,724.97)
            for col in ("open", "high", "low", "close"):
                df[col] = df[col] / 100.0
    else:
        # Format C: plain CSV with normal headers
        df = pd.read_csv(path)
        df.columns = [c.lower() for c in df.columns]

    # Dates: handles both "2012-11-14" and "15-05-2012 08:00"
    df["date"] = pd.to_datetime(df["date"], format="mixed", dayfirst=True)

    # Keep only the columns we need, in our standard order
    df = df[["date", "open", "high", "low", "close", "volume"]]

    # Safety cleaning: drop broken rows, sort oldest-first
    df = df.dropna(subset=["open", "high", "low", "close"])
    if sort:
        df = df.sort_values("date")
    df = df.reset_index(drop=True)
    return df