"""Judges a finished backtest: the honest numbers + the verdict."""

from src.config import CAPITAL


def report(df, trades, name="strategy"):
    final = df["equity"].iloc[-1]
    strat_ret = (final / CAPITAL - 1) * 100

    # the opponent: buy on day 1, sleep
    bh_curve = df["close"] / df["open"].iloc[0] * CAPITAL
    bh_ret = (bh_curve.iloc[-1] / CAPITAL - 1) * 100

    # worst fall (max drawdown) for both
    peak = df["equity"].cummax()
    max_dd = ((df["equity"] - peak) / peak).min() * 100
    bh_peak = bh_curve.cummax()
    bh_dd = ((bh_curve - bh_peak) / bh_peak).min() * 100

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

    print(f"===== {name} =====")
    print(f"Strategy return : {strat_ret:+8.1f}%   (final Rs {final:,.0f})")
    print(f"Buy & hold      : {bh_ret:+8.1f}%   <- the score to beat")
    print(f"Worst fall      : {max_dd:8.1f}%   (buy & hold fell {bh_dd:.1f}%)")
    print(f"Trades          : {len(closed):5d} closed, win rate {win_rate:.0f}%")
    print(f"VERDICT         : {verdict}")

    return {
        "name": name, "return_pct": round(strat_ret, 1),
        "bh_pct": round(bh_ret, 1), "margin": round(margin, 1),
        "max_dd": round(max_dd, 1), "bh_dd": round(bh_dd, 1),
        "trades": len(closed), "win_rate": round(win_rate),
        "final": round(final), "verdict": verdict,
    }