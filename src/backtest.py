"""The time machine: replays history one day at a time.
Golden rule: anything seen at day N's close is acted on at day N+1's OPEN.

Risk exits (both optional):
  stop_loss      exit if close falls X below the ENTRY price   (0.05 = 5%)
  trailing_stop  exit if close falls X below the HIGHEST close
                 since entry - the stop climbs with the trade.
After any stop-out we stay blocked until the signal resets to 0."""

from src.config import CAPITAL, COST_PER_SIDE


def run_backtest(df, stop_loss=None, trailing_stop=None):
    cash = CAPITAL
    units = 0.0
    equity = []
    trades = []
    entry_price = None
    entry_date = None
    highest_close = None
    stop_hit = False
    blocked = False

    for i in range(len(df)):
        want_in = df["position"].iloc[i - 1] if i > 0 else 0
        open_price = df["open"].iloc[i]

        if blocked and want_in == 0:
            blocked = False

        if units > 0 and (want_in == 0 or stop_hit):
            cash = units * open_price * (1 - COST_PER_SIDE)
            trades.append({
                "entry_date": entry_date, "entry": entry_price,
                "exit_date": df["date"].iloc[i], "exit": open_price,
                "pnl_pct": (open_price / entry_price - 1) * 100,
                "reason": "stop" if stop_hit else "signal",
            })
            units = 0.0
            if stop_hit:
                blocked = True
            stop_hit = False

        elif want_in == 1 and units == 0 and not blocked:
            units = cash * (1 - COST_PER_SIDE) / open_price
            cash = 0.0
            entry_price = open_price
            entry_date = df["date"].iloc[i]
            highest_close = open_price

        close = df["close"].iloc[i]
        equity.append(cash + units * close)

        # evening risk checks -> may schedule a sell for tomorrow's open
        if units > 0:
            if close > highest_close:
                highest_close = close
            if stop_loss is not None and close < entry_price * (1 - stop_loss):
                stop_hit = True
            if trailing_stop is not None and close < highest_close * (1 - trailing_stop):
                stop_hit = True

    if units > 0:
        trades.append({
            "entry_date": entry_date, "entry": entry_price,
            "exit_date": None, "exit": None,
            "pnl_pct": (df["close"].iloc[-1] / entry_price - 1) * 100,
            "reason": "open",
        })

    df["equity"] = equity
    return df, trades