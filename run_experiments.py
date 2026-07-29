"""Run many experiments in one go and build the leaderboard.
This is the research loop: idea -> test -> verdict -> next idea."""

import pandas as pd

from src.data_loader import load_csv
from src.indicators import add_ema, add_sma
from src.signals import crossover_signal
from src.backtest import run_backtest
from src.metrics import report
from src.config import RESULTS_DIR

# (file to test on, indicator type, fast period, slow period)
EXPERIMENTS = [
    ("NIFTY_10Y.csv",  "ema", 20, 50),
    ("NIFTY_10Y.csv",  "ema", 9, 21),
    ("NIFTY_10Y.csv",  "sma", 50, 200),
    ("XAUUSDd1.csv",   "ema", 20, 50),
    ("XAUUSDd1.csv",   "sma", 50, 200),
    ("RELIANCEd1.csv", "ema", 20, 50),
]

rows = []
for filename, kind, fast, slow in EXPERIMENTS:
    df = load_csv(filename)
    add = add_ema if kind == "ema" else add_sma
    df = add(df, fast)
    df = add(df, slow)
    df = crossover_signal(df, f"{kind}_{fast}", f"{kind}_{slow}")
    df, trades = run_backtest(df)

    market = filename.replace("d1.csv", "").replace(".csv", "")
    rows.append(report(df, trades, name=f"{kind.upper()} {fast}/{slow} on {market}"))
    print()

# rank by margin (the only score that matters) and save
board = pd.DataFrame(rows).sort_values("margin", ascending=False)
out_file = RESULTS_DIR / "leaderboard.csv"
board.to_csv(out_file, index=False)

print("=" * 60)
print(board[["name", "return_pct", "bh_pct", "margin", "verdict"]].to_string(index=False))
print(f"\nLeaderboard saved -> {out_file}")