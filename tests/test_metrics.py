import math

import pandas as pd
import pytest

from src.metrics import cagr, sharpe, max_drawdown, report
from src.config import CAPITAL
from tests.conftest import make_daily


def test_cagr_doubling_in_one_year():
    assert cagr(100, 200, 365.25) == pytest.approx(100.0)
    assert cagr(100, 100, 0) == 0.0


def test_sharpe_known_value_and_flat():
    s = pd.Series([100, 110, 99, 108.9])            # +10%, -10%, +10%
    rets = s.pct_change().dropna()
    assert sharpe(s) == pytest.approx(rets.mean() / rets.std() * math.sqrt(252))
    assert sharpe(pd.Series([100.0] * 10)) == 0.0


def test_max_drawdown():
    assert max_drawdown(pd.Series([100, 120, 90, 130])) == pytest.approx(-25.0)


def test_report_fields_and_exposure():
    df = make_daily([100, 100, 110, 121])
    df["equity"] = [CAPITAL, CAPITAL, CAPITAL * 1.1, CAPITAL * 1.21]
    df["in_market"] = [0, 1, 1, 1]
    r = report(df, [], quiet=True)
    for k in ["return_pct", "bh_pct", "margin", "max_dd", "bh_dd", "cagr", "bh_cagr",
              "sharpe", "bh_sharpe", "exposure_pct", "trades", "win_rate", "final", "verdict"]:
        assert k in r
    assert r["exposure_pct"] == 75.0
    assert r["return_pct"] == 21.0
