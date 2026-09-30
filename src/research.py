"""One way to run a daily crossover experiment, shared by scripts and server,
so the same experiment always gets the same name (no duplicate board rows)."""

from src.data_loader import load_csv
from src.indicators import add_ema, add_sma
from src.signals import crossover_signal
from src.backtest import run_backtest
from src.metrics import report


def experiment_name(file, kind, fast, slow, stop_loss=None, trailing_stop=None):
    name = f"{kind.upper()} {fast}/{slow} · {file.replace('.csv', '')}"
    if stop_loss:
        name += f" · stop {stop_loss * 100:g}%"
    if trailing_stop:
        name += f" · trail {trailing_stop * 100:g}%"
    return name


def run_daily(file, kind="ema", fast=20, slow=50, stop_loss=None, trailing_stop=None,
              quiet=True):
    if kind not in ("ema", "sma"):
        raise ValueError(f"unknown indicator kind: {kind}")
    if fast >= slow:
        raise ValueError("fast period must be smaller than slow period")
    df = load_csv(file)
    add = add_ema if kind == "ema" else add_sma
    df = add(add(df, fast), slow)
    df = crossover_signal(df, f"{kind}_{fast}", f"{kind}_{slow}")
    df, trades = run_backtest(df, stop_loss=stop_loss, trailing_stop=trailing_stop)
    name = experiment_name(file, kind, fast, slow, stop_loss, trailing_stop)
    row = report(df, trades, name=name, quiet=quiet)
    row.update({"file": file, "kind": kind, "fast": fast, "slow": slow,
                "stop_loss": stop_loss or 0.0, "trailing_stop": trailing_stop or 0.0})
    return df, trades, row
