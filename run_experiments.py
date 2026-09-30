"""Run many experiments in one go and save them to the leaderboard.
This is the research loop: idea -> test -> verdict -> next idea."""

from src.research import run_daily
from src import leaderboard

# (file to test on, indicator type, fast period, slow period)
EXPERIMENTS = [
    ("NIFTY_10Y.csv",  "ema", 20, 50),
    ("NIFTY_10Y.csv",  "ema", 9, 21),
    ("NIFTY_10Y.csv",  "sma", 50, 200),
    ("XAUUSDd1.csv",   "ema", 20, 50),
    ("XAUUSDd1.csv",   "sma", 50, 200),
    ("RELIANCEd1.csv", "ema", 20, 50),
]

if __name__ == "__main__":
    rows = []
    for filename, kind, fast, slow in EXPERIMENTS:
        _, _, row = run_daily(filename, kind, fast, slow, quiet=False)
        rows.append(row)
        print()

    # upsert by name (the only score that matters is margin) and save
    board = leaderboard.save(rows)
    print("=" * 60)
    print(board[["name", "return_pct", "bh_pct", "margin", "sharpe", "verdict"]].to_string(index=False))
    print(f"\nLeaderboard saved -> {leaderboard.LEADERBOARD_FILE}")
