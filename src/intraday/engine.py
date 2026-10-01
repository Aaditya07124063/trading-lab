"""Intraday time machine. Separate from the daily engine on purpose.

Rules enforced HERE (not trusted to strategies):
  * a strategy only ever receives today's bars up to and including the
    bar that just closed - it physically cannot see the future;
  * a signal at bar N's close fills at bar N+1's OPEN, same session only;
  * no new entry fills after `entry_cutoff`; at most `max_entries_per_day`;
  * nothing is ever carried overnight.

Exit convention (ORB v1, approved 2026-10-01, "X2"): every position is squared
off at the OPEN of the 15:00 bar (15:00-15:15 IST). Nothing inside that bar
(high/low/close) and nothing after it (the 15:15 bar, which since NSE's
closing auction of 2026-08-03 prints the auction price) is used. A
stock-session is tradable only if EVERY bar from the session open up to and
including the exit bar is present (`require_complete_session`); otherwise it
is not traded and is reported with the missing bar times. No price is ever
forward-filled or interpolated.

`EngineConfig.legacy_v0()` reproduces the pre-2026-10-01 behaviour (square
off at the CLOSE of the 15:15 bar; only the 15:15 bar required) so that
LEGACY-014/015 remain reproducible. It is NOT the ORB v1 rule.
"""

import math
from dataclasses import dataclass, asdict

import pandas as pd

from src.config import CAPITAL


@dataclass
class EngineConfig:
    capital: float = CAPITAL
    position_fraction: float = 1.0    # share of capital per trade (1.0 = no leverage)
    square_off: str = "15:00"         # exit bar (bar-START time, IST)
    square_off_price: str = "open"    # "open" (ORB v1 / X2) or "close" (legacy only)
    entry_cutoff: str = "14:30"       # no entry FILLS after this bar-open time
    max_entries_per_day: int = 1
    allow_short: bool = True
    sizing: str = "fixed_notional"    # "fixed_notional": every trade sized on `capital`
                                      # (P&L is not reinvested); "compound": on current cash
    require_complete_session: bool = True   # all bars session-open..exit bar must exist

    def __post_init__(self):
        if self.square_off_price not in ("open", "close"):
            raise ValueError("square_off_price must be 'open' or 'close'")
        if self.sizing not in ("fixed_notional", "compound"):
            raise ValueError("sizing must be 'fixed_notional' or 'compound'")
        if self.entry_cutoff >= self.square_off:
            raise ValueError("entry_cutoff must be before the square-off bar")

    @classmethod
    def legacy_v0(cls, **kw):
        """Pre-ORB-v1 engine (used by LEGACY-014/015): exit at the 15:15 bar CLOSE,
        compounding sizing, only the 15:15 bar required. Reproduction only."""
        return cls(**{"square_off": "15:15", "square_off_price": "close", "sizing": "compound",
                      "require_complete_session": False, **kw})


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

    def open(self, time, raw, side, fraction, base=None):
        """side: +1 long, -1 short. `base` = capital to size on (default: current
        cash). Returns False if the budget buys < 1 share."""
        order_side = "buy" if side > 0 else "sell"
        fill = self.costs.slip(raw, order_side)
        budget = (self.cash if base is None else base) * fraction
        qty = math.floor(budget / fill)
        while qty > 0:
            ch = self.costs.charges(order_side, qty * fill)
            if qty * fill + sum(ch.values()) <= budget:
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


def _required_times(df, cfg):
    """Bar-start times that must exist for a session to be tradable."""
    if not cfg.require_complete_session:
        return [cfg.square_off]
    tf = int(pd.Series(sorted(df["time"].unique())).map(
        lambda s: int(s[:2]) * 60 + int(s[3:])).diff().dropna().min())
    t = pd.Timestamp("2000-01-01 09:15")
    end = pd.Timestamp(f"2000-01-01 {cfg.square_off}")
    out = []
    while t <= end:
        out.append(t.strftime("%H:%M"))
        t += pd.Timedelta(minutes=tf)
    if out[-1] != cfg.square_off:
        raise ValueError(f"exit bar {cfg.square_off} is not on this data's {tf}-min grid "
                         "(ORB v1 needs 15-min bars; use EngineConfig.legacy_v0() to "
                         "reproduce old 1-hour runs)")
    return out


