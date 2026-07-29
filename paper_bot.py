"""Paper trading bot - trades FAKE money on real, fresh market data.
Run once every evening after market close (after ~4:00pm Nepal time):
    python3 paper_bot.py
Mechanics mirror the backtester exactly: tonight's decision becomes a
pending order, executed at TOMORROW's real open. No look-ahead, ever.
State: results/paper_state.json | Diary: results/paper_diary.csv"""

import json

import pandas as pd
import yfinance as yf

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


def load_state():
    if STATE_FILE.exists():
        return json.load(open(STATE_FILE))
    return {"accounts": {n: {"cash": START_CASH_EACH, "units": 0.0, "entry": None}
                         for n in SYMBOLS},
            "pending": {}, "last_candle": None}


state = load_state()

# ---------- fetch fresh data for everyone first ----------
hists = {}
for name, ticker in SYMBOLS.items():
    h = yf.Ticker(ticker).history(period="1y", interval="1d", auto_adjust=False)
    if h is None or h.empty:
        print(f"{name}: no data returned, skipped")
        continue
    if getattr(h.index, "tz", None) is not None:
        h.index = h.index.tz_localize(None)
    hists[name] = h

newest = max(str(h.index[-1].date()) for h in hists.values())
if state["last_candle"] == newest:
    print(f"No new market candle since last run ({newest}). "
          "Market closed or already ran today - nothing to do.")
    raise SystemExit

# ---------- one pass per symbol ----------
rows, total_equity = [], 0.0
for name, h in hists.items():
    acc = state["accounts"][name]
    today = str(h.index[-1].date())
    open_today = float(h["Open"].iloc[-1])
    close_today = float(h["Close"].iloc[-1])

    # 1) execute yesterday's pending order at TODAY's real open
    action = state["pending"].pop(name, None)
    if action == "BUY" and acc["units"] == 0:
        acc["units"] = acc["cash"] * (1 - COST_PER_SIDE) / open_today
        acc["cash"], acc["entry"] = 0.0, open_today
        rows.append({"date": today, "symbol": name, "action": "BUY",
                     "price": round(open_today, 2), "note": ""})
        print(f"{name:10s} BOUGHT at {open_today:,.2f}")
    elif action == "SELL" and acc["units"] > 0:
        pnl = (open_today / acc["entry"] - 1) * 100
        acc["cash"] = acc["units"] * open_today * (1 - COST_PER_SIDE)
        acc["units"], acc["entry"] = 0.0, None
        rows.append({"date": today, "symbol": name, "action": "SELL",
                     "price": round(open_today, 2), "note": f"pnl {pnl:+.1f}%"})
        print(f"{name:10s} SOLD at {open_today:,.2f}  (trade pnl {pnl:+.1f}%)")

    # 2) tonight's decision -> pending order for tomorrow's open
    closes = h["Close"]
    fast = closes.ewm(span=FAST, adjust=False).mean().iloc[-1]
    slow = closes.ewm(span=SLOW, adjust=False).mean().iloc[-1]
    want_in = fast > slow
    if want_in and acc["units"] == 0:
        state["pending"][name] = "BUY"
    elif not want_in and acc["units"] > 0:
        state["pending"][name] = "SELL"

    equity = acc["cash"] + acc["units"] * close_today
    total_equity += equity
    status = "IN " if acc["units"] > 0 else "OUT"
    plan = state["pending"].get(name, "hold")
    print(f"{name:10s} [{status}] equity {equity:>9,.0f}   "
          f"ema{FAST} {'>' if want_in else '<'} ema{SLOW}   tomorrow: {plan}")

# ---------- diary + state ----------
rows.append({"date": newest, "symbol": "TOTAL", "action": "EQUITY",
             "price": round(total_equity, 2),
             "note": f"{(total_equity / (START_CASH_EACH * len(SYMBOLS)) - 1) * 100:+.2f}% since start"})
pd.DataFrame(rows).to_csv(DIARY_FILE, mode="a", header=not DIARY_FILE.exists(), index=False)

state["last_candle"] = newest
json.dump(state, open(STATE_FILE, "w"), indent=2)
print(f"\nTotal paper equity: Rs {total_equity:,.0f}  |  diary + state saved in results/")