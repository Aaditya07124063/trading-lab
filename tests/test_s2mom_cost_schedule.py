"""Validation of the S2-MOM-v1 dated delivery cost schedule (Addendum 1 + Supplement 1).

Checks the schedule FILE only. It computes no turnover, cost or return and reads no holdings."""

import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config" / "cost_schedules" / "delivery_nse_eq_s2mom_v1_dated.json"
SCHEDULE_SHA256 = "47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f"
S = json.loads(PATH.read_text())
C = S["components"]
D = dt.date.fromisoformat
START, END = D("2012-07-02"), D("2026-09-01")
AD_VALOREM = ("stt_buy", "stt_sell", "exchange_txn", "ipft", "sebi_fee", "stamp_duty_buy")
UNIT = {"percent": 1e2, "rs_per_lakh": 1e5, "rs_per_crore": 1e7}
VALUE_KEY = {"dp_charge": "billed_rs"}


def on(component, day):
    """The one period of `component` in force on `day` (ISO string)."""
    hits = [p for p in C[component] if D(p["from"]) <= D(day) <= D(p["to"])]
    assert len(hits) == 1, (component, day, len(hits))
    return hits[0]


def val(component, day):
    return on(component, day)[VALUE_KEY.get(component, "rate")]


def test_schedule_is_the_audited_file():
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == SCHEDULE_SHA256


def test_all_required_components_present():
    assert set(C) == set(AD_VALOREM) | {"indirect_tax", "brokerage", "dp_charge"}


def test_no_missing_rate():
    def walk(x, where):
        assert x is not None and x != "", f"empty value at {where}"
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{where}.{k}")
        elif isinstance(x, list):
            assert x, f"empty list at {where}"
            for i, v in enumerate(x):
                walk(v, f"{where}[{i}]")
    walk(S, "schedule")
    for name, periods in C.items():
        for p in periods:
            v = p[VALUE_KEY.get(name, "rate")]
            assert isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0, (name, p["from"])
            assert p["basis"] in S["basis_key"] and isinstance(p["assumption"], bool) and p["note"]


@pytest.mark.parametrize("name", sorted(C))
def test_no_gap_no_overlap_whole_sample(name):
    ps = C[name]
    assert D(ps[0]["from"]) == START and D(ps[-1]["to"]) == END
    for a, b in zip(ps, ps[1:]):
        assert D(a["from"]) <= D(a["to"])
        assert D(b["from"]) == D(a["to"]) + dt.timedelta(days=1), (name, a["to"], b["from"])
    assert (S["sample"]["from"], S["sample"]["to"]) == (START.isoformat(), END.isoformat())


@pytest.mark.parametrize("component,last_day,before,first_day,after", [
    ("exchange_txn", "2020-12-31", 3.25e-5, "2021-01-01", 3.45e-5),
    ("exchange_txn", "2023-03-31", 3.45e-5, "2023-04-01", 3.25e-5),
    ("exchange_txn", "2024-03-31", 3.25e-5, "2024-04-01", 3.22e-5),
    ("exchange_txn", "2024-09-30", 3.22e-5, "2024-10-01", 2.97e-5),
    ("exchange_txn", "2026-02-28", 2.97e-5, "2026-03-01", 3.0699e-5),
    ("ipft", "2023-03-31", 1e-9, "2023-04-01", 1e-6),
    ("ipft", "2026-02-28", 1e-6, "2026-03-01", 1e-9),
    ("sebi_fee", "2014-05-22", 1e-6, "2014-05-23", 2e-6),
    ("sebi_fee", "2017-03-31", 2e-6, "2017-04-01", 1.5e-6),
    ("sebi_fee", "2019-03-31", 1.5e-6, "2019-04-01", 1e-6),
    ("indirect_tax", "2015-05-31", 0.1236, "2015-06-01", 0.14),
    ("indirect_tax", "2015-11-14", 0.14, "2015-11-15", 0.145),
    ("indirect_tax", "2016-05-31", 0.145, "2016-06-01", 0.15),
    ("indirect_tax", "2017-06-30", 0.15, "2017-07-01", 0.18),
    ("brokerage", "2015-11-30", 0.001, "2015-12-01", 0.0),
    ("dp_charge", "2012-12-24", 21.9102, "2012-12-25", 14.045),
    ("dp_charge", "2014-07-03", 14.045, "2014-07-04", 15.1686),
    ("dp_charge", "2024-09-16", 15.93, "2024-09-17", 15.34),
])
def test_effective_date_boundaries(component, last_day, before, first_day, after):
    assert val(component, last_day) == pytest.approx(before, rel=1e-12)
    assert val(component, first_day) == pytest.approx(after, rel=1e-12)
    assert D(first_day) == D(last_day) + dt.timedelta(days=1)


