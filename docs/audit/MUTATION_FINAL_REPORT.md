# Mutation testing — final report, finding F-04 (2026-10-07)

Tool: `scripts/mutation_campaign.py`. Raw results: `docs/audit/remediation/mutation_final/` (one `batch_<k>.jsonl` per batch, appended after every mutation; merged `mutation_results.json`; `code_state.json` = hashes of the code and tests measured).
The forensic campaign's raw results are kept in `docs/audit/remediation/mutation_forensic_20261007.json`.

## 1. Method

1. One deliberate change at a time is applied to a **scratch clone** of the repository (never to the project). The test suite runs in the clone. The file is restored.
2. A mutation is **KILLED** only if a behavioural test fails. Twelve tests compare file hashes or registered code hashes; they fail for any edit of a hashed file and prove nothing about the rule. They are run separately; a mutation that only they catch is reported as **KILLED BY HASH PIN ONLY**, not as killed.
3. A mutation that changes no output for any input is an **EQUIVALENT MUTANT**. It is excluded from the score only with a written proof (section 5).
4. Every batch is recorded. A batch stops cleanly when the disk is nearly full and resumes from its own log; an error in one mutation is recorded and the batch continues.
5. The set is hand-chosen, deterministic and versioned in the tool: the 104 forensic mutations (two registry ones re-pointed at the rewritten registry code) plus 94 added by the remediation, including 45 that attack the new verification tooling itself.

## 1a. Count reconciliation (authoritative: the artifacts of the final run)

**Final mutation campaign (run 3 — the only campaign in the score):** 198 generated · 198 executed · 196 non-equivalent killed · 2 equivalent · 0 survivors · 0 errored · 0 skipped or not applied.

| Count | Value | Source |
|---|---|---|
| Mutations generated (defined in the tool) | **198** = 153 in list `M` (the 104 forensic mutations + 49 added for research logic, statistics, registry, provenance, archive) + 45 in list `EXTRA` (reproduction, validation, environment) | `scripts/mutation_campaign.py`, lists `M` and `EXTRA` |
| Mutations executed in the final run | **198** (198 distinct names) | `mutation_final/batch_*.jsonl` |
| Killed by a behavioural test | 196 | |
| Killed by a hash-pin test only (not equivalent) | 0 | |
| Equivalent (no behavioural test fails; proved equivalent in section 5; the file edit is caught by a hash pin) | 2 | |
| Survived (not equivalent) | 0 | |
| Errored | 0 | |
| Not applied (mutation text not found) | 0 | |
| Skipped / not executed | 0 | defined names absent from the batch files |
| Executed twice | 0 | |
| Sum of the status rows | 198 | must equal 198 |

Batches of the final run (mutation number modulo 3 decides the batch, so the split is deterministic):

| Batch file | Mutations | Results |
|---|---|---|
| `mutation_final/batch_0.jsonl` | 66 | {'KILLED': 65, 'KILLED_BY_HASH_PIN_ONLY': 1} |
| `mutation_final/batch_1.jsonl` | 66 | {'KILLED': 65, 'KILLED_BY_HASH_PIN_ONLY': 1} |
| `mutation_final/batch_2.jsonl` | 66 | {'KILLED': 66} |
| **Total** | **198** | |

**History of the campaign runs.** Only the final run is scored. Earlier runs are kept as records and are not added to any count.

| Run | When / why it ended | Mutations defined | Rows recorded | Used in the score? | Record |
|---|---|---|---|---|---|
| 0 | first attempt, 4 parallel batches; stopped by hand when the disk filled (8 rows are `ERROR: No space left on device`) | 153 (the release-tooling list was still empty) | 37 {'KILLED': 28, 'ERROR': 8, 'KILLED_BY_HASH_PIN_ONLY': 1} | no | `mutation_aborted_runs/*.run0_disk_full.jsonl` |
| 1 | restarted with 3 batches; stopped by hand after 21 mutations to change the method (two-pass run, exact hash-pin list) | 194 | 21 {'KILLED': 21} | no | `mutation_aborted_runs/*.run1_stopped_method_change.jsonl` |
| 2 | complete run of the list as it then was | 194 | 194 {'KILLED': 187, 'SURVIVED': 7} | no — superseded | `mutation_run2_superseded/` |
| 3 (final) | complete run on the final code and the final test suite | 198 | 198 | **yes** | `mutation_final/` |

**The 194 / 196 / 198 discrepancy.**

1. Run 2 executed **194** mutations: the list had 153 + 41 entries when that run started. Its artifacts show 194 rows, 194 distinct names, no error.
2. While run 2 was running, 2 mutations were added to the tool (for the new 'library installed but not loadable' check). The tool then defined **196**. Progress messages written at that time said "196", but run 2 had loaded its list at start and never executed those two. The messages were wrong about the denominator; no result was affected.
3. Run 2 left 7 survivors: 2 equivalent mutants and 5 real ones. Tests were written for the 5, and 2 more mutations were added (two further cutoff checks). The tool now defines **198**.
4. Because code and tests had changed since run 2 started, run 2 was not patched up. The whole list of 198 was executed again on the final state (run 3). Mutations defined now that run 2 never executed: 4 — `+ validation: T* after the cutoff accepted`; `+ validation: cutoff other than the registered T* accepted`; `+ environment: unloadable library not reported`; `+ repro: unloadable dependency accepted`. All of them are in run 3.
5. No mutation is counted twice: the score reads `mutation_final/` only, and the generator of this report stops with an error if a defined mutation is missing from it, appears twice, or is unknown.

