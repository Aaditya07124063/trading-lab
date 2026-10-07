# Reproduction report — finding F-05 (2026-10-07)

Entry point: `python3 scripts/reproduce_s2_mom_v1.py` (also `--verify`, `--report FILE`).
Tests: `tests/test_reproduction.py` (17). Machine-readable result of the last run: `docs/audit/remediation/reproduction_report.json`.

## 1. What the command does

| Step | Check | Fails when |
|---|---|---|
| 1 | Environment: every pinned dependency installed **and loadable**; the environment files equal their registry anchor; `python -O` refused | a dependency is missing or cannot be imported; the specification was edited; optimised mode |
| 2 | Protocol, UNIV-1, cost schedule, C2 specification: file = pin in the script = registry; Addendum 1 and Supplements 1–4 = registry | any of them differs |
| 3 | Registry: valid history, hash chain, state FINAL, exactly one logged run of each of the five registered modes, the six published result hashes | any registry defect; an extra or missing trial; another result hash |
| 4 | Manifest chain: registry anchor → Stage 3 manifest → 8 inputs → Stage 2 files → code files → check files | any broken link (see `PROVENANCE_VERIFICATION_REPORT.md`) |
| 5a | Registered outputs: 18 result files, three code hashes, pre-run checks, the rebuild log (150 of 150), the archive manifest; no unregistered file in a results folder | any mismatch or extra file |
| 5b | Input validation: structure and values of the Stage 3 inputs and of the registered monthly and step E files (explicit raises, not `assert`) | NaN, inf, duplicate, wrong count, wrong date, wrong type, unknown class … |
| 6 | Independent recomputation (below) | any exception |
| 7 | Comparison with the registered files, absolute tolerance 1e-9 (costs 1e-12) | a larger difference, a NaN, a different label or membership |
| 8 | Repository fingerprint before = after | any file created, changed or removed |

It registers nothing, writes nothing inside the repository (the optional report must be outside it), opens no network connection (no network module is imported; tested), and never calls a registered runner. One failed step gives exit code 1. Steps 6–7 do not run if steps 1–5 failed.

## 2. What is recomputed, and how independent it is

The recomputation is a second implementation, written from the protocol text with its own data structures (`Matrices`, `ladder`, `nw_test`, `step_e_costs`, `holm`, `benjamini_hochberg` in the script). It does not import `src/stage3/ladder.py`, `experiment.py`, `step_e.py` or any runner. It restates the protocol constants; a test checks that the restated values equal the frozen ones.

| Recomputed independently | Compared with |
|---|---|
| W, L, benchmark and WML of all 680 step-months (4 steps × 170 months) | `primary_monthly.csv`, `confirmation_monthly.csv` |
| Number of rankable stocks and k of every step-month | same |
| Portfolio membership (W, L, benchmark) of every step-month | `primary_holdings.csv`, `confirmation_holdings.csv` |
| delta = (WML_A − WML_D) × 100, 170 months | `primary_delta.csv`, `confirmation_delta.csv` |
| H1: mean, Newey–West SE, t, two-sided p, 90% interval, §27 label; lag formula | `primary_results.json`, `confirmation_results.json` |
| Step differences A−B, B−C, C−D; the 32 ladder table cells per sample | same |
| Step E: monthly cost of W, L, benchmark under S0–S4, net returns, scenario means, H3, H4 | `*_step_e_monthly.csv`, `step_e_results.json` |
| C2: H2d (both samples), confirmation status, Holm, Benjamini–Hochberg, five block deltas | `c2_results.json` |

**Not independent, and labelled so in the output:**

1. The bootstrap p-value is recomputed with the registered resampler (`src/stage3/stats.py`, `src/intraday/inference.py`) on the independently recomputed delta series. It confirms seed, configuration and the p-value; it is not a second implementation of the resampler.
2. The six sensitivity treatments and the reverse-order ladder are not recomputed. Their file is hash-checked and its internal arithmetic is checked (each saved p-value follows from its saved mean and standard error).
3. Stage 2 and Stage 3 builds are not rerun. Their outputs are verified by hash.

Evidence that the second implementation is a real check and not a copy:

1. It gives the hand-computed numbers of the golden fixture (`tests/test_reproduction.py::test_independent_ladder_gives_the_hand_computed_golden_numbers`).
2. It agrees with the frozen ladder to 1e-12 on a random synthetic world with delistings and gap returns (`…agrees_with_the_frozen_ladder_on_a_random_world`).
3. Its cost function agrees with the frozen cost ledger on synthetic holdings across a brokerage change (`…step_e_costs_agree_with_the_frozen_cost_ledger`).
4. 26 deliberate mutations of the script itself are in the mutation campaign (`MUTATION_FINAL_REPORT.md`, group "release tooling").

## 3. Numerical acceptance criterion

The command accepts a reproduction only if **every** compared quantity meets its rule. The rules are fixed in the script (`TOL = 1e-9`; a test fails if the constant changes) and are written into every report (`acceptance`, and `tolerance` / `within_tolerance` on each row).

