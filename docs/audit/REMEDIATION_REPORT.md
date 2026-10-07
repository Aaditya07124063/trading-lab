# Trading Lab — remediation report (2026-10-07)

Controlled research-integrity hardening of S2-MOM-v1 after the forensic audit of the same day.
The forensic audit's 18 files are preserved byte-identical in `docs/audit/forensic_20261007/` (checked by `tests/test_frozen_code.py::test_original_forensic_audit_files_are_preserved_unchanged`).

## 1. Rules of this phase, and whether each was kept

| Rule | Kept? | Evidence |
|---|---|---|
| No new research | yes | no new hypothesis, sample, parameter or analysis |
| No product features, no UI redesign | yes | `server.py`, `web/` untouched by remediation (they carry earlier uncommitted work of the researcher, left unstaged) |
| S2-MOM hypothesis unchanged | yes | — |
| Frozen protocol unchanged | yes | `f1abd954…d838`; all `docs/research/*` byte-identical to the snapshot |
| No registered experiment rerun | yes | trial log has the same 10 lines and the same size as before; five `s2_mom_v1` runs, as before (`test_registry_and_trial_log_only_grew`) |
| No registered result changed | yes | all 18 result files byte-identical to the snapshot and to the registry |
| History not silently rewritten | yes | registry: first 58 lines byte-identical, 3 lines appended, each with reason and actor; audit reports: originals preserved |
| No test weakened to pass | yes | one existing test file was touched: `tests/test_access_boundary.py` gained two allow-list entries for the two new read-only verification tools. No assertion was removed or loosened anywhere. |
| No commit, no push | yes | changes are staged in the index only |
| Stop conditions | none triggered | no protocol, result, hash, hypothesis, rerun, Stage 2 rebuild or research decision was needed |

## 2. Pre-remediation snapshot

File: `docs/audit/remediation/pre_remediation_snapshot.json` (taken 2026-10-07 before any change; never overwritten — the tool refuses).

| # | Item | Where |
|---|---|---|
| 1 | Complete snapshot | SHA-256 and size of all 6,988 files of the repository (including git-ignored data); a tar of every file that was not in Git (33.8 MB, SHA-256 `e0d90037…92fa`) at `~/Projects/trading-lab-archive/pre_remediation_worktree_20261007.tar.gz` |
| 2 | Hash of every audit file | in the snapshot; also `docs/audit/remediation/forensic_20261007.SHA256SUMS` |
| 3 | Hash of every frozen protocol / addendum / supplement | in the snapshot (`docs/research/*`) |
| 4 | Hash of every registered result | in the snapshot (`results/s2_mom_v1*/*`) |
| 5 | Hash of every Stage 3 input | in the snapshot (`data/stage3/*`) |
| 6 | Git HEAD and working tree | HEAD `7d4cb6d977ee1fbe40351fc6b6049c49af7638b2`, branch `main`, 113 status lines recorded |
| 7 | Python and dependency versions | Python 3.13.5, platform, full `pip freeze` |
| 8 | Files remediation may modify | allow-list inside the snapshot and in `scripts/audit_snapshot.py`: `src/registry/experiments.py`, `requirements.txt`, `README.md`, `REPRODUCIBILITY.md`, `CHANGELOG.md`, `RESEARCH_LOG.md`, `.gitignore`, `pytest.ini`, `EXPERIMENT_REGISTRY.md`, `tests/conftest.py`, `tests/test_access_boundary.py` (allow-list entries only), regenerated reports in `docs/audit/`; append-only: `registry/*.jsonl`; new files only under `docs/audit/`, `tests/`, `scripts/`, `src/registry/`, `release/`, `requirements*.txt` |
| 9 | Confirmation that no registered research artifact is modified | `python3 scripts/audit_snapshot.py verify <snapshot>` after every step: **6,299 of 6,299 frozen files byte-identical** |

## 3. What was done, phase by phase

