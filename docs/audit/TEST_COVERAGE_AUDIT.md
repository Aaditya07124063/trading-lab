# Trading Lab — test-suite quality audit (2026-10-07)

## 1. Baseline

- 451 tests in 28 files, 26 seconds, all pass (real repository and a scratch copy without the raw archive and without git history).
- The suite changes no file in the repository (6,975 files hashed before and after).
- No CI. No coverage or mutation tool is installed in the environment; both were run from a scratch folder for this audit.
- No property-based testing library (`hypothesis`) is installed; the suite has hand-written invariant tests instead.

## 2. Coverage (measured on a scratch copy)

| Measure | Value |
|---|---|
| Statement coverage | 3,009 / 4,181 = **72 %** |
| Branch coverage | 798 / 1,216 = **66 %** |
| Function coverage (functions entered at least once) | 236 / 320 = **74 %** |

Critical path, file by file:

| File | Statements | Cover | What is not executed by any test |
|---|---|---|---|
| `src/stage3/ladder.py` | 212 | 95 % | `gap_rows`; three error branches |
| `src/stage3/stats.py` | 38 | 100 % | — |
| `src/stage3/experiment.py` | 160 | 99 % | — |
| `src/stage3/step_e.py` | 198 | 97 % | four validation error branches |
| `src/stage3/costs.py` | 44 | 100 % | — (the unused first cost model) |
| `src/stage3/protocol.py` | 73 | 84 % | `registration()`, the `__main__` registration block |
| **`src/stage3/data.py`** | 150 | **26 %** | **`build`, `load_inputs`, `load_univ`, `load_ret` body, `verify_provenance`, `with_ret_status` — every hash check and the manifest logic** |
| **`scripts/run_s2_mom.py`** | 88 | **52 %** | **`_write` (run-once guard), `_amend`, the bodies of `checks`, `blinded`, `primary`, `confirmation`, `sensitivity`** |
| `scripts/run_s2_mom_step_e.py` | 57 | 92 % | `__main__` |
| `scripts/run_s2_mom_c2.py` | 116 | 91 % | `main` (registration) |
| `scripts/build_stage3.py` | 9 | 0 % | all |
| **`src/registry/experiments.py`** | 96 | **54 %** | **`environment`, `_next_id`, most of `record`, `log_trial` body, `write_md`** |
| `src/access.py` | 65 | 91 % | `research_load_clean` |
| `src/stage2/universe.py`, `returns.py`, `corporate_actions.py`, `identity.py`, `panel.py` | — | 93–96 % | `entity_quality`, `code_version`, `raw_files` |
| `src/stage2/archive.py` | 120 | 40 % | every download loop |
| **`scripts/build_stage2.py`** | 275 | **0 %** | all (it is itself a 150-check verifier, run by hand) |
| `src/registry/data_registry.py` | 72 | 0 % | all |
| **`evaluate_orb_v1.py`** | 164 | **26 %** | the whole evaluation body (only the refusal path is tested) |
| `update_intraday.py` | 81 | 48 % | `collect_one`, `main` |
| `server.py` | 141 | 82 % | `/api/search`, parts of `/api/add` |

High line coverage did not prevent survivors: `ladder.py` is at 95 % and four of its mutations survive. Coverage shows what is executed, not what is checked.

## 3. Which dangerous bug could still pass all current tests?

Measured, not guessed — see `MUTATION_TEST_REPORT.md`. 24 of 104 deliberate changes keep the suite green. The ones that would change a scientific number:

1. `WML = W + L` instead of `W − L`.
2. Step D drops the return of the exit session.
3. Step D uses the raw return on every row (ignores validated adjustments; counts special-session days in formation).
4. The bootstrap counts one tail only.
5. The §27 label test is reversed; the economic-conclusion test uses the two-sided p.
6. Step E takes each rate at the exit date instead of the trade date.
7. UNIV-1: window 64 instead of 63; 49 valid sessions instead of 50; mean instead of median; identity links from the future.
8. RET-1.1: jump threshold 1.5 instead of 1.4; ex-date boundary moved; validation band 2.0 instead of 1.25.

And the ones that would remove a protection:

9. Stage 3, RET-1.1 and UNIV-1 hash checks switched off.
10. Run-once guard of the main runner switched off.
11. Confirmation allowed without a registered primary run of the same code.
12. Blinded-artifact hash check switched off.

