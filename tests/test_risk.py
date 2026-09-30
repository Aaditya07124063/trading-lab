"""Stops on the real NIFTY run - locks the README finding that a 5% trailing
stop halves return and does not improve drawdown."""

from src.research import run_daily


def test_stops_fire_and_trailing_5pct_finding_holds():
    base = run_daily("NIFTY_10Y.csv")[2]
    _, trades, trail = run_daily("NIFTY_10Y.csv", trailing_stop=0.05)
    assert any(t["reason"] == "stop" for t in trades)
    assert trail["return_pct"] < base["return_pct"] * 0.6
    assert trail["max_dd"] <= base["max_dd"]
    assert "trail 5%" in trail["name"]
