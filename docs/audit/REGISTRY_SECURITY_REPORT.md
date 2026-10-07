# Registry security report — finding F-03 (2026-10-07)

File changed: `src/registry/experiments.py` (rewritten; not part of any registered code hash).
File appended: `registry/experiments.jsonl` (58 → 61 lines; the first 58 are byte-identical).
Tests: `tests/test_registry_state_machine.py` — 235 tests. Raw result list: `docs/audit/remediation/registry_attacks_pytest.txt`.

## 1. What was wrong

The registry was an append-only log read as a source of truth. `amend()` accepted any field. A second line with the same experiment id silently replaced the record. The forensic attack script showed four accepted attacks on a scratch copy: FINAL → PLANNED, a new protocol hash, a replaced provenance block, an empty reason.

## 2. What exists now

1. **States and transitions.**

   | From | May go to |
   |---|---|
   | PLANNED | READY, INVALID, SUPERSEDED |
   | READY | EXECUTING, INVALID, SUPERSEDED |
   | EXECUTING | REGISTERED, INVALID |
   | REGISTERED | FINAL, SUPERSEDED, INVALID, REQUIRES REVALIDATION |
   | FINAL | SUPERSEDED, INVALID, REQUIRES REVALIDATION |
   | REQUIRES REVALIDATION | FINAL (only with explicit revalidation), SUPERSEDED, INVALID |
   | SUPERSEDED, INVALID | nothing |
   | legacy states (EXPLORATORY, DIAGNOSTIC, REPRODUCED, two REQUIRES REBUILD) | SUPERSEDED, INVALID, REQUIRES REVALIDATION |

   A new record may start only as PLANNED, FINAL (the frozen single-use ORB evaluator registers a complete result in one step) or a legacy state. READY, EXECUTING and REGISTERED can only be reached by transition.

2. **Protected fields.**
   - In a frozen state (everything except PLANNED, READY, EXECUTING, REGISTERED, REQUIRES REVALIDATION) only two things are possible: change `status` along the table, and add new keys to `anchors`. Every other field is refused, even a rewrite with the same value.
   - In every state: identity fields (`experiment_id`, `executed_at`, `protocol_id`, `protocol_version`, `protocol_file`, `protocol_sha256`, `freeze_commit`, `environment`) cannot be replaced, and any recorded hash (any field or nested key whose name contains `sha256`, once it has a value) cannot be replaced or removed.
   - The only way to replace them: the experiment must be in REQUIRES REVALIDATION and the caller must pass `_revalidation=True`. The amendment then records `revalidation_required: true` with the old and the new hash. Returning to FINAL also needs the explicit flag.

3. **Every amendment records:** experiment id, previous state, new state, timezone-aware timestamp, reason (non-empty), actor/tool, changed fields, SHA-256 of each field before and after, the revalidation flag, and the SHA-256 of the whole file before the line (`chain_prev_sha256`).

4. **Fail-closed reader.** Every call of `current()` validates the whole file and raises `RegistryError` on: a truncated or unreadable line, a blank line, a duplicate experiment id, an exact duplicate line, an amendment of an unknown id, a duplicate key inside a line, a changed or missing historical line, a broken chain, and any post-history line that breaks the rules above. Rules are checked on read as well as on write, so a hand-appended line gets no special treatment. The last duplicate is never selected.

5. **History.** The 58 lines that existed before the state machine are pinned by `GENESIS_SHA256`. They are not rewritten and not re-interpreted: a test proves that they fold to exactly the same view as the pre-remediation code produced (SHA-256 of the folded view `6c09fdf4…8b88`).

6. **Writes.** File lock, full validation, one line, flush, fsync. `EXPERIMENT_REGISTRY.md` is written to a temporary name and renamed.

7. **Trial log (F-11).** `TRADING_LAB_NO_TRIAL_LOG` suppresses logging only inside pytest. Set anywhere else, it raises.

## 3. Attacks and results

