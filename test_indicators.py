"""Add EMAs to real NIFTY data and read today's live signal."""

from src.data_loader import load_csv
from src.indicators import add_ema, add_sma

df = load_csv("NIFTY_10Y.csv")
df = add_ema(df, 20)
df = add_ema(df, 50)
df = add_sma(df, 200)

# Show the last 3 days with the new columns
print(df[["date", "close", "ema_20", "ema_50", "sma_200"]].tail(3).to_string(index=False))

# The magic moment: what does the strategy say TODAY?
fast_above = df["ema_20"].iloc[-1] > df["ema_50"].iloc[-1]
print()
print("Today EMA-20 is", "ABOVE" if fast_above else "BELOW", "EMA-50")
print("EMA 20/50 crossover says:", "BE IN the market" if fast_above else "STAY OUT")