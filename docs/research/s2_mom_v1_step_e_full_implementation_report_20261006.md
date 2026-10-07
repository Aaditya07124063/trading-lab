# S2-MOM-v1 — step E full implementation and test report (2026-10-06, second report)

**Step E is implemented and tested. It was NOT run.** No real cost, turnover, net return, break-even or H4 result was calculated. No step E result file exists. Every test uses made-up holdings, ranks and returns. Nothing was committed.

This report follows `s2_mom_v1_step_e_implementation_report_20261006.md` (class 1 costs only). It covers the rest: Supplement 2 (rulings 8–16) and Supplement 3 (rulings 19–20).

**Revised the same day** after the implementation review: ruling 21 (section 3a) and the registration requirement (section 3b) are applied. The hashes and test counts below are the final ones.

## 1. Files

| File | Status | SHA-256 |
|---|---|---|
| `src/stage3/step_e.py` | changed | `17e1908270bf544878164ed6b0704af5ba74a7a440055684f78b0cc56c397554` |
| `scripts/run_s2_mom_step_e.py` | created | `997d25ba88111eea113b0f52a8cc16f2948bc59cad689c085dd3e07d0508ae6d` |
| `tests/test_s2mom_step_e_scenarios.py` | created | `20ec5842fb0936d143944b9a44ffd77e42c90e87b3c7714ba0c95915628a5977` |
| `tests/test_access_boundary.py` | one allow-list line added | `401bad026d8fc408e65bc3e96b5512dd3776d306580704011de641a4ecb02f33` |
| `tests/test_s2mom_step_e.py` | unchanged | `7db365f7116f56f4809264c05ba10b5fe90eedae33a2caed3d0b0fd961d44e10` |
| this report; `RESEARCH_LOG.md` | created; one entry added | — |

- **Implementation hash:** the SHA-256 of `src/stage3/step_e.py` above.
- **Runner hash:** the SHA-256 of `scripts/run_s2_mom_step_e.py` above.
- **Combined step E code hash** (both files, the value the runner will register): `a6845d30b0cb65101fe6c3ea4623dd6753c2b7734d2ea2471cc4b88f51aacc54`.
- The registered experiment code is untouched: `f57c9321fa8a32172a6c0cd9b2e066bcf07144790836fd79a956a407219fa1d1`.

## 2. What was implemented

| # | Requirement | Where |
|---|---|---|
| 1 | S0–S4, frozen values, imported from the registered constants and not retyped | `cost_ledger` (`slippage_S*_rs`, `cost_fraction_S*`) |
| 2 | Both samples | runner, `SAMPLES` |
| 3, 5, 22 | Exactly five inputs, each with its SHA-256; all five checked before any read; refusal if one differs | runner, `INPUTS`, `run` |
| 4 | One access-boundary entry | `tests/test_access_boundary.py`, key `scripts/run_s2_mom_step_e.py` |
| 6 | Join holdings `(t, entity)` → UNIV-1 `(selection_date, entity_id)`; no other key, no other date | `rank_index`, `rank_at` |
| 7 | Formation guard, **W and L only** (ruling 21): UNIV-1 rank == saved `liquidity_rank`; mismatch, empty saved rank, duplicate or null key, invalid rank → hard failure before any cost | `check_formation_ranks`, `RANK_GUARDED`, `rank_index`, `band` |
| 8, 9 | Exit orders use the rank at the exit rebalance; 1–200, 201–500, and the 201–500 fallback above 500 or unranked; a missing row is a hard failure | `cost_ledger`, `band`, `rank_at` |
| 10 | First month bought from cash | `cost_ledger` (drift is empty in the first month of a sample) |
| 11 | No terminal liquidation | `cost_ledger` (orders exist only at entry sessions) |
| 12, 13 | W and benchmark costed; L costed as a hypothetical long portfolio | `PORTFOLIOS`, runner |
| 14 | Hypothetical net WML = gross WML − cost of W − cost of L; every L cost and net column and every net WML column carries the word "hypothetical" | `net_returns` |
| 15 | H3: one-sided Newey–West with the registered function | `one_sided_test`, `summarise` |
| 16 | H4 only in the primary sample and only if H3 is supported | `summarise` |
| 17 | Break-even `x / d`, primary only, with the two fixed texts | `break_even`, `summarise` |
| 18 | S1–S4 described as pre-specified cost scenarios | module and runner text, output statement |
| 21, 23 | Dedicated runner; refuses if its output directory, or a partial one, exists | runner, `run` |
| 24 | No raw market data, no UNIV-1 rebuild | runner reads three UNIV-1 columns only |
| 25 | Existing artifacts preserved | section 6 |

Slippage is added after the class 1 total, so it never enters the tax base. The class 1 columns are identical with and without slippage (tested).

