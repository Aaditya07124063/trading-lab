"""S2-MOM-v1 cost model (protocol §13 and §23). Delivery trades.

Class 1 - statutory / exchange / broker charges: explicit inputs in
config/cost_schedules/delivery_nse_eq_s2mom.json, each with its evidence and its `basis`:
  HISTORICAL_EVIDENCE       archived evidence covers the whole study period
  CURRENT_RATE_ASSUMPTION   frozen §13 fallback: "Where a historical rate cannot be evidenced, the
                            current rate is applied to the whole sample and labelled as an
                            assumption." Needs archived evidence of the CURRENT rate, the period it
                            is assumed for, and why history could not be evidenced. It is reported
                            as an assumption in every output, never as historical fact.
A rate that is null, lacks archived evidence, or has no valid basis makes every cost calculation
raise: it can never become zero.
Class 2 - slippage: the assumed scenarios S0-S4 of the protocol (src.stage3.protocol.SLIPPAGE_BPS).
"""

import json

from src.config import BASE_DIR
from src.stage3.protocol import NOTIONAL_RS, SLIPPAGE_BPS

SCHEDULE = BASE_DIR / "config" / "cost_schedules" / "delivery_nse_eq_s2mom.json"
COMPONENTS = ("stt_buy", "stt_sell", "exchange_txn", "sebi_fee", "stamp_duty_buy", "gst_rate",
              "brokerage", "dp_charge_rs_per_scrip_sold")


class CostEvidenceMissing(Exception):
    """A statutory/exchange/broker rate has no archived evidence."""


def load_schedule(path=None):
    s = json.loads((path or SCHEDULE).read_text())
    absent = [c for c in COMPONENTS if c not in s["components"]]
    if absent:
        raise CostEvidenceMissing(f"cost schedule lacks components: {absent}")
    return s


BASES = ("HISTORICAL_EVIDENCE", "CURRENT_RATE_ASSUMPTION")


def _usable(c):
    if c.get("rate") is None or not c.get("evidence_archived") or c.get("basis") not in BASES:
        return False
    return c["basis"] == "HISTORICAL_EVIDENCE" or bool(c.get("assumed_for_period") and c.get("why_history_unavailable"))


def missing_evidence(schedule):
    """Components that cannot be used: null rate, no archived evidence, or no valid basis."""
    return [c for c in COMPONENTS if not _usable(schedule["components"][c])]


def assumptions(schedule):
    """Every component used under the §13 current-rate fallback - to be printed with any cost result."""
    return [{"component": c, "rate": v["rate"], "assumed_for_period": v["assumed_for_period"],
             "why_history_unavailable": v["why_history_unavailable"]}
            for c, v in schedule["components"].items() if v.get("basis") == "CURRENT_RATE_ASSUMPTION" and _usable(v)]


def side_rates(schedule, scenario, band="1-200"):
    """One-way cost as a fraction of traded value: (buy_rate, sell_rate), excluding the flat
    depository charge. Raises if any evidenced input is missing."""
    gaps = missing_evidence(schedule)
    if gaps:
        raise CostEvidenceMissing(f"no archived evidence for: {gaps}")
    c = {k: v["rate"] for k, v in schedule["components"].items()}
    slip = SLIPPAGE_BPS[scenario][band] / 1e4
    taxed = (c["exchange_txn"] + c["sebi_fee"] + c["brokerage"]) * (1 + c["gst_rate"])   # GST on all three (§13)
    buy = c["stt_buy"] + c["stamp_duty_buy"] + taxed + slip
    sell = c["stt_sell"] + taxed + slip
    return buy, sell


def rebalance(target, drift):
    """Protocol §23. target, drift: {stock: weight}. Returns one-way turnover, the bought and
    sold fractions of portfolio value and the number of stocks with a sale."""
    names = set(target) | set(drift)
    d = {n: target.get(n, 0.0) - drift.get(n, 0.0) for n in names}
    bought = sum(v for v in d.values() if v > 0)
    sold = -sum(v for v in d.values() if v < 0)
    return {"turnover_one_way": 0.5 * (bought + sold), "bought": bought, "sold": sold,
            "n_sold": sum(1 for v in d.values() if v < -1e-12)}


def rebalance_cost(trade, schedule, scenario, band="1-200"):
    """Cost of one rebalance as a fraction of portfolio value."""
    buy, sell = side_rates(schedule, scenario, band)
    dp = schedule["components"]["dp_charge_rs_per_scrip_sold"]["rate"] * trade["n_sold"] / NOTIONAL_RS
    return trade["bought"] * buy + trade["sold"] * sell + dp


def breakeven_one_way(excess_s0_mean, traded_w_mean, traded_bm_mean):
    """Slippage (fraction, one way) at which the mean net excess return of W over the benchmark
    is zero. Net excess is linear in slippage: excess_S0 - s * (traded_W - traded_BM), where
    traded = bought + sold per month. None when slippage does not reduce the excess."""
    extra = traded_w_mean - traded_bm_mean
    return excess_s0_mean / extra if extra > 0 else None
