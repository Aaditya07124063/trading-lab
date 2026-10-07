"""F-03: the registry is a fail-closed, hash-chained state machine. Adversarial tests.

Every test works on a temporary registry file or on a temporary COPY of the real one. No test
writes registry/experiments.jsonl or registry/trials.jsonl.
"""

import hashlib
import itertools
import json
import shutil
import sys
from pathlib import Path

import pytest

from src.registry import experiments as reg
from src.registry.experiments import RegistryError

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "registry" / "experiments.jsonl"
H1, H2 = "a" * 64, "b" * 64


def entry(eid="T-1", status="PLANNED", **extra):
    return {k: "n/a" for k in reg.REQUIRED} | {"experiment_id": eid, "status": status, "protocol_sha256": H1,
                                              "protocol_id": eid, "provenance": {"primary_run": None}} | extra


@pytest.fixture
def R(tmp_path, monkeypatch):
    f = tmp_path / "experiments.jsonl"
    monkeypatch.setattr(reg, "EXPERIMENTS", f)
    return f


def walk(eid, *states):
    for s in states:
        reg.amend(eid, f"move to {s}", status=s, _revalidation=(s == "FINAL" and reg.current()[eid]["status"] == "REQUIRES REVALIDATION"))


def final(R, eid="T-1"):
    reg.record(entry(eid), env={"git_commit": "x"})
    reg.amend(eid, "primary registered", provenance={"primary_run": {"results_sha256": H1, "code_sha256": H2}})
    walk(eid, "READY", "EXECUTING", "REGISTERED", "FINAL")
    return R.read_bytes()


def refused(R, match, fn):
    before = R.read_bytes()
    with pytest.raises(RegistryError, match=match):
        fn()
    assert R.read_bytes() == before, "a refused action changed the registry file"


# ------------------------------------------------------------------ transitions
def test_the_documented_life_cycle_is_accepted_and_every_amendment_is_fully_described(R):
    final(R)
    assert reg.current()["T-1"]["status"] == "FINAL"
    lines = [json.loads(x) for x in R.read_text().splitlines()]
    for a in lines[1:]:
        assert all(k in a for k in reg.META), a
        assert a["amends"] == "T-1" and a["reason"].strip() and a["actor"].strip()
        assert a["amended_at"][-6] in "+-" and a["amended_at"][-3] == ":"            # timezone-aware timestamp
        assert a["changed_fields"] == sorted(k for k in a if k not in reg.META)
        assert set(a["previous_hashes"]) == set(a["new_hashes"]) == set(a["changed_fields"])
    assert [(a["previous_state"], a["new_state"]) for a in lines[2:]] == [
        ("PLANNED", "READY"), ("READY", "EXECUTING"), ("EXECUTING", "REGISTERED"), ("REGISTERED", "FINAL")]
    assert lines[1]["previous_hashes"]["provenance"] == hashlib.sha256(
        json.dumps({"primary_run": None}, sort_keys=True).encode()).hexdigest()


def test_transition_table_is_exactly_the_approved_one():
    T = reg.TRANSITIONS
    assert T["PLANNED"] >= {"READY"} and T["READY"] >= {"EXECUTING"} and T["EXECUTING"] >= {"REGISTERED"} and T["REGISTERED"] >= {"FINAL"}
    assert T["FINAL"] == {"SUPERSEDED", "INVALID", "REQUIRES REVALIDATION"}
    assert T["SUPERSEDED"] == set() == T["INVALID"]
    assert not {"PLANNED", "READY", "EXECUTING", "REGISTERED"} & set().union(*(T[s] for s in ("FINAL", "SUPERSEDED", "INVALID")))
    for legacy in reg.LEGACY_STATUSES:
        assert T[legacy] == T["FINAL"]
    assert "FINAL" not in T["PLANNED"] | T["READY"] | T["EXECUTING"]                   # no shortcut to FINAL