**Outputs the runner will write, when authorised,** into a new directory `results/s2_mom_v1_step_e/`: a per-order ledger and a monthly file for each sample, and `step_e_results.json`. The registered directory `results/s2_mom_v1/` is not written to. Every result file carries the timing statement and the disclosures of Addendum 1 and Supplements 1–3. The runner then appends its run to the registry and the trials log, as the registered runner does.

## 3. Points for the reviewer

1. **H3 lag in the confirmation sample is 3, not 4.** The instruction said "lag-4 rule". Frozen §15 and the registered code give lag 4 for the primary sample (T = 114) and lag 3 for the confirmation sample (T = 56). The code uses the registered value for each sample, so it reproduces the registered H3 statistics. H4 exists only in the primary sample and uses lag 4.
2. **H3 is recomputed from the approved monthly files, then compared with the registered decision.** The registered result JSON files are not among the five inputs, so they are not read. The run stops if H3 does not come out as recorded in Supplement 2 (primary supported, confirmation not supported).
3. **Both undefined break-even cases at once.** If `d <= 0` and `x <= 0` together, both fixed texts are reported. Ruling 12 does not say which comes first.
4. **Output directory.** The outputs go to `results/s2_mom_v1_step_e/`, not inside `results/s2_mom_v1/`, because an existing test requires that directory to hold exactly the 12 registered files.
5. **A rebalance with no order costs nothing.** If a portfolio has no weight change at a rebalance, its cost is zero. A month missing from the holdings or from the gross returns is still a hard failure.
6. **The formation guard has never met real data.** If a saved `liquidity_rank` of a W or L stock differs from its UNIV-1 rank, or is empty, the run stops before any cost. That would need a ruling, not a code change. The benchmark is not guarded (ruling 21).
7. **The runner will also stop** if a holding month is not "OK", if months are not consecutive, or if a file does not hold the expected sample label (`PRIMARY`, `OOS`).

## 3a. Ruling 21 — scope of the formation-rank guard (reviewer, 2026-10-06)

- The equality guard `UNIV-1 rank at the selection date == saved holdings.liquidity_rank` applies **only to W and L**.
- For W and L a mismatch, an empty saved rank, a null or duplicate UNIV-1 key, or an invalid rank is a hard failure before any cost.
- The guard is **not** applied to the benchmark. The benchmark is not a ranked W/L selection, so the W/L selection invariant is not imposed on it.
- The benchmark is still costed under the same step E rules. The rank that sets its slippage band comes from the same UNIV-1 lookup `(t, entity) → (selection_date, entity_id)` at the rebalance where the order trades. Its saved `liquidity_rank` is not used.
- The lookup itself stays strict for every portfolio, the benchmark included: a missing row, a duplicate or null key, or an invalid rank stops the run.
- Nothing else changed.

**Where ruling 21 is recorded.** It narrows Supplement 3 §3.1, which says "for every held stock". Supplement 3 is registered and was not edited. Ruling 21 is recorded in this report, in `RESEARCH_LOG.md` and in the code (`RANK_GUARDED`). It is **not** in a registered supplement. If it should be, that needs a Supplement 4.

## 3b. Registration by the runner (approved, with a requirement)

- The registry and the trials log are written only after `run` has returned, which happens only when every output file is complete and hashed.
- A refused, failed or interrupted run raises before that point and registers nothing.
- Outputs are written into `results/s2_mom_v1_step_e.partial/` and the directory is renamed to its final name only when complete. A run that fails while writing leaves the partial directory in place; it is never deleted or overwritten, and a later run refuses to start until the reviewer decides what to do with it.
- An existing output directory is never overwritten.

## 4. Tests

`tests/test_s2mom_step_e_scenarios.py`: **41 tests, 41 passed.** **Whole repository: 440 passed, 0 failed** (399 before step E was completed; 436 before ruling 21).

| Required case | Test |
|---|---|
| Formation rank equality | `test_formation_rank_equal_to_saved_liquidity_rank_passes` |
| Formation rank mismatch | `test_formation_rank_mismatch_is_a_hard_failure_before_any_cost` |
| Guard covers W and L, not the benchmark (ruling 21) | `test_formation_rank_guard_covers_w_and_l_but_not_the_benchmark`, `test_runner_does_not_guard_benchmark_ranks_but_guards_w_and_l` |
| Duplicate or null UNIV-1 key | `test_duplicate_or_null_univ1_key_is_a_hard_failure` |
| Missing exit lookup | `test_missing_exit_lookup_is_a_hard_failure_with_no_other_date_or_identifier` |
| Invalid rank | `test_invalid_rank_is_a_hard_failure` (3 cases) |
| Exit 1–200, 201–500, above 500, unranked | `test_exit_order_uses_the_rank_at_the_exit_rebalance` (6 cases) |
| Both-leg cost sign | `test_hypothetical_net_wml_deducts_the_costs_of_both_legs` |
| Break-even undefined cases | `test_break_even_and_its_undefined_cases` |
| First-month purchase | `test_first_month_is_a_full_purchase_from_cash_with_slippage` |
| No terminal liquidation | `test_no_terminal_liquidation` |
| Frozen S0–S4 values; not taxed | `test_frozen_scenario_values_are_used_exactly`, `test_slippage_applies_to_buys_and_sells_and_is_never_taxed` |
| H3 → H4; confirmation H4 not run | `test_h4_and_break_even_only_in_the_primary_sample_with_h3_supported`, `test_h3_that_differs_from_the_registered_decision_is_refused`, `test_one_sided_test_is_the_registered_newey_west_test` |
| Samples independent, each from cash | `test_each_sample_starts_from_cash_independently` |