def test_constant_inputs():
    for day in ("2012-07-02", "2019-06-15", "2026-09-01"):
        assert val("stt_buy", day) == val("stt_sell", day) == 0.001
        assert val("stamp_duty_buy", day) == 0.00015
    assert on("brokerage", "2012-07-02")["cap_rs_per_order"] == 20.0
    assert on("brokerage", "2026-09-01")["cap_rs_per_order"] == 0.0


def test_units():
    for name in AD_VALOREM + ("brokerage",):
        for p in C[name]:
            assert p["rate"] == pytest.approx(p["stated"] / UNIT[p["stated_unit"]], rel=1e-12), (name, p["from"])
            assert 0 <= p["rate"] < 0.01, (name, p["rate"])          # a fraction of traded value, never a percent
    for p in C["indirect_tax"]:
        assert p["rate"] == pytest.approx(p["stated"] / 100) and 0.1 < p["rate"] < 0.2
    for p in C["dp_charge"]:
        assert p["unit"] == "rs_per_stock_per_sell_day_tax_included" and 10 < p["billed_rs"] < 25
    assert {p["stated_unit"] for p in C["exchange_txn"]} == {"rs_per_lakh"}
    assert {p["stated_unit"] for n in ("ipft", "sebi_fee") for p in C[n]} == {"rs_per_crore"}


def test_tax_base_is_the_frozen_one():
    conv = S["conventions"]
    assert conv["indirect_tax_base"] == ["brokerage", "exchange_txn", "ipft", "sebi_fee"]
    assert not {"stt_buy", "stt_sell", "stamp_duty_buy", "dp_charge"} & set(conv["indirect_tax_base"])
    assert "never taxed again" in conv["sell_side_charge"]


def test_education_cess_period_is_12_percent_plus_3_percent_of_it():
    p = on("indirect_tax", "2012-07-02")
    parts = p["parts"]
    assert parts["service_tax_official"] == 12.0
    assert p["stated"] == pytest.approx(12.0 * (1 + (parts["education_cess_pct_of_tax_broker_evidence"]
                                                   + parts["higher_education_cess_pct_of_tax_broker_evidence"]) / 100))


def test_dp_charge_includes_exactly_the_tax_in_force_once():
    for p in C["dp_charge"]:
        for day in (p["from"], p["to"]):                               # one tax rate across the whole period
            assert val("indirect_tax", day) == p["tax_rate_included"], (p["from"], day)
        assert p["billed_rs"] == pytest.approx(p["pretax_rs"] * (1 + p["tax_rate_included"]), abs=1e-9)
    assert val("dp_charge", "2026-09-01") == 15.34                     # the amount the broker itself prints
    assert [p["pretax_rs"] for p in C["dp_charge"]] == [19.5, 12.5, 13.5, 13.5, 13.5, 13.5, 13.5, 13.5, 13.5, 13.0]


def test_ipft_is_separate_and_never_double_counted():
    # the transaction charge carries the circulars' own figures, without the contribution
    assert [p["stated"] for p in C["exchange_txn"]] == [3.25, 3.45, 3.25, 3.22, 2.97, 3.0699]
    assert [p["stated"] for p in C["ipft"]] == [0.01, 10, 0.01]
    # NSE/FA/73061 tabulates charge + contribution = Rs 307 per crore on both sides of 1 March 2026
    for day in ("2026-02-28", "2026-03-01"):
        assert (val("exchange_txn", day) + val("ipft", day)) * 1e7 == pytest.approx(307.0, abs=1e-6)
    # NSE/FA/56129: charge Rs 325 per crore plus a contribution of Rs 10 per crore from 1 April 2023
    assert (val("exchange_txn", "2023-04-01") + val("ipft", "2023-04-01")) * 1e7 == pytest.approx(335.0, abs=1e-6)


