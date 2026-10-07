"""Writes the data-driven audit files from recorded evidence (no judgement is computed here: statuses are stated below).

    python3 docs/audit/remediation/build_tables.py

Reads   docs/audit/forensic_20261007/findings.json           (the original 30 findings, never modified)
        docs/audit/remediation/mutation_final/*.json          (scripts/mutation_campaign.py)
Writes  docs/audit/findings.json, docs/audit/requirements_traceability.csv, docs/audit/test_matrix.csv,
        docs/audit/MUTATION_FINAL_REPORT.md
"""

import csv
import json
from collections import Counter
from pathlib import Path

A = Path(__file__).resolve().parents[1]
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("mutation_campaign", A.parents[1] / "scripts" / "mutation_campaign.py")
CAMPAIGN = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CAMPAIGN)
DEFINED = [m[1] for m in CAMPAIGN.M + CAMPAIGN.EXTRA]


def _rows(pattern):
    return {f.name: [json.loads(x) for x in f.read_text().splitlines()] for f in sorted((A / "remediation").glob(pattern))}
ORIG = json.loads((A / "forensic_20261007/findings.json").read_text())
MUT = json.loads((A / "remediation/mutation_final/mutation_results.json").read_text())
BEFORE = json.loads((A / "remediation/mutation_forensic_20261007.json").read_text())      # the forensic campaign, 104 mutations
K = "tests/test_s2mom_mutation_kills.py"
REG, PROV, FI, REP, ENV, VC, ARCH, FC, MS = ("tests/test_registry_state_machine.py", "tests/test_provenance_chain.py", "tests/test_failure_injection.py",
                                             "tests/test_reproduction.py", "tests/test_environment.py", "tests/test_version_control.py",
                                             "tests/test_release_archive.py", "tests/test_frozen_code.py", "tests/test_manuscript_verification.py")

