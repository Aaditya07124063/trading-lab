import pandas as pd
import pytest


def make_daily(opens, closes=None, start="2024-01-01"):
    """Synthetic daily candles. closes default to opens."""
    closes = closes if closes is not None else opens
    n = len(opens)
    return pd.DataFrame({
        "date": pd.bdate_range(start, periods=n),
        "open": [float(x) for x in opens], "high": [float(max(o, c)) for o, c in zip(opens, closes)],
        "low": [float(min(o, c)) for o, c in zip(opens, closes)],
        "close": [float(x) for x in closes], "volume": [0] * n,
    })


@pytest.fixture
def tmp_board(tmp_path, monkeypatch):
    from src import leaderboard
    f = tmp_path / "leaderboard.csv"
    monkeypatch.setattr(leaderboard, "LEADERBOARD_FILE", f)
    return f