def test_january_2021_increase_is_in_the_transaction_charge_only():
    assert (val("exchange_txn", "2021-01-01") - val("exchange_txn", "2020-12-31")) * 1e5 == pytest.approx(0.20)
    assert val("ipft", "2020-12-31") == val("ipft", "2021-01-01") == val("ipft", "2023-03-31") == 1e-9
    assert on("ipft", "2021-01-01")["from"] == "2012-07-02"            # no IPFT period starts in January 2021


def test_every_fallback_and_assumption_is_marked():
    flagged = {(n, p["from"], p["to"], p["basis"]) for n, ps in C.items() if n != "dp_charge" for p in ps if p["assumption"]}
    assert flagged == {
        ("stt_buy", "2012-07-02", "2026-09-01", "FALLBACK_CURRENT_RATE"),
        ("stt_sell", "2012-07-02", "2026-09-01", "FALLBACK_CURRENT_RATE"),
        ("ipft", "2012-07-02", "2023-03-31", "FALLBACK_CURRENT_RATE"),
        ("stamp_duty_buy", "2012-07-02", "2020-06-30", "FALLBACK_CURRENT_RATE"),
        ("indirect_tax", "2012-07-02", "2015-05-31", "ARCHIVED_EVIDENCE_WITH_APPROVED_READING"),
        ("indirect_tax", "2016-06-01", "2016-10-08", "EVIDENCE_BRACKET_ASSUMPTION"),
    }
    for n, ps in C.items():
        for p in ps:
            assert p["assumption"] == (p["basis"] != "ARCHIVED_EVIDENCE") or n == "dp_charge"
    # the depository charge inherits the tax assumptions and carries ruling 4 for 2016-10-09..2020-02-16
    assert [(p["from"], p["to"]) for p in C["dp_charge"] if p["assumption"]] == [
        ("2012-07-02", "2012-12-24"), ("2012-12-25", "2014-07-03"), ("2014-07-04", "2015-05-31"),
        ("2016-06-01", "2016-10-08"), ("2016-10-09", "2017-06-30"), ("2017-07-01", "2020-02-16")]
    assert "not direct official-rate evidence" in on("indirect_tax", "2016-06-01")["note"]
    assert "NOT from an official file" in on("indirect_tax", "2012-07-02")["note"]


def test_conventions_match_addendum_1():
    c = S["conventions"]
    assert c["notional_rs_per_portfolio"] == 10_000_000
    assert c["notional_reset_every_rebalance"] is True and c["compounding"] is False
    assert c["orders_per_stock_per_rebalance"] == 1
    assert c["order_value"] == "abs(target weight - drifted weight) x notional_rs_per_portfolio"
    assert "once per stock sold per rebalance" in c["sell_side_charge"]
    assert "retail individual" in S["account"]


def test_reproducible_from_archived_evidence():
    manifest = {r["file"]: r["sha256"] for r in csv.DictReader(open(ROOT / "docs/evidence/s2mom_costs/MANIFEST.csv"))}
    seen = 0
    for name, periods in C.items():
        for p in periods:
            for e in p["evidence"]:
                f = ROOT / e["file"]
                assert f.is_file(), e["file"]
                assert hashlib.sha256(f.read_bytes()).hexdigest() == e["sha256"], e["file"]
                if f.parent.name == "s2mom_costs":
                    assert manifest[f.name] == e["sha256"], e["file"]
                seen += 1
            if p["basis"] == "FALLBACK_CURRENT_RATE":                  # fallback needs current-rate evidence and a reason
                assert len(p["evidence"]) >= 2 and ("fallback" in p["note"].lower())
    assert seen > 100
    for key, f in (("protocol_sha256", "phase3a_momentum_protocol.md"),
                   ("addendum1_sha256", "phase3a_momentum_protocol_addendum1_costs.md"),
                   ("supplement1_sha256", "phase3a_momentum_protocol_addendum1_supplement1.md")):
        assert hashlib.sha256((ROOT / "docs/research" / f).read_bytes()).hexdigest() == S["parents"][key]