# id: (status, remediation, regression test, adversarial test, evidence)
S = {
 "F-01": ("FIXED + REGRESSION PROTECTED", "CLOSED 2026-10-08. Research release committed (f5bfed89bc7b1bd258dbe81ff9da2be8f44acbdc), tagged s2-mom-v1-release-1, pushed to the private origin; data archive packed to an external USB drive and verified; a fresh clone of the tag with the data restored from that drive passed the suite and the reproduction (F01_CLOSURE_PLAN.md, Closure record). Before that: all research-critical files staged for one commit. Large data outside Git: content-addressed archive manifest (5,637 files, SHA-256 each), deterministic tar hash, manifest and tar hash anchored in the registry, verify/pack/materialize tool. Guard test fails on any untracked or merely ignored research file.",
          f"{VC} (3); {ARCH} (11)", f"{ARCH}: changed, missing, extra file; rewritten manifest; wrong tar; path traversal; symlink; no overwrite",
          "F01_CLOSURE_PLAN.md Closure record: remote ref and tag verified, USB tar SHA-256 bb4b9659...1ac2 re-read, fresh clone 960 passed (tag) / 964 passed (main), reproduction PASS in a clean Conda environment."),
 "F-02": ("FIXED + REGRESSION PROTECTED", "Registry anchor (line 59) of the Stage 3 manifest SHA-256; verifier walks registry -> manifest -> files, Stage 2 inputs, code hashes; exact file set; no symlink, traversal or duplicate entry.",
          f"{PROV} (24)", f"{PROV}; {FI}: 18 file attacks on inputs, manifest, code", "PROVENANCE_VERIFICATION_REPORT.md; mutation group 'guards and registry' (provenance mutations)"),
 "F-03": ("FIXED + REGRESSION PROTECTED", "src/registry/experiments.py rewritten: state machine, protected fields, explicit revalidation, full amendment metadata, hash chain, pinned history, fail-closed reader, lock + fsync.",
          f"{REG} (235)", f"{REG}: 156 state pairs, forged amendments with a valid chain, parser attacks, history rewrites; {FI}: 11 registry attacks on a copy of the real registry",
          "REGISTRY_SECURITY_REPORT.md; the 58 historical lines fold to the pre-remediation view (hash pinned in a test)"),
 "F-04": ("FIXED + REGRESSION PROTECTED", "Tests written against the surviving mutations: hand-computed golden ladder world, hand Newey-West, both bootstrap tails, 12-row decision table, runner gates, loader hash checks, Stage 2 rules, step E rates; mutation campaign tool with recorded batches.",
          f"{K} (68)", "scripts/mutation_campaign.py on scratch clones", "MUTATION_FINAL_REPORT.md"),
 "F-05": ("FIXED + REGRESSION PROTECTED", "scripts/reproduce_s2_mom_v1.py: 8 steps, independent implementation of ladder A-D, delta, Newey-West, step E costs, C2 arithmetic; read-only; fail closed.",
          f"{REP} (17)", f"{FI}: 46 file attacks through the verification steps", "REPRODUCTION_REPORT.md: PASS in the registered interpreter and in a clean Conda environment; 8,257 numbers, all within 1e-9; largest difference 6.7e-14"),
 "F-06": ("FIXED + REGRESSION PROTECTED", "Conda contract (environment.yml, conda-osx-arm64.lock), ENVIRONMENT.json and requirements-lock.txt (exact pins), anchored in the registry (lines 60 and 61); environment() records scipy, pyarrow, platform; verifier reports versions, missing, mismatched and unloadable libraries.",
          f"{ENV} (9)", f"{FI}: 3 environment-metadata attacks; {ENV}: simulated missing / mismatched / unloadable library", "DEPENDENCY_FINAL_REPORT.md: official environment = Conda osx-arm64; clean Conda rebuild reproduces (PASS); pip unsupported and documented; second machine untested (N-01)."),
 "F-07": ("REPORT-ONLY FROZEN", "Frozen ladder.wide() unchanged. Outside it: integrity.validate_stage3 rejects duplicates, NaN, inf, returns <= -100%, unknown classes, wrong counts, before any recomputation; the comparison refuses NaN/inf.",
          f"{FI} (43 value attacks)", f"{FI}", "FAILURE_INJECTION_REPORT.md section 4.2. The frozen runner path itself still does not validate; it cannot run again for v1."),
 "F-08": ("REPORT-ONLY FROZEN", "Frozen runner unchanged (documented limitation). Registered outputs cannot be replaced silently: hash check, unregistered-file check, registry refuses re-registration on FINAL. New tooling writes tmp + fsync + rename.",
          f"{K}::test_each_mode_runs_once_an_existing_output_is_never_overwritten; {FI}::test_an_interrupted_write_never_leaves_a_complete_looking_file", f"{FI}: truncate an output, add an unexpected file (results), unregistered rerun",
          "REMEDIATION_REPORT.md section 8"),
 "F-09": ("ACCEPTED RISK", "Registered code hashes cannot be widened without changing registered values. Every executed first-party file, hashed or not, is now pinned to the pre-remediation snapshot by a test.",
          f"{FC} (37 files)", "mutation campaign: resampler and Stage 2 mutations killed behaviourally", "A library upgrade is still outside every hash; the numerical comparison of the reproduction is the control."),
 "F-10": ("REPORT-ONLY FROZEN", "13 assert statements inventoried (7 data.py, 1 protocol.py, 1 access.py, 4 evaluate_orb_v1.py). The 9 on the S2-MOM path are restated as explicit raises (validate_stage3, validate_cutoffs). The reproduction refuses python -O.",
          f"{ENV}::test_inventory_of_assert_statements_in_frozen_research_code_is_complete, ::test_python_O_really_disables_the_frozen_asserts_and_the_explicit_checks_still_fire, ::test_cutoff_asserts_are_restated_as_explicit_checks",
          f"{FI}: last session is not T*, 113 months, 199-stock universe, step A list changes", "The 4 asserts of the ORB evaluator are not restated (single-use frozen evaluator; runbook rule)."),
 "F-11": ("FIXED + REGRESSION PROTECTED", "log_trial: the variable suppresses logging only inside pytest; anywhere else it raises.", f"{REG}::test_trial_log_cannot_be_silenced_outside_the_test_suite",
          "mutation '+ trial log silenced outside pytest'", "REGISTRY_SECURITY_REPORT.md"),
 "F-12": ("FIXED + REGRESSION PROTECTED", "Pre-run check files and the Stage 2 rebuild log anchored in the registry; the reproduction requires all_passed with the registered code hash and recounts 150 OK lines in the log.",
          f"{PROV}::test_stage2_inputs_code_and_check_files_are_part_of_the_chain", f"{FI}", "PROVENANCE_VERIFICATION_REPORT.md section 4 (residual: the log proves no change since 2026-10-07, not what happened on 2026-10-05)"),
 "F-13": ("REPORT-ONLY FROZEN", "No change. The real-data perturbation check is narrower than protocol B2 says. Needs a reviewer ruling or a deviation entry (researcher's decision).", "-", "-", "forensic RESEARCH_INTEGRITY_AUDIT.md"),
 "F-14": ("OPEN", "Not changed: server.py is the web UI (out of scope of this phase by instruction) and is not on the S2-MOM path.", "-", "-", "THREAT_MODEL.md T13"),
 "F-15": ("OPEN", "Not changed. The snapshot verifier and the reproduction now separate collector files from research files. The collector exited 1 again on 2026-10-07 18:30.", "-", "-", "logs/; needs the researcher's review inside Yahoo's 60-day window"),
 "F-16": ("REPORT-ONLY FROZEN", "No change (archive.py hash is embedded in Stage 2 manifests). Every archived raw file is now also in the external archive manifest.", f"{ARCH}", "-", "-"),
 "F-17": ("REPORT-ONLY FROZEN", "Frozen step_e.net_returns unchanged. Outside it: validate_step_e and a registered-file test reject any zero, missing or non-finite cost; the independent cost function raises on a missing rank.",
          f"{K}::test_step_e_net_is_gross_minus_cost_and_gross_is_copied_unchanged_in_the_registered_files; {FI}::test_step_e_validation_refuses_zero_missing_or_non_finite_costs", "mutation '+ validation: zero cost accepted'", "every registered month has a positive cost (340 months x 15 columns)"),
 "F-18": ("OPEN", "Not changed (ORB v1 evaluator, not S2-MOM).", "-", "-", "forensic TEST_COVERAGE_AUDIT.md"),
 "F-19": ("REPORT-ONLY FROZEN", "No change. The independent implementation applies the same per-portfolio rule; cross-portfolio re-count in the registered runs: 0 (forensic audit).", f"{REP}", "-", "note for S2-MOM-v2"),
 "F-20": ("ACCEPTED RISK", "Duplicated constants remain in frozen files. New: the reproduction restates the protocol constants independently and a test requires them to equal the frozen ones.",
          f"{REP}::test_the_script_restates_the_protocol_constants_independently_and_they_agree", "-", "-"),
 "F-21": ("OPEN", "No change. The pre-registered information ratio is not reported and not in the deviation log. Researcher's decision.", "-", "-", "RESEARCH decision R-x of the forensic audit"),
 "F-22": ("REPORT-ONLY FROZEN", "No change to the rule. All four labels are now pinned by a 12-row table test and by a check that the registered labels follow from the registered numbers.",
          f"{K}::test_h1_decision_table, ::test_registered_h1_labels_follow_from_the_registered_numbers", "mutations 'H1 decision threshold flipped', '+ MATERIAL without the size condition', '+ IMMATERIAL without the interval condition'", "the reading 'significant but inside +/-0.10 = DETECTED_SIZE_UNCERTAIN' still needs a reviewer ruling"),
 "F-23": ("REPORT-ONLY FROZEN", "No change. Guard from outside: tests and the reproduction check that the lag equals floor(4 (n/100)^(2/9)) for the registered n.", f"{K}::test_frozen_lags_equal_the_protocol_formula_for_the_registered_sample_sizes", "mutations 'NW lag primary 4->5', '+ NW lag OOS 3->4'", "-"),
 "F-24": ("REPORT-ONLY FROZEN", "No change (Stage 2 code hash embedded in manifests).", "-", "-", "-"),
 "F-25": ("REPORT-ONLY FROZEN", "No change. Guard from outside: validate_delisting_types fails on any delisting wording other than the three known ones.", "reproduction step 5", "-", "observed: Voluntary Delisting, Compulsory Delisting, Delisting - Liquidation"),
 "F-26": ("FIXED + REGRESSION PROTECTED", "environment(): explicit 'git unavailable' instead of swallowed exceptions; platform and architecture recorded; new registry lines carry timezone-aware timestamps. Not changed: git_dirty still looks at src and *.py only.",
          f"{REG}::test_environment_records_every_numerical_dependency_and_the_platform, ::test_the_documented_life_cycle_is_accepted_and_every_amendment_is_fully_described", "-", "-"),
 "F-27": ("REPORT-ONLY FROZEN", "No change. Disclosure item: the placebo gate has a built-in 5% false-failure rate (p = 0.054 in the confirmation sample). The check files are now anchored.", "-", "-", "-"),
 "F-28": ("FIXED", "REPRODUCIBILITY.md has a full S2-MOM-v1 section; README points to it; CHANGELOG updated; SYSTEM_ARCHITECTURE.md and DATA_FLOW.md rewritten as the system map.", "-", "-", "documentation; no executable regression test"),
 "F-29": ("FIXED + REGRESSION PROTECTED", "The reproduction compares numbers at 1e-9 and reports environment differences; frozen byte-identity checks are unchanged for the protected runs.", f"{FI}::test_the_numerical_comparison_refuses_nan_inf_shape_and_out_of_tolerance_values", "mutations '+ repro: tolerance 1e-9 -> 1', '+ repro: comparison never fails'", "REPRODUCTION_REPORT.md"),
 "F-30": ("ACCEPTED RISK", "Frozen modules can still be imported and called directly. A result computed that way cannot be registered on the FINAL experiment; an extra trial-log line fails the reproduction. A private computation that logs nothing cannot be prevented by code.",
          f"{REG}::test_the_frozen_runners_can_no_longer_re_register_a_run", f"{FI}: unregistered rerun", "THREAT_MODEL.md T4; runbook rule 3"),
}
NEW = [
 {"id": "N-01", "severity": "P3", "file": "release/s2_mom_v1/ ; requirements-lock.txt", "description": "Reproducibility contract. Found during remediation: a fresh venv built with pip from the pinned versions cannot load scipy 1.15.3 on macOS 27 arm64 (the PyPI wheel has a malformed zero-fill section that the loader rejects); the reproduction fails closed. Resolved: the official environment is stated as Conda osx-arm64 (environment.yml, conda-osx-arm64.lock), pip is documented as unsupported, and a clean Conda environment built from environment.yml reproduced the results (PASS). Still open: no second machine, OS or CPU has been tried, and the lab's daily work still runs in the shared Anaconda base environment.",
  "why_it_matters": "Third-party reproduction is demonstrated on one machine only. A conda update of the base environment changes the study's environment.", "proposed_fix": "Run the reproduction once on a second Apple-silicon Mac; work in the dedicated s2mom environment.",
  "status": "OPEN", "evidence": "DEPENDENCY_FINAL_REPORT.md; REPRODUCTION_REPORT.md runs C, D, E"},
 {"id": "N-02", "severity": "P3", "file": "docs/manuscript/s2_mom_v1/manuscript.md", "description": "Table A5 prints the hashes of the protocol, Addendum 1, Supplement 1 and Supplement 4, but not of Supplements 2 and 3, although the text cites Supplements 1-4 and says 'Hashes are in Appendix Table A5'.",
  "why_it_matters": "Incomplete disclosure table in a draft manuscript. No result is affected: both supplements are registered in the registry record (addenda) with their SHA-256, the files match, the reproduction verifies them, and no specification requires Table A5 to be complete (the builder's list is a curated selection; no protocol, supplement, results guide or C2 specification defines the table).",
  "proposed_fix": "Add the two rows in the next manuscript revision (two lines in REGISTERED of build_manuscript.py, then rebuild). Not done now: the rebuild rewrites manuscript.md/.html/.docx/.pdf and number_audit.csv, which are frozen in this pre-release phase.",
  "status": "ACCEPTED RISK", "evidence": "MANUSCRIPT_VERIFICATION_REPORT.md; PRE_RELEASE_CHECKLIST.md section 3. Classified DOCUMENTATION ONLY, not a release requirement."},
 {"id": "N-03", "severity": "P3", "file": "registry/experiments.jsonl", "description": "Removing lines from the END of the registry leaves a valid shorter history. It is detected only where something depends on those lines (the reproduction requires the anchors and state FINAL) and by Git.",
  "why_it_matters": "Tail truncation is not caught by the registry module alone.", "proposed_fix": "Push the repository; optionally pin the registry head hash in each release note.", "status": "ACCEPTED RISK", "evidence": "REGISTRY_SECURITY_REPORT.md section 5"},
 {"id": "N-04", "severity": "P3", "file": "results/s2_mom_v1/sensitivity_results.json", "description": "The six sensitivity treatments and the reverse-order ladder are not recomputed by the independent implementation; they are verified by hash, by code hash and by internal arithmetic only. The bootstrap p-value is recomputed with the registered resampler, not a second one.",
  "why_it_matters": "For these numbers the evidence is 'unchanged since registration', not 'independently reproduced'.", "proposed_fix": "Extend the independent implementation, if the researcher wants that evidence.", "status": "ACCEPTED RISK", "evidence": "REPRODUCTION_REPORT.md section 2"},
 {"id": "N-05", "severity": "P2", "file": "host machine", "description": "The laptop holding the only copy has about 3 GB of free disk and several GB of swap in use. During remediation a parallel test run filled the disk once (on scratch clones only; the repository was verified intact afterwards).",
  "why_it_matters": "A full disk can interrupt a write of the registry or of the collector, and it blocks making the archive tar.", "proposed_fix": "Free disk space (about 2 GB of stale scratch copies from the forensic audit session are under /private/tmp/claude-501/); then pack the archive to external storage.", "status": "OPEN", "evidence": "REMEDIATION_REPORT.md section 12"},
 {"id": "N-06", "severity": "P3", "file": "docs/manuscript/s2_mom_v1/ (section 15, 'Repository state')", "description": "The manuscript said the code, results and manuscript were 'not yet committed'. Corrected on 2026-10-08 after the release commit, as one presentation sentence, in manuscript.template.md, manuscript.md, manuscript.html and manuscript.docx; tests/test_manuscript_n06.py proves that undoing that sentence restores the registered bytes. manuscript.pdf was NOT rebuilt (rebuild excluded by the researcher) and still carries the old sentence.",
  "why_it_matters": "The PDF export is stale in one paragraph; no number or conclusion is affected.", "proposed_fix": "Regenerate the PDF at the next manuscript export.",
  "status": "ACCEPTED RISK", "evidence": "tests/test_manuscript_n06.py (PROVEN BY TEST); manuscript checks 59 PASS, 1 FLAG (N-02)"}]

