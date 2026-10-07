"""Tests of the step E cost code (src/stage3/step_e.py).

Every holding used here is SYNTHETIC. No test reads the saved holdings or computes a real
historical cost; the registered result files are only hashed, to prove they are untouched."""

import copy
import hashlib
import inspect
import json
from pathlib import Path

import pandas as pd
import pytest

from src.stage3 import step_e
from src.stage3.step_e import CostScheduleError, cost_ledger, monthly_costs, net_of_class1, order_cost, period

ROOT = Path(__file__).resolve().parents[1]
S = step_e.load_schedule()
CR = 10_000_000


def holdings(months, portfolio="W", step="D", sample="PRIMARY"):
    """months: [(t, s_plus, s_pp, {stock: (begin_weight, end_weight)})] -> a frame like *_holdings.csv."""
    return pd.DataFrame([{"sample": sample, "step": step, "t": t, "holding_month": sp[:7], "s_plus": sp, "s_pp": spp,
                          "month_status": "OK", "portfolio": portfolio, "entity": e, "begin_weight": b, "end_weight": w}
                         for t, sp, spp, book in months for e, (b, w) in book.items()])


TWO_MONTHS = [("2013-12-31", "2014-01-02", "2014-02-03", {"A": (0.5, 0.6), "B": (0.5, 0.4)}),
              ("2014-01-31", "2014-02-03", "2014-03-03", {"A": (0.5, 0.5), "C": (0.5, 0.5)})]


# ------------------------------------------------------------------ schedule loading
def test_loads_only_the_approved_schedule(tmp_path):
    assert hashlib.sha256(step_e.SCHEDULE.read_bytes()).hexdigest() == step_e.SCHEDULE_SHA256
    assert set(S["components"]) == set(step_e.COMPONENTS)
    changed = tmp_path / "schedule.json"
    changed.write_text(step_e.SCHEDULE.read_text().replace('"rate": 0.001', '"rate": 0.0005', 1))
    with pytest.raises(CostScheduleError, match="not the approved schedule"):
        step_e.load_schedule(changed)


def test_parent_documents_are_checked(tmp_path):
    for rel in step_e.PARENTS.values():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("edited")
    with pytest.raises(CostScheduleError, match="differs from the hash recorded"):
        step_e.load_schedule(root=tmp_path)


@pytest.mark.parametrize("name", step_e.COMPONENTS)
def test_no_gap_no_overlap(name):
    step_e.validate(copy.deepcopy(S))
    gap, overlap = copy.deepcopy(S), copy.deepcopy(S)
    if len(S["components"][name]) > 1:
        del gap["components"][name][1 if len(S["components"][name]) > 2 else 0]
        overlap["components"][name][1]["from"] = overlap["components"][name][0]["from"]
    else:
        gap["components"][name][0]["from"] = "2012-08-01"
        overlap["components"][name].append(copy.deepcopy(overlap["components"][name][0]))
    for bad in (gap, overlap):
        with pytest.raises(CostScheduleError):
            step_e.validate(bad)


# ------------------------------------------------------------------ one order, by hand
def test_buy_order_by_hand():
    c = order_cost(S, "2014-01-02", 0.01)                       # Rs 1,00,000 bought
    assert c["side"] == "BUY" and c["order_value_rs"] == pytest.approx(100_000)
    assert c["stt_rs"] == pytest.approx(100.0)                  # 0.1%
    assert c["stamp_duty_rs"] == pytest.approx(15.0)            # 0.015%, buyer
    assert c["exchange_txn_rs"] == pytest.approx(3.25)          # Rs 3.25 per lakh
    assert c["ipft_rs"] == pytest.approx(0.0001)                # Rs 0.01 per crore
    assert c["sebi_fee_rs"] == pytest.approx(0.1)               # Rs 10 per crore
    assert c["brokerage_rs"] == pytest.approx(20.0)             # lower of 0.1% (Rs 100) or Rs 20
    assert c["tax_base_rs"] == pytest.approx(20.0 + 3.25 + 0.0001 + 0.1)
    assert c["indirect_tax_rate"] == 0.1236
    assert c["indirect_tax_rs"] == pytest.approx(0.1236 * 23.3501)
    assert c["dp_charge_rs"] == 0.0
    assert c["total_cost_rs"] == pytest.approx(100 + 15 + 3.25 + 0.0001 + 0.1 + 20 + 0.1236 * 23.3501)


