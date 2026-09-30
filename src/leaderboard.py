"""The research diary. Saving is always an explicit act - never a side
effect of merely running a backtest. One row per experiment name."""

import pandas as pd

from src.config import RESULTS_DIR

LEADERBOARD_FILE = RESULTS_DIR / "leaderboard.csv"

COLUMNS = ["name", "file", "kind", "fast", "slow", "stop_loss", "trailing_stop",
           "return_pct", "bh_pct", "margin", "cagr", "bh_cagr", "sharpe", "bh_sharpe",
           "max_dd", "bh_dd", "exposure_pct", "trades", "win_rate", "final", "verdict", "status"]


def load():
    if not LEADERBOARD_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(LEADERBOARD_FILE).reindex(columns=COLUMNS)


def save(rows):
    """Upsert result rows by name, keep the fixed schema, rank by margin."""
    new = pd.DataFrame(rows).reindex(columns=COLUMNS)
    old = load()
    board = pd.concat([old, new], ignore_index=True) if len(old) else new
    board = board.drop_duplicates(subset="name", keep="last")
    board = board.sort_values("margin", ascending=False).reset_index(drop=True)
    LEADERBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    board.to_csv(LEADERBOARD_FILE, index=False)
    return board