| Phase | Finding | What was added or changed | Tests added |
|---|---|---|---|
| 1 Version control | F-01 | `.gitignore` (rebuild log no longer ignored; comment on the archive rule); `scripts/release_archive.py`; `release/s2_mom_v1/ARCHIVE_MANIFEST.json`; 255 files staged in total by the end | `test_release_archive.py` 11, `test_version_control.py` 3 |
| 2 Provenance chain | F-02, F-12 | `src/registry/integrity.py::verify_stage3`; registry line 59 (anchors) | `test_provenance_chain.py` 24 |
| 3 Registry state machine | F-03, F-11, F-26 | `src/registry/experiments.py` rewritten | `test_registry_state_machine.py` 235 |
| 4 Mutation-resistant tests | F-04 | tests only; `scripts/mutation_campaign.py` | `test_s2mom_mutation_kills.py` 68 |
| 5 Reproduction | F-05, F-29 | `scripts/reproduce_s2_mom_v1.py` | `test_reproduction.py` 17 |
| 6 Dependencies | F-06 | `release/s2_mom_v1/environment.yml`, `conda-osx-arm64.lock`, `ENVIRONMENT.json`; `requirements-lock.txt`; `integrity.environment_report`; registry lines 60 and 61 | `test_environment.py` 9 |
| 7 Failure injection | — | `integrity.validate_stage3`, `validate_monthly`, `validate_step_e`, `validate_cutoffs`, `validate_delisting_types` | `test_failure_injection.py` 104 |
| 8 Writes and asserts | F-08, F-10 | no frozen file changed; see section 6 | part of the above |
| 9 Test quality | — | measurements, section 7 | `test_frozen_code.py` 41 |
| 10 Manuscript | — | `scripts/verify_manuscript.py` | `test_manuscript_verification.py` 1 |
| 11 System map | F-28 | `SYSTEM_ARCHITECTURE.md`, `DATA_FLOW.md`, `THREAT_MODEL.md`, `REPRODUCIBILITY.md`, `README.md` pointer, `CHANGELOG.md` | — |
| 12 Final audit | — | reports in this folder | — |

Order: the brief asked for Phase 2 before Phase 3. The verifier of Phase 2 and the state machine of Phase 3 were written together, and the real anchor was appended only once the state machine existed, so that the anchoring line itself is a fully described, chain-linked amendment and not a legacy-format line. Nothing else was reordered.

Tests: **451 before, 964 after** (513 new). New code: about 2,250 lines of tooling and 2,100 lines of tests. Frozen code changed: 0 lines.

## 4. Files

**Modified (9 tracked files in the staged set):**

