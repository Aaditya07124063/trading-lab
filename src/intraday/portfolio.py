"""ORB v1 portfolio aggregation and random baselines (approved 2026-10-01).

PORTFOLIO DAILY RETURN (the primary statistic's unit):

    R_t = sum_i NetPnL_{i,t} / (N * K)

  N = 50  - size of the frozen NIFTY 50 universe (fixed; never the number of
            stocks that happened to trade or have data)
  K = Rs 1,00,000 - fixed notional per stock per session; every trade is sized
            on K (integer shares, entry fill + entry charges <= K, no leverage);
            P&L is NOT reinvested (EngineConfig.sizing = "fixed_notional")
  NetPnL_{i,t} - rupee P&L of stock i's trade on session t after brokerage,
            STT, exchange, SEBI, stamp, GST and slippage; 0 if stock i did not
            trade (no breakout, non-tradable session, no data, or entry
            refused). Unused capital stays in cash at 0% (no interest).
  t ranges over every portfolio session in the evaluation window, including
            sessions on which no stock traded (R_t = 0).

So R_t is the return on total fixed portfolio capital (N*K), NOT the average
return of the stocks that traded.
"""

import json

import numpy as np
import pandas as pd

from src.config import BASE_DIR

UNIVERSE_FILE = BASE_DIR / "data" / "metadata" / "universe" / "NIFTY50_frozen_20261001.json"
COST_KEYS = ["brokerage", "stt", "exchange", "sebi", "stamp", "gst"]


def frozen_universe():
    return [c["symbol"] for c in json.load(open(UNIVERSE_FILE))["constituents"]]


def portfolio_daily(results, sessions, n_universe, capital):
    """results: {symbol: engine result dict}. sessions: the evaluation calendar.
    Returns one row per session with rupee sums and the portfolio return."""
    idx = pd.Index(sorted({str(s) for s in sessions}), name="session")
    cols = ["gross_pnl", "slippage", "total_charges", "net_pnl"] + COST_KEYS
    agg = pd.DataFrame(0.0, index=idx, columns=cols)
    agg["n_trades"] = 0
    agg["n_non_tradable"] = 0
    for sym, r in results.items():
        t = r["trades"]
        if len(t):
            g = t.groupby("session")[cols].sum()
            g = g[g.index.isin(idx)]
            agg.loc[g.index, cols] += g
            n = t.groupby("session").size()
            n = n[n.index.isin(idx)]
            agg.loc[n.index, "n_trades"] += n
        for s, _ in r.get("missing_bars", []):
            if s in idx:
                agg.loc[s, "n_non_tradable"] += 1
    denom = float(n_universe) * float(capital)
    agg["net_ret"] = agg["net_pnl"] / denom
    agg["gross_ret"] = agg["gross_pnl"] / denom
    return agg


# --------------------------------------------------- vectorised trade P&L

def _charges(costs, side_is_buy, turnover):
    """Vectorised CostModel.charges (same formulas). side_is_buy: bool array."""
    flat = np.full_like(turnover, costs.brokerage_flat, dtype=float)
    pct = costs.brokerage_pct * turnover
    brokerage = {"flat": flat, "pct": pct, "min": np.minimum(flat, pct)}[costs.brokerage_mode]
    stt = np.where(side_is_buy, 0.0, costs.stt_sell_pct * turnover)
    exchange = costs.exchange_pct * turnover
    sebi = costs.sebi_pct * turnover
    stamp = np.where(side_is_buy, costs.stamp_buy_pct * turnover, 0.0)
    gst = costs.gst_pct * (brokerage + exchange + sebi)
    return brokerage + stt + exchange + sebi + stamp + gst