| Kind of quantity | Rule |
|---|---|
| Monthly returns (fraction), delta (percent per month), means, standard errors, t-statistics, p-values, interval bounds, Holm and Benjamini–Hochberg values | absolute difference ≤ **1e-9** |
| Step E monthly costs (fraction of the Rs 1 crore notional) | absolute difference ≤ **1e-12** |
| Number of rankable stocks, k, portfolio membership, decision labels, confirmation status, rejections, lags, bootstrap configuration | **exactly equal** |
| Any NaN or infinite value, or a different number of values | FAIL |

Why absolute and why 1e-9: the quantities are of order 1e-3 to 1e1; a wrong rule moves them by many orders of magnitude more than that (in the golden fixture every rule violation changes a return by at least 1e-3); floating-point noise is below 1e-13 (measured, below). The frozen C2 runner uses the same 1e-9 for its own guards.

## 4. Results

| Run | Interpreter and environment | Result |
|---|---|---|
| A | Registered interpreter (`/opt/anaconda3/bin/python3`), normal shell | **PASS**, all 8 steps |
| B | Registered interpreter, empty process environment (`env -i`, `-E -s -B`, other working directory) — the test `test_reproduction_command_in_a_clean_process` | **PASS**, exit 0, repository unchanged |
| C | Fresh venv built with `pip install` from the pins | **FAIL, closed**: the PyPI wheel of scipy 1.15.3 cannot be loaded on macOS 27 arm64 (cause in `DEPENDENCY_FINAL_REPORT.md` section 2). pip is not a supported mechanism. |
| D | **Clean Conda environment created from `release/s2_mom_v1/environment.yml`**, empty process environment | **PASS**, exit 0, all 8 steps |
| E | Another machine, OS or CPU | not run |

Numbers of run A (`docs/audit/remediation/reproduction_report.json`):

| | |
|---|---|
| Quantities compared | 117 |
| Numbers compared | 8,257 |
| Within tolerance | **117 of 117 quantities — every one of the 8,257 numbers** |
| Exactly equal (difference 0) | 26 quantities (all counts, memberships, labels; some statistics) |
| Largest absolute difference | **6.7057e-14** |
| Where | "confirmation step difference B−C: mean, t, p" — the **t-statistic** of the mean of WML_B − WML_C in the confirmation sample |
| Declared tolerance for that quantity | 1e-9 (the difference is about 15,000 times smaller) |
| Next largest | 5.55e-14 (primary delta series), 4.44e-14 (confirmation delta series), 2.5e-14 (two other step differences) |

**Why the difference exists — verified by a separate calculation, not assumed.**

1. The two implementations compound returns differently. The frozen code sums `log(1 + r)` and takes `exp`; the independent code multiplies `(1 + r)`. Both are correct; they round differently in the last bit.
2. Measured effect on the 224 monthly returns of the confirmation sample (W, L, benchmark, WML): largest difference **5.4e-16** as a fraction — two units in the last place of a number near 1. About 5% of the monthly returns are bit-identical, the others differ in the last one or two bits.
3. Converted to percent (×100) and differenced between steps, that becomes at most **5.4e-14** per month for the B − C series.
4. The mean of that series is small (0.0612% per month) and its standard error is 0.0601. The recomputed mean differs from the registered one by 4.0e-15; the standard error by 5.6e-17. The t-statistic is mean / standard error = 1.0175089334553473 (recomputed) against 1.0175089334552803 (registered): difference **6.7e-14**, relative difference 6.6e-14.
5. Cross-check: feeding the **registered** monthly series into the independent Newey–West function gives t = 1.0175089334552858, which differs from the registered t by only 5.6e-15. So the test statistic code agrees to the last bits, and the 6.7e-14 comes from the last-bit differences of the monthly returns, amplified by dividing a small mean by a small standard error.

Run D (clean Conda environment) has the same largest difference in the same quantity. Compared with run A, 11 of the 117 quantities have a different last-digit difference (all below 1e-13); the other 106 are identical. So results are **not** bit-identical between two environments built from the same builds of Python and the numerical packages — which is the reason the contract is a tolerance.

Honest reading: **reproduction is demonstrated in the registered interpreter and in a Conda environment rebuilt from the specification, on one machine. It is not demonstrated on a second machine or another platform.**

## 5. Fail-closed behaviour

`tests/test_failure_injection.py` runs the verification steps against a scratch copy with one thing broken: 46 file attacks, 46 rejected, each for the expected reason (`FAILURE_INJECTION_REPORT.md`). In a clone without the external data the command exits 1 with "missing input"; it does not skip the missing part and does not download anything.

## 6. What a reader still has to trust

1. That `data/stage2` was built from the raw archive as recorded (hash evidence and the 2026-10-05 rebuild log; not rerun here).
2. That the registered sensitivity results are what the registered code produced (hash and code-hash evidence; not recomputed).
3. That the second implementation and the first do not share a misunderstanding of the protocol. Both were written from the same text; the golden fixture's expected values were worked out by hand from that text, which lowers this risk but does not remove it. A reader who doubts a rule should check that rule in the golden fixture (`tests/test_s2mom_mutation_kills.py`, part 1), where each number is written as arithmetic.

## 7. Status

F-05: **FIXED + REGRESSION PROTECTED** for "an executable, independent reproduction exists and fails closed".
Open sub-item (N-01): reproduction on a second machine or platform.