| Adversarial case | Test |
|---|---|
| Input-hash mismatch (each of the five) | `test_runner_refuses_an_input_whose_hash_differs_before_any_read` |
| Output overwrite | `test_runner_never_overwrites_existing_output` |
| Registration only after complete success; nothing registered on refusal, failure or interruption; partial output never overwritten | `test_registration_only_after_a_complete_successful_run`, `test_a_run_that_fails_while_writing_leaves_no_final_directory_and_is_not_rerun` |
| Unauthorised file access | `test_runner_end_to_end_on_synthetic_files` (records every read), `test_runner_reads_no_other_file_and_no_raw_market_data`, `test_runner_inputs_are_exactly_the_five_registered_in_supplement_3` |
| Invalid identifiers and ranks | `test_unknown_identifier_is_never_mapped`, `test_runner_writes_nothing_when_a_rank_or_identifier_is_invalid`, `test_runner_refuses_files_of_the_wrong_sample` |
| One access-boundary entry; not yet executed | `test_one_access_boundary_entry_for_step_e`, `test_step_e_has_not_been_executed_and_writes_outside_the_registered_results` |

The runner tests run on made-up files in a temporary directory. The real inputs are only hashed.

## 5. Independent verification against Supplements 1–3

A separate hand calculation, not part of the test files: made-up holdings for two months in January and February 2014, with the class 1 rates typed in by hand. 42 checks, all pass, to 12 significant figures:

- class 1 cost of W in a first month bought from cash, and in a month with a trim, an exit and an entry;
- slippage under each of S0–S4, with the exit priced at its exit-rebalance rank (777, fallback) and not its held rank (200);
- net W, hypothetical cost of L, hypothetical net WML = gross − cost W − cost L;
- traded value, the break-even `x / d`, no order at the final boundary, slippage outside the tax base.

A second hand check for ruling 21, 9 checks, all pass: W and L with an equal saved rank are costed; W and L with a different or empty saved rank are refused; a benchmark stock with a different or empty saved rank is costed, with its band and slippage taken from its UNIV-1 rank; a benchmark stock with no UNIV-1 row is refused.

## 6. Unchanged

| Item | SHA-256 | |
|---|---|---|
| `results/s2_mom_v1/primary_holdings.csv` | `3887995763861a2ed17e280f1f975c6fd716dab4923c954d3ca70b91c2d93748` | unchanged |
| `results/s2_mom_v1/primary_monthly.csv` | `f7c8d3ab5a0ef7a08b6a0ca8a12bf26a1f901006c21637cf7886e297b97bb372` | unchanged |
| `results/s2_mom_v1/confirmation_holdings.csv` | `96bb174ed2942e7b93630ae445d11817551a44e15b90e5454272ddb79aa825b0` | unchanged |
| `results/s2_mom_v1/confirmation_monthly.csv` | `4d88f385375ad681f85be739b292097e2e898acb6acb71013230c67415a43ce3` | unchanged |
| `data/stage2/universe/univ1_pit_universe.parquet` | `2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42` | unchanged |
| Frozen protocol | `f1abd954…bd838` | unchanged |
| Addendum 1, Supplements 1, 2, 3 | `d12ccaa6…ffefe`, `ab28fd17…253b3`, `6c373c5f…6a888`, `682191de…580ce` | unchanged |
| Dated cost schedule | `47a9bad4…a10f` | unchanged |

- All 12 files of `results/s2_mom_v1/`, all of `data/stage3/`, the registry and the registered code are byte-identical to a snapshot taken before this step.
- `results/s2_mom_v1_step_e/` does not exist, and no partial directory exists. The registry has no step E run. The trials log has no new line.

## 7. Before step E may be executed

1. Reviewer review of this implementation and of the points in section 3.
2. Explicit, separate authorisation to execute: `python3 scripts/run_s2_mom_step_e.py execute`.