def trade_net_pnl(entry_raw, exit_raw, direction, costs, capital):
    """Net rupee P&L of trades with the engine's exact fill, sizing and cost
    rules (fixed notional `capital`). Arrays broadcast; direction is +1/-1."""
    entry_raw, exit_raw, d = np.broadcast_arrays(np.asarray(entry_raw, float),
                                                 np.asarray(exit_raw, float),
                                                 np.asarray(direction, float))
    s = costs.slippage_bps / 10_000
    f_in = entry_raw * (1 + d * s)                     # long entry = buy (pays up)
    f_out = exit_raw * (1 - d * s)                     # long exit = sell (receives less)
    buy_in = d > 0
    qty = np.floor(capital / f_in)
    for _ in range(5):                                 # same rule as Book.open
        over = (qty > 0) & (qty * f_in + _charges(costs, buy_in, qty * f_in) > capital)
        if not over.any():
            break
        qty = np.where(over, qty - 1, qty)
    ch = _charges(costs, buy_in, qty * f_in) + _charges(costs, ~buy_in, qty * f_out)
    return np.where(qty > 0, d * qty * (f_out - f_in) - ch, 0.0)


# ------------------------------------------------------------- baselines

def sign_flip_baseline(trades, n_sessions, n_universe, capital, b, seed, chunk=2000):
    """Baseline E (random direction at the ORB's own entry/exit times).
    Each actual ORB trade keeps its stock, session, entry and exit times and
    quantity; its direction is replaced by an independent fair coin. Under H0
    (direction carries no information) the GROSS P&L of trade j is
    s_j * gross_j with s_j = +/-1; costs (charges + slippage) are NOT sign
    flipped and are charged as actually incurred. Statistic: mean daily
    portfolio net return over all n_sessions. Returns B draws."""
    g = trades["gross_pnl"].to_numpy(float)
    c = (trades["slippage"] + trades["total_charges"]).to_numpy(float)
    rng = np.random.default_rng(seed)
    denom = float(n_universe) * float(capital) * n_sessions
    out = np.empty(b)
    for k in range(0, b, chunk):
        m = min(chunk, b - k)
        s = rng.choice(np.array([-1.0, 1.0]), size=(m, len(g)))
        out[k:k + m] = (s * g - c).sum(axis=1) / denom
    return out


def random_entry_baseline(cands, exit_raw, costs, n_sessions, n_universe, capital, b, seed,
                          chunk=500):
    """Baseline D (random entry time AND random direction).
    For EVERY actual ORB trade (same stock, same session, same number of trades)
    draw an entry bar uniformly from that session's ORB-FEASIBLE entry bars
    (bar opens from 10:00 - the earliest time an ORB entry can fill, after a
    signal on the 09:45 bar's close - through the entry cutoff 14:30 inclusive:
    19 bars on complete sessions) and a fair-coin
    direction; enter at that bar's OPEN, exit at the ORB v1 exit (15:00 OPEN),
    same fixed-notional sizing, slippage and charges as the strategy.
    cands: (J, M) candidate entry opens per trade; exit_raw: (J,) exit opens.
    Returns B draws of the mean daily portfolio net return over n_sessions."""
    cands = np.asarray(cands, float)
    exit_raw = np.asarray(exit_raw, float)
    j, m_c = cands.shape
    rng = np.random.default_rng(seed)
    denom = float(n_universe) * float(capital) * n_sessions
    out = np.empty(b)
    rows = np.arange(j)
    for k in range(0, b, chunk):
        m = min(chunk, b - k)
        pick = rng.integers(0, m_c, size=(m, j))
        d = rng.choice(np.array([-1.0, 1.0]), size=(m, j))
        entry = cands[rows[None, :], pick]
        out[k:k + m] = trade_net_pnl(entry, exit_raw[None, :], d, costs, capital).sum(axis=1) / denom
    return out


def entry_candidates(df, trades, first_entry="10:00", entry_cutoff="14:30", exit_time="15:00"):
    """For each trade (row of `trades`), the opens of its session's eligible
    entry bars and the exit-bar open. Sessions are complete (engine rule)."""
    by = {s: d.set_index("time") for s, d in df.groupby(df["session"].astype(str))}
    cands, exits = [], []
    for s in trades["session"]:
        d = by[s]
        el = d[(d.index >= first_entry) & (d.index <= entry_cutoff)]["open"].to_numpy(float)
        cands.append(el)
        exits.append(float(d.loc[exit_time, "open"]))
    width = {len(c) for c in cands}
    if len(width) > 1:
        raise ValueError(f"unequal candidate counts {width} - incomplete session reached baseline D")
    return np.vstack(cands) if cands else np.empty((0, 0)), np.array(exits)