INVARIANTS = [  # (n, invariant, mutations that break it, designed test)
 (1, "WML = W - L", ["WML = W + L"], f"{K}::test_golden_monthly_returns_of_every_step_by_hand"),
 (2, "WML must not equal W + L", ["WML = W + L"], f"{K}::test_golden_monthly_returns_of_every_step_by_hand; ::test_registered_monthly_files_satisfy_wml_and_delta_identities"),
 (3, "Step D includes the correct holding-window returns", ["holding drops exit session (RG)", "+ holding drops exit session (naive)", "holding includes entry-session return (naive)", "exit one session early (s > nxt -> >=)"], f"{K}::test_golden_sensitivity_of_step_d_to_each_boundary"),
 (4, "Step D does not silently use raw returns", ["RG uses non-research-grade rows", "+ step D holding uses raw returns", "+ span rows counted as research-grade"], f"{K}::test_golden_step_d_uses_research_returns_never_raw"),
 (5, "Flagged RET-1.1 rows excluded according to protocol", ["RG formation ignores flagged rows", "+ flagged holding day not filled", "neutral fill -> zero", "gap rows research-grade", "jump threshold 1.4->1.5"], f"{K}::test_golden_ranking_window_30pct_selection_and_tie_breaks; ::test_ret1_jump_threshold_is_40_percent"),
 (6, "Ranking window boundaries", ["formation reaches entry session (look-ahead)", "formation reaches selection date t (no skip)", "+ formation window includes m(12) session", "skip month removed", "formation 12->11"], f"{K}::test_golden_ranking_window_30pct_selection_and_tie_breaks"),
 (7, "30% portfolio selection", ["breakpoint 0.30->0.31", "+ k = floor(0.30 n) (no rounding)"], f"{K}::test_golden_ranking_window_30pct_selection_and_tie_breaks"),
 (8, "Deterministic tie-breaking", ["tie-break reversed", "rank ascending (losers as winners)"], f"{K}::test_golden_ranking_window_30pct_selection_and_tie_breaks"),
 (9, "Equal weighting", ["portfolio return = median", "+ equal weight -> value weight"], f"{K}::test_golden_monthly_returns_of_every_step_by_hand"),
 (10, "No-row behaviour", ["rankable needs only m1 price", "delisting rule off everywhere", "+ delta paired on step A only"], f"{K}::test_no_rankable_stock_and_no_row_behaviour"),
 (11, "Benchmark definition", ["+ benchmark = whole universe, not the rankable stocks"], f"{K}::test_golden_monthly_returns_of_every_step_by_hand"),
 (12, "A/B/C/D universe differences", ["step D spec uses pool universe", "step A uses PIT date", "step A pool filter removed", "top200 takes n+1", "survivor pool = everyone"], f"{K}::test_golden_monthly_returns_of_every_step_by_hand"),
 (13, "Delisting treatment", ["delisting return sign", "delisting rule also in steps A/B", "delist OTHER -30%->-3%", "+ voluntary delisting -30%", "voluntary class mislabelled", "gap return counted twice (no consumed)"], f"{K}::test_golden_delisting_rule_only_from_step_c_and_by_class"),
 (14, "Missing-return handling", ["missing-price stop disabled"], f"{K}::test_missing_price_in_the_panel_stops_the_run"),
 (15, "H1 two-sided / tail direction", ["p one-tailed reported as two-sided", "H1 decision threshold flipped", "economic conclusion uses two-sided p", "+ winners-beat-universe uses two-sided p", "+ MATERIAL without the size condition", "+ IMMATERIAL without the interval condition", "+ reference threshold 0.10->0.20", "alpha .05->.10", "ci90 uses 97.5% quantile"], f"{K}::test_newey_west_test_by_hand_is_two_sided_and_lag_sensitive; ::test_h1_decision_table; ::test_economic_conclusions_are_one_sided_at_5_percent"),
 (16, "Newey-West lag", ["NW lag primary 4->5", "+ NW lag OOS 3->4", "NW Bartlett weight -> 1", "NW variance / (n-1)", "SE without sqrt(n)"], f"{K}::test_frozen_lags_equal_the_protocol_formula_for_the_registered_sample_sizes; ::test_newey_west_test_by_hand_is_two_sided_and_lag_sensitive"),
 (17, "Bootstrap tail calculation", ["bootstrap one-sided", "bootstrap not null-centred"], f"{K}::test_bootstrap_p_value_counts_both_tails"),
 (18, "Bootstrap seed / configuration", ["+ bootstrap seed changed", "+ bootstrap resamples 10000->1000", "PW block length forced 1", "bootstrap resampler not circular/blocks iid"], f"{K}::test_bootstrap_seed_and_configuration_are_the_registered_ones"),
 (19, "Step E cost application", ["rate date = exit not entry", "STT sell uses buy rate key swapped", "net = gross + cost", "drift ignored (full rebuy each month)", "indirect tax also on STT", "schedule period boundary exclusive"], f"{K}::test_step_e_rates_are_the_ones_in_force_on_the_entry_session_not_the_exit; ::test_step_e_buy_and_sell_use_their_own_stt_rate"),
 (20, "Confirmation gating", ["confirmation without same-code primary", "blinded artifact gate off", "runner pre-run-check gate off", "runner provenance gate off", "pending decisions ignored", "C2 confirmation rule sign ignored"], f"{K}::test_confirmation_requires_a_registered_primary_run_with_the_same_code; ::test_blinded_artifact_must_exist_and_match_its_registered_hash"),
 (21, "Same-code primary / confirmation requirement", ["confirmation without same-code primary"], f"{K}::test_confirmation_requires_a_registered_primary_run_with_the_same_code"),
 (22, "Protocol hash verification", ["protocol hash check off", "registry protocol hash check off", "+ repro: pinned protocol hash not checked", "+ provenance: protocol link not checked"], "tests/test_stage3_infra.py::test_h_runner_refuses_a_changed_protocol_or_registry_record"),
 (23, "Stage 3 provenance verification", ["stage3 input hash check off", "RET-1.1 hash check off", "UNIV-1 hash check off", "+ provenance: manifest anchor not checked", "+ provenance: missing anchor tolerated", "+ provenance: file hashes not checked", "+ provenance: output set not exact", "+ provenance: duplicate manifest key accepted", "+ provenance: unexpected file accepted", "+ provenance: symlinked input accepted", "+ provenance: RET-1.1 folder not compared"], f"{K}::test_load_inputs_refuses_a_stage3_file_that_differs_from_the_manifest; {PROV}"),
 (24, "Registry state protection", ["registry duplicate id allowed", "registry unknown status allowed", "+ registry: FINAL -> PLANNED allowed", "+ registry: transition check off", "+ registry: frozen-state protection off", "+ registry: empty reason accepted", "+ registry: recorded hashes replaceable", "+ registry: identity fields replaceable", "+ registry: anchors replaceable", "+ registry: hash chain not checked", "+ registry: history pin not checked", "+ registry: duplicate line accepted", "+ registry: amendments not validated on read", "+ registry: revalidation gate off", "runner overwrite guard off"], f"{REG}"),
]
EQUIVALENT = {
 "identity links from the future": "EQUIVALENT MUTANT. `_components(known, lk, t)` only joins segments that are both in `known`, and a segment is in `known` only if its first session is <= t. A link's `effective` date is the first session of its later segment, so every link that can be used already has effective <= t. Removing the filter changes no output for any input. The invariant itself (decision at t identical on truncated data) is tested by tests/test_stage2_universe.py::test_decision_on_t_identical_with_full_or_truncated_data.",
 "ex-date boundary prev_date <= ex": "EQUIVALENT MUTANT. `merge_asof(direction='forward')` attaches an event to the first row with date >= ex_date. For that row prev_date < ex_date always holds when the entity has a row on the ex-date or before it, and prev_date == ex_date is impossible (the row on the ex-date itself would have been matched). `<` and `<=` select the same rows for any input.",
}


