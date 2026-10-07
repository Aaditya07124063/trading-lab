# Trading Lab — final release gate (state on 2026-10-07, after the forensic audit, before any remediation)

**Verdict: NOT READY FOR RELEASE.** P0 = 0. P1 = 6, all open. Phases 26–28 of the audit brief (remediation, post-fix attack, final gate) have not been carried out; they wait for the researcher's approval (`REMEDIATION_PLAN.md`, section 2).

This file does not say the code is secure, bug-free or fully verified. It says what is proven, by what, and what is not.

| Gate item | State | Evidence | Label |
|---|---|---|---|
| System architecture mapped | done | `SYSTEM_ARCHITECTURE.md` | VERIFIED BY INSPECTION |
| All executable paths mapped | done (19 entry points, classified) | `SYSTEM_ARCHITECTURE.md` table B | VERIFIED BY INSPECTION |
| Requirements traced to implementation | done (43 requirements) | `REQUIREMENTS_TRACEABILITY.md`, `.csv` | mixed — 20 PASS, 17 PARTIAL, 3 MISSING, 2 CONTRADICTED, 1 UNVERIFIED |
| Critical invariants executable | **no** | 24 of 104 mutations survive; trust-boundary code at 26 % coverage | PROVEN BY TEST (the gap) |
| P0 findings = 0 | **yes** | `BUG_FINDINGS.md` | — |
| P1 findings = 0 or accepted | **no** — 6 open (F-01 … F-06) | `BUG_FINDINGS.md` | — |
| Critical mutation tests killed | **no** — 80 / 104 (77 %); research logic 30 / 34 | `MUTATION_TEST_REPORT.md` | PROVEN BY TEST |
| Leakage tests pass | yes (suite) and yes on real data (saved pre-run checks) | tests; `checks/pre_run_checks_*.json` | PROVEN BY TEST; check files unanchored (F-12); narrower than B2 (F-13) |
| Numerical invariants pass | yes for the registered data | independent recomputation, statsmodels cross-check | PROVEN by recomputation |
| Deterministic rerun property verified | yes on this machine; cross-machine not tested | audit recomputation ≤ 5e-16 | PROVEN (one machine) · UNVERIFIED (others) |
| Atomic-write behaviour verified | partly — step E and C2 yes; main runner, Stage 3 manifest, registry no | tests; F-08, F-03 | PROVEN BY TEST / VERIFIED BY INSPECTION |
| Corrupted-artifact detection verified | yes for result files, protocol, schedule, step E / C2 inputs; **no for Stage 3 inputs with a rewritten manifest** | tests; attack script (F-02) | PROVEN |
| Registry state machine verified | **no** — there is none | attack script (F-03) | PROVEN (the gap) |
| No unsafe bypass path | **no** — direct import (L-01), hand-made gate evidence (L-04), environment switches (L-08, L-09) | `LOOPHOLE_AUDIT.md` | VERIFIED BY INSPECTION / PROVEN |
| No secret leakage | yes | `THREAT_MODEL.md` | VERIFIED BY INSPECTION |
| Dependency versions recorded | in the audit file only; not pinned in the repository; scipy/pyarrow absent from four of five registered runs | `DEPENDENCY_AUDIT.md` (F-06) | DOCUMENTATION ONLY |
| Clean-environment reproduction documented | drafted in the audit; **cannot be executed** until F-01 and F-06 are fixed | `REPRODUCIBILITY_AUDIT.md` | DOCUMENTATION ONLY |
| Frozen protocol unchanged | yes — `f1abd954…d838` | hash recomputed | SUPPORTED BY HASH |
| Registered research outputs unchanged | yes — all 18 registered result files | hashes recomputed against the registry | SUPPORTED BY HASH |
| Full test suite passes | yes — 451 passed; repository byte-identical afterwards | pytest run; file-hash comparison | PROVEN BY TEST |
| Regression suite passes | not applicable yet (no remediation, no new regression tests) | — | — |
| Final hashes recorded | see below | — | SUPPORTED BY HASH |
| Documentation matches implementation | **no** — 13 open items | `DOCUMENTATION_CODE_AUDIT.md` | VERIFIED BY INSPECTION |
| Release report generated | this folder | — | — |

## Hashes at the end of the audit (unchanged from the registry)