@pytest.mark.parametrize("a, b", [p for p in itertools.product(sorted(reg.STATUSES), repeat=2) if p[0] != p[1]])
def test_every_pair_of_states_is_decided_by_the_table_and_nothing_else(a, b):
    exp = {"status": a}
    rec = {"amends": "X", "amended_at": "t", "reason": "r", "actor": "test", "previous_state": a, "new_state": b,
           "changed_fields": ["status"], "previous_hashes": {"status": reg._sha(a)}, "new_hashes": {"status": reg._sha(b)},
           "revalidation_required": b == "REQUIRES REVALIDATION" or a == "REQUIRES REVALIDATION", "chain_prev_sha256": "x", "status": b}
    if b in reg.TRANSITIONS[a]:
        reg._check_amendment(exp, rec)
    else:
        with pytest.raises(RegistryError, match="illegal transition"):
            reg._check_amendment(exp, rec)


@pytest.mark.parametrize("target", ["PLANNED", "READY", "EXECUTING", "REGISTERED", "EXPLORATORY", "DIAGNOSTIC"])
def test_final_cannot_be_downgraded(R, target):
    final(R)
    refused(R, "illegal transition FINAL", lambda: reg.amend("T-1", "downgrade", status=target))
    assert reg.current()["T-1"]["status"] == "FINAL"


def test_no_shortcuts_and_terminal_states_are_terminal(R):
    reg.record(entry(), env={})
    refused(R, "illegal transition PLANNED -> FINAL", lambda: reg.amend("T-1", "skip", status="FINAL"))
    refused(R, "illegal transition PLANNED -> EXECUTING", lambda: reg.amend("T-1", "skip", status="EXECUTING"))
    refused(R, "unknown status", lambda: reg.amend("T-1", "typo", status="DONE"))
    walk("T-1", "INVALID")
    for s in ("PLANNED", "FINAL", "SUPERSEDED", "REQUIRES REVALIDATION"):
        refused(R, "illegal transition INVALID", lambda s=s: reg.amend("T-1", "revive", status=s))


# ------------------------------------------------------------------ protected fields
@pytest.mark.parametrize("change", [
    {"protocol_sha256": H2}, {"provenance": {"primary_run": {"results_sha256": H2, "code_sha256": H2}}},
    {"provenance": {}}, {"results": "better"}, {"hypothesis": "new"}, {"parameters": {"top_n": 201}},
    {"random_seed": 1}, {"environment": {}}, {"brand_new_field": 1}, {"status": "SUPERSEDED", "results": "x"},
    {"protocol_sha256": H1},          # even a same-value rewrite of a protected field is refused
])
def test_protected_fields_of_a_final_experiment_are_immutable(R, change):
    final(R)
    refused(R, "immutable", lambda: reg.amend("T-1", "attack", **change))


def test_anchors_can_be_added_to_a_final_experiment_but_never_changed_or_removed(R):
    final(R)
    reg.anchor("T-1", "anchor the manifest", stage3_manifest_sha256=H1)
    reg.anchor("T-1", "anchor a second thing", other={"x.json": H2})
    assert reg.current()["T-1"]["anchors"] == {"stage3_manifest_sha256": H1, "other": {"x.json": H2}}
    refused(R, "already recorded", lambda: reg.anchor("T-1", "re-anchor", stage3_manifest_sha256=H2))
    refused(R, "only gain keys", lambda: reg.amend("T-1", "replace", anchors={"stage3_manifest_sha256": H2, "other": {"x.json": H2}}))
    refused(R, "only gain keys", lambda: reg.amend("T-1", "drop", anchors={"other": {"x.json": H2}}))
    refused(R, "only gain keys", lambda: reg.amend("T-1", "nested", anchors={"stage3_manifest_sha256": H1, "other": {"x.json": H1}}))
    refused(R, "only gain keys", lambda: reg.amend("T-1", "not a dict", anchors="x"))