def main():
    by = {m["mutation"]: m for m in MUT}
    old = {m["mutation"]: m["status"] for m in BEFORE}
    count = Counter(m["status"] for m in MUT)
    for name in EQUIVALENT:                 # no behavioural test can fail: the mutant computes the same outputs for every input
        if by.get(name, {}).get("status") in ("SURVIVED", "KILLED_BY_HASH_PIN_ONLY"):
            by[name]["run_status"] = by[name]["status"]
            by[name]["status"] = "EQUIVALENT"
    c = Counter(m["status"] for m in MUT)
    scored = [m for m in MUT if m["status"] not in ("EQUIVALENT", "NOT_APPLIED", "ERROR")]
    survivors = [m for m in MUT if m["status"] == "SURVIVED"]
    orig = [m for m in MUT if not m["mutation"].startswith("+")]
    orig_scored = [m for m in orig if m["status"] != "EQUIVALENT"]

    # ---------------- findings.json
    findings = []
    for f in ORIG["findings"]:
        st, fix, reg_t, adv, ev = S[f["id"]]
        findings.append({**f, "status_forensic_20261007": f.get("status"), "status": st, "remediation": fix,
                         "regression_test_after": reg_t, "adversarial_test": adv, "evidence_after": ev})
    for n in NEW:
        findings.append({**n, "found_during": "remediation 2026-10-07"})
    sev = lambda items, s, states: sum(1 for x in items if x["severity"] == s and x["status"] in states)
    closed = ("FIXED", "FIXED + REGRESSION PROTECTED")
    summary = {s: {"before": ORIG["severity_counts"].get(s, 0), "found_during_remediation": sum(n["severity"] == s for n in NEW),
                   **{k: sum(1 for x in findings if x["severity"] == s and x["status"] == k)
                      for k in ("FIXED", "FIXED + REGRESSION PROTECTED", "ACCEPTED RISK", "REPORT-ONLY FROZEN", "OPEN")}} for s in ("P0", "P1", "P2", "P3")}
    (A / "findings.json").write_text(json.dumps({
        "audit_date": "2026-10-07", "remediation_date": "2026-10-07", "head": "7d4cb6d977ee1fbe40351fc6b6049c49af7638b2 + staged, uncommitted working tree",
        "original_findings": "docs/audit/forensic_20261007/findings.json (unchanged)", "statuses_used": ["FIXED", "FIXED + REGRESSION PROTECTED", "ACCEPTED RISK", "REPORT-ONLY FROZEN", "OPEN"],
        "severity_counts_before": ORIG["severity_counts"], "summary_after": summary, "findings": findings}, indent=1) + "\n")

    # ---------------- requirements_traceability.csv
    rows = list(csv.DictReader(open(A / "forensic_20261007/requirements_traceability.csv")))
    upd = {
     "Point-in-time universe (63-session liquidity ending t)": ("PASS", f"{K}::test_univ1_liquidity_window_is_63_sessions_and_needs_50_valid_ones; ::test_univ1_liquidity_is_the_median_not_the_mean", "mutations 63->64, 50->49, mean-vs-median now killed"),
     "Point-in-time identity (links effective <= t)": ("PASS", "tests/test_stage2_universe.py::test_decision_on_t_identical_with_full_or_truncated_data", "the surviving mutation is an equivalent mutant (proof in MUTATION_FINAL_REPORT.md)"),
     "Trade one session after selection; hold (s+, s++]": ("PASS", f"{K}::test_golden_sensitivity_of_step_d_to_each_boundary", "exit-session mutations (naive and research-grade) killed; independent recomputation"),
     "WML = W - L; delta = WML_A - WML_D in percent": ("PASS", f"{K}::test_golden_monthly_returns_of_every_step_by_hand; ::test_golden_delta_is_wml_a_minus_wml_d_in_percent", "'WML = W + L' killed; identity checked on the registered files"),
     "Step D uses research-grade returns only; span days excluded": ("PASS", f"{K}::test_golden_step_d_uses_research_returns_never_raw", "raw-return mutations killed (fixture has raw != adjusted)"),
     "Missing price stops the run (B1.2)": ("PASS", f"{K}::test_missing_price_in_the_panel_stops_the_run", "mutation killed"),
     "Input values are finite, unique and classified": ("PASS", f"{FI} (43 value attacks)", "integrity.validate_stage3, outside frozen code; frozen wide() itself unchanged (F-07)"),
     "Stage 3 inputs are the hashed ones": ("PASS", f"{PROV}; {K}::test_load_inputs_refuses_a_stage3_file_that_differs_from_the_manifest", "manifest anchored in the registry; three loader hash-check mutations killed"),
     "Stationary bootstrap, 10,000 resamples, null-centred, two-sided, fixed seed": ("PASS", f"{K}::test_bootstrap_p_value_counts_both_tails; ::test_bootstrap_seed_and_configuration_are_the_registered_ones", "one-sided mutation killed; resampler not independently re-implemented (N-04)"),
     "Section 27 decision labels": ("PASS", f"{K}::test_h1_decision_table", "12-row table; flipped-threshold mutation killed; reading of one cell awaits a ruling (F-22)"),
     "Primary before confirmation, same code hash": ("PASS", f"{K}::test_confirmation_requires_a_registered_primary_run_with_the_same_code", "mutation killed; reproduction checks the registered code hashes are equal"),
     "Each mode runs once; nothing is overwritten": ("PASS", f"{K}::test_each_mode_runs_once_an_existing_output_is_never_overwritten; {REG}::test_the_frozen_runners_can_no_longer_re_register_a_run", "mutation killed; registry refuses re-registration"),
     "Pre-run leakage checks pass on real data before any result": ("PARTIAL", f"{PROV}; reproduction step 5", "check files now anchored (F-12 fixed); still narrower than protocol B2 (F-13, report-only)"),
     "Stage 2 rebuild passes 150 of 150 before the study": ("PARTIAL", "reproduction step 5 (recounts the anchored log)", "log anchored and recounted; rebuild not rerun (stop condition)"),
     "Costs: dated rates in force on the trade date": ("PASS", f"{K}::test_step_e_rates_are_the_ones_in_force_on_the_entry_session_not_the_exit", "'rate at exit date' killed; independent recomputation"),
     "No cost is ever set to zero": ("PARTIAL", f"{FI}::test_step_e_validation_refuses_zero_missing_or_non_finite_costs", "frozen fillna(0) remains (F-17, report-only); zero costs rejected from outside; none in the registered files"),
     "Registered artifacts cannot be lost": ("PARTIAL", f"{VC}; {ARCH}", "staged + archive manifest + guard; commit, push and off-laptop copy still to do (F-01 OPEN)"),
     "Registry is append-only with valid state transitions": ("PASS", f"{REG} (233)", "state machine, chain, pinned history (F-03 fixed)"),
     "Every run is in the trial log": ("PASS", f"{REG}::test_trial_log_cannot_be_silenced_outside_the_test_suite; reproduction step 3", "env switch closed (F-11); exactly five registered runs required; frozen crash window remains for future studies (F-08)"),
     "Runs are deterministic": ("PARTIAL", f"{REP}", "tolerance 1e-9 in the registered interpreter and in a rebuilt Conda environment (last digits differ between the two); second machine not demonstrated (N-01)"),
     "Environment of each run is recorded": ("PASS", f"{ENV}", "pinned, anchored, verified (F-06 fixed); historical run blocks keep their gap, disclosed"),
     "Reproduction from a clean environment is documented": ("PASS", f"{REP}::test_reproduction_command_in_a_clean_process", "documented and executable; PASS in a clean process and in a clean Conda environment; one machine only (N-01)"),
     "Manuscript numbers come only from registered files": ("PASS", f"{MS}", "565 numbers re-read from registered files; one disclosure flag (N-02)"),
    }
    out = []
    for r in rows:
        if r["requirement"] in upd:
            st, test, ver = upd[r["requirement"]]
            r = {**r, "status_forensic_20261007": r["status"], "status": st, "test_after": test, "verification_after": ver}
        else:
            r = {**r, "status_forensic_20261007": r["status"], "test_after": r["test"], "verification_after": r["verification"]}
        out.append(r)
    out += [
     {"requirement": "Stage 3 manifest is anchored in the registry", "implementation": "src/registry/integrity.py", "function": "verify_stage3", "test": "-", "artifact": "registry line 59", "verification": "-", "status_forensic_20261007": "MISSING", "status": "PASS", "test_after": PROV, "verification_after": "24 adversarial tests; failure injection"},
     {"requirement": "Every external (git-ignored) research file has a content hash and immutable provenance", "implementation": "scripts/release_archive.py", "function": "build_manifest, verify, pack, materialize", "test": "-", "artifact": "release/s2_mom_v1/ARCHIVE_MANIFEST.json", "verification": "-", "status_forensic_20261007": "MISSING", "status": "PASS", "test_after": f"{ARCH}; {VC}", "verification_after": "5,637 files; cross-checked against two independent manifests"},
     {"requirement": "Registered results are independently reproducible by one command", "implementation": "scripts/reproduce_s2_mom_v1.py", "function": "main", "test": "-", "artifact": "docs/audit/remediation/reproduction_report.json", "verification": "-", "status_forensic_20261007": "MISSING", "status": "PASS", "test_after": REP, "verification_after": "PASS; 8,257 numbers; largest difference 6.7e-14; sensitivity not recomputed (N-04)"},
     {"requirement": "Frozen research files are byte-identical to the registered state", "implementation": "scripts/audit_snapshot.py", "function": "verify", "test": "-", "artifact": "docs/audit/remediation/pre_remediation_snapshot.json", "verification": "-", "status_forensic_20261007": "-", "status": "PASS", "test_after": FC, "verification_after": "6,299 frozen files identical; 37 code files pinned by test"},
     {"requirement": "Corrupted research inputs fail closed", "implementation": "src/registry/integrity.py; scripts/reproduce_s2_mom_v1.py", "function": "verify_stage3, validate_stage3, validate_monthly, validate_step_e", "test": "-", "artifact": "docs/audit/remediation/failure_injection_results.json", "verification": "-", "status_forensic_20261007": "PARTIAL", "status": "PASS", "test_after": FI, "verification_after": "113 attacks: 112 rejected, 1 shown harmless, 0 silently accepted"},
    ]
    cols = ["requirement", "implementation", "function", "test", "artifact", "verification", "status_forensic_20261007", "status", "test_after", "verification_after"]
    with open(A / "requirements_traceability.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in cols} for r in out])

    # ---------------- test_matrix.csv
    tm = list(csv.DictReader(open(A / "forensic_20261007/test_matrix.csv")))
    change = {
     "stage2.universe.build": {"boundary": "yes", "regression_test": "yes"}, "stage2.returns.build": {"boundary": "yes", "regression_test": "yes"},
     "stage2.corporate_actions": {"regression_test": "yes"},
     "stage3.data.build/load_inputs": {"happy_path": "partial", "missing_input": "yes", "malformed_input": "yes", "adversarial_input": "yes", "failure": "yes", "security": "yes", "regression_test": "yes"},
     "stage3.ladder (A-D)": {"empty_input": "yes", "malformed_input": "partial", "failure": "yes", "regression_test": "yes"},
     "stage3.stats": {"boundary": "yes", "adversarial_input": "partial", "regression_test": "yes"},
     "stage3.experiment.analyse": {"boundary": "yes", "regression_test": "yes"},
     "scripts/run_s2_mom.py": {"happy_path": "partial", "missing_input": "yes", "adversarial_input": "yes", "failure": "yes", "security": "yes", "regression_test": "yes"},
     "registry.experiments": {k: "yes" for k in ("happy_path", "empty_input", "missing_input", "malformed_input", "boundary", "adversarial_input", "failure", "determinism", "security", "regression_test")} | {"recovery": "partial"},
    }
    for r in tm:
        r.update(change.get(r["component"], {}))
    yes = lambda **k: {"happy_path": "yes", "empty_input": "yes", "missing_input": "yes", "malformed_input": "yes", "boundary": "yes", "adversarial_input": "yes",
                       "failure": "yes", "recovery": "partial", "determinism": "yes", "security": "yes", "regression_test": "yes", **k}
    tm += [{"component": "registry.integrity.verify_stage3 (provenance chain)", **yes()},
           {"component": "registry.integrity.validate_* (input values)", **yes(recovery="no")},
           {"component": "registry.integrity.environment_report", **yes(empty_input="no", malformed_input="partial", recovery="no")},
           {"component": "scripts/reproduce_s2_mom_v1.py", **yes(empty_input="partial", recovery="no")},
           {"component": "scripts/release_archive.py", **yes(recovery="yes")},
           {"component": "scripts/verify_manuscript.py", **yes(empty_input="no", missing_input="partial", malformed_input="no", boundary="partial", adversarial_input="no", recovery="no", security="partial")},
           {"component": "scripts/mutation_campaign.py / audit_snapshot.py", "happy_path": "yes (used, not unit-tested)", "empty_input": "no", "missing_input": "no", "malformed_input": "no", "boundary": "no",
            "adversarial_input": "no", "failure": "partial", "recovery": "yes (resume)", "determinism": "yes", "security": "partial", "regression_test": "no"}]
    with open(A / "test_matrix.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(tm[0].keys()))
        w.writeheader()
        w.writerows(tm)

    # ---------------- MUTATION_FINAL_REPORT.md
    L = ["# Mutation testing — final report, finding F-04 (2026-10-07)", "",
         "Tool: `scripts/mutation_campaign.py`. Raw results: `docs/audit/remediation/mutation_final/` (one `batch_<k>.jsonl` per batch, appended after every mutation; merged `mutation_results.json`; `code_state.json` = hashes of the code and tests measured).",
         "The forensic campaign's raw results are kept in `docs/audit/remediation/mutation_forensic_20261007.json`.", "",
         "## 1. Method", "",
         "1. One deliberate change at a time is applied to a **scratch clone** of the repository (never to the project). The test suite runs in the clone. The file is restored.",
         "2. A mutation is **KILLED** only if a behavioural test fails. Twelve tests compare file hashes or registered code hashes; they fail for any edit of a hashed file and prove nothing about the rule. They are run separately; a mutation that only they catch is reported as **KILLED BY HASH PIN ONLY**, not as killed.",
         "3. A mutation that changes no output for any input is an **EQUIVALENT MUTANT**. It is excluded from the score only with a written proof (section 5).",
         "4. Every batch is recorded. A batch stops cleanly when the disk is nearly full and resumes from its own log; an error in one mutation is recorded and the batch continues.",
         "5. The set is hand-chosen, deterministic and versioned in the tool: the 104 forensic mutations (two registry ones re-pointed at the rewritten registry code) plus "
         f"{len(MUT) - len(orig)} added by the remediation, including {sum(m['group'] == 'release tooling' for m in MUT)} that attack the new verification tooling itself.", "",
         *reconciliation(MUT),
         "## 2. Score", "",
         "Column 1 is the forensic campaign of 2026-10-07 (a different, earlier test suite). Columns 2 and 3 are both read from the final campaign (run 3); column 2 is the subset of the 104 forensic mutations within it. Runs 0–2 of the remediation appear nowhere in this table.", "",
         "| | Forensic audit (before) | Final campaign: the 104 forensic mutations | Final campaign: all |", "|---|---|---|---|",
         f"| Mutations | {len(BEFORE)} | {len(orig)} | {len(MUT)} |",
         f"| Killed by a behavioural test | {sum(v == 'KILLED' for v in old.values())} | {sum(m['status'] == 'KILLED' for m in orig)} | {c['KILLED']} |",
         f"| Killed by a hash pin or constant-equality test only | {sum(v == 'KILLED_BY_HASH_PIN_ONLY' for v in old.values())} | {sum(m['status'] == 'KILLED_BY_HASH_PIN_ONLY' for m in orig)} | {c['KILLED_BY_HASH_PIN_ONLY']} |",
         f"| Equivalent mutants (proved) | not classified | {sum(m['status'] == 'EQUIVALENT' for m in orig)} | {c['EQUIVALENT']} |",
         f"| **Survived** | **{sum(v == 'SURVIVED' for v in old.values())}** | **{sum(m['status'] == 'SURVIVED' for m in orig)}** | **{c['SURVIVED']}** |",
         f"| Not applied / error | 0 | {sum(m['status'] in ('NOT_APPLIED', 'ERROR') for m in orig)} | {c['NOT_APPLIED'] + c['ERROR']} |",
         f"| **Mutation score** (behavioural kills / non-equivalent mutations) | **{sum(v == 'KILLED' for v in old.values())}/{len(BEFORE)} = {100 * sum(v == 'KILLED' for v in old.values()) / len(BEFORE):.0f}%** | **{sum(m['status'] == 'KILLED' for m in orig)}/{len(orig_scored)} = {100 * sum(m['status'] == 'KILLED' for m in orig) / len(orig_scored):.0f}%** | **{c['KILLED']}/{len(scored)} = {100 * c['KILLED'] / len(scored):.0f}%** |", "",
         "The forensic report counted 80 of 104 as killed (77 behavioural + 3 by a constant-equality test). The table above uses the stricter count in every column.", "",
         "| Group | Mutations | Killed | Hash pin only | Equivalent | Survived |", "|---|---|---|---|---|---|"]
    for g in sorted({m["group"] for m in MUT}):
        ms = [m for m in MUT if m["group"] == g]
        L.append(f"| {g} | {len(ms)} | {sum(m['status'] == 'KILLED' for m in ms)} | {sum(m['status'] == 'KILLED_BY_HASH_PIN_ONLY' for m in ms)} | {sum(m['status'] == 'EQUIVALENT' for m in ms)} | {sum(m['status'] == 'SURVIVED' for m in ms)} |")
    L += ["", "## 3. The 24 survivors of the forensic audit", "", "| # | File | Mutation | Now | Killed by (first failing behavioural test) |", "|---|---|---|---|---|"]
    n = 0
    for name, st in old.items():
        if st == "SURVIVED":
            n += 1
            m = by[name]
            L.append(f"| {n} | `{m['file']}` | {name} | {m['status'].replace('_', ' ')} | {('`' + m['killed_by'] + '`') if m.get('killed_by') else ('see section 5' if m['status'] == 'EQUIVALENT' else '—')} |")
    L += ["", "## 4. Mutation matrix for the 24 research-critical invariants", "",
          "mutation → affected invariant → expected failing test → test file → result", "",
          "| # | Invariant | Mutations that break it | Designed test | Result |", "|---|---|---|---|---|"]
    for num, inv, muts, test in INVARIANTS:
        res = [by[x]["status"] for x in muts if x in by]
        missing = [x for x in muts if x not in by]
        if missing:
            raise SystemExit(f"invariant {num}: unknown mutation(s) {missing}")
        verdict = "all killed" if all(r == "KILLED" for r in res) else "; ".join(f"{x}: {by[x]['status']}" for x in muts if by[x]["status"] != "KILLED")
        L.append(f"| {num} | {inv} | {len(muts)}: {'; '.join(muts)} | `{test}` | {verdict} |")
    L += ["", "## 5. Equivalent mutants", ""]
    for name, why in EQUIVALENT.items():
        L += [f"**{name}** (`{by[name]['file']}`) — result of the run: {by[name].get('run_status', by[name]['status']).replace('_', ' ')} "
              "(no behavioural test fails; the edit of the frozen file is caught by the hash pin `tests/test_frozen_code.py`).", "", why, ""]
    L += ["Supporting evidence for both (a differential check run once on 2026-10-07, in memory, not part of the suite): the original and the mutated "
          "function were run on random synthetic data — 40 worlds with symbol and ISIN changes for UNIV-1, 60 worlds with ex-dates on and off session "
          "days and missing rows for RET-1 — and returned identical frames every time. The argument above is the proof; the check is corroboration.", ""]
    L += ["## 6. Critical survivors", ""]
    if survivors:
        L += ["| File | Mutation | Group | Why it survives | Risk |", "|---|---|---|---|---|"]
        for m in survivors:
            L.append(f"| `{m['file']}` | {m['mutation']} | {m['group']} | {SURVIVOR_NOTES.get(m['mutation'], 'not analysed')} | |")
    else:
        L.append("None. No mutation in any group passes the behavioural tests, apart from the two proved-equivalent mutants.")
    pins = [m for m in MUT if m["status"] == "KILLED_BY_HASH_PIN_ONLY"]
    L += ["", "## 7. Killed by a hash pin or constant-equality test only", ""]
    if pins:
        L += ["These are detected, but only because a test compares a constant or a file hash. No behavioural test notices the change.", "",
              "| File | Mutation | Pin test | Comment |", "|---|---|---|---|"]
        for m in pins:
            L.append(f"| `{m['file']}` | {m['mutation']} | `{m.get('killed_by')}` | {PIN_NOTES.get(m['mutation'], '')} |")
    else:
        L.append("None.")
    L += ["", "## 8. Every mutation", "", "| Group | File | Mutation | Result | First failing behavioural test |", "|---|---|---|---|---|"]
    for m in MUT:
        L.append(f"| {m['group']} | `{m['file']}` | {m['mutation']} | {m['status'].replace('_', ' ')} | {('`' + m['killed_by'] + '`') if m.get('killed_by') and m['status'] == 'KILLED' else ''} |")
    L += ["", "## 9. Limits", "",
          "1. Hand-chosen mutations, not an exhaustive mutation tool. A mutation score describes this list. It is not a statement about all possible defects.",
          "2. Stage 2 mutations are tested on synthetic data. The real Stage 2 build was not rerun (stop condition); for real data the protection is the pinned hashes.",
          "3. `scripts/build_stage2.py` and `src/stage3/data.py::build` are not executed by any test (0% and 49% line coverage of the two files). Their outputs are verified by hash and by explicit validation, not by rerunning them.",
          "4. A killed mutant shows that a test notices that one change. It does not show the code is right; the independent recomputation and the hand-computed fixture address that.",
          "5. `code_state.json` records the hashes of the mutated files and of the test files at the end of the final run; a test or code change after that makes this report stale."]
    (A / "MUTATION_FINAL_REPORT.md").write_text("\n".join(L) + "\n")
    print(dict(c), "score", f"{c['KILLED']}/{len(scored)}", "| original set", sum(m["status"] == "KILLED" for m in orig), "/", len(orig_scored))
    print("survivors:", [m["mutation"] for m in survivors])
    print("pin only:", [m["mutation"] for m in pins])
    print({s: v for s, v in summary.items()})


def reconciliation(mut):
    """Section 1a: every count comes from the artifacts on disk, not from memory."""
    final = _rows("mutation_final/batch_*.jsonl")
    names = [r["mutation"] for rows in final.values() for r in rows]
    dup = sorted({n for n in names if names.count(n) > 1})
    missing = [n for n in DEFINED if n not in names]
    extra = [n for n in names if n not in DEFINED]
    merged = [m["mutation"] for m in mut]
    c = Counter(m["status"] for m in mut)
    if dup or missing or extra or sorted(merged) != sorted(names) or len(DEFINED) != len(set(DEFINED)):
        raise SystemExit(f"CAMPAIGN INCOMPLETE OR INCONSISTENT: duplicates {dup}, not executed {missing}, unknown {extra}")
    run0, run1, run2 = _rows("mutation_aborted_runs/*run0*"), _rows("mutation_aborted_runs/*run1*"), _rows("mutation_run2_superseded/batch_*.jsonl")
    n = lambda d: sum(len(v) for v in d.values())
    st = lambda d: dict(Counter(r["status"] for v in d.values() for r in v))
    run2_names = {r["mutation"] for v in run2.values() for r in v}
    added = [x for x in DEFINED if x not in run2_names]
    L = ["## 1a. Count reconciliation (authoritative: the artifacts of the final run)", "",
         "**Final mutation campaign (run 3 — the only campaign in the score):** "
         f"{len(DEFINED)} generated · {len(names)} executed · {c['KILLED']} non-equivalent killed · {c['EQUIVALENT']} equivalent · "
         f"{c['SURVIVED']} survivors · {c['ERROR']} errored · {len(missing) + c['NOT_APPLIED']} skipped or not applied.", "",
         "| Count | Value | Source |", "|---|---|---|",
         f"| Mutations generated (defined in the tool) | **{len(DEFINED)}** = {len(CAMPAIGN.M)} in list `M` (the 104 forensic mutations + {len(CAMPAIGN.M) - 104} added for research logic, statistics, registry, provenance, archive) + {len(CAMPAIGN.EXTRA)} in list `EXTRA` (reproduction, validation, environment) | `scripts/mutation_campaign.py`, lists `M` and `EXTRA` |",
         f"| Mutations executed in the final run | **{len(names)}** ({len(set(names))} distinct names) | `mutation_final/batch_*.jsonl` |",
         f"| Killed by a behavioural test | {c['KILLED']} | |",
         f"| Killed by a hash-pin test only (not equivalent) | {c['KILLED_BY_HASH_PIN_ONLY']} | |",
         f"| Equivalent (no behavioural test fails; proved equivalent in section 5; the file edit is caught by a hash pin) | {c['EQUIVALENT']} | |",
         f"| Survived (not equivalent) | {c['SURVIVED']} | |",
         f"| Errored | {c['ERROR']} | |",
         f"| Not applied (mutation text not found) | {c['NOT_APPLIED']} | |",
         f"| Skipped / not executed | {len(missing)} | defined names absent from the batch files |",
         f"| Executed twice | {len(dup)} | |",
         f"| Sum of the status rows | {sum(c.values())} | must equal {len(DEFINED)} |", "",
         "Batches of the final run (mutation number modulo 3 decides the batch, so the split is deterministic):", "",
         "| Batch file | Mutations | Results |", "|---|---|---|"]
    for name, rows in final.items():
        L.append(f"| `mutation_final/{name}` | {len(rows)} | {dict(Counter(r['status'] for r in rows))} |")
    L += [f"| **Total** | **{len(names)}** | |", "",
          "**History of the campaign runs.** Only the final run is scored. Earlier runs are kept as records and are not added to any count.", "",
          "| Run | When / why it ended | Mutations defined | Rows recorded | Used in the score? | Record |", "|---|---|---|---|---|---|",
          f"| 0 | first attempt, 4 parallel batches; stopped by hand when the disk filled (8 rows are `ERROR: No space left on device`) | 153 (the release-tooling list was still empty) | {n(run0)} {st(run0)} | no | `mutation_aborted_runs/*.run0_disk_full.jsonl` |",
          f"| 1 | restarted with 3 batches; stopped by hand after {n(run1)} mutations to change the method (two-pass run, exact hash-pin list) | 194 | {n(run1)} {st(run1)} | no | `mutation_aborted_runs/*.run1_stopped_method_change.jsonl` |",
          f"| 2 | complete run of the list as it then was | 194 | {n(run2)} {st(run2)} | no — superseded | `mutation_run2_superseded/` |",
          f"| 3 (final) | complete run on the final code and the final test suite | {len(DEFINED)} | {len(names)} | **yes** | `mutation_final/` |", "",
          "**The 194 / 196 / 198 discrepancy.**", "",
          "1. Run 2 executed **194** mutations: the list had 153 + 41 entries when that run started. Its artifacts show 194 rows, 194 distinct names, no error.",
          "2. While run 2 was running, 2 mutations were added to the tool (for the new 'library installed but not loadable' check). The tool then defined **196**. Progress messages written at that time said \"196\", but run 2 had loaded its list at start and never executed those two. The messages were wrong about the denominator; no result was affected.",
          f"3. Run 2 left 7 survivors: 2 equivalent mutants and 5 real ones. Tests were written for the 5, and 2 more mutations were added (two further cutoff checks). The tool now defines **{len(DEFINED)}**.",
          f"4. Because code and tests had changed since run 2 started, run 2 was not patched up. The whole list of {len(DEFINED)} was executed again on the final state (run 3). Mutations defined now that run 2 never executed: {len(added)} — " + "; ".join(f"`{x}`" for x in added) + ". All of them are in run 3.",
          "5. No mutation is counted twice: the score reads `mutation_final/` only, and the generator of this report stops with an error if a defined mutation is missing from it, appears twice, or is unknown.", ""]
    return L


def failure_report():
    r = json.loads((A / "remediation/failure_injection_results.json").read_text())
    f, v = [x for x in r if x["layer"] == "files"], [x for x in r if x["layer"] == "values"]
    other = [("Registered monthly file validator", 10), ("Step E file validator", 6), ("Numerical comparison (NaN, inf, shape, tolerance, label)", 5),
             ("Interrupted writes (archive pack, registry summary)", 2)]
    total, acc = len(r) + sum(n for _, n in other) + 1, [x for x in r if x["outcome"] != "REJECTED"]
    wrong = [x for x in r if not x.get("expected_reason_seen")]
    out = ["# Failure-injection report — Phase 7 (2026-10-07)", "",
           "Every attack below was made on a **scratch copy** or on **synthetic frames**. The real repository was not touched.",
           "Suite: `tests/test_failure_injection.py`. Table source: `docs/audit/remediation/failure_injection_results.json`, written by `python3 tests/test_failure_injection.py OUT.json` on the final code.", "",
           "## 1. Method", "", "Two layers are attacked separately, so that one cannot hide behind the other.", "",
           "1. **File layer.** A scratch copy of the registered artifacts (registry, protocol, Stage 3 inputs, results, code, environment files) is made. One thing is broken. The verification steps of `scripts/reproduce_s2_mom_v1.py` are run on the copy. The attack counts as rejected only if the verdict is FAIL **and** the message names the expected reason.",
           "2. **Value layer.** An attacker who could make every hash valid would still have to pass the value checks. A complete, valid set of synthetic Stage 3 frames is built (170 months, 510 universes of 200 stocks). One defect is inserted. `integrity.validate_stage3` must raise with the expected message.", "",
           "A third group checks the validators of the registered monthly and step E files, the numerical comparison of the reproduction, and interrupted writes (these are pytest cases, not rows of the JSON table).", "",
           "Outcome classes, as the brief requires: **A = rejected**; **B = allowed operation that cannot change a result** (shown, not assumed).", "",
           "## 2. Result", "", "| Layer | Attacks | Rejected (A) | Allowed (B) | Silently accepted |", "|---|---|---|---|---|",
           f"| Files (scratch copy, whole verification) | {len(f)} | {sum(x['outcome'] == 'REJECTED' for x in f)} | 0 | {sum(x['outcome'] != 'REJECTED' for x in f)} |",
           f"| Values (hash-valid synthetic inputs) | {len(v)} | {sum(x['outcome'] == 'REJECTED' for x in v)} | 0 | {sum(x['outcome'] != 'REJECTED' for x in v)} |"]
    out += [f"| {name} | {n} | {n} | 0 | 0 |" for name, n in other]
    out += ["| Reordered panel rows | 1 | 0 | 1 | 0 |", f"| **Total** | **{total}** | **{total - 1 - len(acc)}** | **1** | **{len(acc)}** |", "",
            f"Rows of the table rejected for the expected reason: {len(r) - len(wrong)} of {len(r)}." + ("" if not wrong else " NOT for the expected reason: " + "; ".join(x["attack"] for x in wrong)), "",
            "## 3. The attacks required by the brief", "", "| Required attack | Where it is covered | Outcome |", "|---|---|---|"]
    req = [("corrupt one input", "files: 2 variants"), ("corrupt one manifest entry", "files"), ("rewrite the manifest", "files"),
           ("delete one input", "files (also: delete the manifest, delete a registered output)"), ("duplicate one input", "files; duplicate manifest key in `tests/test_provenance_chain.py`"),
           ("add an unexpected file", "files: inputs folder and results folder"), ("modify one result", "files"),
           ("modify protocol hash", "files: protocol file, a supplement, and a forged registry amendment"), ("modify code hash", "files: ladder, C2 runner, and a forged registry amendment"),
           ("modify registry state", "files: forged FINAL → PLANNED with a valid chain; in-place rewrite of history"), ("duplicate registry record", "files: record and amendment"),
           ("alter confirmation status", "files: confirmation result file, C2 file, forged registry headline"), ("alter environment metadata", "files: specification file, registry record, manifest build block"),
           ("insert NaN", "files (result file); values (naive return, research return, rank); monthly validator; comparison"), ("insert +inf", "files (step E file); values; monthly validator; comparison"),
           ("insert -inf", "files (input); values; monthly validator"), ("duplicate monthly row", "files (delta file); values (calendar); monthly validator; step E validator"),
           ("reorder rows", "files (calendar: rejected by hash); values (calendar order: rejected); panel rows: **class B**, section 5"),
           ("alter a date", "files; values (exit before entry, holiday, unparseable, missing)"), ("alter entity id", "files; values (panel, universe)"),
           ("alter return value", "files (registered delta); the independent recomputation compares all 680 step-months"), ("alter cost", "files (schedule; step E output); cost-function agreement test"),
           ("remove a required column", "files; values (panel, calendar); monthly validator; step E validator"), ("change column type", "files; values (returns, date, rank as text); monthly validator"),
           ("truncate an output", "files (results JSON, holdings CSV)"), ("interrupt a write if safely testable", "files (half-written registry line); interrupted archive pack and registry summary leave no final file")]
    out += [f"| {a} | {b} | {'rejected / B' if 'class B' in b else 'rejected'} |" for a, b in req]
    out += ["", "## 4. Full table", "", "### 4.1 File layer", "", "| # | Attack | What was done | Outcome | Message (first 150 characters) |", "|---|---|---|---|---|"]
    out += [f"| {n} | {x['attack']} | {x['action']} | {x['outcome']} | {x['message'][:150].replace('|', '/')} |" for n, x in enumerate(f, 1)]
    out += ["", "### 4.2 Value layer", "", "| # | Defect inserted into otherwise valid inputs | Outcome | Message |", "|---|---|---|---|"]
    out += [f"| {n} | {x['attack']} | {x['outcome']} | {x['message'][:150].replace('|', '/')} |" for n, x in enumerate(v, 1)]
    out += ["", "## 5. The one class B case", "",
            "**Reordering the rows of the panel.** If the bytes of the file change, the hash layer rejects it (file-layer case \"reorder rows\"). The question for the value layer is different: does row order carry information? It does not. The test `test_reordering_panel_rows_is_an_allowed_operation_that_cannot_change_a_result` shuffles every row, validates the frames, builds the matrices and shows that every matrix is identical cell for cell. Reordering the **calendar** is different: month order is checked and a swap is rejected.", "",
            "## 6. What was not attacked", "",
            "1. Stage 2 raw files and datasets were not corrupted file by file in this suite (1.4 GB). They are covered by the manifest chain (`tests/test_provenance_chain.py`, synthetic) and by the archive verifier (`tests/test_release_archive.py`, synthetic).",
            "2. A simultaneous, consistent rewrite of the registry history **and** of the pinned history hash in code was not attempted: it is a deliberate edit of two tracked files, visible in Git, and outside what local code can prevent (`THREAT_MODEL.md`, section 1).",
            "3. Removing only the newest registry line is detected through the environment anchor (the superseded anchor then no longer matches the files). Removing lines that nothing depends on would not be detected by local code (finding N-03).",
            "4. Power loss during a registry append cannot be simulated safely. Its result is tested: a half-written last line makes the registry unreadable with a clear message.",
            "5. The frozen runners' own non-atomic writes (F-08) cannot occur again for S2-MOM-v1 because every mode has run; they were not exercised.", "",
            "## 7. Status", "", "No silent acceptance of a corrupted research input was found among these attacks. This is evidence about the attacks listed, not a proof that no other corruption exists."]
    (A / "FAILURE_INJECTION_REPORT.md").write_text("\n".join(out) + "\n")
    print("failure injection:", total, "attacks,", total - 1 - len(acc), "rejected, 1 class B,", len(acc), "silently accepted; wrong reason:", len(wrong))


SURVIVOR_NOTES = {}
PIN_NOTES = {}

GATE_HEAD = """# Trading Lab — final release gate for S2-MOM-v1 (2026-10-08, after remediation and the final adversarial audit)

The forensic gate of 2026-10-07 is kept unchanged in `docs/audit/forensic_20261007/FINAL_RELEASE_GATE.md`.

## Verdict: PASS

F-01 was closed on 2026-10-08 and every one of its conditions was verified (section 2a). P0 = 0. Every P1 is fixed and regression-protected. The remaining P2 and P3 items are listed with their status in section 3; none of them blocks the release of the registered S2-MOM-v1 results.

| | |
|---|---|
| Release commit (commit 1) | `f5bfed89bc7b1bd258dbe81ff9da2be8f44acbdc` — "S2-MOM-v1 research release 1" |
| UI commit (commit 2) | `29c15129143ea071816a5aca53376d26f8b997bd` |
| Release tag | `s2-mom-v1-release-1`, annotated, tag object `0db0b0854bf62a44ee36d24bd3b1bcab4402e2cd`, target commit 1 |
| Remote | `origin` = `github.com/Aaditya07124063/trading-lab`, **private** (unauthenticated API and web page: 404); remote `main` and tag verified equal to local |
| External data archive | `/Volumes/DON'T OPEN/trading-lab-release/s2-mom-v1-data-baa0b47040101031.tar`, 1,552,240,640 bytes, SHA-256 `bb4b9659da4d991bb99c32a5fa5ee4765ab0bde9bf5d498a70e1c4fded681ac2` |
| Closure commit (commit 3) | holds this file, the closure record and the N-06 correction; its id is in `git log`, not in this file |

This file does not say the system is free of defects. It says what was shown, how, and what was not.

Evidence labels: **PROVEN BY TEST** (an automated test or a recorded run demonstrates it) · **VERIFIED BY INSPECTION** (read and checked by hand or with a one-off command) · **SUPPORTED BY HASH** (a hash equals a recorded value) · **DOCUMENTATION ONLY** (written down, not executed) · **UNVERIFIED**.

## 1. The twelve release criteria

| # | Criterion | State | Evidence | Label |
|---|---|---|---|---|
| 1 | Research results independently reproduced | **met** for primary, confirmation, step E, C2. **Not** for the six sensitivity treatments, the reverse ladder and the bootstrap resampler (N-04) | `REPRODUCTION_REPORT.md`: 117 quantities, 8,257 numbers, all within 1e-9; largest difference 6.7e-14, explained | PROVEN BY TEST (recomputed part) · SUPPORTED BY HASH (sensitivity) |
| 2 | Research-critical mutations are detected | **met** | `MUTATION_FINAL_REPORT.md`: 198 generated, 198 executed, 196 killed by a behavioural test, 2 proved equivalent, 0 survived, 0 errors; 24 of 24 invariants | PROVEN BY TEST |
| 3 | Provenance cannot be silently rewritten | **met** for accident and single-file edits | `PROVENANCE_VERIFICATION_REPORT.md`: 24 tests, 19 file attacks | PROVEN BY TEST |
| 4 | Registry state cannot be silently downgraded | **met**; limit: lines removed from the end of the file that nothing depends on (N-03) | `REGISTRY_SECURITY_REPORT.md`: 235 tests, 12 attacks on a copy of the real registry | PROVEN BY TEST · limit VERIFIED BY INSPECTION |
| 5 | Corrupted inputs fail closed | **met** for the attacks tried | `FAILURE_INJECTION_REPORT.md`: 113 attacks, 112 rejected, 1 shown harmless, 0 silently accepted | PROVEN BY TEST |
| 6 | Confirmation cannot bypass primary-run requirements | **met** in the runner (gate tests, mutation killed) and in the registry (equal code hashes checked). Direct import of the frozen modules remains possible (F-30, accepted risk) | `tests/test_s2mom_mutation_kills.py` part 4 | PROVEN BY TEST · bypass VERIFIED BY INSPECTION |
| 7 | Reproduction works from a clean environment | **met on one machine**: clean process; clean Conda environment; and a fresh clone of the pushed tag with the data restored from the external archive | `REPRODUCTION_REPORT.md` runs B and D; `F01_CLOSURE_PLAN.md` Closure record | PROVEN BY TEST · UNVERIFIED (other machines) |
| 8 | Dependencies are reproducible | **met for the official contract** (Conda, osx-arm64, exact builds, explicit lock). pip is not supported and is documented as such. Second machine not tried (N-01) | `DEPENDENCY_FINAL_REPORT.md` | PROVEN BY TEST (Conda rebuild) · UNVERIFIED (other machines) |
| 9 | Frozen research artifacts remain byte-identical | **met** | 6,299 of 6,299 frozen files equal the pre-remediation snapshot; 37 frozen code files and 85 artifacts pinned by `tests/test_frozen_code.py` | SUPPORTED BY HASH |
| 10 | Every P1 is fixed or explicitly justified | **met**: all six P1 fixed and regression-protected; F-01 closed on 2026-10-08 | section 2a | PROVEN BY TEST · SUPPORTED BY HASH |
| 11 | P2 / P3 risks are documented | **met** | section 2; `findings.json`; `THREAT_MODEL.md` | DOCUMENTATION ONLY |
| 12 | No silent failure path remains for research-critical data | **met on the verification path** (reproduction, validators). **Not** inside the frozen runner path (F-07, F-08, F-10, F-17 are report-only): that path cannot run again for v1, and its outputs are checked from outside | section 2 | PROVEN BY TEST (outside guards) · VERIFIED BY INSPECTION (frozen gaps) |

## 2a. F-01 closure (2026-10-08)

| Condition | Result | Label |
|---|---|---|
| Research release committed | commit 1 `f5bfed8`, 256 files, equal hash for hash to `EXACT_COMMIT_CONTENTS.md` | SUPPORTED BY HASH |
| Pushed to a private second location | `git ls-remote origin`: `refs/heads/main` = `29c1512`, tag peels to `f5bfed8`; repository not publicly visible | VERIFIED BY INSPECTION |
| Release tag exists and targets commit 1 | `s2-mom-v1-release-1^{}` = `f5bfed89…acbdc` locally, remotely and in the fresh clone | VERIFIED BY INSPECTION |
| Data archive outside the laptop | USB tar: SHA-256 equal to the registry anchor when written, and again on an independent re-read; 5,637 members = manifest; no cache, temporary, hidden or unrelated file | SUPPORTED BY HASH |
| Fresh clone succeeds | cloned from the private remote into a new directory, checked out at the tag, clean working tree | VERIFIED BY INSPECTION |
| Data restores from the archive | `release_archive.py materialize` from the USB tar: 5,637 files restored and verified | PROVEN BY TEST |
| Executable reproduction succeeds | clean Conda environment (Python 3.13.5, numpy 2.1.3, pandas 2.2.3, scipy 1.15.3, pyarrow 19.0.0, exact builds, empty process environment): PASS, exit 0; 117 quantities, 8,257 numbers, all within tolerance; largest difference 6.7e-14 | PROVEN BY TEST |
| Registered outputs and hashes match | reproduction steps 2–5 in the clone: protocol, 5 addenda/supplements, UNIV-1, cost schedule, 18 result files, 3 code hashes, manifest chain | SUPPORTED BY HASH |
| Full tests pass | fresh clone at the tag: 960 passed, 0 failed, 0 skipped; at `main`: 964 passed | PROVEN BY TEST |
| No frozen research artifact changed | 6,295 of 6,295 frozen files byte-identical; the 4 manuscript files corrected for N-06 differ only by one sentence (`tests/test_manuscript_n06.py`) | SUPPORTED BY HASH · PROVEN BY TEST |

## 2. Final-audit checklist (run on the final state, 2026-10-07 23:21 to 2026-10-08)

| # | Check | Result | Label |
|---|---|---|---|
| 1 | Full test suite | 964 passed, 0 failed (451 before) | PROVEN BY TEST |
| 2 | Mutation testing again | **final campaign (run 3, the only one scored): 198 generated, 198 executed, 196 non-equivalent killed, 2 equivalent, 0 survivors, 0 errored, 0 skipped.** Runs 0–2 were aborted or superseded; they are recorded separately and not part of any score | PROVEN BY TEST |
| 3 | All failure-injection attacks | 113: 112 rejected, 1 class B, 0 silent | PROVEN BY TEST |
| 4 | Registry attacks | 235 tests pass; 12 scratch-copy attacks rejected | PROVEN BY TEST |
| 5 | Provenance attacks | 24 tests pass; 19 scratch-copy attacks rejected | PROVEN BY TEST |
| 6 | Clean-environment reproduction | PASS (clean process; clean Conda environment); pip environment fails closed | PROVEN BY TEST |
| 7 | All frozen artifact hashes | 6,299 of 6,299 identical before N-06; 6,295 of 6,295 after it (the 4 corrected manuscript text files are pinned by the reversal test instead) | SUPPORTED BY HASH · PROVEN BY TEST |
| 8 | All registered result hashes | 18 of 18 files equal the registry; six headline hashes equal the pins in the reproduction script | SUPPORTED BY HASH |
| 9 | No registered research result changed | same as 7 and 8 | SUPPORTED BY HASH |
| 10 | No protocol file changed | protocol `f1abd954…d838`, Addendum 1, Supplements 1–4: file = registry = pin | SUPPORTED BY HASH |
| 11 | No unauthorized experiment rerun | trial log byte-identical to the snapshot (10 lines, five `s2_mom_v1` runs); results folders hold only registered files | SUPPORTED BY HASH · PROVEN BY TEST (`test_registry_and_trial_log_only_grew`) |
| 12 | Working-tree cleanliness | **clean for every research path** after commits 1–3; still uncommitted and outside the release by decision: the collector's files (`data/india/*`, `data/raw/collection_log.jsonl`, `data/raw/manifest.jsonl`). Before the commits: Research-critical paths: 0 untracked files (guard test). Unstaged: `server.py`, `web/`, `README.md` (UI work), collector data. The staged set minus `src/research_view.py` and `tests/test_ui_api.py`, exported to a scratch git repository: 960 passed, 0 failed, 0 skipped; reproduction PASS | VERIFIED BY INSPECTION · PROVEN BY TEST |
| 13 | Every P1 / P2 / P3 finding inspected | 35 findings: 30 forensic + 5 found during remediation | section 3 |

## 3. Findings

Statuses used: FIXED · FIXED + REGRESSION PROTECTED · ACCEPTED RISK · REPORT-ONLY FROZEN · OPEN. Nothing is marked FIXED because code changed; each FIXED row names the test that fails if the fix is removed.

"""


def gate():
    doc = json.loads((A / "findings.json").read_text())
    f, summ = doc["findings"], doc["summary_after"]
    L = [GATE_HEAD, "| Severity | Before | Found during remediation | Fixed | Fixed + regression protected | Accepted risk | Report-only frozen | Open |", "|---|---|---|---|---|---|---|---|"]
    for s in ("P0", "P1", "P2", "P3"):
        v = summ[s]
        L.append(f"| {s} | {v['before']} | {v['found_during_remediation']} | {v['FIXED']} | {v['FIXED + REGRESSION PROTECTED']} | {v['ACCEPTED RISK']} | {v['REPORT-ONLY FROZEN']} | {v['OPEN']} |")
    L += ["", "| ID | Sev | Previous finding | Remediation | Regression test | Adversarial test | Evidence | Final status |", "|---|---|---|---|---|---|---|---|"]
    cell = lambda x: str(x).replace("|", "/").replace("\n", " ")
    for x in f:
        if x["id"].startswith("F-"):
            L.append(f"| {x['id']} | {x['severity']} | {cell(x['description'][:260])}{'…' if len(x['description']) > 260 else ''} | {cell(x['remediation'])} | {cell(x['regression_test_after'])} | {cell(x['adversarial_test'])} | {cell(x['evidence_after'])} | **{x['status']}** |")
        else:
            L.append(f"| {x['id']} | {x['severity']} | (found during remediation) {cell(x['description'])} | {cell(x['proposed_fix'])} | — | — | {cell(x['evidence'])} | **{x['status']}** |")
    opens = [x for x in f if x["status"] == "OPEN"]
    L += ["", "## 4. Open items, by who can close them", "", "| ID | Sev | Needs | Who |", "|---|---|---|---|"]
    who = {"F-01": ("commit, push, off-laptop copy of the archive", "researcher"), "F-14": ("fix `/api/add` (POST, symbol pattern, no overwrite) — UI code, out of scope of this phase", "researcher's approval, then code"),
           "N-06": ("regenerate manuscript.pdf at the next export", "author"), "F-15": ("review the rejected BEL / CIPLA bars; the collector exited 1 again on 2026-10-07", "researcher"), "F-18": ("end-to-end tests of the ORB evaluator", "separate task (not S2-MOM)"),
           "F-21": ("decide: report the information ratio or record a deviation", "researcher (research decision)"), "N-01": ("one reproduction on a second Apple-silicon Mac; work in the dedicated Conda environment", "researcher"),
           "N-05": ("free disk space on the laptop", "researcher")}
    for x in opens:
        L.append(f"| {x['id']} | {x['severity']} | {who[x['id']][0]} | {who[x['id']][1]} |")
    L += ["", "Research-affecting changes after the frozen experiment: **NONE.** No experiment was rerun (trial log: 10 lines, 5 S2-MOM runs, byte-identical to the pre-remediation snapshot, also in the fresh clone).", "",
          "Research decisions that are not software and were not touched: F-13, F-21, F-22, F-27, and R-1 … R-8 of the forensic `RESEARCH_INTEGRITY_AUDIT.md`.", "",
          "## 5. Hashes at the end of remediation (all unchanged from the registry and from the forensic gate)", "",
          "| Item | SHA-256 |", "|---|---|",
          "| Frozen protocol | `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838` |",
          "| UNIV-1 | `2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42` |",
          "| Cost schedule (dated) | `47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f` |",
          "| Main code hash (primary = sensitivity = confirmation) | `f57c9321fa8a32172a6c0cd9b2e066bcf07144790836fd79a956a407219fa1d1` |",
          "| Step E code hash | `a6845d30b0cb65101fe6c3ea4623dd6753c2b7734d2ea2471cc4b88f51aacc54` |",
          "| C2 code hash | `505b2e4ed9d4e1f34dc2e441f2ff73e8399998e4744a6f0b4b7d62e59668b3fa` |",
          "| Blinded precision | `1e26341044f3e46052fdcda53a56721124412e26d5b93156bf274a9a4de5c693` |",
          "| Primary results | `fe7e95ba97482d6d53faba543d860e4f0d1e50cfa0312d669e910346d41ef857` |",
          "| Sensitivity results | `7d6081d8c4a099f7cd1d7d688791c23180d6977536ae4c7860a08b429ff0c19b` |",
          "| Confirmation results | `38d1d0a9fbb1d22a19b7912ec4e6285d1dbcb920ffd0e6d99ea19e096c304d92` |",
          "| Step E results | `675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0` |",
          "| C2 results | `cf977e8a5efce7ba83ce91bf70ae247ed1aea96c7004f8d03162669097689513` |",
          "", "New in remediation:", "", "| Item | Value |", "|---|---|",
          "| Registry history pin (first 58 lines) | `8fae608a52cc41312525ce9cf25da467b2cacb033b8350c064f1244652dd5f9d` |",
          "| Stage 3 manifest (anchored) | `6f08fd0fb389d36027e02bb06b9e8ff06ee1d7cb45c30c15c6c41dd79c711fe5` |",
          "| External data archive | `s2-mom-v1-data-baa0b47040101031`, tar SHA-256 `bb4b9659da4d991bb99c32a5fa5ee4765ab0bde9bf5d498a70e1c4fded681ac2` |",
          "| Registry lines | 61 (58 historical + 3 anchoring amendments), state of S2-MOM-v1: FINAL |",
          "", "## 6. What this gate does not cover", "",
          "0. Every check above ran on one machine (macOS 27, Apple silicon). A second machine, OS or CPU is UNVERIFIED (N-01).",
          "1. Whether the science is right: the research decisions listed above, the literature, the interpretation.",
          "2. A second machine, another operating system or CPU.",
          "3. A deliberate, coordinated rewrite by the repository owner of the registry, the pinned constants and the verifier together. Local code cannot prevent that; pushed Git history and distributed hashes can expose it.",
          "4. The ORB v1 study and the legacy tools, except where they share the registry."]
    (A / "FINAL_RELEASE_GATE.md").write_text("\n".join(L) + "\n")
    print("gate written; open:", [x["id"] for x in opens])


if __name__ == "__main__":
    main()
    failure_report()
    gate()
