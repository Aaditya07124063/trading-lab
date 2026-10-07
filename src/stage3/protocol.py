"""S2-MOM-v1: frozen-protocol constants, registry record and fail-closed guards (Phase 3B).

The frozen protocol (docs/research/phase3a_momentum_protocol.md) is the source of truth.
Every constant below is copied from it; the section is named beside each one. Nothing here
may be changed without a new protocol version (S2-MOM-v2).

    verify_protocol()     raises unless the protocol file on disk has the frozen SHA-256
                          AND the registry record carries the same SHA-256
    require_ready(...)    raises unless every open decision is closed (and, for costs,
                          every evidenced rate is present) - the runner calls this first
"""

import hashlib

import pandas as pd

from src.access import RESEARCH_CUTOFF
from src.config import BASE_DIR
from src.registry import experiments

PROTOCOL_ID = "S2-MOM-v1"
PROTOCOL_VERSION = "revision 4"
PROTOCOL_FILE = "docs/research/phase3a_momentum_protocol.md"
PROTOCOL_SHA256 = "f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838"
FREEZE_COMMIT = "7d4cb6d977ee1fbe40351fc6b6049c49af7638b2"
UNIV1_SHA256 = "2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42"

T_STAR = pd.Timestamp("2026-09-30")            # B1.1: last UNIV-1 selection date / last session
FIRST_T = pd.Timestamp("2012-06-29")           # §9: first selection date
LAST_T = pd.Timestamp("2026-07-31")            # §9: last selection date
PRIMARY_LAST_T = pd.Timestamp("2021-11-30")    # B3: holding month Dec 2021 is the last primary month
FORMATION_MONTHS = 12                          # §7
SKIP_MONTHS = 1                                # §8
BREAKPOINT = 0.30                              # §10
TOP_N = 200                                    # B1.1
NW_LAG = {"PRIMARY": 4, "OOS": 3, "POOLED": 4}  # §15: floor(4*(T/100)^(2/9))
ALPHA = 0.05                                   # §2
BOOTSTRAP_RESAMPLES = 10_000                   # §15
REFERENCE_THRESHOLD = 0.10                     # §27: percent per month
DELIST_RETURN = {"VOLUNTARY": 0.0, "OTHER": -0.30}   # §22
NOTIONAL_RS = 1e7                              # §13: Rs 1 crore per portfolio
# §13 class 2: assumed one-way slippage in basis points, by liquidity band. Scenarios, not estimates.
SLIPPAGE_BPS = {"S0": {"1-200": 0, "201-500": 0}, "S1": {"1-200": 5, "201-500": 15},
                "S2": {"1-200": 10, "201-500": 30}, "S3": {"1-200": 25, "201-500": 75},
                "S4": {"1-200": 50, "201-500": 150}}
STEPS = ("A", "B", "C", "D", "E")

assert T_STAR <= pd.Timestamp(RESEARCH_CUTOFF)


class ProtocolMismatch(Exception):
    """The frozen protocol file or its registry record does not match the frozen SHA-256."""


class NotReady(Exception):
    """An open decision or missing evidence blocks execution (fail closed)."""


def file_sha256(path):
    return hashlib.sha256((BASE_DIR / path).read_bytes()).hexdigest()


def registration():
    """Current registry record for S2-MOM-v1 (amendments folded in)."""
    rec = experiments.current().get(PROTOCOL_ID)
    if rec is None:
        raise ProtocolMismatch(f"{PROTOCOL_ID} is not registered in registry/experiments.jsonl")
    return rec


def verify_protocol(path=None, record=None):
    """Refuse unless the protocol file AND its registry record carry the frozen SHA-256."""
    got = file_sha256(path or PROTOCOL_FILE)
    if got != PROTOCOL_SHA256:
        raise ProtocolMismatch(f"protocol file SHA-256 {got} != frozen {PROTOCOL_SHA256}")
    rec = record if record is not None else registration()
    if rec.get("protocol_sha256") != PROTOCOL_SHA256:
        raise ProtocolMismatch("registry record does not carry the frozen protocol SHA-256")
    return rec


def require_ready(record, need_costs=False):
    """Fail closed: every open decision must have been closed by a registry amendment."""
    pending = record.get("pending_decisions") or {}
    if pending:
        raise NotReady("open decisions block execution: " + ", ".join(sorted(pending)))
    missing = [k for k in DECISION_KEYS if k not in (record.get("decisions") or {})]
    if missing:
        raise NotReady(f"registry record lacks decisions: {missing}")
    wrong = {k: record["decisions"][k] for k, v in RESOLVED_DECISIONS.items() if record["decisions"][k] != v}
    if wrong:
        raise NotReady(f"registry decisions differ from the reviewed values: {wrong}")
    if need_costs:
        from src.stage3.costs import load_schedule, missing_evidence
        gaps = missing_evidence(load_schedule())
        if gaps:
            raise NotReady(f"cost evidence missing (never defaulted to zero): {gaps}")
    return record["decisions"]