For items 7 and 8 the real data are still protected by the pinned UNIV-1 and RET-1.1 hashes, but only when `scripts/build_stage2.py` is run by hand.

## 4. Tests that give less assurance than their name suggests

| Test | What it asserts | What it does not show |
|---|---|---|
| `test_registered_result_files_are_byte_identical` (`test_s2mom_step_e.py`) | the ten result files hash to the registry values; the folder lists exactly 12 names | that the numbers follow from the inputs. "Hashed only; nothing is recomputed" |
| `test_registered_step_e_outputs_are_intact_…`, `test_registered_c2_output_is_intact` | same, for step E and C2; exactly one logged run | same |
| `test_frozen_orb_methodology_unchanged` (15 cases) | file hashes | behaviour |
| `test_protocol_file_matches_the_frozen_hash_and_constants` | constants equal typed values | that the code uses them correctly (three mutations are caught here and nowhere else) |
| `test_runner_stops_before_reading_any_data_until_every_gate_has_passed` | each early gate raises, with `verify_protocol`, `require_ready`, `verify_provenance` replaced by stubs | the real functions in sequence; the run-once guard; the same-code rule for confirmation; any successful run |
| `test_module_is_separate_from_the_registered_code_and_writes_nothing`, `test_ui_code_cannot_run_or_write_research`, `test_no_yahoo_anywhere_in_methodology` | a list of strings is absent from the source text | behaviour (a write through another function name would pass) |
| `test_g_samples_end_at_protocol_exit_sessions_…` | the source text of `load_inputs` contains two phrases | that `load_inputs` refuses anything (it is never executed) |
| `test_pre_run_checks_catch_a_pipeline_that_uses_the_future` | the check fails for one synthetic leak | the liquidity/membership part of protocol B2 check 1 on real data |
| `test_research_view_is_read_only_and_reports_registered_facts` | the API view reflects today's registry | — (appropriate for a view) |

These tests are useful as tripwires. They should not be counted as proof of the invariant in their names.

## 5. Tests that are strong

1. Leakage tests in `test_stage3_ladder.py` (`test_a_…` to `test_f_…`) and `test_stage2_universe.py`: they change future data and compare past decisions, and they check that the injection "did bite later".
2. `test_s2mom_step_e.py` hand calculations of every cost component, boundary dates and the "future information cannot change a past cost" test.
3. `test_newey_west_matches_statsmodels`: an independent reference implementation.
4. `test_access_boundary.py`: the authorization gate is tested in a real temporary git repository; poison values after the cutoff must never surface in any endpoint.
5. `test_s2mom_cost_schedule.py::test_reproducible_from_archived_evidence`: the schedule is tied to checksummed evidence files.

## 6. Property tests asked for in the audit brief — status

| Property | Status |
|---|---|
| Adding an irrelevant stock cannot change existing stock returns | not tested |
| Changing future data cannot change historical decisions | **tested** (ladder, universe, step E) and checked on real data by the pre-run checks |
| Reordering input rows cannot change results | tested for step E (`test_deterministic_and_independent_of_row_order`); not for the ladder or Stage 2 |
| Reordering files cannot change results | not tested (loops are sorted — by inspection) |
| Duplicate input must fail or be rejected | tested for UNIV-1 keys in step E; **not for the ladder panel** (F-07) |
| Scaling prices consistently preserves returns | not tested |
| Zero-cost scenario never costs more than a positive-cost scenario | not tested as a property (true by construction: slippage ≥ 0 is added) |
| Increasing slippage cannot improve net return | not tested as a property |
| Deleting a required input fails loudly | tested for step E and C2; verified for Stage 3 by the audit attack script |
| Corrupting a registered artifact is detected | tested (hash-pin tests, research view) |
| Changing the protocol hash invalidates protected execution | tested |
| Changing the cost-schedule hash invalidates protected execution | tested |
| Changing the code hash invalidates protected execution | **not tested** (mutation 11 survives) |
| Rerun from identical inputs gives identical outputs | tested on synthetic data; proven on real data by the audit recomputation |
| Partial output is never treated as complete | tested for step E and C2; **not for the main runner** (F-08) |