def test_recorded_hashes_cannot_be_replaced_before_final_either(R):
    reg.record(entry(), env={"git_commit": "x"})
    reg.amend("T-1", "blinded", provenance={"primary_run": None, "blinded_sha256": H1})          # None -> value: allowed
    reg.amend("T-1", "primary", provenance={"primary_run": {"results_sha256": H1}, "blinded_sha256": H1})
    refused(R, "recorded hash", lambda: reg.amend("T-1", "swap result", provenance={"primary_run": {"results_sha256": H2}, "blinded_sha256": H1}))
    refused(R, "recorded hash", lambda: reg.amend("T-1", "drop result", provenance={"blinded_sha256": H1}))
    refused(R, "protocol_sha256 cannot be replaced", lambda: reg.amend("T-1", "new protocol", protocol_sha256=H2))
    refused(R, "environment cannot be replaced", lambda: reg.amend("T-1", "env", environment={"git_commit": "y"}))
    refused(R, "only possible in state REQUIRES REVALIDATION", lambda: reg.amend("T-1", "fake", _revalidation=True, protocol_sha256=H2))
    reg.amend("T-1", "decision closed", decisions={"a": 1})                                      # ordinary planning field: allowed
    assert reg.current()["T-1"]["provenance"]["primary_run"] == {"results_sha256": H1}


def test_hashes_change_only_through_explicit_revalidation(R):
    final(R)
    reg.amend("T-1", "input defect found", status="REQUIRES REVALIDATION")
    last = json.loads(R.read_text().splitlines()[-1])
    assert last["revalidation_required"] is True and last["previous_state"] == "FINAL"
    refused(R, "cannot be replaced without explicit revalidation", lambda: reg.amend("T-1", "quiet swap", protocol_sha256=H2))
    refused(R, "recorded hash", lambda: reg.amend("T-1", "quiet swap", provenance={"primary_run": {"results_sha256": H2, "code_sha256": H2}}))
    refused(R, "needs an explicit revalidation", lambda: reg.amend("T-1", "back to final", status="FINAL"))
    reg.amend("T-1", "revalidated against protocol v2", _revalidation=True, protocol_sha256=H2,
              provenance={"primary_run": {"results_sha256": H2, "code_sha256": H2}})
    last = json.loads(R.read_text().splitlines()[-1])
    assert last["revalidation_required"] is True and last["previous_hashes"]["protocol_sha256"] == reg._sha(H1) \
        and last["new_hashes"]["protocol_sha256"] == reg._sha(H2)
    reg.amend("T-1", "revalidation complete", _revalidation=True, status="FINAL")
    cur = reg.current()["T-1"]
    assert cur["status"] == "FINAL" and cur["protocol_sha256"] == H2
    assert [h.get("protocol_sha256") for h in cur["history"] if "protocol_sha256" in h] == [H1]      # the old hash is kept


@pytest.mark.parametrize("reason", ["", "   ", "\n", None, 7])
def test_empty_amendment_reasons_are_refused(R, reason):
    reg.record(entry(), env={})
    refused(R, "empty reason", lambda: reg.amend("T-1", reason, decisions={}))


def test_reserved_and_derived_fields_cannot_be_amended(R):
    reg.record(entry(), env={})
    for k in ("amends", "previous_state", "chain_prev_sha256", "actor", "amended_at"):
        refused(R, "reserved", lambda k=k: reg.amend("T-1", "x", **{k: "y"}))
    refused(R, "derived", lambda: reg.amend("T-1", "x", history=[]))
    with pytest.raises(KeyError):
        reg.amend("NOPE", "x", status="READY")


# ------------------------------------------------------------------ records
def test_new_records_duplicate_ids_unknown_and_non_initial_statuses(R):
    with pytest.raises(RegistryError, match="unknown status"):
        reg.record(entry(status="DONE"), env={})
    for s in ("READY", "EXECUTING", "REGISTERED", "SUPERSEDED", "INVALID", "REQUIRES REVALIDATION"):
        with pytest.raises(RegistryError, match="cannot start in state"):
            reg.record(entry(status=s), env={})
    with pytest.raises(RegistryError, match="missing fields"):
        reg.record({"status": "PLANNED"}, env={})
    assert not R.exists() or R.read_bytes() == b""
    reg.record(entry(), env={})
    refused(R, "already registered", lambda: reg.record(entry(), env={}))
    refused(R, "already registered", lambda: reg.record(entry(status="FINAL", results="other"), env={}))