| Item | SHA-256 |
|---|---|
| Frozen protocol | `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838` |
| UNIV-1 | `2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42` |
| Cost schedule (dated) | `47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f` |
| Main code hash (primary = sensitivity = confirmation) | `f57c9321fa8a32172a6c0cd9b2e066bcf07144790836fd79a956a407219fa1d1` |
| Step E code hash | `a6845d30b0cb65101fe6c3ea4623dd6753c2b7734d2ea2471cc4b88f51aacc54` |
| C2 code hash | `505b2e4ed9d4e1f34dc2e441f2ff73e8399998e4744a6f0b4b7d62e59668b3fa` |
| Blinded precision | `1e26341044f3e46052fdcda53a56721124412e26d5b93156bf274a9a4de5c693` |
| Primary results | `fe7e95ba97482d6d53faba543d860e4f0d1e50cfa0312d669e910346d41ef857` |
| Sensitivity results | `7d6081d8c4a099f7cd1d7d688791c23180d6977536ae4c7860a08b429ff0c19b` |
| Confirmation results | `38d1d0a9fbb1d22a19b7912ec4e6285d1dbcb920ffd0e6d99ea19e096c304d92` |
| Step E results | `675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0` |
| C2 results | `cf977e8a5efce7ba83ce91bf70ae247ed1aea96c7004f8d03162669097689513` |

## Answers to the eleven questions

**A. Can the current code be trusted?** For the registered S2-MOM-v1 numbers: yes, with evidence — an independent implementation reproduces every A–D step-month, δ, the H1 statistics and every step E cost to about 1e-16, and every hash matches. As a system that "cannot silently corrupt results and can be independently verified": not yet — the code and results are not in version control, the registry can be rewritten, part of the hash chain is unanchored, and 24 deliberate bugs pass the tests.

**B. What can silently produce an incorrect scientific result?** A future edit of the ladder, statistics or cost code in any of the 24 ways listed in the mutation report (for example `WML = W + L`, a dropped exit day in step D, a one-tailed bootstrap count). Malformed input values in a rebuilt panel (F-07). A missing portfolio-month in step E costed at zero (F-17). None of these is present in the registered runs.

**C. What can corrupt data?** Loss of untracked files (F-01). A registry amendment or duplicate line (F-03). An edited Stage 3 file with a rewritten manifest (F-02). `/api/add` overwriting a daily CSV (F-14). A non-zip HTTP 200 body stored in the raw archive (F-16).

**D. What can bypass frozen safeguards?** Direct import of the Stage 3 modules (L-01). Hand-made gate evidence (L-04). A change in a module outside the hashed file list (L-05). `TRADING_LAB_NO_TRIAL_LOG` and `python -O` (L-08, L-09). Deleting an output file to re-open a "runs once" mode (L-06).

**E. What can make two runs produce different results?** A different numpy / pandas / pyarrow / scipy version or CPU (last digits, parquet bytes — then the byte-identity checks refuse). A new NSE list snapshot (detected). Nothing else was found: seeds are fixed, orderings are explicit, no clock or locale reaches a hashed output.

**F. What can make a failed run look successful?** In the main runner, a crash after the results JSON is written leaves a complete-looking file that is unregistered and unlogged (F-08); a partial JSON also counts as "already exists". A NaN test statistic is labelled `INCONCLUSIVE` (F-07). The collector's failure is visible only as exit code 1 in a log (F-15).

**G. Which critical assumptions are enforced only by documentation?** "Called only by the runner". "Each mode runs once" (file existence). "The registry is never edited". "Every run is in the trial log". "Stage 2 rebuild passed 150 of 150" (hand-entered). "Code developed on synthetic and permuted data only". "Raw files are never modified".

**H. Which safeguards are not executable?** The seven structural checks of the Stage 3 build and three cutoff/window checks are `assert` statements (off under `-O`). The same-code rule for confirmation, the run-once guard of the main runner and all three Stage 3 loader hash checks exist in code but are executed by no test.

**I. Which tests provide false confidence?** The "registered … intact / byte identical" tests (hash only), the constants test, the gate-order test (stubs), the source-text tests (`"… not in src"`), and `test_g_samples_end_at_protocol_exit_sessions…` (checks wording in a function that is never run). Details in `TEST_COVERAGE_AUDIT.md` section 4.

**J. What must be fixed before final release?** F-01 to F-06, plus F-11, F-12, the reproduction document, and the researcher's decisions on R-1 … R-8.

**K. What can safely wait?** F-14, F-15, F-18, every P3, and every finding that needs a frozen-code change — on condition that the independent verifier is added and the limitations are published with the results.