## 2. Score

Column 1 is the forensic campaign of 2026-10-07 (a different, earlier test suite). Columns 2 and 3 are both read from the final campaign (run 3); column 2 is the subset of the 104 forensic mutations within it. Runs 0–2 of the remediation appear nowhere in this table.

| | Forensic audit (before) | Final campaign: the 104 forensic mutations | Final campaign: all |
|---|---|---|---|
| Mutations | 104 | 104 | 198 |
| Killed by a behavioural test | 77 | 102 | 196 |
| Killed by a hash pin or constant-equality test only | 3 | 0 | 0 |
| Equivalent mutants (proved) | not classified | 2 | 2 |
| **Survived** | **24** | **0** | **0** |
| Not applied / error | 0 | 0 | 0 |
| **Mutation score** (behavioural kills / non-equivalent mutations) | **77/104 = 74%** | **102/102 = 100%** | **196/196 = 100%** |

The forensic report counted 80 of 104 as killed (77 behavioural + 3 by a constant-equality test). The table above uses the stricter count in every column.

| Group | Mutations | Killed | Hash pin only | Equivalent | Survived |
|---|---|---|---|---|---|
| costs (step E) | 17 | 17 | 0 | 0 | 0 |
| guards and registry | 49 | 49 | 0 | 0 | 0 |
| release tooling | 45 | 45 | 0 | 0 | 0 |
| research logic | 44 | 44 | 0 | 0 | 0 |
| stage 2 data | 18 | 16 | 0 | 2 | 0 |
| statistics and decisions | 25 | 25 | 0 | 0 | 0 |

## 3. The 24 survivors of the forensic audit

| # | File | Mutation | Now | Killed by (first failing behavioural test) |
|---|---|---|---|---|
| 1 | `src/stage3/experiment.py` | economic conclusion uses two-sided p | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 2 | `src/stage3/step_e.py` | rate date = exit not entry | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 3 | `src/stage3/ladder.py` | missing-price stop disabled | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 4 | `src/stage2/universe.py` | liquidity window 63->64 | KILLED | `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_window_is_63_sessions_and_needs_50_valid_ones` |
| 5 | `scripts/run_s2_mom.py` | confirmation without same-code primary | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 6 | `src/stage2/universe.py` | min valid 50->49 | KILLED | `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_window_is_63_sessions_and_needs_50_valid_ones` |
| 7 | `src/stage2/returns.py` | jump threshold 1.4->1.5 | KILLED | `tests/test_s2mom_mutation_kills.py::test_ret1_jump_threshold_is_40_percent` |
| 8 | `src/stage3/ladder.py` | holding drops exit session (RG) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 9 | `src/stage3/stats.py` | bootstrap one-sided | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 10 | `src/stage3/step_e.py` | STT sell uses buy rate key swapped | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 11 | `src/stage3/data.py` | stage3 input hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 12 | `scripts/run_s2_mom.py` | blinded artifact gate off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 13 | `src/stage2/universe.py` | identity links from the future | EQUIVALENT | `tests/test_frozen_code.py::test_frozen_code_is_byte_identical_to_the_pre_remediation_snapshot[src/stage2/universe.py]` |
| 14 | `src/stage2/returns.py` | event attached to row before ex-date | KILLED | `tests/test_s2mom_mutation_kills.py::test_ret1_event_is_attached_to_the_first_row_on_or_after_its_ex_date` |
| 15 | `src/stage3/ladder.py` | WML = W + L | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 16 | `src/stage3/ladder.py` | RG uses non-research-grade rows | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 17 | `src/stage3/data.py` | RET-1.1 hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 18 | `src/registry/experiments.py` | registry unknown status allowed | KILLED | `tests/test_registry_state_machine.py::test_new_records_duplicate_ids_unknown_and_non_initial_statuses` |
| 19 | `src/stage2/universe.py` | liquidity mean instead of median | KILLED | `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_is_the_median_not_the_mean` |
| 20 | `src/stage2/returns.py` | ex-date boundary prev_date <= ex | EQUIVALENT | `tests/test_frozen_code.py::test_frozen_code_is_byte_identical_to_the_pre_remediation_snapshot[src/stage2/returns.py]` |
| 21 | `src/stage2/corporate_actions.py` | validation band 1.25->2.0 | KILLED | `tests/test_s2mom_mutation_kills.py::test_corporate_action_validation_band_is_25_percent[0.35-0.5-DISCREPANT]` |
| 22 | `src/stage3/experiment.py` | H1 decision threshold flipped | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 23 | `src/stage3/data.py` | UNIV-1 hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| 24 | `scripts/run_s2_mom.py` | runner overwrite guard off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |

## 4. Mutation matrix for the 24 research-critical invariants

mutation → affected invariant → expected failing test → test file → result

