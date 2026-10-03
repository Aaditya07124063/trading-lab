"""One way to run a daily crossover experiment, shared by scripts and server,
so the same experiment always gets the same name (no duplicate board rows)."""

from src.access import research_load_clean, research_load_csv
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
              quiet=True, clean=False):
    """clean=True: raw minus reviewed exclusions (src/datasets.py)."""
    if kind not in ("ema", "sma"):
        raise ValueError(f"unknown indicator kind: {kind}")
    if fast >= slow:
        raise ValueError("fast period must be smaller than slow period")
    df = research_load_clean(file)[0] if clean else research_load_csv(file)   # cutoff 2026-09-30
    add = add_ema if kind == "ema" else add_sma
    df = add(add(df, fast), slow)
    df = crossover_signal(df, f"{kind}_{fast}", f"{kind}_{slow}")
    df, trades = run_backtest(df, stop_loss=stop_loss, trailing_stop=trailing_stop)
    name = experiment_name(file, kind, fast, slow, stop_loss, trailing_stop) + (" · clean" if clean else "")
    row = report(df, trades, name=name, quiet=quiet)
    row.update({"file": file, "kind": kind, "fast": fast, "slow": slow,
                "stop_loss": stop_loss or 0.0, "trailing_stop": trailing_stop or 0.0})
    return df, trades, row