def test_sell_order_by_hand():
    c = order_cost(S, "2014-01-02", -0.01)
    assert c["side"] == "SELL" and c["order_value_rs"] == pytest.approx(100_000)
    assert c["stt_rs"] == pytest.approx(100.0)
    assert c["stamp_duty_rs"] == 0.0                            # buyer only
    assert c["dp_charge_rs"] == 14.045                          # Rs 12.5 + 12.36% tax, as billed
    assert c["tax_base_rs"] == pytest.approx(23.3501)           # the depository charge is not in the base
    assert c["total_cost_rs"] == pytest.approx(100 + 3.25 + 0.0001 + 0.1 + 20 + 0.1236 * 23.3501 + 14.045)


def test_stt_both_sides_stamp_duty_buyer_only_dp_seller_only():
    for day in ("2012-07-02", "2019-06-03", "2026-09-01"):
        b, s = order_cost(S, day, 0.02), order_cost(S, day, -0.02)
        assert b["stt_rs"] == s["stt_rs"] == pytest.approx(200.0)
        assert b["stamp_duty_rs"] == pytest.approx(30.0) and s["stamp_duty_rs"] == 0.0
        assert b["dp_charge_rs"] == 0.0 and s["dp_charge_rs"] > 0
        assert b["stamp_duty_buy_period_from"] and s["stamp_duty_buy_period_from"] == ""   # "" = not charged on this side
        assert s["dp_charge_period_from"] and b["dp_charge_period_from"] == ""
        assert b["stt_buy_period_from"] and b["stt_sell_period_from"] == "" and s["stt_sell_period_from"]
        assert s["total_cost_rs"] - b["total_cost_rs"] == pytest.approx(s["dp_charge_rs"] - b["stamp_duty_rs"])


def test_brokerage():
    assert order_cost(S, "2014-01-02", 0.0005)["brokerage_rs"] == pytest.approx(5.0)      # 0.1% of Rs 5,000
    assert order_cost(S, "2014-01-02", 0.002)["brokerage_rs"] == pytest.approx(20.0)      # exactly at the cap
    assert order_cost(S, "2014-01-02", 0.9)["brokerage_rs"] == 20.0                       # one order, one cap
    assert order_cost(S, "2015-11-30", -0.5)["brokerage_rs"] == 20.0
    assert order_cost(S, "2015-12-01", -0.5)["brokerage_rs"] == 0.0                       # zero from 1 Dec 2015
    assert order_cost(S, "2026-09-01", 0.5)["brokerage_rs"] == 0.0


def test_exchange_charge_and_ipft_are_separate_and_counted_once():
    full = lambda day: order_cost(S, day, 1.0)                  # Rs 1 crore of value
    assert full("2020-12-31")["exchange_txn_rs"] == pytest.approx(325.0) and full("2020-12-31")["ipft_rs"] == pytest.approx(0.01)
    assert full("2023-04-03")["exchange_txn_rs"] == pytest.approx(325.0) and full("2023-04-03")["ipft_rs"] == pytest.approx(10.0)
    for day in ("2024-10-01", "2026-02-27", "2026-03-02"):      # NSE/FA/73061: charge + contribution = Rs 307 per crore
        assert full(day)["exchange_txn_rs"] + full(day)["ipft_rs"] == pytest.approx(307.0)
    c = full("2025-01-02")                                      # the tax base holds each of them exactly once
    assert c["tax_base_rs"] == pytest.approx(c["brokerage_rs"] + c["exchange_txn_rs"] + c["ipft_rs"] + c["sebi_fee_rs"])
    assert c["total_cost_rs"] == pytest.approx(sum(c[k] for k in step_e.COST_COLUMNS))
    assert "tax_base_rs" not in step_e.COST_COLUMNS


def test_january_2021_increase_is_counted_once_in_the_exchange_charge():
    before, after = order_cost(S, "2020-12-31", 1.0), order_cost(S, "2021-01-01", 1.0)
    assert after["exchange_txn_rs"] - before["exchange_txn_rs"] == pytest.approx(20.0)    # Rs 0.20 per lakh
    assert after["ipft_rs"] == before["ipft_rs"] == pytest.approx(0.01)                   # not added again as IPFT
    assert after["ipft_period_from"] == "2012-07-02"


def test_sebi_fee():
    for day, rs in (("2014-05-22", 10), ("2014-05-23", 20), ("2017-03-31", 20), ("2017-04-03", 15),
                    ("2019-04-01", 10), ("2020-09-01", 10)):                                # no halving in 2020-21 (ruling 5)
        assert order_cost(S, day, 1.0)["sebi_fee_rs"] == pytest.approx(rs)