| # | Invariant | Mutations that break it | Designed test | Result |
|---|---|---|---|---|
| 1 | WML = W - L | 1: WML = W + L | `tests/test_s2mom_mutation_kills.py::test_golden_monthly_returns_of_every_step_by_hand` | all killed |
| 2 | WML must not equal W + L | 1: WML = W + L | `tests/test_s2mom_mutation_kills.py::test_golden_monthly_returns_of_every_step_by_hand; ::test_registered_monthly_files_satisfy_wml_and_delta_identities` | all killed |
| 3 | Step D includes the correct holding-window returns | 4: holding drops exit session (RG); + holding drops exit session (naive); holding includes entry-session return (naive); exit one session early (s > nxt -> >=) | `tests/test_s2mom_mutation_kills.py::test_golden_sensitivity_of_step_d_to_each_boundary` | all killed |
| 4 | Step D does not silently use raw returns | 3: RG uses non-research-grade rows; + step D holding uses raw returns; + span rows counted as research-grade | `tests/test_s2mom_mutation_kills.py::test_golden_step_d_uses_research_returns_never_raw` | all killed |
| 5 | Flagged RET-1.1 rows excluded according to protocol | 5: RG formation ignores flagged rows; + flagged holding day not filled; neutral fill -> zero; gap rows research-grade; jump threshold 1.4->1.5 | `tests/test_s2mom_mutation_kills.py::test_golden_ranking_window_30pct_selection_and_tie_breaks; ::test_ret1_jump_threshold_is_40_percent` | all killed |
| 6 | Ranking window boundaries | 5: formation reaches entry session (look-ahead); formation reaches selection date t (no skip); + formation window includes m(12) session; skip month removed; formation 12->11 | `tests/test_s2mom_mutation_kills.py::test_golden_ranking_window_30pct_selection_and_tie_breaks` | all killed |
| 7 | 30% portfolio selection | 2: breakpoint 0.30->0.31; + k = floor(0.30 n) (no rounding) | `tests/test_s2mom_mutation_kills.py::test_golden_ranking_window_30pct_selection_and_tie_breaks` | all killed |
| 8 | Deterministic tie-breaking | 2: tie-break reversed; rank ascending (losers as winners) | `tests/test_s2mom_mutation_kills.py::test_golden_ranking_window_30pct_selection_and_tie_breaks` | all killed |
| 9 | Equal weighting | 2: portfolio return = median; + equal weight -> value weight | `tests/test_s2mom_mutation_kills.py::test_golden_monthly_returns_of_every_step_by_hand` | all killed |
| 10 | No-row behaviour | 3: rankable needs only m1 price; delisting rule off everywhere; + delta paired on step A only | `tests/test_s2mom_mutation_kills.py::test_no_rankable_stock_and_no_row_behaviour` | all killed |
| 11 | Benchmark definition | 1: + benchmark = whole universe, not the rankable stocks | `tests/test_s2mom_mutation_kills.py::test_golden_monthly_returns_of_every_step_by_hand` | all killed |
| 12 | A/B/C/D universe differences | 5: step D spec uses pool universe; step A uses PIT date; step A pool filter removed; top200 takes n+1; survivor pool = everyone | `tests/test_s2mom_mutation_kills.py::test_golden_monthly_returns_of_every_step_by_hand` | all killed |
| 13 | Delisting treatment | 6: delisting return sign; delisting rule also in steps A/B; delist OTHER -30%->-3%; + voluntary delisting -30%; voluntary class mislabelled; gap return counted twice (no consumed) | `tests/test_s2mom_mutation_kills.py::test_golden_delisting_rule_only_from_step_c_and_by_class` | all killed |
| 14 | Missing-return handling | 1: missing-price stop disabled | `tests/test_s2mom_mutation_kills.py::test_missing_price_in_the_panel_stops_the_run` | all killed |
| 15 | H1 two-sided / tail direction | 9: p one-tailed reported as two-sided; H1 decision threshold flipped; economic conclusion uses two-sided p; + winners-beat-universe uses two-sided p; + MATERIAL without the size condition; + IMMATERIAL without the interval condition; + reference threshold 0.10->0.20; alpha .05->.10; ci90 uses 97.5% quantile | `tests/test_s2mom_mutation_kills.py::test_newey_west_test_by_hand_is_two_sided_and_lag_sensitive; ::test_h1_decision_table; ::test_economic_conclusions_are_one_sided_at_5_percent` | all killed |
| 16 | Newey-West lag | 5: NW lag primary 4->5; + NW lag OOS 3->4; NW Bartlett weight -> 1; NW variance / (n-1); SE without sqrt(n) | `tests/test_s2mom_mutation_kills.py::test_frozen_lags_equal_the_protocol_formula_for_the_registered_sample_sizes; ::test_newey_west_test_by_hand_is_two_sided_and_lag_sensitive` | all killed |
| 17 | Bootstrap tail calculation | 2: bootstrap one-sided; bootstrap not null-centred | `tests/test_s2mom_mutation_kills.py::test_bootstrap_p_value_counts_both_tails` | all killed |
| 18 | Bootstrap seed / configuration | 4: + bootstrap seed changed; + bootstrap resamples 10000->1000; PW block length forced 1; bootstrap resampler not circular/blocks iid | `tests/test_s2mom_mutation_kills.py::test_bootstrap_seed_and_configuration_are_the_registered_ones` | all killed |
| 19 | Step E cost application | 6: rate date = exit not entry; STT sell uses buy rate key swapped; net = gross + cost; drift ignored (full rebuy each month); indirect tax also on STT; schedule period boundary exclusive | `tests/test_s2mom_mutation_kills.py::test_step_e_rates_are_the_ones_in_force_on_the_entry_session_not_the_exit; ::test_step_e_buy_and_sell_use_their_own_stt_rate` | all killed |
| 20 | Confirmation gating | 6: confirmation without same-code primary; blinded artifact gate off; runner pre-run-check gate off; runner provenance gate off; pending decisions ignored; C2 confirmation rule sign ignored | `tests/test_s2mom_mutation_kills.py::test_confirmation_requires_a_registered_primary_run_with_the_same_code; ::test_blinded_artifact_must_exist_and_match_its_registered_hash` | all killed |
| 21 | Same-code primary / confirmation requirement | 1: confirmation without same-code primary | `tests/test_s2mom_mutation_kills.py::test_confirmation_requires_a_registered_primary_run_with_the_same_code` | all killed |
| 22 | Protocol hash verification | 4: protocol hash check off; registry protocol hash check off; + repro: pinned protocol hash not checked; + provenance: protocol link not checked | `tests/test_stage3_infra.py::test_h_runner_refuses_a_changed_protocol_or_registry_record` | all killed |
| 23 | Stage 3 provenance verification | 11: stage3 input hash check off; RET-1.1 hash check off; UNIV-1 hash check off; + provenance: manifest anchor not checked; + provenance: missing anchor tolerated; + provenance: file hashes not checked; + provenance: output set not exact; + provenance: duplicate manifest key accepted; + provenance: unexpected file accepted; + provenance: symlinked input accepted; + provenance: RET-1.1 folder not compared | `tests/test_s2mom_mutation_kills.py::test_load_inputs_refuses_a_stage3_file_that_differs_from_the_manifest; tests/test_provenance_chain.py` | all killed |
| 24 | Registry state protection | 15: registry duplicate id allowed; registry unknown status allowed; + registry: FINAL -> PLANNED allowed; + registry: transition check off; + registry: frozen-state protection off; + registry: empty reason accepted; + registry: recorded hashes replaceable; + registry: identity fields replaceable; + registry: anchors replaceable; + registry: hash chain not checked; + registry: history pin not checked; + registry: duplicate line accepted; + registry: amendments not validated on read; + registry: revalidation gate off; runner overwrite guard off | `tests/test_registry_state_machine.py` | all killed |

