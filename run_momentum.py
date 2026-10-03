"""Momentum portfolio (Varsity module 10):
every month, hold the TOP_N stocks with the best last-6-month return.
Opponent: buying all four equally and sleeping."""

import pandas as pd

from src.access import research_load_csv   # cutoff 2026-09-30
from src.config import CAPITAL, COST_PER_SIDE

FILES = {"RELIANCE": "RELIANCEd1.csv", "TCS": "TCSd1.csv",
         "HDFCBANK": "HDFCBANKd1.csv", "INFY": "INFYd1.csv"}
LOOKBACK = 126     # ~6 months of trading days
HOLD = 21          # ~1 month before re-ranking
TOP_N = 2

# one aligned table of closing prices (only dates ALL four have)
prices = pd.DataFrame({name: research_load_csv(f).set_index("date")["close"]
                       for name, f in FILES.items()}).dropna()
print(f"Universe: {list(FILES)} | {len(prices):,} common days "
      f"({prices.index[0].date()} -> {prices.index[-1].date()})\n")

value = CAPITAL
current = set()
pick_counter = {name: 0 for name in FILES}

for i in range(LOOKBACK, len(prices) - 1, HOLD):
    # rank by last-6-month performance, take the best TOP_N
    momentum = prices.iloc[i] / prices.iloc[i - LOOKBACK] - 1
    picks = set(momentum.nlargest(TOP_N).index)
    for p in picks:
        pick_counter[p] += 1

    if picks != current:                      # pay costs only when we switch
        value *= (1 - 2 * COST_PER_SIDE)
    current = picks

    # hold the picks equally for the next month
    segment = prices[list(picks)].iloc[i:i + HOLD + 1]
    month_growth = (segment.iloc[-1] / segment.iloc[0]).mean()
    value *= month_growth

# the opponent: equal money in all four on day 1, then sleep
bh_growth = (prices.iloc[-1] / prices.iloc[LOOKBACK]).mean()
bh_value = CAPITAL * bh_growth

mom_ret = (value / CAPITAL - 1) * 100
bh_ret = (bh_value / CAPITAL - 1) * 100

print(f"Momentum top-{TOP_N} : {mom_ret:+10.1f}%   (final Rs {value:,.0f})")
print(f"Equal buy & hold : {bh_ret:+10.1f}%   (final Rs {bh_value:,.0f})")
print(f"Margin           : {mom_ret - bh_ret:+10.1f} points")
print("\nHow often each stock was picked:")
for name, n in sorted(pick_counter.items(), key=lambda x: -x[1]):
    print(f"  {name:10s} {n:4d} months")