# Reviewer decisions of 2026-10-05 (Phase 3B reviews). They interpret the frozen protocol; they do not
# amend it. Fixed in code, recorded in the registry, and checked by require_ready().
BOOTSTRAP_SEED = 20261005
RESOLVED_DECISIONS = {
    "sample_data_end": "PROTOCOL_EXIT_SESSION",    # protocol exit sessions; never after the research cutoff
    "p_value_distribution": "NORMAL",              # asymptotic standard normal for the Newey-West test
    "bootstrap_seed": BOOTSTRAP_SEED,
    "neutral_fill": "EQUAL_MEAN",                  # §20(b): simple mean of the other stocks' same-day returns
    "exit_gap_return_step_d": "REALISED_RAW_GAP_RETURN",   # §22 applied literally, steps C and D alike
    "exit_gap_lookahead": "TO_RESEARCH_CUTOFF",    # §22 'trades again later' / 'never trades again': all research data
}
PENDING_DECISIONS = {}
DECISION_KEYS = tuple(RESOLVED_DECISIONS)


def registry_entry():
    """The registry record. It references the frozen protocol; it does not restate it."""
    return {
        "experiment_id": PROTOCOL_ID,
        "protocol_id": PROTOCOL_ID, "protocol_version": PROTOCOL_VERSION, "protocol_file": PROTOCOL_FILE,
        "protocol_sha256": PROTOCOL_SHA256, "freeze_commit": FREEZE_COMMIT, "frozen_on": "2026-10-05",
        "registered_on": "2026-10-05",
        "research_question": "How much do common historical-data and backtesting shortcuts distort measured "
                             "cross-sectional momentum in Indian equities? (protocol §1)",
        "primary_estimand": "delta(t) = WML_A(t) - WML_D(t), monthly, percent (protocol §2)",
        "hypothesis": "H1: mean of delta != 0, two-sided, alpha 0.05 (protocol §2)",
        "null_hypothesis": "mean of delta = 0",
        "strategy": "S2-MOM-v1 12-1 cross-sectional momentum, bias ladder A-E",
        "instrument": "NSE EQ companies", "timeframe": "daily data, monthly holding",
        "universe": "UNIV-1 members (steps C-E); survivor pool variants (steps A-B); protocol B1 and §6",
        "universe_version": "UNIV-1", "universe_sha256": UNIV1_SHA256,
        "return_version": "RET-1.1 (ret_research, primary; special-session spans excluded); protocol §20",
        "identity_version": "ID-1",
        "start": "2012-07 (holding month)", "end": "2026-08 (holding month)",
        "primary_sample": {"holding_months": ["2012-07", "2021-12"], "first_selection_date": str(FIRST_T.date()),
                           "last_selection_date": str(PRIMARY_LAST_T.date()), "months": 114},
        "oos_sample": {"holding_months": ["2022-01", "2026-08"], "first_selection_date": "2021-12-31",
                       "last_selection_date": str(LAST_T.date()), "months": 56,
                       "nature": "chronological out-of-sample; not an independently designed experiment"},
        "dataset_id": "RET-1.1 + UNIV-1 + ID-1 (data/stage2), rebuilt by scripts/build_stage2.py",
        "dataset_sha256": "see data/stage3/s2_mom_v1/manifest.json (input hashes) once built",
        "dataset_stage": "stage2 research-grade", "feature_set": "past returns only",
        "parameters": {"formation_months": FORMATION_MONTHS, "skip_months": SKIP_MONTHS, "holding_months": 1,
                       "entry": "close of first session after the selection date", "breakpoint": BREAKPOINT,
                       "weights": "equal", "top_n": TOP_N, "t_star": str(T_STAR.date())},
        "training_period": "none (no fitting)", "validation_period": "none (nothing tuned)",
        "test_period": "primary 2012-07..2021-12; chronological OOS 2022-01..2026-08",
        "oos_status": "not run",
        "cost_model": "protocol §13: evidenced statutory/exchange/broker charges "
                      "(config/cost_schedules/delivery_nse_eq_s2mom.json) + assumed slippage scenarios",
        "slippage": SLIPPAGE_BPS, "benchmark": "equal weight of all rankable stocks in the same step (§24)",
        "cash_treatment": "fully invested; missed exits per §22", "dividends": "not included (price returns)",
        "random_seed": BOOTSTRAP_SEED,
        "statistical_tests": {"primary": "mean of delta, Newey-West HAC, lag 4, two-sided 5%",
                              "robustness": "stationary bootstrap, 10,000 resamples, automatic block length",
                              "reference_threshold_pct_per_month": REFERENCE_THRESHOLD},
        "results": "none - experiment not run",
        "limitations": "see protocol §30",
        "viewed_before_finalization": "no result computed or viewed",
        "provenance": {"code": "src/stage3/, scripts/build_stage3.py, scripts/run_s2_mom.py",
                       "data_manifest": "data/stage3/s2_mom_v1/manifest.json",
                       "blinded_precision_artifact_sha256": None, "primary_run": None, "confirmation_run": None},
        "pending_decisions": PENDING_DECISIONS, "decisions": dict(RESOLVED_DECISIONS),
        "status": "PLANNED",
    }


if __name__ == "__main__":      # one-off registration: python3 -m src.stage3.protocol
    if file_sha256(PROTOCOL_FILE) != PROTOCOL_SHA256:
        raise ProtocolMismatch("protocol file does not match the frozen SHA-256 - not registering")
    rec = experiments.record(registry_entry())
    experiments.write_md()
    print("registered", rec["experiment_id"], rec["status"])
