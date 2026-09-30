"""Intraday time machine. Separate from the daily engine on purpose.

Rules enforced HERE (not trusted to strategies):
  * a strategy only ever receives today's bars up to and including the
    bar that just closed - it physically cannot see the future;
  * a signal at bar N's close fills at bar N+1's OPEN, same session only;
  * no new entry fills after `entry_cutoff`; at most `max_entries_per_day`;
  * every position is squared off at the CLOSE of the `square_off` bar
    (15:15). Sessions without that bar are NOT traded (and are reported),
    because you cannot know intraday that the data will end early;
  * nothing is ever carried overnight.
"""

import math
from dataclasses import dataclass, asdict

import pandas as pd

from src.config import CAPITAL


@dataclass
class EngineConfig:
    capital: float = CAPITAL
    position_fraction: float = 1.0    # share of current equity per trade (1.0 = no leverage)
    square_off: str = "15:15"         # square off at this bar's CLOSE
    entry_cutoff: str = "14:30"       # no entry FILLS after this bar-open time
    max_entries_per_day: int = 1
    allow_short: bool = True


class Book:
    """Cash + at most one open position. All costs flow through here."""

    def __init__(self, capital, costs):
        self.cash = float(capital)
        self.costs = costs
        self.pos = None               # dict while a position is open
        self.trades = []

    def equity(self, mark):
        if not self.pos:
            return self.cash
        p = self.pos
        return self.cash + p["side"] * p["qty"] * (mark - p["entry_fill"])

    def open(self, time, raw, side, fraction):
        """side: +1 long, -1 short. Returns False if capital buys < 1 share."""
        order_side = "buy" if side > 0 else "sell"
        fill = self.costs.slip(raw, order_side)
        qty = math.floor(self.cash * fraction / fill)
        while qty > 0:
            ch = self.costs.charges(order_side, qty * fill)
            if qty * fill + sum(ch.values()) <= self.cash * fraction:
                break
            qty -= 1
        if qty <= 0:
            return False
        self.cash -= sum(ch.values())
        self.pos = {"side": side, "qty": qty, "entry_time": time, "entry_raw": raw,
                    "entry_fill": fill, "entry_charges": ch}
        return True

    def close(self, time, raw, reason):
        p = self.pos
        order_side = "sell" if p["side"] > 0 else "buy"
        fill = self.costs.slip(raw, order_side)
        ch = self.costs.charges(order_side, p["qty"] * fill)
        self.cash += p["side"] * p["qty"] * (fill - p["entry_fill"]) - sum(ch.values())
        charges = {k: p["entry_charges"][k] + ch[k] for k in ch}
        gross = p["side"] * p["qty"] * (raw - p["entry_raw"])
        slippage = p["qty"] * (abs(p["entry_fill"] - p["entry_raw"]) + abs(fill - raw))
        net = gross - slippage - sum(charges.values())
        self.trades.append({
            "session": str(pd.Timestamp(time).date()),
            "side": "LONG" if p["side"] > 0 else "SHORT", "qty": p["qty"],
            "entry_time": str(p["entry_time"]), "entry_price": p["entry_raw"],
            "entry_fill": round(p["entry_fill"], 4),
            "exit_time": str(time), "exit_price": raw, "exit_fill": round(fill, 4),
            "reason": reason, "gross_pnl": gross, "slippage": slippage,
            **charges, "total_charges": sum(charges.values()), "net_pnl": net,
            "net_pct": net / (p["qty"] * p["entry_raw"]) * 100,
        })
        self.pos = None


def _tradable_sessions(df, square_off):
    has_sq = df.groupby("session")["time"].apply(lambda t: (t == square_off).any())
    return set(has_sq[has_sq].index), sorted(str(s) for s in has_sq[~has_sq].index)


def run_intraday(df, strategy, costs, cfg=None):
    """df: output of load_intraday (sorted, with session/time columns).
    Returns dict with trades, equity (per bar), skipped sessions, config."""
    cfg = cfg or EngineConfig()
    book = Book(cfg.capital, costs)
    tradable, skipped = _tradable_sessions(df, cfg.square_off)
    curve = []

    for session, day in df.groupby("session", sort=True):
        if session not in tradable:
            continue
        day = day[day["time"] <= cfg.square_off]
        strategy.start_session(session)
        pending, entries = None, 0

        for i in range(len(day)):
            bar = day.iloc[i]

            # 1) fill last bar's decision at THIS bar's open
            if pending is not None:
                target, pending = pending, None
                pos = book.pos["side"] if book.pos else 0
                if pos and target != pos:
                    book.close(bar["date"], bar["open"], "signal")
                    pos = 0
                if target and not pos:
                    if bar["time"] > cfg.entry_cutoff or entries >= cfg.max_entries_per_day:
                        pass                                   # entry refused
                    elif book.open(bar["date"], bar["open"], target, cfg.position_fraction):
                        entries += 1

            # 2) square-off at the 15:15 close - nothing survives the session
            if bar["time"] == cfg.square_off:
                if book.pos:
                    book.close(bar["date"], bar["close"], "square_off")
                curve.append((bar["date"], book.equity(bar["close"]), 0))
                break

            curve.append((bar["date"], book.equity(bar["close"]),
                          book.pos["side"] if book.pos else 0))

            # 3) strategy sees ONLY bars up to now -> order for next bar's open
            pos = book.pos["side"] if book.pos else 0
            target = strategy.on_bar(day.iloc[:i + 1], pos)
            if target is not None:
                if target not in (-1, 0, 1):
                    raise ValueError(f"strategy returned {target}; must be -1, 0, 1 or None")
                if target == -1 and not cfg.allow_short:
                    raise ValueError("strategy wants to short but allow_short=False")
                if target != pos:
                    pending = target

        assert book.pos is None, f"position left open overnight on {session}"

    equity = pd.DataFrame(curve, columns=["date", "equity", "position"])
    return {"trades": pd.DataFrame(book.trades), "equity": equity,
            "skipped_sessions": skipped, "config": asdict(cfg), "costs": costs.describe(),
            "strategy": strategy.name}


def run_open_to_close_benchmark(df, costs, cfg=None):
    """BUY every session at the first bar's open, SELL at the square-off bar's
    close. Same sessions, sizing and costs as the strategy."""
    cfg = cfg or EngineConfig()
    book = Book(cfg.capital, costs)
    tradable, skipped = _tradable_sessions(df, cfg.square_off)
    curve = []
    for session, day in df.groupby("session", sort=True):
        if session not in tradable:
            continue
        day = day[day["time"] <= cfg.square_off]
        first, last = day.iloc[0], day.iloc[-1]
        book.open(first["date"], first["open"], +1, cfg.position_fraction)
        for _, bar in day.iloc[:-1].iterrows():
            curve.append((bar["date"], book.equity(bar["close"]), 1 if book.pos else 0))
        if book.pos:
            book.close(last["date"], last["close"], "square_off")
        curve.append((last["date"], book.equity(last["close"]), 0))
    return {"trades": pd.DataFrame(book.trades),
            "equity": pd.DataFrame(curve, columns=["date", "equity", "position"]),
            "skipped_sessions": skipped, "config": asdict(cfg), "costs": costs.describe(),
            "strategy": "open-to-close benchmark"}
