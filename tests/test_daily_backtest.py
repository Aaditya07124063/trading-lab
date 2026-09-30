"""Daily engine: timing, costs, and regression locks on published results."""

import pytest

from src.backtest import run_backtest
from src.config import CAPITAL, COST_PER_SIDE
from src.research import run_daily
from tests.conftest import make_daily


def test_signal_fills_at_next_open_not_same_bar():
    df = make_daily([100, 110, 120, 130])
    df["position"] = [1, 1, 1, 1]
    df, trades = run_backtest(df)
    assert trades[0]["entry_date"] == df["date"].iloc[1]
    assert trades[0]["entry"] == 110
    assert df["in_market"].tolist() == [0, 1, 1, 1]


def test_round_trip_pays_cost_both_sides():
    df = make_daily([100, 100, 100, 100])
    df["position"] = [1, 0, 0, 0]
    df, trades = run_backtest(df)
    assert df["equity"].iloc[-1] == pytest.approx(CAPITAL * (1 - COST_PER_SIDE) ** 2)
    assert trades[0]["exit_date"] == df["date"].iloc[2]


def test_future_prices_cannot_change_past_equity():
    a = make_daily([100, 101, 102, 103, 104, 105])
    b = make_daily([100, 101, 102, 103, 104, 999])
    for df in (a, b):
        df["position"] = [1, 1, 0, 1, 1, 1]
    ea = run_backtest(a)[0]["equity"].iloc[:-1].tolist()
    eb = run_backtest(b)[0]["equity"].iloc[:-1].tolist()
    assert ea == eb


def test_trailing_stop_exits_next_open_and_blocks_reentry():
    df = make_daily([100, 100, 120, 100, 100, 100], [100, 100, 120, 100, 100, 100])
    df["position"] = [1, 1, 1, 1, 1, 1]
    df, trades = run_backtest(df, trailing_stop=0.10)
    assert trades[0]["reason"] == "stop"
    assert trades[0]["exit_date"] == df["date"].iloc[4]    # close at bar 3 < 108 -> exit bar 4
    assert len(trades) == 1                                 # blocked until signal resets


# README / leaderboard numbers must not silently drift (static data files)
@pytest.mark.parametrize("file,kind,fast,slow,kw,ret,bh,dd,trades", [
    ("NIFTY_10Y.csv", "ema", 20, 50, {}, 184.8, 181.6, -15.1, 16),
    ("NIFTY_10Y.csv", "ema", 9, 21, {}, 116.9, 181.6, -18.2, 47),
    ("NIFTY_10Y.csv", "sma", 50, 200, {}, 34.4, 181.6, -42.6, 7),
    ("XAUUSDd1.csv", "sma", 50, 200, {}, 24.6, 14.2, -17.0, 7),
    ("XAUUSDd1.csv", "ema", 20, 50, {}, 3.1, 14.2, -26.0, 27),
])
def test_regression_published_results(file, kind, fast, slow, kw, ret, bh, dd, trades):
    r = run_daily(file, kind, fast, slow, **kw)[2]
    assert (r["return_pct"], r["bh_pct"], r["max_dd"], r["trades"]) == (ret, bh, dd, trades)


def test_bad_params_rejected():
    with pytest.raises(ValueError):
        run_daily("NIFTY_10Y.csv", "ema", 50, 20)
    with pytest.raises(ValueError):
        run_daily("NIFTY_10Y.csv", "wma", 20, 50)