# ------------------------------------------------------------------ fail-closed parser
def tamper(R, fn):
    lines = R.read_bytes().split(b"\n")[:-1]
    out = fn(lines)
    R.write_bytes(out if isinstance(out, bytes) else b"".join(x + b"\n" for x in out))


@pytest.mark.parametrize("name, fn, match", [
    ("truncated last line", lambda L: b"\n".join(L)[:-20], "truncated"),
    ("garbage line", lambda L: L + [b"not json"], "unreadable"),
    ("blank line", lambda L: L[:2] + [b""] + L[2:], "unreadable"),
    ("non-record line", lambda L: L + [b"[1, 2]"], "not a record"),
    ("duplicate experiment record (never last-wins)", lambda L: L + [L[0]], "duplicates an earlier record"),
    ("second record with the same id", lambda L: L + [json.dumps(json.loads(L[0]) | {"results": "other"}).encode()], "hash chain|duplicate experiment id"),
    ("exact duplicate amendment", lambda L: L + [L[-1]], "duplicates an earlier record"),
    ("edited middle line", lambda L: L[:2] + [L[2].replace(b"READY", b"READY ")] + L[3:], "hash chain|misstates|unknown status"),
    ("removed middle line", lambda L: L[:2] + L[3:], "hash chain"),
    ("reordered lines", lambda L: L[:2] + [L[3], L[2]] + L[4:], "hash chain"),
    ("amendment before its record", lambda L: [L[1], L[0]] + L[2:], "unknown experiment|hash chain"),
    ("legacy-format amendment appended by hand", lambda L: L + [b'{"amends": "T-1", "amended_at": "x", "reason": "x", "status": "PLANNED"}'], "hash chain"),
    ("duplicate key inside a line", lambda L: L[:-1] + [L[-1][:-1] + b', "status": "PLANNED"}'], "duplicate key"),
])
def test_parser_fails_closed(R, name, fn, match):
    final(R)
    tamper(R, fn)
    with pytest.raises(RegistryError, match=match):
        reg.current()
    with pytest.raises(RegistryError):                         # and nothing can be appended to a broken registry
        reg.amend("T-1", "after tamper", status="SUPERSEDED")


def forge(R, **fields):
    """A hand-made amendment with a CORRECT hash chain and self-consistent hashes - only the rules can stop it."""
    exp, raw = reg.current()["T-1"], R.read_bytes()
    changes = {k: v for k, v in fields.items() if k not in reg.META}
    rec = {"amends": "T-1", "amended_at": "2026-10-07T00:00:00+05:30", "reason": "forged", "actor": "attacker",
           "previous_state": exp["status"], "new_state": changes.get("status", exp["status"]), "changed_fields": sorted(changes),
           "previous_hashes": {k: (reg._sha(exp[k]) if k in exp else None) for k in sorted(changes)},
           "new_hashes": {k: reg._sha(v) for k, v in sorted(changes.items())}, "revalidation_required": False,
           "chain_prev_sha256": hashlib.sha256(raw).hexdigest(), **fields}
    R.write_bytes(raw + json.dumps(rec).encode() + b"\n")