## 5. Equivalent mutants

**identity links from the future** (`src/stage2/universe.py`) — result of the run: KILLED BY HASH PIN ONLY (no behavioural test fails; the edit of the frozen file is caught by the hash pin `tests/test_frozen_code.py`).

EQUIVALENT MUTANT. `_components(known, lk, t)` only joins segments that are both in `known`, and a segment is in `known` only if its first session is <= t. A link's `effective` date is the first session of its later segment, so every link that can be used already has effective <= t. Removing the filter changes no output for any input. The invariant itself (decision at t identical on truncated data) is tested by tests/test_stage2_universe.py::test_decision_on_t_identical_with_full_or_truncated_data.

**ex-date boundary prev_date <= ex** (`src/stage2/returns.py`) — result of the run: KILLED BY HASH PIN ONLY (no behavioural test fails; the edit of the frozen file is caught by the hash pin `tests/test_frozen_code.py`).

EQUIVALENT MUTANT. `merge_asof(direction='forward')` attaches an event to the first row with date >= ex_date. For that row prev_date < ex_date always holds when the entity has a row on the ex-date or before it, and prev_date == ex_date is impossible (the row on the ex-date itself would have been matched). `<` and `<=` select the same rows for any input.

Supporting evidence for both (a differential check run once on 2026-10-07, in memory, not part of the suite): the original and the mutated function were run on random synthetic data — 40 worlds with symbol and ISIN changes for UNIV-1, 60 worlds with ex-dates on and off session days and missing rows for RET-1 — and returned identical frames every time. The argument above is the proof; the check is corroboration.

## 6. Critical survivors

None. No mutation in any group passes the behavioural tests, apart from the two proved-equivalent mutants.

## 7. Killed by a hash pin or constant-equality test only

None.

## 8. Every mutation