def test_indirect_tax_base_and_rates():
    for day, rate in (("2015-05-29", 0.1236), ("2015-06-01", 0.14), ("2015-11-16", 0.145), ("2016-06-01", 0.15),
                      ("2017-06-30", 0.15), ("2017-07-03", 0.18)):
        for d in (0.03, -0.03):
            c = order_cost(S, day, d)
            assert c["indirect_tax_rate"] == rate
            assert c["indirect_tax_rs"] == pytest.approx(rate * (c["brokerage_rs"] + c["exchange_txn_rs"] + c["ipft_rs"] + c["sebi_fee_rs"]))
    assert step_e.TAX_BASE == S["conventions"]["indirect_tax_base"]


def test_depository_charge_once_per_stock_sold_whatever_the_size():
    assert order_cost(S, "2012-07-02", -1e-9)["dp_charge_rs"] == 21.9102                  # any reduction counts
    assert order_cost(S, "2012-07-02", -0.9)["dp_charge_rs"] == 21.9102
    for day, rs in (("2012-12-24", 21.9102), ("2012-12-26", 14.045), ("2014-07-04", 15.1686), ("2015-06-01", 15.39),
                    ("2015-11-16", 15.4575), ("2016-06-01", 15.525), ("2017-07-03", 15.93), ("2024-09-16", 15.93),
                    ("2024-09-17", 15.34), ("2026-09-01", 15.34)):
        c = order_cost(S, day, -0.01)
        assert c["dp_charge_rs"] == rs
        assert c["indirect_tax_rs"] == pytest.approx(c["indirect_tax_rate"] * c["tax_base_rs"])   # no tax on top of it


# ------------------------------------------------------------------ the ledger
def test_ledger_orders_weights_and_notional():
    led = cost_ledger(holdings(TWO_MONTHS), S)
    got = {(r.t, r.entity): r for r in led.itertuples()}
    assert set(got) == {("2013-12-31", "A"), ("2013-12-31", "B"), ("2014-01-31", "A"), ("2014-01-31", "B"), ("2014-01-31", "C")}
    first = got[("2013-12-31", "A")]                            # first month: a full purchase from cash
    assert (first.side, first.drift_weight, first.target_weight, first.trade_date) == ("BUY", 0.0, 0.5, "2014-01-02")
    assert first.order_value_rs == pytest.approx(0.5 * CR)
    a, b, c = (got[("2014-01-31", e)] for e in "ABC")
    assert (a.side, a.weight_change, a.order_value_rs) == ("SELL", pytest.approx(-0.1), pytest.approx(0.1 * CR))   # trimmed from 0.6 to 0.5
    assert (b.side, b.target_weight, b.order_value_rs) == ("SELL", 0.0, pytest.approx(0.4 * CR))                   # exit
    assert (c.side, c.drift_weight, c.order_value_rs) == ("BUY", 0.0, pytest.approx(0.5 * CR))                     # entry
    assert a.dp_charge_rs == b.dp_charge_rs == 14.045 and c.dp_charge_rs == 0.0
    assert (led["notional_rs"] == CR).all() and (led["order_value_rs"] == led["weight_change"].abs() * CR).all()
    assert (led["cost_fraction"] == led["total_cost_rs"] / CR).all()
    assert led.groupby(["t", "entity"]).size().max() == 1       # one order per stock per rebalance


def test_every_cost_is_traceable():
    led = cost_ledger(holdings(TWO_MONTHS), S)
    need = {"t", "trade_date", "entity", "drift_weight", "target_weight", "weight_change", "order_value_rs", "side",
            "tax_base_rs", "indirect_tax_rate", "total_cost_rs", "cost_fraction", "assumptions", *step_e.COST_COLUMNS,
            *(f"{c}_period_from" for c in step_e.COMPONENTS)}
    assert need <= set(led.columns)
    assert led["total_cost_rs"].tolist() == pytest.approx(led[step_e.COST_COLUMNS].sum(axis=1).tolist())
    m = monthly_costs(led)
    assert m["cost_fraction"].tolist() == pytest.approx(led.groupby("t")["total_cost_rs"].sum().div(CR).tolist())
    assert m["n_orders"].tolist() == [2, 3] and m["n_sold"].tolist() == [0, 2]
    assert m["traded_fraction"].tolist() == pytest.approx([1.0, 1.0])


def test_zero_weight_change_makes_no_order():
    months = [TWO_MONTHS[0], ("2014-01-31", "2014-02-03", "2014-03-03", {"A": (0.6, 0.6), "B": (0.4, 0.4)})]
    led = cost_ledger(holdings(months), S)
    assert set(led["t"]) == {"2013-12-31"}                      # second month: nothing changes, nothing is charged
    with pytest.raises(CostScheduleError):
        order_cost(S, "2014-02-03", 0.0)
    with pytest.raises(CostScheduleError):
        order_cost(S, "2014-02-03", float("nan"))