| # | Attack | Before | Now | Test |
|---|---|---|---|---|
| 1 | FINAL → PLANNED | accepted | refused | `test_final_cannot_be_downgraded[PLANNED]`, real-registry copy |
| 2 | FINAL → EXECUTING | accepted | refused | `…[EXECUTING]` |
| 3 | FINAL → READY | accepted | refused | `…[READY]` |
| 4 | Any of the 156 state pairs not in the table | accepted | refused | `test_every_pair_of_states_is_decided_by_the_table_and_nothing_else` |
| 5 | Replace a protected field of a FINAL experiment (11 variants) | accepted | refused | `test_protected_fields_of_a_final_experiment_are_immutable` |
| 6 | Duplicate experiment id | refused on write only | refused on write and read, also when the second record is complete and correctly chain-linked | `test_new_records_…`, `test_a_second_record_with_the_same_id_is_refused_even_with_a_valid_chain` |
| 7 | Duplicate registry record (hand-appended copy) | last one won silently | refused | `test_parser_fails_closed[duplicate experiment record (never last-wins)]` |
| 8 | Empty amendment reason (`""`, spaces, newline, None, a number) | accepted | refused | `test_empty_amendment_reasons_are_refused` |
| 9 | Protocol hash replacement without revalidation | accepted | refused | `test_recorded_hashes_cannot_be_replaced_before_final_either`, `test_hashes_change_only_through_explicit_revalidation` |
| 10 | Provenance replacement without revalidation | accepted | refused | same |
| 11 | Result hash replacement or removal without revalidation | accepted | refused | same |
| 12 | Change or remove an anchor | — | refused | `test_anchors_can_be_added_…but_never_changed_or_removed` |
| 13 | Truncated last line, garbage line, blank line, reordered lines, removed line, edited line, duplicate key | partly loud, partly silent | all refused | `test_parser_fails_closed` (13 cases) |
| 14 | Hand-forged amendment with a correct hash chain and consistent hashes (10 variants) | accepted | refused on read | `test_a_hand_forged_amendment_with_a_valid_chain_is_still_refused_on_read` |
| 15 | Rewrite, drop or truncate a historical line of the real registry (6 variants, on a copy) | accepted | refused | `test_any_rewrite_of_the_registered_history_is_detected` |
| 16 | The frozen runner re-registers a run on the FINAL experiment | accepted | refused | `test_the_frozen_runners_can_no_longer_re_register_a_run` |
| 17 | Amendment of an experiment that does not exist, correctly chain-linked | KeyError deep in the fold | refused with a registry error | `test_an_amendment_of_an_unknown_experiment_is_refused_even_with_a_valid_chain` |
| 18 | Trial log silenced by an environment variable outside the tests | accepted | refused | `test_trial_log_cannot_be_silenced_outside_the_test_suite` |

Registry attacks in the test suite: 235 run, 235 pass (each "pass" = the attack was refused and the file was byte-identical afterwards, or the legal action was accepted).
Registry attacks in the failure-injection suite (on a scratch copy of the real registry and trial log): 12 run, 12 rejected.
Registry mutations in the mutation campaign: see `MUTATION_FINAL_REPORT.md`, group "guards and registry".

## 4. The three lines appended to the real registry

| Line | When | What | Why |
|---|---|---|---|
| 59 | 2026-10-07 18:17 +05:30 | `anchors`: Stage 3 manifest hash, three check-file hashes, two cost-schedule hashes, external archive (id, manifest hash, tar hash) | F-02, F-12 |
| 60 | 2026-10-07 (evening) | `anchors`: hashes of `ENVIRONMENT.json` and `requirements-lock.txt`, the environment observed after the fact | F-06 |

| 61 | 2026-10-07 (night) | `anchors.environment_files_sha256_v2`: hashes of the four corrected environment files (Conda specification, explicit lock, `ENVIRONMENT.json`, `requirements-lock.txt`) | F-06 / N-01: the first lock file implied a pip rebuild that does not work; the reason of the line says that v2 supersedes the anchor of line 60 for verification and why |

State before and after all three lines: FINAL. No status, protocol, provenance or result field changed. Each line states in its reason that no experiment was rerun. Line 60 was not removed or altered: an anchor can never be changed, so the correction is a new key and a recorded supersession.

## 5. Limits (stated, not hidden)

1. Removing lines from the **end** of the registry leaves a valid shorter history. It is noticed where something needs those lines (the reproduction requires the anchors and state FINAL). The complete control is Git.
2. A person who edits `GENESIS_SHA256` and the registry together defeats the pin. That edit is visible in the Git diff of a code file.
3. The lock is advisory (`flock`); it protects against two writers that both use this module.
4. The frozen runners know nothing about READY / EXECUTING / REGISTERED. For S2-MOM-v1 this does not matter (every mode has run; the record is FINAL). A new study must move through the states with `amend(status=…)`; a new runner should do it itself.
