# Trading Lab — prioritised remediation plan (2026-10-07)

**Status: PLAN ONLY. Nothing below has been done.** The audit changed no code, no test, no registry line and no artifact; it only added `docs/audit/`.

Rules that apply to every step (from the audit brief): one logical fix at a time · regression test with the fix · targeted tests, then the full suite · verify frozen and registered hashes after each step · no protocol change · no rerun of a registered mode · record every change.

## 1. Which files must not change

A change to any of these alters a registered hash. They are **report-only** unless the researcher approves an exception or opens a new protocol version.

| Hash | Files |
|---|---|
| Main code hash `f57c9321…` (primary, sensitivity, confirmation) | `src/stage3/protocol.py`, `ladder.py`, `data.py`, `stats.py`, `costs.py`, `experiment.py`, `scripts/run_s2_mom.py` |
| Step E code hash `a6845d30…` | `src/stage3/step_e.py`, `scripts/run_s2_mom_step_e.py` |
| C2 code hash `505b2e4e…` | `scripts/run_s2_mom_c2.py` |
| Stage 2 manifests (`code_sha256` inside `panel1_1_manifest.json`, `ret1_1_manifest.json`) | `src/stage2/panel.py`, `archive.py`, `returns.py`, `corporate_actions.py`, `identity.py` (and `universe.py` by the UNIV-1 freeze) |
| ORB v1 frozen hashes | `src/intraday/*` (8 files), ORB protocol, cost files, calendar and index evidence |
| Protocol, addendum, supplements, cost schedule, every file under `results/s2_mom_v1*`, `data/stage2`, `data/stage3` | as registered |

Free to change: `src/registry/experiments.py`, `src/research_view.py`, `server.py`, `tests/*` (adding tests), new scripts, requirement files, top-level documents.

## 2. Decisions needed from the researcher before any step

| # | Decision | Why it is yours |
|---|---|---|
| Q1 | **Commit the working tree now, exactly as it is?** (F-01) | A commit is your action. It changes no file content, so no hash changes. Options: one commit for the experiment, a separate one for collector data |
| Q2 | **May the audit append amendments to `registry/experiments.jsonl`?** (F-02, F-06, F-12) | The registry is a registered artifact. Appending is its designed use, but only you approve entries. Proposed entries: Stage 3 manifest hash; hashes of the two pre-run check files; the environment observed on 2026-10-07 (labelled "after the fact"); the commit id from Q1 |
| Q3 | **Registry state machine: which transitions are legal?** (F-03) | Proposed: PLANNED → any; FINAL → SUPERSEDED / INVALID / REQUIRES REVALIDATION only; protected fields can never change; reason must be non-empty |
| Q4 | **Frozen-code findings (F-07, F-08, F-09, F-10, F-13, F-17, F-19, F-22, F-23, F-25, F-30): keep for S2-MOM-v2, or approve an exception now?** | Recommendation: do **not** touch frozen code. All of them are covered for the registered runs by evidence in this audit; guard them from outside with the verifier and tests |
| Q5 | **Research disclosures R-1 to R-8** (`RESEARCH_INTEGRITY_AUDIT.md`) | Scientific judgement, not software |

## 3. Order of work after approval

### Stage A — protect what exists (no code change)

| Step | Finding | Action | Verification | Hash impact |
|---|---|---|---|---|
| A1 | F-01 | Commit the tree; tag `s2-mom-v1-registered` | `git status` clean for `src`, `scripts`, `tests`, `config`, `docs/research`, `results/s2_mom_v1*`, `data/stage3` manifests; full suite; every registered hash recomputed | none (content unchanged) |
| A2 | F-05 | Copy the git-ignored inputs (`data/raw/nse_archive`, `data/stage2/datasets`, `panel.parquet`) to a second location with a checksum list | checksums equal the manifests | none |

### Stage B — P1 fixes outside frozen code (one commit each)

| Step | Finding | Root cause | Fix | Test | Hash impact |
|---|---|---|---|---|---|
| B1 | F-04 | invariants were tested where convenient, not where a break would hurt | add `tests/test_s2mom_regressions.py` covering G-01 … G-09, G-13 (tests only) | each of the 24 surviving mutations must now fail; rerun the mutation set | none |
| B2 | F-05 | "runs once" left no way to recompute | add `scripts/verify_s2_mom.py` — the audit's independent implementation: hashes, ladder A–D, δ, H1, step E, structural checks with explicit raises, value checks of F-07 — read-only, prints PASS/FAIL, exit code | opt-in `pytest -m golden` that runs it when the git-ignored inputs are present | none |
| B3 | F-03 | registry written as a log, read as a source of truth | state machine, protected fields, non-empty reason, duplicate-id error, lock + fsync, previous-line hash for **new** lines only | golden test: the existing 58 lines fold to exactly the same `current()` view as before; each illegal action is refused | none (file not rewritten) |
| B4 | F-02, F-12 | manifest and check files never reached the registry | after Q2: append one amendment with the manifest content hash and the two check-file hashes; the verifier compares them | tampered-file + rewritten-manifest test is refused by the verifier | registry gains lines; `EXPERIMENT_REGISTRY.md` regenerated; no result hash changes |
| B5 | F-06 | environment grew without a pin | pinned requirement files; `environment()` records scipy, pyarrow, platform; after Q2 append the observed environment | test: every third-party import under `src/stage2`, `src/stage3`, `src/registry` is in `environment()` | none |

### Stage C — P2 fixes outside frozen code

| Step | Finding | Fix |
|---|---|---|
| C1 | F-11 | `log_trial` suppresses only under pytest; otherwise raises when the variable is set |
| C2 | F-14 | `/api/add`: POST, strict symbol pattern, never overwrite an existing file, atomic write |
| C3 | F-18 | synthetic end-to-end tests of `evaluate_orb_v1.run` (tests only) |
| C4 | F-09, F-20 | tests that pin the first-party import graph of each runner and assert that duplicated constants and patterns are equal |
| C5 | F-15 | review the two rejected collector datasets; report code and data dirtiness separately |
| C6 | F-28, D-01 | write the S2-MOM section of `REPRODUCIBILITY.md` and a README pointer |
| C7 | F-29 | covered by B2 (tolerance-based comparison) |

### Stage D — report-only items (frozen code)

F-07, F-08, F-10, F-13, F-16, F-17, F-19, F-21, F-22, F-23, F-24, F-25, F-27, F-30. Each has an outside guard in Stage B/C where one is possible (verifier checks, runbook rules). Each should be listed in a "known limitations of the v1 code" note and carried into the design of any S2-MOM-v2.

Runbook rules to adopt now (documentation, no code): never run a runner with `python -O`; never set `TRADING_LAB_NO_TRIAL_LOG` outside pytest; never delete a file under `results/`; record a crashed run in the deviation log and the trial log by hand; compute results only through the runners or the verifier.

### Stage E — adversarial post-fix audit (Phase 27) and release gate (Phase 28)

Repeat: the mutation set (target: no survivor in "research logic" and "guards"), the attack script (registry, inputs, CLI), the independent recomputation, the full hash sweep, the before/after file-hash comparison of the test run. Then fill in `FINAL_RELEASE_GATE.md`.

## 4. What must be fixed before a final release, and what can wait

**Before release:** F-01, F-02, F-03, F-04, F-05, F-06 (all P1), plus F-11 and F-12 (cheap, and they close gate loopholes), plus the documentation step C6 and the researcher's decisions on R-1 … R-8.

**Can wait:** F-14, F-15, F-18 (not on the S2-MOM path), every P3, and every frozen-code item — provided the verifier of B2 is in place and the limitations note is published with the results.
