import pandas as pd

from src.indicators import add_ema, add_sma


def test_sma_is_plain_average_and_warmup_is_nan():
    df = add_sma(pd.DataFrame({"close": [1.0, 2, 3, 4, 5]}), 3)
    assert df["sma_3"].isna().sum() == 2
    assert df["sma_3"].tolist()[2:] == [2.0, 3.0, 4.0]


def test_ema_standard_formula():
    df = add_ema(pd.DataFrame({"close": [10.0, 20.0]}), 3)   # alpha = 2/(3+1) = 0.5
    assert df["ema_3"].tolist() == [10.0, 15.0]


def test_ema_uses_no_future_values():
    a = add_ema(pd.DataFrame({"close": [1.0, 2, 3, 4, 5]}), 3)["ema_3"]
    b = add_ema(pd.DataFrame({"close": [1.0, 2, 3, 4, 500]}), 3)["ema_3"]
    assert a.iloc[:4].tolist() == b.iloc[:4].tolist()
