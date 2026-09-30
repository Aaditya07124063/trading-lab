"""Paper trading bot - trades FAKE money on real, fresh market data.
Run once every evening after market close (after ~4:00pm Nepal time):
    python3 paper_bot.py
Mechanics mirror the backtester exactly: a decision at day T's close becomes
a pending order that fills at the open of day T+1 - the next trading day
after T, never a later one. If runs are skipped, every missed day is replayed
in order, so each order still fills at its own T+1 open. No look-ahead, ever.
State: results/paper_state.json | Diary: results/paper_diary.csv"""

import json

import pandas as pd

from src.config import RESULTS_DIR, COST_PER_SIDE

SYMBOLS = {
    "NIFTYBEES": "NIFTYBEES.NS",   # ETF that tracks NIFTY 50 (buyable in real life)
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS",
}
START_CASH_EACH = 20_000           # 5 x 20k = 1 lakh total
FAST, SLOW = 20, 50                # the strategy the lab validated as "weak edge"

STATE_FILE = RESULTS_DIR / "paper_state.json"
DIARY_FILE = RESULTS_DIR / "paper_diary.csv"


def new_state(symbols):
    return {"accounts": {n: {"cash": START_CASH_EACH, "units": 0.0, "entry": None}
                         for n in symbols},
            "pending": {}, "last_candle": None}


def load_state():
    if STATE_FILE.exists():
        state = json.load(open(STATE_FILE))
    else:
        state = new_state(SYMBOLS)
    # older state files stored pending orders as a bare "BUY"/"SELL"
    for name, order in list(state["pending"].items()):
        if isinstance(order, str):
            state["pending"][name] = {"action": order, "signal_date": state["last_candle"]}
    return state


def fetch_histories():
    import yfinance as yf
    hists = {}
    for name, ticker in SYMBOLS.items():
        h = yf.Ticker(ticker).history(period="1y", interval="1d", auto_adjust=False)
        if h is None or h.empty:
            print(f"{name}: no data returned, skipped")
            continue
        if getattr(h.index, "tz", None) is not None:
            h.index = h.index.tz_localize(None)
        h.index = pd.DatetimeIndex(h.index).normalize()
        hists[name] = h
    return hists


def step(state, hists):
    """Replay every candle newer than state['last_candle'], oldest first.
    Mutates state; returns diary rows. hists: {name: DataFrame with Open/Close,
    DatetimeIndex of trading days}."""
    last = pd.Timestamp(state["last_candle"]) if state["last_candle"] else None
    if last is None:
        # first ever run: only tonight's decision, nothing to fill yet
        new_dates = [max(h.index[-1] for h in hists.values())]
    else:
        new_dates = sorted({d for h in hists.values() for d in h.index if d > last})

    last_close = {}
    for name, h in hists.items():
        past = h[h.index <= new_dates[0]] if new_dates else h
        if len(past):
            last_close[name] = float(past["Close"].iloc[-1])

    rows = []
    for day in new_dates:
        today = str(day.date())
        for name, h in hists.items():
            if day not in h.index:
                continue
            acc = state["accounts"][name]
            i = h.index.get_loc(day)
            open_today = float(h["Open"].iloc[i])
            close_today = float(h["Close"].iloc[i])

            # 1) fill the pending order - only if today is exactly T+1
            order = state["pending"].pop(name, None)
            if order:
                sig = pd.Timestamp(order["signal_date"])
                prev = h.index[i - 1] if i > 0 else None
                if prev != sig:
                    rows.append({"date": today, "symbol": name, "action": "EXPIRED",
                                 "price": None,
                                 "note": f"{order['action']} from {sig.date()} had no T+1 bar in data"})
                elif order["action"] == "BUY" and acc["units"] == 0:
                    acc["units"] = acc["cash"] * (1 - COST_PER_SIDE) / open_today
                    acc["cash"], acc["entry"] = 0.0, open_today
                    rows.append({"date": today, "symbol": name, "action": "BUY",
                                 "price": round(open_today, 2), "note": ""})
                elif order["action"] == "SELL" and acc["units"] > 0:
                    pnl = (open_today / acc["entry"] - 1) * 100
                    acc["cash"] = acc["units"] * open_today * (1 - COST_PER_SIDE)
                    acc["units"], acc["entry"] = 0.0, None
                    rows.append({"date": today, "symbol": name, "action": "SELL",
                                 "price": round(open_today, 2), "note": f"pnl {pnl:+.1f}%"})

            # 2) tonight's decision (closes up to TODAY only) -> order for T+1
            closes = h["Close"].iloc[:i + 1]
            fast = closes.ewm(span=FAST, adjust=False).mean().iloc[-1]
            slow = closes.ewm(span=SLOW, adjust=False).mean().iloc[-1]
            want_in = fast > slow
            if want_in and acc["units"] == 0:
                state["pending"][name] = {"action": "BUY", "signal_date": today}
            elif not want_in and acc["units"] > 0:
                state["pending"][name] = {"action": "SELL", "signal_date": today}
            last_close[name] = close_today

        total = sum(a["cash"] + a["units"] * last_close.get(n, 0.0)
                    for n, a in state["accounts"].items())
        start = START_CASH_EACH * len(state["accounts"])
        rows.append({"date": today, "symbol": "TOTAL", "action": "EQUITY",
                     "price": round(total, 2),
                     "note": f"{(total / start - 1) * 100:+.2f}% since start"})
        state["last_candle"] = today
    return rows


def main():
    state = load_state()
    hists = fetch_histories()
    if not hists:
        raise SystemExit("No data fetched - nothing to do.")
    rows = step(state, hists)
    if not rows:
        print(f"No new market candle since last run ({state['last_candle']}). "
              "Market closed or already ran today - nothing to do.")
        return
    for r in rows:
        print(f"{r['date']}  {r['symbol']:10s} {r['action']:8s} {r['price']}  {r['note']}")
    for name, order in state["pending"].items():
        print(f"pending: {name} {order['action']} (signal {order['signal_date']}, fills next open)")
    pd.DataFrame(rows).to_csv(DIARY_FILE, mode="a", header=not DIARY_FILE.exists(), index=False)
    json.dump(state, open(STATE_FILE, "w"), indent=2)
    print("diary + state saved in results/")


if __name__ == "__main__":
    main()