| File | Changed by remediation? |
|---|---|
| `src/registry/experiments.py` | yes — rewritten |
| `registry/experiments.jsonl` | yes — lines 59 and 60 appended (lines 38–58 are the researcher's earlier uncommitted registrations) |
| `tests/test_access_boundary.py` | yes — two allow-list entries (three earlier entries are the researcher's) |
| `.gitignore` | yes — rebuild log un-ignored, archive rule explained (two earlier lines are the researcher's) |
| `EXPERIMENT_REGISTRY.md` | yes — regenerated from the registry |
| `REPRODUCIBILITY.md`, `CHANGELOG.md` | yes — S2-MOM-v1 section, two changelog lines |
| `RESEARCH_LOG.md`, `registry/trials.jsonl` | no — the researcher's earlier uncommitted work, staged unchanged |
 `README.md` gained one pointer paragraph and is left unstaged with the researcher's UI edits.

**Added by remediation:**
`src/registry/integrity.py`;
`scripts/audit_snapshot.py`, `release_archive.py`, `reproduce_s2_mom_v1.py`, `mutation_campaign.py`, `verify_manuscript.py`;
`tests/test_release_archive.py`, `test_version_control.py`, `test_provenance_chain.py`, `test_registry_state_machine.py`, `test_s2mom_mutation_kills.py`, `test_reproduction.py`, `test_environment.py`, `test_failure_injection.py`, `test_frozen_code.py`, `test_manuscript_verification.py`;
`release/s2_mom_v1/ARCHIVE_MANIFEST.json`, `ENVIRONMENT.json`, `environment.yml`, `conda-osx-arm64.lock`; `requirements-lock.txt`;
`docs/audit/*` (this set), `docs/audit/forensic_20261007/*` (copies), `docs/audit/remediation/*` (evidence).

**Staged for the first time, unchanged in content (the experiment itself):** `src/stage3/`, `scripts/run_s2_mom*.py`, `scripts/build_stage3.py`, seven S2-MOM/UI test files, `config/cost_schedules/delivery_nse_eq_s2mom*.json`, `docs/research/*` (addendum, supplements, deviation log, specifications), `docs/evidence/s2mom_*`, `data/stage3/s2_mom_v1/*` except the panel, `results/s2_mom_v1*/*`, `docs/manuscript/s2_mom_v1/*`, `src/research_view.py`.

**Deliberately not staged:** `server.py`, `web/*`, `README.md` (UI work; `tests/test_ui_api.py` and `src/research_view.py` belong with it and should be committed together with it — see section 10), and the collector's files under `data/india/`, `data/raw/collection_log.jsonl`, `data/raw/manifest.jsonl`.

## 5. The three registry lines

| Line | Reason recorded in the line | Fields |
|---|---|---|
| 59 | F-02 and F-12: anchor the Stage 3 manifest, the check files, the rebuild log, the cost schedules, the external archive | `anchors` (new) |
| 60 | F-06: anchor the pinned environment specification, observed after the fact | `anchors` (two keys added) |
| 61 | Reproducibility contract: the corrected environment files (Conda specification, explicit lock, corrected wording about pip) supersede the anchor of line 60 for verification; line 60 stays | `anchors` (one key added) |

State FINAL before and after. `previous_hashes`, `new_hashes`, actor and chain hash are in each line. The anchored hashes equal the pre-remediation snapshot hashes.

## 6. Phase 8 — non-atomic writes and assert-based guards

**Frozen code was not modified.**

Non-atomic writes (F-08):

1. Limitation, documented: `scripts/run_s2_mom.py::_write` checks `exists()` and then writes; the CSV files and the registration follow. A crash in between leaves a readable, unregistered result. The Stage 3 manifest is also written in place.
2. This cannot happen again for S2-MOM-v1: every mode has run, and the registry now refuses a second registration on the FINAL experiment.
3. A registered output cannot be replaced silently: its hash is in the registry (immutable), the reproduction compares every file, rejects any unregistered file in a results folder, and requires exactly five logged runs.
4. All new tooling writes to a temporary name, fsyncs where it matters, and renames: registry summary, archive manifest, archive tar, restored archive members, reproduction report. Registry appends are one line under a lock with fsync. Tested by `test_an_interrupted_write_never_leaves_a_complete_looking_file` and the "interrupted registry write" attack.

Assert-based guards (F-10):

| File | asserts | What they guard | Disabled by `python -O`? | Explicit equivalent outside `assert` |
|---|---|---|---|---|
| `src/stage3/data.py::build` | 7 | last session = T\*; 170 months and first/last date; 114/56 split; holding windows exist; step A list = UNIV-1 members at T\*, 200; step C = UNIV-1 members, 200; step B has 200 | yes | `integrity.validate_stage3` (each one, among about 45 explicit checks) |
| `src/stage3/protocol.py` | 1 | T\* ≤ research cutoff | yes | `integrity.validate_cutoffs` |
| `src/access.py` | 1 | cutoff + 1 day = holdout start | yes | `integrity.validate_cutoffs` |
| `evaluate_orb_v1.py` | 4 | ORB configuration, frozen universe file, universe size, session window | yes | **none** (ORB single-use evaluator, outside S2-MOM; runbook rule: never run with `-O`) |

`tests/test_environment.py` holds this inventory as data and fails if an `assert` appears or disappears in frozen research code, and if the release tooling ever uses `assert` as a guard. A subprocess test shows that under `-O` an `assert` is gone and the explicit check still fires. The reproduction refuses to run optimised.

## 7. Phase 9 — test quality

Coverage was measured on the final suite with coverage.py 7.16.2 from a scratch directory (nothing was installed into the environment); summary in `docs/audit/remediation/coverage_summary.json`. **Coverage is reported, not used as the release criterion.**

| | Before (forensic) | After |
|---|---|---|
| Tests | 451 | 964 |
| Line + branch coverage, `src/` and `scripts/` | 71% | 74% (3,823 of 5,066 lines; 1,128 of 1,584 branches) |
| `src/registry/experiments.py` | 54% | 92% (257 of 276 lines, 111 of 122 branches) |
| `src/registry/integrity.py` | — | 98% (247 of 250 lines, 64 of 66 branches) |
| `src/stage3/data.py` | 26% | 49% (the loaders and their hash checks are now run, once on the real inputs; `build()` is still not executed by any test) |
| `scripts/run_s2_mom.py` | 52% | 67% (every gate is now run; the compute-and-write branches cannot run without registering) |
| `src/stage3/ladder.py`, `stats.py`, `experiment.py`, `step_e.py` | 95–100% | 97–100% |
| `scripts/reproduce_s2_mom_v1.py` | — | 69% in-process; the full recomputation runs in a subprocess that coverage did not follow |
| `scripts/build_stage2.py`, `build_stage3.py`, `audit_snapshot.py`, `mutation_campaign.py` | 0% | 0% (build scripts: not rerun by instruction; the two audit tools were used, not unit-tested) |

| Measure | Value | Source |
|---|---|---|
| Mutation score | before: 77 of 104 killed by a behavioural test (74%), 24 survivors. After: 196 of 196 non-equivalent mutations killed (198 executed; 2 proved equivalent); 0 survivors | `MUTATION_FINAL_REPORT.md` |
| Critical-invariant coverage | 24 of 24 invariants of the brief have a designed test and mutations that break them (section 4 of that report) | |
| Negative-test coverage | the large majority of the 513 new tests assert a **refusal**: nearly all of the 235 registry tests, 23 of 24 provenance tests, 103 of 104 failure-injection tests, 8 of 11 archive tests, and the gate and loader tests of the mutation-kill file. The remainder assert correct values (golden fixture, statistics, agreement of the two implementations). Not counted one by one. | test files |
| Failure-injection coverage | 26 of 26 attack kinds of the brief; 113 attacks: 112 rejected, 1 shown harmless, 0 silently accepted | `FAILURE_INJECTION_REPORT.md` |

The primary criterion — "can each research-critical invariant be shown to fail when deliberately violated?" — is answered per invariant in `MUTATION_FINAL_REPORT.md` section 4.

## 8. What was verified after each step

After every remediation: targeted tests, the full suite, `scripts/audit_snapshot.py verify`, and the staged diff summary. The frozen-hash verification passed every time (6,299 or 6,300 frozen files, depending on whether one newly allow-listed test file is counted). The full suite failed twice, both times for the intended reason: the new version-control guard reported files I had created and not yet staged.

## 9. Incidents during remediation

1. **Disk full on scratch clones.** A first mutation run with four parallel batches drove the machine into swap; the disk (3 GB free at the start) filled and eight mutations ended in "No space left on device". The run was stopped, the scratch clones removed, and the repository verified intact (snapshot verification PASS). The tool now checks free space before every mutation, records every result as it goes, and resumes. Four campaign runs exist in total; only the last, complete one is scored, and the records of the other three are kept (`MUTATION_FINAL_REPORT.md` section 1a).
2. **Clean pip environment.** The pinned scipy wheel from PyPI does not load on this OS. The reproduction failed closed. This became finding N-01. It led to a stricter environment check (import, not just version), to an explicit Conda contract, and to a correction of the lock file's wording, recorded as registry line 61. A clean Conda environment built from the contract file then reproduced the results. Building it downloaded some packages into the Conda package cache of this machine; the scratch environment was removed.
3. **A too-wide "hash pin" pattern** in the first version of the mutation tool would have classified three behavioural provenance tests as hash pins. It was replaced by an exact list of twelve tests before the reported run.
4. **The intraday collector ran at 18:30** during remediation and changed 58 data files plus its logs (exit code 1 again, F-15). These files are outside the research chain; the verifier lists them separately.

## 10. What the researcher has to do

1. **Decide on the commit.** Everything is staged. Suggested split: (a) the experiment and the remediation — the staged set; (b) UI: `server.py`, `web/`, `README.md` (with `tests/test_ui_api.py` and `src/research_view.py`, which are currently in the staged set and must go into whichever commit comes first together with `server.py`, or the suite of the first commit will fail); (c) collector data. Then tag, then push. Until then F-01 is open.
2. **Store the archive off the laptop:** `python3 scripts/release_archive.py pack <external disk>/s2-mom-v1-data-baa0b47040101031.tar` (1.55 GB; the command verifies the hash).
3. **Free disk space** before either (about 2 GB of scratch copies from the forensic session are under `/private/tmp/claude-501/`; they were not deleted because they were not created in this session).
4. **Environment:** run the reproduction once on a second Apple-silicon Mac, and move the daily work from the Anaconda base environment into the dedicated one (`conda create -n s2mom --file release/s2_mom_v1/conda-osx-arm64.lock`) (N-01).
5. **Research decisions that are not software:** F-13 (perturbation check narrower than B2), F-21 (information ratio not reported), F-22 (one cell of the §27 table), F-27 (placebo gate), and R-1 … R-8 of the forensic `RESEARCH_INTEGRITY_AUDIT.md`.
6. **Manuscript:** add the hashes of Supplements 2 and 3 to Table A5 (N-02).
7. **Collector:** review the rejected BEL and CIPLA bars (F-15).
