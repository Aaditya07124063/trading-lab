"""Every number a finished intraday backtest must report."""

import math

import pandas as pd

from src.metrics import cagr, max_drawdown

COST_KEYS = ["brokerage", "stt", "exchange", "sebi", "stamp", "gst"]


def daily_equity(equity):
    """Session-end equity, one value per trading day."""
    return equity.groupby(equity["date"].dt.date)["equity"].last()


def summarize(result, capital):
    t, eq = result["trades"], result["equity"]
    final = float(eq["equity"].iloc[-1]) if len(eq) else float(capital)
    days = daily_equity(eq) if len(eq) else pd.Series(dtype=float)
    rets = pd.concat([pd.Series([float(capital)]), days.reset_index(drop=True)]).pct_change().dropna()
    sharpe = (rets.mean() / rets.std() * math.sqrt(252)) if len(rets) > 1 and rets.std() > 0 else 0.0
    span = (eq["date"].iloc[-1] - eq["date"].iloc[0]).days + 1 if len(eq) else 0

    n = len(t)
    net = t["net_pnl"] if n else pd.Series(dtype=float)
    wins, losses = net[net > 0], net[net <= 0]
    costs = {k: float(t[k].sum()) if n else 0.0 for k in COST_KEYS}
    slippage = float(t["slippage"].sum()) if n else 0.0
    return {
        "strategy": result["strategy"],
        "initial_capital": float(capital), "final_capital": round(final, 2),
        "gross_pnl": round(float(t["gross_pnl"].sum()) if n else 0.0, 2),
        **{k: round(v, 2) for k, v in costs.items()},
        "total_charges": round(sum(costs.values()), 2),
        "total_slippage": round(slippage, 2),
        "total_costs": round(sum(costs.values()) + slippage, 2),
        "net_pnl": round(final - capital, 2),
        "return_pct": round((final / capital - 1) * 100, 2),
        "cagr": round(cagr(capital, final, span), 2),
        "sharpe": round(sharpe, 2),
        "max_dd": round(max_drawdown(pd.concat([pd.Series([float(capital)]), eq["equity"]])), 2)
                  if len(eq) else 0.0,
        "trades": n,
        "long_trades": int((t["side"] == "LONG").sum()) if n else 0,
        "short_trades": int((t["side"] == "SHORT").sum()) if n else 0,
        "win_rate": round(len(wins) / n * 100, 1) if n else 0.0,
        "profit_factor": round(wins.sum() / -losses.sum(), 2) if n and losses.sum() < 0 else None,
        "avg_trade": round(net.mean(), 2) if n else 0.0,
        "avg_win": round(wins.mean(), 2) if len(wins) else 0.0,
        "avg_loss": round(losses.mean(), 2) if len(losses) else 0.0,
        "largest_win": round(net.max(), 2) if n else 0.0,
        "largest_loss": round(net.min(), 2) if n else 0.0,
        "exposure_pct": round(float((eq["position"] != 0).mean()) * 100, 1) if len(eq) else 0.0,
        "sessions": int(len(days)),
        "skipped_sessions": len(result["skipped_sessions"]),
        "start": str(eq["date"].iloc[0]) if len(eq) else None,
        "end": str(eq["date"].iloc[-1]) if len(eq) else None,
    }


def compare(strategy_summary, bench_summary):
    s, b = strategy_summary, bench_summary
    return {"benchmark_return_pct": b["return_pct"],
            "strategy_return_pct": s["return_pct"],
            "strategy_minus_benchmark": round(s["return_pct"] - b["return_pct"], 2),
            "benchmark_max_dd": b["max_dd"], "benchmark_sharpe": b["sharpe"],
            "benchmark_costs": b["total_costs"]}
