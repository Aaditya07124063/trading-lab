"""Fixed stop vs trailing stop vs no stop - let the lab judge all three."""

from src.data_loader import load_csv
from src.indicators import add_ema
from src.signals import crossover_signal
from src.backtest import run_backtest
from src.metrics import report


def prepare():
    df = load_csv("NIFTY_10Y.csv")
    df = add_ema(df, 20)
    df = add_ema(df, 50)
    df = crossover_signal(df, "ema_20", "ema_50")
    return df


for label, kwargs in [
    ("no stop", {}),
    ("5% fixed stop", {"stop_loss": 0.05}),
    ("5% trailing stop", {"trailing_stop": 0.05}),
    ("10% trailing stop", {"trailing_stop": 0.10}),
]:
    df, trades = run_backtest(prepare(), **kwargs)
    report(df, trades, name=f"EMA 20/50 NIFTY - {label}")
    fired = len([t for t in trades if t["reason"] == "stop"])
    print(f"stops fired: {fired}\n")