"""Judges a finished backtest: the honest numbers + the verdict."""

import math

from src.config import CAPITAL


def cagr(start_value, end_value, days):
    """Compound annual growth rate in %, from calendar days elapsed."""
    if days <= 0 or start_value <= 0 or end_value <= 0:
        return 0.0
    return ((end_value / start_value) ** (365.25 / days) - 1) * 100


def sharpe(values, periods_per_year=252):
    """Annualised Sharpe of per-bar returns (risk-free = 0). 0 if flat."""
    rets = values.pct_change().dropna()
    sd = rets.std()
    if len(rets) < 2 or not sd or math.isnan(sd):
        return 0.0
    return rets.mean() / sd * math.sqrt(periods_per_year)


def max_drawdown(values):
    """Worst peak-to-trough fall in %, as a negative number."""
    peak = values.cummax()
    return ((values - peak) / peak).min() * 100


def report(df, trades, name="strategy", quiet=False):
    final = df["equity"].iloc[-1]
    strat_ret = (final / CAPITAL - 1) * 100

    # the opponent: buy on day 1, sleep
    bh_curve = df["close"] / df["open"].iloc[0] * CAPITAL
    bh_ret = (bh_curve.iloc[-1] / CAPITAL - 1) * 100

    # worst fall (max drawdown) for both
    max_dd = max_drawdown(df["equity"])
    bh_dd = max_drawdown(bh_curve)

    days = (df["date"].iloc[-1] - df["date"].iloc[0]).days
    strat_cagr = cagr(CAPITAL, final, days)
    bh_cagr = cagr(CAPITAL, bh_curve.iloc[-1], days)
    strat_sharpe = sharpe(df["equity"])
    bh_sharpe = sharpe(bh_curve)
    exposure = df["in_market"].mean() * 100 if "in_market" in df else float("nan")

    closed = [t for t in trades if t["exit"] is not None]
    wins = sum(1 for t in closed if t["pnl_pct"] > 0)
    win_rate = 100 * wins / len(closed) if closed else 0

    margin = strat_ret - bh_ret
    if margin > 10:
        verdict = "BEATS buy & hold"
    elif margin > 0:
        verdict = "WEAK EDGE - real but thin, verify before trusting"
    else:
        verdict = "LOSES to buy & hold - bin it"

    if not quiet:
        print(f"===== {name} =====")
        print(f"Strategy return : {strat_ret:+8.1f}%   (final Rs {final:,.0f})")
        print(f"Buy & hold      : {bh_ret:+8.1f}%   <- the score to beat")
        print(f"CAGR            : {strat_cagr:+8.1f}%   (buy & hold {bh_cagr:+.1f}%)")
        print(f"Sharpe          : {strat_sharpe:8.2f}    (buy & hold {bh_sharpe:.2f})")
        print(f"Worst fall      : {max_dd:8.1f}%   (buy & hold fell {bh_dd:.1f}%)")
        print(f"In market       : {exposure:8.0f}%   of bars")
        print(f"Trades          : {len(closed):5d} closed, win rate {win_rate:.0f}%")
        print(f"VERDICT         : {verdict}")

    return {
        "name": name, "return_pct": round(strat_ret, 1),
        "bh_pct": round(bh_ret, 1), "margin": round(margin, 1),
        "max_dd": round(max_dd, 1), "bh_dd": round(bh_dd, 1),
        "cagr": round(strat_cagr, 2), "bh_cagr": round(bh_cagr, 2),
        "sharpe": round(strat_sharpe, 2), "bh_sharpe": round(bh_sharpe, 2),
        "exposure_pct": round(exposure, 1),
        "trades": len(closed), "win_rate": round(win_rate),
        "final": round(final), "verdict": verdict,
    }