| Group | File | Mutation | Result | First failing behavioural test |
|---|---|---|---|---|
| research logic | `src/stage3/protocol.py` | breakpoint 0.30->0.31 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/protocol.py` | skip month removed | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/protocol.py` | formation 12->11 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/protocol.py` | top_n 200->201 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/protocol.py` | delist OTHER -30%->-3% | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/protocol.py` | NW lag primary 4->5 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/protocol.py` | alpha .05->.10 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/protocol.py` | slippage S1 5->6 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | entry same session (s > t -> >=) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | exit one session early (s > nxt -> >=) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | rank ascending (losers as winners) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | tie-break reversed | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | formation reaches entry session (look-ahead) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | formation reaches selection date t (no skip) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | holding includes entry-session return (naive) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | holding drops exit session (RG) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | neutral fill -> zero | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | delisting return sign | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | delisting rule also in steps A/B | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | delisting rule off everywhere | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | RG formation ignores flagged rows | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | gap return counted twice (no consumed) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | WML = W + L | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | delta sign flipped (D - A) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | delta not in percent | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | step A pool filter removed | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | top200 takes n+1 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | naive factor inverted | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | RG uses non-research-grade rows | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | rankable needs only m1 price | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | portfolio return = median | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | missing-price stop disabled | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | step D spec uses pool universe | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | step A uses PIT date | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/stats.py` | NW Bartlett weight -> 1 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/stats.py` | NW variance / (n-1) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/stats.py` | p one-tailed reported as two-sided | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/stats.py` | ci90 uses 97.5% quantile | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/stats.py` | bootstrap not null-centred | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/stats.py` | bootstrap one-sided | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/stats.py` | SE without sqrt(n) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/experiment.py` | H1 decision threshold flipped | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/experiment.py` | economic conclusion uses two-sided p | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/experiment.py` | reliability fill W or L -> and | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `scripts/run_s2_mom_c2.py` | holm multiplier constant | KILLED | `tests/test_manuscript_verification.py::test_manuscript_is_supported_by_registered_artifacts` |
| statistics and decisions | `scripts/run_s2_mom_c2.py` | BH divisor dropped | KILLED | `tests/test_manuscript_verification.py::test_manuscript_is_supported_by_registered_artifacts` |
| statistics and decisions | `scripts/run_s2_mom_c2.py` | C2 confirmation rule sign ignored | KILLED | `tests/test_manuscript_verification.py::test_manuscript_is_supported_by_registered_artifacts` |
| costs (step E) | `src/stage3/step_e.py` | stamp duty on sells too | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | dp charge on buys not sells | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | brokerage cap ignored (max) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | net = gross + cost | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | slippage bps as percent | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | band boundary rank<200 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | H4 p tail reversed | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | break-even inverted | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | schedule period boundary exclusive | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | turnover not halved | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | STT sell uses buy rate key swapped | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | indirect tax also on STT | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | drift ignored (full rebuy each month) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | rate date = exit not entry | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | hypothetical net WML ignores L cost | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/data.py` | cutoff guard off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/data.py` | stage3 input hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/data.py` | RET-1.1 hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/data.py` | UNIV-1 hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/data.py` | voluntary class mislabelled | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/data.py` | survivor pool = everyone | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/protocol.py` | protocol hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/protocol.py` | registry protocol hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/stage3/protocol.py` | pending decisions ignored | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `scripts/run_s2_mom.py` | runner overwrite guard off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `scripts/run_s2_mom.py` | runner provenance gate off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `scripts/run_s2_mom.py` | runner pre-run-check gate off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `scripts/run_s2_mom.py` | confirmation without same-code primary | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `scripts/run_s2_mom.py` | blinded artifact gate off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `scripts/run_s2_mom_step_e.py` | step E input hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `scripts/run_s2_mom_step_e.py` | step E overwrite guard off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| costs (step E) | `src/stage3/step_e.py` | step E schedule hash check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `scripts/run_s2_mom_c2.py` | C2 input hash check off | KILLED | `tests/test_manuscript_verification.py::test_manuscript_is_supported_by_registered_artifacts` |
| costs (step E) | `src/stage3/costs.py` | cost evidence gap -> usable | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/registry/experiments.py` | registry duplicate id allowed | KILLED | `tests/test_leaderboard.py::test_registry_rejects_incomplete_and_duplicate_records` |
| statistics and decisions | `src/registry/experiments.py` | registry unknown status allowed | KILLED | `tests/test_registry_state_machine.py::test_new_records_duplicate_ids_unknown_and_non_initial_statuses` |
| guards and registry | `src/access.py` | research_frame includes holdout day | KILLED | `tests/test_access_boundary.py::test_watchlist_never_shows_october` |
| stage 2 data | `src/stage2/universe.py` | liquidity window shifted 1 session into the future | KILLED | `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_window_is_63_sessions_and_needs_50_valid_ones` |
| stage 2 data | `src/stage2/universe.py` | liquidity window 63->64 | KILLED | `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_window_is_63_sessions_and_needs_50_valid_ones` |
| stage 2 data | `src/stage2/universe.py` | min valid 50->49 | KILLED | `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_window_is_63_sessions_and_needs_50_valid_ones` |
| stage 2 data | `src/stage2/universe.py` | identity links from the future | EQUIVALENT |  |
| stage 2 data | `src/stage2/universe.py` | liquidity mean instead of median | KILLED | `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_is_the_median_not_the_mean` |
| stage 2 data | `src/stage2/universe.py` | liquidity rank ascending | KILLED | `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_is_the_median_not_the_mean` |
| stage 2 data | `src/stage2/universe.py` | fund units admitted | KILLED | `tests/test_stage2_universe.py::test_etf_never_enters_equity_universe` |
| stage 2 data | `src/stage2/universe.py` | universe cutoff guard off | KILLED | `tests/test_stage2_universe.py::test_post_cutoff_row_refused` |
| stage 2 data | `src/stage2/returns.py` | jump threshold 1.4->1.5 | KILLED | `tests/test_s2mom_mutation_kills.py::test_ret1_jump_threshold_is_40_percent` |
| stage 2 data | `src/stage2/returns.py` | event attached to row before ex-date | KILLED | `tests/test_s2mom_mutation_kills.py::test_ret1_event_is_attached_to_the_first_row_on_or_after_its_ex_date` |
| stage 2 data | `src/stage2/returns.py` | ex-date boundary prev_date <= ex | EQUIVALENT |  |
| stage 2 data | `src/stage2/returns.py` | gap rows research-grade | KILLED | `tests/test_stage2_returns.py::test_delisting_and_relisting_gap` |
| stage 2 data | `src/stage2/returns.py` | unvalidated factor applied | KILLED | `tests/test_stage2_returns.py::test_unresolved_events_stay_unresolved[closes0-ev0-EVENT_INCONCLUSIVE]` |
| stage 2 data | `src/stage2/returns.py` | returns cutoff guard off | KILLED | `tests/test_stage2_returns.py::test_cutoff_and_verified_start` |
| stage 2 data | `src/stage2/returns.py` | large residual 10%->50% | KILLED | `tests/test_stage2_returns.py::test_validated_adjustment_with_large_residual_is_flagged_not_research_grade` |
| stage 2 data | `src/stage2/corporate_actions.py` | bonus factor inverted | KILLED | `tests/test_stage2_corporate_actions.py::test_parse_adjusting_subjects[Bonus` |
| stage 2 data | `src/stage2/corporate_actions.py` | validation band 1.25->2.0 | KILLED | `tests/test_s2mom_mutation_kills.py::test_corporate_action_validation_band_is_25_percent[0.35-0.5-DISCREPANT]` |
| stage 2 data | `src/stage2/corporate_actions.py` | post-cutoff corporate actions kept | KILLED | `tests/test_stage2_corporate_actions.py::test_load_events_drops_post_cutoff_and_non_eq` |
| statistics and decisions | `src/intraday/inference.py` | PW block length forced 1 | KILLED | `tests/test_orb_v1_stats.py::test_block_length_grows_with_dependence` |
| statistics and decisions | `src/intraday/inference.py` | bootstrap resampler not circular/blocks iid | KILLED | `tests/test_orb_v1_stats.py::test_stationary_bootstrap_se_reflects_autocorrelation` |
| research logic | `src/stage3/ladder.py` | + equal weight -> value weight | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | + benchmark = whole universe, not the rankable stocks | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | + holding drops exit session (naive) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | + step D holding uses raw returns | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | + span rows counted as research-grade | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | + flagged holding day not filled | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | + k = floor(0.30 n) (no rounding) | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | + delta paired on step A only | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/protocol.py` | + voluntary delisting -30% | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| research logic | `src/stage3/ladder.py` | + formation window includes m(12) session | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/protocol.py` | + bootstrap seed changed | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/protocol.py` | + bootstrap resamples 10000->1000 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/protocol.py` | + NW lag OOS 3->4 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/protocol.py` | + reference threshold 0.10->0.20 | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/experiment.py` | + MATERIAL without the size condition | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/experiment.py` | + IMMATERIAL without the interval condition | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| statistics and decisions | `src/stage3/experiment.py` | + winners-beat-universe uses two-sided p | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/registry/experiments.py` | + registry: duplicate id accepted on read | KILLED | `tests/test_registry_state_machine.py::test_a_second_record_with_the_same_id_is_refused_even_with_a_valid_chain` |
| guards and registry | `src/registry/experiments.py` | + registry: non-initial start state accepted | KILLED | `tests/test_registry_state_machine.py::test_new_records_duplicate_ids_unknown_and_non_initial_statuses` |
| guards and registry | `src/registry/experiments.py` | + registry: FINAL -> PLANNED allowed | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/registry/experiments.py` | + registry: transition check off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/registry/experiments.py` | + registry: frozen-state protection off | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/registry/experiments.py` | + registry: empty reason accepted | KILLED | `tests/test_registry_state_machine.py::test_empty_amendment_reasons_are_refused[]` |
| guards and registry | `src/registry/experiments.py` | + registry: recorded hashes replaceable | KILLED | `tests/test_registry_state_machine.py::test_recorded_hashes_cannot_be_replaced_before_final_either` |
| guards and registry | `src/registry/experiments.py` | + registry: identity fields replaceable | KILLED | `tests/test_registry_state_machine.py::test_recorded_hashes_cannot_be_replaced_before_final_either` |
| guards and registry | `src/registry/experiments.py` | + registry: anchors replaceable | KILLED | `tests/test_registry_state_machine.py::test_anchors_can_be_added_to_a_final_experiment_but_never_changed_or_removed` |
| guards and registry | `src/registry/experiments.py` | + registry: hash chain not checked | KILLED | `tests/test_registry_state_machine.py::test_parser_fails_closed[removed` |
| guards and registry | `src/registry/experiments.py` | + registry: history pin not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/registry/experiments.py` | + registry: duplicate line accepted | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[duplicate` |
| guards and registry | `src/registry/experiments.py` | + registry: truncated last line tolerated | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[interrupted` |
| guards and registry | `src/registry/experiments.py` | + registry: amendments not validated on read | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| guards and registry | `src/registry/experiments.py` | + registry: revalidation gate off | KILLED | `tests/test_registry_state_machine.py::test_hashes_change_only_through_explicit_revalidation` |
| guards and registry | `src/registry/experiments.py` | + registry: revalidation allowed from any state | KILLED | `tests/test_registry_state_machine.py::test_recorded_hashes_cannot_be_replaced_before_final_either` |
| guards and registry | `src/registry/experiments.py` | + registry: revalidation unlocks without the state | KILLED | `tests/test_registry_state_machine.py::test_recorded_hashes_cannot_be_replaced_before_final_either` |
| guards and registry | `src/registry/experiments.py` | + registry: misstated previous state accepted | KILLED | `tests/test_registry_state_machine.py::test_a_hand_forged_amendment_with_a_valid_chain_is_still_refused_on_read[fields6-misstates` |
| guards and registry | `src/registry/experiments.py` | + registry: orphan amendment accepted | KILLED | `tests/test_registry_state_machine.py::test_an_amendment_of_an_unknown_experiment_is_refused_even_with_a_valid_chain` |
| guards and registry | `src/registry/experiments.py` | + trial log silenced outside pytest | KILLED | `tests/test_registry_state_machine.py::test_trial_log_cannot_be_silenced_outside_the_test_suite` |
| guards and registry | `src/registry/integrity.py` | + provenance: manifest anchor not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[corrupt` |
| guards and registry | `src/registry/integrity.py` | + provenance: missing anchor tolerated | KILLED | `tests/test_provenance_chain.py::test_missing_manifest_and_missing_anchor_fail` |
| guards and registry | `src/registry/integrity.py` | + provenance: file hashes not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[corrupt` |
| guards and registry | `src/registry/integrity.py` | + provenance: output set not exact | KILLED | `tests/test_provenance_chain.py::test_path_traversal_or_unexpected_path_fails[../../../outside.csv]` |
| guards and registry | `src/registry/integrity.py` | + provenance: duplicate manifest key accepted | KILLED | `tests/test_provenance_chain.py::test_duplicate_manifest_entry_fails_even_when_the_registry_names_that_manifest` |
| guards and registry | `src/registry/integrity.py` | + provenance: unexpected file accepted | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[duplicate` |
| guards and registry | `src/registry/integrity.py` | + provenance: symlinked input accepted | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[symlink` |
| guards and registry | `src/registry/integrity.py` | + provenance: protocol link not checked | KILLED | `tests/test_provenance_chain.py::test_registry_record_and_manifest_must_name_the_same_protocol_and_universe` |
| guards and registry | `src/registry/integrity.py` | + provenance: RET-1.1 folder not compared | KILLED | `tests/test_provenance_chain.py::test_stage2_inputs_code_and_check_files_are_part_of_the_chain[<lambda>-dataset` |
| guards and registry | `scripts/release_archive.py` | + archive: tar hash not checked on restore | KILLED | `tests/test_release_archive.py::test_materialize_refuses_a_wrong_archive_and_never_overwrites` |
| guards and registry | `scripts/release_archive.py` | + archive: unknown member accepted | KILLED | `tests/test_release_archive.py::test_materialize_refuses_path_traversal_and_unknown_members` |
| guards and registry | `scripts/release_archive.py` | + archive: existing file overwritten | KILLED | `tests/test_release_archive.py::test_materialize_refuses_a_wrong_archive_and_never_overwrites` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: independent WML = W + L | KILLED | `tests/test_reproduction.py::test_independent_ladder_gives_the_hand_computed_golden_numbers` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: tolerance 1e-9 -> 1 | KILLED | `tests/test_failure_injection.py::test_the_numerical_comparison_refuses_nan_inf_shape_and_out_of_tolerance_values` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: comparison never fails | KILLED | `tests/test_failure_injection.py::test_the_numerical_comparison_refuses_nan_inf_shape_and_out_of_tolerance_values` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: NaN accepted in the comparison | KILLED | `tests/test_failure_injection.py::test_the_numerical_comparison_refuses_nan_inf_shape_and_out_of_tolerance_values` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: label comparison never fails | KILLED | `tests/test_failure_injection.py::test_the_numerical_comparison_refuses_nan_inf_shape_and_out_of_tolerance_values` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: registry state not checked | KILLED | `tests/test_reproduction.py::test_reproduction_requires_the_registry_state_final[PLANNED]` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: trial log not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[unregistered` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: result file hashes not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: unregistered result file accepted | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[add` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: registered code hash not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: pinned protocol hash not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: addenda hashes not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[modify` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: python -O accepted | KILLED | `tests/test_reproduction.py::test_python_O_is_refused` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: environment anchor not checked | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[delete` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: missing dependency accepted | KILLED | `tests/test_reproduction.py::test_python_O_is_refused` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: independent ladder ignores the delisting return | KILLED | `tests/test_reproduction.py::test_independent_ladder_gives_the_hand_computed_golden_numbers` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: independent ladder drops the exit session | KILLED | `tests/test_reproduction.py::test_independent_ladder_gives_the_hand_computed_golden_numbers` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: independent ladder ranks ascending | KILLED | `tests/test_reproduction.py::test_independent_ladder_gives_the_hand_computed_golden_numbers` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: independent step E ignores drift | KILLED | `tests/test_reproduction.py::test_independent_step_e_costs_agree_with_the_frozen_cost_ledger` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: independent step E taxes STT | KILLED | `tests/test_reproduction.py::test_independent_step_e_costs_agree_with_the_frozen_cost_ledger` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: one-sided p tail reversed | KILLED | `tests/test_reproduction.py::test_independent_newey_west_holm_and_bh` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: Newey-West without Bartlett weights | KILLED | `tests/test_reproduction.py::test_independent_newey_west_holm_and_bh` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: report may be written inside the repository | KILLED | `tests/test_reproduction.py::test_the_script_cannot_register_or_overwrite_anything` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: a failed step still ends in PASS | KILLED | `tests/test_failure_injection.py::test_file_attack_is_rejected[corrupt` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: repository change not detected | KILLED | `tests/test_reproduction.py::test_a_run_that_changes_the_repository_fails` |
| release tooling | `src/registry/integrity.py` | + validation: missing naive return accepted | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[insert` |
| release tooling | `src/registry/integrity.py` | + validation: infinite value accepted | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[insert` |
| release tooling | `src/registry/integrity.py` | + validation: return of -100% accepted | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[return` |
| release tooling | `src/registry/integrity.py` | + validation: duplicate panel row accepted | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[duplicate` |
| release tooling | `src/registry/integrity.py` | + validation: unknown row class accepted | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[unknown` |
| release tooling | `src/registry/integrity.py` | + validation: last session need not be T* | KILLED | `tests/test_environment.py::test_python_O_really_disables_the_frozen_asserts_and_the_explicit_checks_still_fire` |
| release tooling | `src/registry/integrity.py` | + validation: month count not checked | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[duplicate` |
| release tooling | `src/registry/integrity.py` | + validation: universe size not checked | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[199-stock` |
| release tooling | `src/registry/integrity.py` | + validation: step A list may change | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[step` |
| release tooling | `src/registry/integrity.py` | + validation: calendar order not checked | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[alter` |
| release tooling | `src/registry/integrity.py` | + validation: non-OK month accepted | KILLED | `tests/test_failure_injection.py::test_registered_monthly_file_validation[a` |
| release tooling | `src/registry/integrity.py` | + validation: zero cost accepted | KILLED | `tests/test_failure_injection.py::test_step_e_validation_refuses_zero_missing_or_non_finite_costs` |
| release tooling | `src/registry/integrity.py` | + validation: NaN in registered returns accepted | KILLED | `tests/test_failure_injection.py::test_value_attack_is_rejected_even_when_every_hash_would_be_valid[insert` |
| release tooling | `src/registry/integrity.py` | + validation: cutoff consistency not checked | KILLED | `tests/test_environment.py::test_cutoff_asserts_are_restated_as_explicit_checks` |
| release tooling | `src/registry/integrity.py` | + validation: T* after the cutoff accepted | KILLED | `tests/test_environment.py::test_cutoff_asserts_are_restated_as_explicit_checks` |
| release tooling | `src/registry/integrity.py` | + validation: cutoff other than the registered T* accepted | KILLED | `tests/test_environment.py::test_cutoff_asserts_are_restated_as_explicit_checks` |
| release tooling | `src/registry/integrity.py` | + environment: version mismatch not reported | KILLED | `tests/test_environment.py::test_environment_report_states_python_os_architecture_versions_missing_and_mismatches` |
| release tooling | `src/registry/integrity.py` | + environment: unloadable library not reported | KILLED | `tests/test_environment.py::test_environment_report_states_python_os_architecture_versions_missing_and_mismatches` |
| release tooling | `scripts/reproduce_s2_mom_v1.py` | + repro: unloadable dependency accepted | KILLED | `tests/test_reproduction.py::test_python_O_is_refused` |
| release tooling | `src/registry/integrity.py` | + environment: missing package not reported | KILLED | `tests/test_environment.py::test_environment_report_states_python_os_architecture_versions_missing_and_mismatches` |

## 9. Limits

1. Hand-chosen mutations, not an exhaustive mutation tool. A mutation score describes this list. It is not a statement about all possible defects.
2. Stage 2 mutations are tested on synthetic data. The real Stage 2 build was not rerun (stop condition); for real data the protection is the pinned hashes.
3. `scripts/build_stage2.py` and `src/stage3/data.py::build` are not executed by any test (0% and 49% line coverage of the two files). Their outputs are verified by hash and by explicit validation, not by rerunning them.
4. A killed mutant shows that a test notices that one change. It does not show the code is right; the independent recomputation and the hand-computed fixture address that.
5. `code_state.json` records the hashes of the mutated files and of the test files at the end of the final run; a test or code change after that makes this report stale.
