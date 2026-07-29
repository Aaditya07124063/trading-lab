"""The first full run of the lab: data -> indicators -> signal -> time machine -> judge."""

from src.data_loader import load_csv
from src.indicators import add_ema
from src.signals import crossover_signal
from src.backtest import run_backtest
from src.metrics import report

df = load_csv("NIFTY_10Y.csv")
df = add_ema(df, 20)
df = add_ema(df, 50)
df = crossover_signal(df, "ema_20", "ema_50")
df, trades = run_backtest(df)
report(df, trades, name="EMA 20/50 crossover on NIFTY 50")