def tradable_sessions(df, cfg):
    """(set of tradable sessions, list of (session, [missing times]) for the rest).
    Depends only on which bars EXIST, never on prices."""
    need = _required_times(df, cfg)
    ok, missing = set(), []
    for session, times in df.groupby("session")["time"]:
        gone = [t for t in need if t not in set(times)]
        if gone:
            missing.append((str(session), gone))
        else:
            ok.add(session)
    return ok, missing


def _tradable_sessions(df, square_off):          # legacy helper, kept for reference
    has_sq = df.groupby("session")["time"].apply(lambda t: (t == square_off).any())
    return set(has_sq[has_sq].index), sorted(str(s) for s in has_sq[~has_sq].index)


def _exit_price(bar, cfg):
    return bar["open"] if cfg.square_off_price == "open" else bar["close"]


def run_intraday(df, strategy, costs, cfg=None):
    """df: output of load_intraday (sorted, with session/time columns).
    Returns dict with trades, equity (per bar), skipped sessions, config."""
    cfg = cfg or EngineConfig()
    book = Book(cfg.capital, costs)
    base = cfg.capital if cfg.sizing == "fixed_notional" else None
    tradable, missing = tradable_sessions(df, cfg)
    curve = []

    for session, day in df.groupby("session", sort=True):
        if session not in tradable:
            continue
        day = day[day["time"] <= cfg.square_off]
        strategy.start_session(session)
        pending, entries = None, 0

        for i in range(len(day)):
            bar = day.iloc[i]

            # X2: at the exit bar NOTHING new fills; flat at its OPEN, stop.
            if bar["time"] == cfg.square_off and cfg.square_off_price == "open":
                if book.pos:
                    book.close(bar["date"], bar["open"], "square_off")
                curve.append((bar["date"], book.equity(bar["open"]), 0))
                break

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
                    elif book.open(bar["date"], bar["open"], target, cfg.position_fraction, base):
                        entries += 1

            # 2) legacy square-off at the bar CLOSE - nothing survives the session
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
            "skipped_sessions": [s for s, _ in missing], "missing_bars": missing,
            "config": asdict(cfg), "costs": costs.describe(), "strategy": strategy.name}


def run_open_to_close_benchmark(df, costs, cfg=None):
    """BUY every session at the first bar's (09:15) open, SELL at the exit
    bar using the SAME exit convention as the strategy (ORB v1: 15:00 OPEN).
    Same tradable sessions, sizing and costs as the strategy."""
    cfg = cfg or EngineConfig()
    book = Book(cfg.capital, costs)
    base = cfg.capital if cfg.sizing == "fixed_notional" else None
    tradable, missing = tradable_sessions(df, cfg)
    curve = []
    for session, day in df.groupby("session", sort=True):
        if session not in tradable:
            continue
        day = day[day["time"] <= cfg.square_off]
        first, last = day.iloc[0], day.iloc[-1]
        book.open(first["date"], first["open"], +1, cfg.position_fraction, base)
        for _, bar in day.iloc[:-1].iterrows():
            curve.append((bar["date"], book.equity(bar["close"]), 1 if book.pos else 0))
        px = _exit_price(last, cfg)
        if book.pos:
            book.close(last["date"], px, "square_off")
        curve.append((last["date"], book.equity(px), 0))
    return {"trades": pd.DataFrame(book.trades),
            "equity": pd.DataFrame(curve, columns=["date", "equity", "position"]),
            "skipped_sessions": [s for s, _ in missing], "missing_bars": missing,
            "config": asdict(cfg), "costs": costs.describe(),
            "strategy": "open-to-close benchmark"}
