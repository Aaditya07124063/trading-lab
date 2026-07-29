"""Indicators: new columns calculated from price history.
Each function takes the table, adds ONE column, returns the table."""


def add_sma(df, period):
    """Simple moving average: plain average of the last <period> closes."""
    df[f"sma_{period}"] = df["close"].rolling(period).mean()
    return df


def add_ema(df, period):
    """Exponential moving average: recent closes count more.
    adjust=False = the standard formula every trading book uses."""
    df[f"ema_{period}"] = df["close"].ewm(span=period, adjust=False).mean()
    return df