@pytest.mark.parametrize("fields, match", [
    ({"status": "PLANNED"}, "illegal transition FINAL -> PLANNED"),
    ({"status": "EXECUTING"}, "illegal transition"),
    ({"protocol_sha256": H2}, "immutable"),
    ({"provenance": {"primary_run": {"results_sha256": H2}}}, "immutable"),
    ({"status": "SUPERSEDED", "reason": " "}, "empty reason"),
    ({"status": "SUPERSEDED", "actor": ""}, "no actor"),
    ({"status": "SUPERSEDED", "previous_state": "REGISTERED"}, "misstates the state"),
    ({"status": "SUPERSEDED", "changed_fields": []}, "changed_fields"),
    ({"status": "SUPERSEDED", "new_hashes": {"status": H1}}, "hashes do not match"),
    ({"status": "FINAL", "revalidation_required": True}, "only possible in state"),
])
def test_a_hand_forged_amendment_with_a_valid_chain_is_still_refused_on_read(R, fields, match):
    final(R)
    forge(R, **fields)
    with pytest.raises(RegistryError, match=match):
        reg.current()


def test_a_forged_amendment_without_required_metadata_is_refused(R):
    final(R)
    raw = R.read_bytes()
    R.write_bytes(raw + json.dumps({"amends": "T-1", "reason": "x", "status": "SUPERSEDED",
                                    "chain_prev_sha256": hashlib.sha256(raw).hexdigest()}).encode() + b"\n")
    with pytest.raises(RegistryError, match="lacks"):
        reg.current()


# ------------------------------------------------------------------ the real registry (temporary copy)
@pytest.fixture
def real_copy(tmp_path, monkeypatch):
    f = tmp_path / "experiments.jsonl"
    shutil.copy(REAL, f)
    monkeypatch.setattr(reg, "EXPERIMENTS", f)
    monkeypatch.setattr(reg, "_CANONICAL", f)                  # the copy gets the pinned history of the real file
    return f


def test_registered_history_is_pinned_and_folds_to_the_pre_remediation_view(tmp_path):
    raw = REAL.read_bytes()
    prefix = b"".join(x + b"\n" for x in raw.split(b"\n")[:reg.GENESIS_LINES])
    assert hashlib.sha256(prefix).hexdigest() == reg.GENESIS_SHA256
    f = tmp_path / "prefix.jsonl"
    f.write_bytes(prefix)
    view = json.dumps(reg.load(f, (reg.GENESIS_LINES, reg.GENESIS_SHA256)), sort_keys=True, default=str)
    # the folded view of the 58 historical lines, as produced by the pre-remediation code (7d4cb6d)
    assert hashlib.sha256(view.encode()).hexdigest() == "6c09fdf45d214347d65d549f11cd180e0ceff38c94f8fc2d4bd43fa5c6228b88"
    assert reg.current()["S2-MOM-v1"]["status"] == "FINAL"


@pytest.mark.parametrize("fn", [
    lambda L: [L[0].replace(b"LEGACY-001", b"LEGACY-00X")] + L[1:],
    lambda L: L[:40] + L[41:],                                  # drop the Stage 2 rebuild amendment
    lambda L: L[:52] + L[53:],                                  # drop PLANNED -> FINAL
    lambda L: L[:42] + [L[42].replace(b"fe7e95ba", b"00000000")] + L[43:],      # re-point the primary result hash
    lambda L: L[:37],                                           # truncate the history
    lambda L: [],
])
def test_any_rewrite_of_the_registered_history_is_detected(real_copy, fn):
    tamper(real_copy, fn)
    with pytest.raises(RegistryError, match="registered history|hash chain|unknown experiment"):
        reg.current()


def test_missing_real_registry_fails_closed(real_copy):
    real_copy.unlink()
    with pytest.raises(RegistryError, match="missing"):
        reg.current()