def test_deterministic_and_independent_of_row_order():
    h = holdings(TWO_MONTHS)
    a, b = cost_ledger(h, S), cost_ledger(h.copy(), S)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(a, cost_ledger(h.sample(frac=1, random_state=7), S))
    assert json.dumps(order_cost(S, "2018-03-01", -0.0123), sort_keys=True) == json.dumps(order_cost(S, "2018-03-01", -0.0123), sort_keys=True)


def test_fallback_and_assumption_flags_travel_with_each_order():
    buy, sell = order_cost(S, "2013-03-01", 0.01)["assumptions"], order_cost(S, "2013-03-01", -0.01)["assumptions"]
    assert set(buy.split(";")) == {"stt_buy:FALLBACK_CURRENT_RATE", "stamp_duty_buy:FALLBACK_CURRENT_RATE", "ipft:FALLBACK_CURRENT_RATE",
                                   "indirect_tax:ARCHIVED_EVIDENCE_WITH_APPROVED_READING"}
    assert set(sell.split(";")) == {"stt_sell:FALLBACK_CURRENT_RATE", "ipft:FALLBACK_CURRENT_RATE",
                                    "indirect_tax:ARCHIVED_EVIDENCE_WITH_APPROVED_READING",
                                    "dp_charge:ARCHIVED_EVIDENCE_WITH_APPROVED_READING"}
    assert "indirect_tax:EVIDENCE_BRACKET_ASSUMPTION" in order_cost(S, "2016-07-01", 0.01)["assumptions"]
    assert order_cost(S, "2025-01-02", 0.01)["assumptions"] == "stt_buy:FALLBACK_CURRENT_RATE"
    assert order_cost(S, "2025-01-02", -0.01)["assumptions"] == "stt_sell:FALLBACK_CURRENT_RATE"


# ------------------------------------------------------------------ adversarial
def test_future_information_cannot_change_a_past_cost():
    day, base = "2016-01-04", order_cost(S, "2016-01-04", -0.02)
    future = copy.deepcopy(S)
    for name, periods in future["components"].items():          # corrupt every period that starts after the trade date
        for p in periods:
            if p["from"] > day:
                for k in ("rate", "billed_rs", "cap_rs_per_order"):
                    if k in p:
                        p[k] = p[k] * 7 + 3
    assert order_cost(future, day, -0.02) == base
    led = cost_ledger(holdings(TWO_MONTHS), S)                  # later months do not change earlier rows
    one = cost_ledger(holdings(TWO_MONTHS[:1]), S)
    pd.testing.assert_frame_equal(led[led["t"] == "2013-12-31"].reset_index(drop=True), one)
    led2 = cost_ledger(holdings(TWO_MONTHS), future)            # nor do later rates
    pd.testing.assert_frame_equal(led, led2)


@pytest.mark.parametrize("component,key,eff,old,new", [
    ("sebi_fee", "sebi_fee_rs", "2014-05-23", 10.0, 20.0),
    ("exchange_txn", "exchange_txn_rs", "2021-01-01", 325.0, 345.0),
    ("exchange_txn", "exchange_txn_rs", "2024-10-01", 322.0, 297.0),
    ("ipft", "ipft_rs", "2023-04-01", 0.01, 10.0),
    ("indirect_tax", "indirect_tax_rate", "2015-06-01", 0.1236, 0.14),
    ("indirect_tax", "indirect_tax_rate", "2017-07-01", 0.15, 0.18),
    ("dp_charge", "dp_charge_rs", "2012-12-25", 21.9102, 14.045),
    ("brokerage", "brokerage_rs", "2015-12-01", 20.0, 0.0),
])
def test_rate_change_on_before_and_after_its_effective_date(component, key, eff, old, new):
    d = pd.Timestamp(eff)
    cost = lambda day: order_cost(S, day.date().isoformat(), -1.0)[key]
    assert cost(d - pd.Timedelta(days=1)) == pytest.approx(old)             # the day before: old rate
    assert cost(d) == pytest.approx(new)                                    # on the effective date: new rate
    assert cost(d + pd.Timedelta(days=1)) == pytest.approx(new)             # the day after: new rate
    assert period(S, component, eff)["from"] == eff


