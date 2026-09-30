"""The loader must turn all three CSV dialects into one clean format."""

import pytest

from src.data_loader import load_csv

COLS = ["date", "open", "high", "low", "close", "volume"]


@pytest.mark.parametrize("name", ["NIFTY_10Y.csv", "NIFTY50d1.csv", "XAUUSDd1.csv", "XAUUSDm15.csv"])
def test_standard_format(name):
    df = load_csv(name)
    assert list(df.columns) == COLS
    assert len(df) > 100
    assert df["date"].is_monotonic_increasing
    assert not df[["open", "high", "low", "close"]].isna().any().any()


def test_gold_is_rescaled_from_x100():
    df = load_csv("XAUUSDd1.csv")
    assert 500 < df["close"].median() < 5000      # dollars, not x100 integers


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_csv("NOPE.csv")