@pytest.mark.parametrize("attack", [
    lambda: reg.amend("S2-MOM-v1", "x", status="PLANNED"),
    lambda: reg.amend("S2-MOM-v1", "x", status="EXECUTING"),
    lambda: reg.amend("S2-MOM-v1", "x", status="READY"),
    lambda: reg.amend("S2-MOM-v1", "x", protocol_sha256="0" * 64),
    lambda: reg.amend("S2-MOM-v1", "x", provenance={"primary_run": {"files_sha256": {}, "code_sha256": "f"}}),
    lambda: reg.amend("S2-MOM-v1", "", status="SUPERSEDED"),
    lambda: reg.amend("S2-MOM-v1", "x", results={"headline": "momentum works"}),
    lambda: reg.amend("S2-MOM-v1", "x", addenda=[]),
    lambda: reg.amend("S2-MOM-v1", "x", decisions={}),
    lambda: reg.amend("LEGACY-001", "x", provenance={"stage2_rebuild": {"checks_passed": 150}}),
    lambda: reg.amend("LEGACY-001", "x", status="FINAL"),
    lambda: reg.record(json.loads(REAL.read_text().splitlines()[37])),
])
def test_attacks_on_the_registered_experiment_are_refused(real_copy, attack):
    before = real_copy.read_bytes()
    with pytest.raises(RegistryError):
        attack()
    assert real_copy.read_bytes() == before


def test_the_frozen_runners_can_no_longer_re_register_a_run(real_copy):
    """scripts/run_s2_mom*.py register by replacing `provenance`; on a FINAL experiment that is refused."""
    rec = reg.current()["S2-MOM-v1"]
    before = real_copy.read_bytes()
    with pytest.raises(RegistryError, match="immutable"):
        reg.amend("S2-MOM-v1", "primary run registered", provenance={**rec["provenance"], "primary_run": {"results_sha256": H1}})
    assert real_copy.read_bytes() == before


# ------------------------------------------------------------------ trial log and environment (F-11, F-26)
def test_trial_log_cannot_be_silenced_outside_the_test_suite(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "TRIALS", tmp_path / "trials.jsonl")
    assert reg.log_trial("k", {}, "d", {}, "s") is None and not reg.TRIALS.exists()      # conftest sets the variable
    monkeypatch.delitem(sys.modules, "pytest")
    with pytest.raises(RegistryError, match="outside the test suite"):
        reg.log_trial("k", {}, "d", {}, "s")
    monkeypatch.delenv("TRADING_LAB_NO_TRIAL_LOG")
    assert reg.log_trial("k", {}, "d", {}, "s")["kind"] == "k" and reg.trial_count("k") == 1
    reg.TRIALS.write_text(reg.TRIALS.read_text() + '{"at": "trunc')
    with pytest.raises(RegistryError, match="truncated"):
        reg.trial_count()


def test_environment_records_every_numerical_dependency_and_the_platform():
    env = reg.environment()
    assert {"pandas", "numpy", "scipy", "pyarrow"} <= set(env["packages"])
    assert all(env["packages"][p] != "not installed" for p in ("pandas", "numpy", "scipy", "pyarrow"))
    assert env["python"] and env["platform"] and env["machine"] and "unknown" not in (env["git_commit"],)


def _append_with_valid_chain(R, rec):
    raw = R.read_bytes()
    R.write_bytes(raw + json.dumps({**rec, "chain_prev_sha256": hashlib.sha256(raw).hexdigest()}).encode() + b"\n")


def test_a_second_record_with_the_same_id_is_refused_even_with_a_valid_chain(R):
    """Never 'last record wins': a complete, chain-linked second record for an existing id must stop every read."""
    final(R)
    _append_with_valid_chain(R, entry("T-1", status="PLANNED", results="a fresh start"))
    with pytest.raises(RegistryError, match="duplicate experiment id 'T-1'"):
        reg.current()


def test_an_amendment_of_an_unknown_experiment_is_refused_even_with_a_valid_chain(R):
    final(R)
    _append_with_valid_chain(R, {"amends": "GHOST", "amended_at": "2026-10-08T00:00:00+05:30", "reason": "x", "actor": "attacker",
                                 "previous_state": "PLANNED", "new_state": "PLANNED", "changed_fields": [], "previous_hashes": {},
                                 "new_hashes": {}, "revalidation_required": False})
    with pytest.raises(RegistryError, match="amends unknown experiment 'GHOST'"):
        reg.current()