def test_no_cost_when_a_schedule_period_is_missing():
    holed = copy.deepcopy(S)
    del holed["components"]["sebi_fee"][1]                      # 2014-05-23 .. 2017-03-31 removed
    with pytest.raises(CostScheduleError, match="no cost is calculated"):
        order_cost(holed, "2015-01-02", 0.01)
    with pytest.raises(CostScheduleError):
        cost_ledger(holdings([("2014-12-31", "2015-01-02", "2015-02-02", {"A": (1.0, 1.0)})]), holed)
    nulled = copy.deepcopy(S)
    nulled["components"]["stt_buy"][0]["rate"] = None
    with pytest.raises(CostScheduleError, match="missing or invalid rate"):
        step_e.validate(nulled)
    for day in ("2012-07-01", "2026-09-02"):                    # outside the schedule: nothing is extrapolated
        with pytest.raises(CostScheduleError):
            order_cost(S, day, 0.01)


def test_holdings_that_cannot_be_costed_raise():
    gap = [TWO_MONTHS[0], ("2014-02-28", "2014-03-03", "2014-04-01", {"A": (1.0, 1.0)})]          # a month is missing
    with pytest.raises(CostScheduleError, match="not consecutive"):
        cost_ledger(holdings(gap), S)
    bad = holdings(TWO_MONTHS)
    bad.loc[0, "month_status"] = "EXCLUDED"
    with pytest.raises(CostScheduleError):
        cost_ledger(bad, S)
    with pytest.raises(CostScheduleError, match="no saved holdings"):
        cost_ledger(holdings(TWO_MONTHS), S, portfolio="BM")


def test_notional_is_never_compounded():
    # the portfolio doubles in value in month 1; month 2 is still costed on Rs 1 crore
    grown = [("2013-12-31", "2014-01-02", "2014-02-03", {"A": (0.5, 0.5), "B": (0.5, 0.5)}),
             ("2014-01-31", "2014-02-03", "2014-03-03", {"C": (0.5, 0.5), "D": (0.5, 0.5)})]
    led = cost_ledger(holdings(grown), S)
    assert (led["notional_rs"] == CR).all()
    buys = led[led["side"] == "BUY"]
    assert buys["order_value_rs"].tolist() == pytest.approx([0.5 * CR] * 4)                 # month 2 buys = month 1 buys
    assert led[led["side"] == "SELL"]["order_value_rs"].tolist() == pytest.approx([0.5 * CR] * 2)
    assert "gross" not in inspect.signature(cost_ledger).parameters and "returns" not in inspect.signature(cost_ledger).parameters
    assert step_e.NOTIONAL_RS == CR == S["conventions"]["notional_rs_per_portfolio"]


def test_gross_returns_are_copied_never_changed():
    h = holdings(TWO_MONTHS)
    monthly = pd.DataFrame({"step": ["D", "D", "C"], "t": ["2013-12-31", "2014-01-31", "2013-12-31"],
                            "W": [0.0123456789012345, -0.0234567890123456, 0.5], "BM": [0.01, 0.02, 0.03]})
    h0, m0 = h.copy(deep=True), monthly.copy(deep=True)
    costs = monthly_costs(cost_ledger(h, S))
    net = net_of_class1(monthly, costs, "W")
    pd.testing.assert_frame_equal(h, h0)                        # inputs untouched
    pd.testing.assert_frame_equal(monthly, m0)
    assert net["gross"].tolist() == [0.0123456789012345, -0.0234567890123456]               # bit-identical copy
    assert (net["net_S0"] == net["gross"] - net["cost_fraction"]).all() and (net["cost_fraction"] > 0).all()
    with pytest.raises(CostScheduleError, match="no saved gross return"):
        net_of_class1(monthly[monthly["t"] != "2014-01-31"], costs, "W")


def test_module_is_separate_from_the_registered_code_and_writes_nothing():
    src = inspect.getsource(step_e)
    for banned in ("import costs", "import ladder", "import experiment", "stage3.costs", "stage3.ladder", "stage3.experiment",
                   "to_csv", "write_text", "write_bytes", "open("):
        assert banned not in src, banned


def test_registered_result_files_are_byte_identical():
    want = {}
    for line in (ROOT / "registry" / "experiments.jsonl").read_text().splitlines():
        prov = json.loads(line).get("provenance") or {}
        for run in ("primary_run", "confirmation_run"):
            want.update((prov.get(run) or {}).get("files_sha256") or {})
    assert len(want) == 10
    for name, sha in want.items():
        assert hashlib.sha256((ROOT / "results" / "s2_mom_v1" / name).read_bytes()).hexdigest() == sha, name
    assert sorted(p.name for p in (ROOT / "results" / "s2_mom_v1").iterdir()) == sorted([*want, "blinded_precision.json", "sensitivity_results.json"])
