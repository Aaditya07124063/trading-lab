# Trading Lab — bug findings (forensic audit, 2026-10-07)

Severity: **P0** can invalidate results, corrupt data, silently produce false results or break integrity/security · **P1** serious correctness, reproducibility or testability problem · **P2** meaningful engineering weakness · **P3** minor.

Counts: P0 = 0 · P1 = 6 · P2 = 14 · P3 = 10. Total 30.

**No finding changes a registered number.** Every registered A–D and step E figure was reproduced by independent code (see `RESEARCH_INTEGRITY_AUDIT.md`). No P0 was found.

`Frozen` = the fix would change a file inside a registered code hash; such findings are reported only and are not to be fixed without explicit approval.

| ID | Sev | File | One-line description | Frozen |
|---|---|---|---|---|
| F-01 | P1 | repository (git) | The whole S2-MOM-v1 experiment is outside version control: src/stage3/, scripts/run_s2_mom*.py, scripts/build_stage3.py, seven test files, the deliver | no |
| F-02 | P1 | src/stage3/data.py | data/stage3/s2_mom_v1/manifest.json is the only integrity anchor for the Stage 3 inputs (calendar, universes, identity, sessions, gap rows, panel) | no |
| F-03 | P1 | src/registry/experiments.py | The registry is not a state machine | no |
| F-04 | P1 | tests/ | 24 of 104 deliberate mutations of critical logic pass the whole 451-test suite | no |
| F-05 | P1 | repository | There is no executable reproduction or verification of the registered results | no |
| F-06 | P1 | requirements.txt ; src/registry/experiments.py | No dependency is pinned and there is no lock file | no |
| F-07 | P2 | src/stage3/ladder.py ; src/stage3/stats.py | The matrix builder does not validate the values it is given | yes |
| F-08 | P2 | scripts/run_s2_mom.py | Output writing is neither atomic nor exclusive | yes |
| F-09 | P2 | scripts/run_s2_mom.py ; scripts/run_s2_mom_step_e.py ; scripts/run_s2_mom_c2.py | The code hashes do not cover everything the runs execute | yes |
| F-10 | P2 | src/stage3/data.py ; src/stage3/protocol.py ; src/access.py ; evaluate_orb_v1.py | Safeguards are written as assert statements: the seven structural checks of the Stage 3 build (last session = T*, 170 months, 114/56 split, step A/B/C | yes |
| F-11 | P2 | src/registry/experiments.py | The environment variable TRADING_LAB_NO_TRIAL_LOG (meant for tests) silently disables trial logging for any real run started from a shell where it is  | no |
| F-12 | P2 | scripts/run_s2_mom.py | Two gates rest on hand-editable evidence | yes |
| F-13 | P2 | src/stage3/experiment.py | The real-data perturbation check scrambles returns and research-grade flags after t | yes |
| F-14 | P2 | server.py | GET /api/add downloads a Yahoo history and overwrites data/india/<symbol>d1.csv in place, non-atomically, with no confirmation | no |
| F-15 | P2 | scripts/collect_intraday.sh ; update_intraday.py | The launchd collector appends to 58 git-tracked data files in the research working tree every weekday, so the tree is permanently dirty and the regist | no |
| F-16 | P2 | src/stage2/archive.py | Any HTTP 200 response body is stored as a permanent raw file and recorded with its hash | yes |
| F-17 | P2 | src/stage3/step_e.py | A portfolio-month with no ledger row gets cost 0 through fillna(0.0), and the guard only requires costed months to be a subset of gross months | yes |
| F-18 | P2 | evaluate_orb_v1.py | The single-use ORB v1 holdout evaluator has 26 % line coverage; its body is exercised only by two manual dry runs on development data (identical resul | no |
| F-19 | P3 | src/stage3/ladder.py | The 'gap return already booked' set is kept per portfolio | yes |
| F-20 | P3 | src/stage3/ladder.py ; src/stage2/returns.py ; src/stage2/identity.py ; src/stage2/universe.py ; scripts/ | Duplicated rules and constants: the 'unadjustable event' pattern exists in returns.py and again in ladder.py; three union-find implementations with tw | no |
| F-21 | P3 | src/stage3/experiment.py | Protocol section 14 defines the Sharpe-type ratio of long-only portfolios as the information ratio against the step's benchmark | yes |
| F-22 | P3 | src/stage3/experiment.py | Decision order: a significant estimate whose 90 % interval lies wholly inside +/-0.10 is labelled DETECTED_SIZE_UNCERTAIN; the protocol table can also | yes |
| F-23 | P3 | src/stage3/protocol.py ; src/stage3/experiment.py | The Newey-West lag is looked up by sample name, not computed from the number of months actually tested | yes |
| F-24 | P3 | src/stage2/panel.py | Numeric fields are coerced (malformed -> NaN) and rows whose date cannot be parsed are dropped from the date comparison, then stamped with the file's  | yes |
| F-25 | P3 | src/stage3/data.py | Delisting class is decided by a case-sensitive substring test for 'Voluntary' in free text copied from the NSE file | yes |
| F-26 | P3 | src/registry/experiments.py | environment() swallows every exception from git and reports 'unknown'; timestamps are naive local time; git_dirty looks only at 'src' and '*.py'. | no |
| F-27 | P3 | src/stage3/experiment.py | The placebo gate requires p > 0.05 for one fixed seed, so it fails for about 5 % of seeds by construction | yes |
| F-28 | P3 | README.md ; REPRODUCIBILITY.md ; METHODOLOGY.md ; CHANGELOG.md | None of the four top-level documents mentions Stage 3 or S2-MOM-v1 | no |
| F-29 | P2 | scripts/run_s2_mom.py ; src/stage3/data.py ; scripts/build_stage2.py | Reproduction is defined as byte identity of CSV and parquet files | no |
| F-30 | P2 | src/stage3/data.py ; src/stage3/experiment.py | Any Python session can import the Stage 3 modules and compute any sample's results directly | yes |

## F-01 — P1

- **File:** `repository (git)`
- **Function:** -
- **Line:** -
- **Description:** The whole S2-MOM-v1 experiment is outside version control: src/stage3/, scripts/run_s2_mom*.py, scripts/build_stage3.py, seven test files, the delivery cost schedules, addendum 1 and supplements 1-4, the deviation log, data/stage3/, results/s2_mom_v1*/, the manuscript, and 21 registry + 6 trial lines are untracked or uncommitted. The registry's freeze_commit and environment.git_commit (7d4cb6d) contain none of this code.
- **Why it matters:** There is exactly one copy of the registered code and results, on one disk. git clean -fd, git stash -u, a bad checkout or a disk fault destroys it. No third party can obtain the code that produced the registered hashes. 'git_dirty: true' is the only trace.
- **Reproduction:** git status --short | grep '^??' ; git ls-files src/stage3 (empty) ; git show 7d4cb6d --stat (protocol only)
- **Expected behaviour:** Registered code, inputs manifests, results and registry lines are committed; the registry names a commit that contains them.
- **Actual behaviour:** 112 changed/untracked paths; registered experiment code not in any commit.
- **Proposed fix:** Commit the current tree as it is (no content change, so every SHA-256 stays the same); tag it; record the commit id in a registry amendment. Decide whether data/india collector changes go in the same or a separate commit.
- **Test that will prevent regression:** Test: every path in the registered CODE tuples, every registered result file and the Stage 3 manifest is tracked by git (git ls-files --error-unmatch) and unmodified at HEAD.
- **Evidence:** VERIFIED BY INSPECTION (git status, git ls-files)
- **Needs a frozen-code change:** no

## F-02 — P1

- **File:** `src/stage3/data.py`
- **Function:** load_inputs / build / verify_provenance
- **Line:** 175-185, 194-197, 223-233
- **Description:** data/stage3/s2_mom_v1/manifest.json is the only integrity anchor for the Stage 3 inputs (calendar, universes, identity, sessions, gap rows, panel). The manifest itself is anchored nowhere: its hash is not in the registry (provenance.data_manifest is a path), not in code, and the file is untracked. verify_provenance() checks Stage 2 inputs and three code files, not the Stage 3 outputs.
- **Why it matters:** Inputs and manifest can change together (hand edit, or delete-and-rebuild after any upstream change) and the runner accepts them. The hash chain from registry to the numbers the ladder reads has a missing link.
- **Reproduction:** On a scratch copy: append one byte to primary/calendar.csv -> load_inputs raises. Put the new hash into manifest.json -> load_inputs returns normally.
- **Expected behaviour:** A changed Stage 3 input is refused even if the manifest was changed with it.
- **Actual behaviour:** Accepted silently once the manifest matches.
- **Proposed fix:** (a) Record the SHA-256 of the manifest 'content' block in the registry by an amendment (value today is consistent with the registered results: proven by the audit recomputation). (b) Add a verification command and a test that compare the manifest with the registered value. Enforcing it inside the runner would change scripts/run_s2_mom.py (frozen) - do that only in a later protocol version.
- **Test that will prevent regression:** Test: tampered Stage 3 file + rewritten manifest is rejected by the verifier; registered manifest hash equals the file on disk.
- **Evidence:** PROVEN (audit attack script, scratch copy)
- **Needs a frozen-code change:** no

## F-03 — P1

- **File:** `src/registry/experiments.py`
- **Function:** amend / current / record / _read
- **Line:** 56-109
- **Description:** The registry is not a state machine. amend() accepts any field: status FINAL -> PLANNED, a new protocol_sha256, a provenance block that replaces (not merges) the registered run hashes, an empty reason. current() lets a second line with the same experiment_id discard every earlier amendment. No file lock, no fsync, no checksum chain; appends are plain open('a'). A truncated last line makes the whole registry unreadable (fail loud, no recovery tool).
- **Why it matters:** The registry is the root of trust for 'what was registered'. Any helper, test or hand edit can re-point a registered result to different hashes or flip its status without an error.
- **Reproduction:** On a scratch copy: experiments.amend('S2-MOM-v1','x',status='PLANNED'); amend(..., protocol_sha256='0'*64); amend(..., provenance={'primary_run': {...}}); amend(..., ''); append a duplicate record line -> current()['S2-MOM-v1']['status'] == 'PLANNED'.
- **Expected behaviour:** Invalid transitions, changes to protected fields, loss of registered hashes, empty reasons and duplicate ids are refused.
- **Actual behaviour:** All accepted. Only an unknown id or an unknown status string is refused.
- **Proposed fix:** In experiments.py (not part of any registered code hash): protected-field list (experiment_id, protocol_sha256, freeze_commit, universe_sha256, registered files_sha256 of an existing run); allowed status transitions; non-empty reason; current() raises on a duplicate id; append under an exclusive lock with flush+fsync; each new line carries the SHA-256 of the previous line. Must accept the existing 58 lines unchanged.
- **Test that will prevent regression:** State-machine tests: FINAL -> PLANNED refused; protected field change refused; registered run hashes cannot be dropped or altered; duplicate id raises; existing registry file still folds to the same current() view (golden).
- **Evidence:** PROVEN (audit attack script, scratch copy)
- **Needs a frozen-code change:** no

## F-04 — P1

- **File:** `tests/`
- **Function:** -
- **Line:** -
- **Description:** 24 of 104 deliberate mutations of critical logic pass the whole 451-test suite. Among them: WML = W + L; step D drops the exit-session return; step D uses raw returns on every row; the H1 decision threshold reversed; a one-sided bootstrap count; the Stage 3, RET-1.1 and UNIV-1 hash checks switched off; the run-once guard switched off; confirmation allowed without a same-code primary run; cost rates taken at the exit date; identity links from the future; liquidity window 64 instead of 63. src/stage3/data.py has 26 % line coverage; scripts/run_s2_mom.py 52 %; src/registry/experiments.py 54 %.
- **Why it matters:** These are exactly the 'dangerous bug that keeps every test green' cases. The registered numbers are right today (proven by independent recomputation) but the suite would not notice if the code were changed tomorrow.
- **Reproduction:** See MUTATION_TEST_REPORT.md; each survivor was applied to a scratch copy and the full suite run. Three were re-confirmed by hand (451 passed).
- **Expected behaviour:** Every listed mutation fails at least one behavioural test.
- **Actual behaviour:** 24 survive.
- **Proposed fix:** Add tests only (no source change): see TEST_GAP_MATRIX.md G-01..G-16.
- **Test that will prevent regression:** Re-run the mutation set; target: zero survivors in the 'research logic' and 'guards' groups.
- **Evidence:** PROVEN BY TEST (mutation run on scratch copies)
- **Needs a frozen-code change:** no

## F-05 — P1

- **File:** `repository`
- **Function:** -
- **Line:** -
- **Description:** There is no executable reproduction or verification of the registered results. The 'golden' tests only hash the result files. Registered modes refuse to rerun by design, and no verify mode recomputes and compares. A clean clone also lacks the inputs: data/raw/nse_archive, data/stage2/datasets and panel.parquet are git-ignored, and the NSE list snapshots cannot be re-downloaded in their original version.
- **Why it matters:** The stated standard is independent verifiability. Today it needs the original laptop plus new code written by the verifier.
- **Reproduction:** grep -n 'hashed only' tests/ ; .gitignore ; scripts/run_s2_mom.py _write
- **Expected behaviour:** A documented command recomputes the A-D series, delta, H1 and step E from the Stage 3 inputs with independent code and compares with the registered files at a stated tolerance.
- **Actual behaviour:** No such command. The audit wrote one outside the repository (all 680 step-months and all step E months match to <= 5e-16).
- **Proposed fix:** Add scripts/verify_s2_mom.py (the audit's independent implementation), an opt-in slow test that runs it when the git-ignored inputs are present, and a deposit plan for the git-ignored inputs (archive with checksums).
- **Test that will prevent regression:** pytest -m golden: independent recomputation equals registered monthly/delta/step E files within 1e-9.
- **Evidence:** VERIFIED BY INSPECTION; recomputation PROVEN by the audit script
- **Needs a frozen-code change:** no

## F-06 — P1

- **File:** `requirements.txt ; src/registry/experiments.py`
- **Function:** environment
- **Line:** 38-53
- **Description:** No dependency is pinned and there is no lock file. numpy, scipy and pyarrow are used by the experiment and not declared. The registry environment block of the primary, sensitivity, confirmation and step E runs records neither scipy (p-values) nor pyarrow (parquet bytes behind the input hashes). The lab runs in the shared base Anaconda environment.
- **Why it matters:** The exact environment of the registered runs cannot be rebuilt from the repository, and a routine conda update changes it silently.
- **Reproduction:** cat requirements.txt ; python3 -c "from src.registry.experiments import environment; print(environment())"
- **Expected behaviour:** Exact versions of every package on the research path are pinned in the repository and recorded with each run.
- **Actual behaviour:** Eight unpinned names; scipy/pyarrow unrecorded for four of five runs.
- **Proposed fix:** Add pinned requirement files (versions in DEPENDENCY_AUDIT.md); add scipy, pyarrow and platform to environment(); record the environment observed on 2026-10-07 by a registry amendment labelled 'observed after the fact'; use a project virtual environment.
- **Test that will prevent regression:** Test: environment() contains every package imported under src/stage2, src/stage3, src/registry; pinned file equals installed versions.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** no

## F-07 — P2

- **File:** `src/stage3/ladder.py ; src/stage3/stats.py`
- **Function:** wide ; mean_test
- **Line:** 107-143 ; 28-38
- **Description:** The matrix builder does not validate the values it is given. Duplicate (date, entity) rows: the last one wins. A return of -100 % becomes -inf, below -100 % becomes NaN, +inf stays inf. A research-grade row with a missing return becomes 0. An unknown class value is treated as 'no information' (return 0, not flagged). mean_test returns NaN for NaN input without raising, and the section 27 decision then reads INCONCLUSIVE.
- **Why it matters:** This is the UNTRUSTED -> TRUSTED boundary for the numbers the ladder uses. Today it is safe only because the input file is hash-pinned and happens to be clean.
- **Reproduction:** Audit attack script, section 'ladder numerical / structural inputs' (all seven cases accepted silently).
- **Expected behaviour:** Fail loudly on duplicates, non-finite or <= -1 returns, a missing return on a research-grade row, an unknown class, and NaN in a test series.
- **Actual behaviour:** Accepted silently. The registered panel has none of these (checked: 2,115,961 rows).
- **Proposed fix:** Report only. A validation function could live outside the frozen files (called by the verifier of F-05); a guard inside wide()/mean_test belongs to the next protocol version.
- **Test that will prevent regression:** Property tests: each malformed input raises.
- **Evidence:** PROVEN (attack script); registered data verified clean by the audit
- **Needs a frozen-code change:** yes — report only

## F-08 — P2

- **File:** `scripts/run_s2_mom.py`
- **Function:** _write ; main
- **Line:** 46-52, 96-107
- **Description:** Output writing is neither atomic nor exclusive. _write checks exists() and then calls write_text (race between two processes; a kill mid-write leaves a partial JSON that then counts as 'already exists'). The five CSV files are written with plain to_csv after the JSON. The trial log and the registry amendment come last. The run-once check happens after the whole analysis has been computed.
- **Why it matters:** A crash between the first write and registration leaves a complete, readable primary or confirmation result that is unregistered and absent from the trial log. The natural recovery (delete and rerun) is an unrecorded second look.
- **Reproduction:** Read lines 96-107: _write(json) -> to_csv x5 -> log_trial -> _amend.
- **Expected behaviour:** Check run-once before computing; write everything into a temporary directory, fsync, rename once; log the trial start before computing and the completion after.
- **Actual behaviour:** Check-then-write; fail-late; no start record.
- **Proposed fix:** Report only (frozen file). Until then: operational rule in the runbook - never delete a result file; record any crashed run in the deviation log and the trial log by hand.
- **Test that will prevent regression:** Kill-during-write test on a temporary directory: no final file, rerun allowed only after an explicit recorded reset.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** yes — report only

## F-09 — P2

- **File:** `scripts/run_s2_mom.py ; scripts/run_s2_mom_step_e.py ; scripts/run_s2_mom_c2.py`
- **Function:** code_sha
- **Line:** 34-39 ; 40, 57-58 ; 50, 64-65
- **Description:** The code hashes do not cover everything the runs execute. Main: not src/intraday/inference.py (bootstrap), src/stage2/returns.py (JUMP), src/access.py, src/config.py, src/registry/experiments.py. Step E: only step_e.py and its runner - not stats.py (the Newey-West test) and protocol.py (alpha, lags, slippage table), which it imports. C2: only the script - not stats.py. Library versions are in no hash.
- **Why it matters:** 'Same code hash' is weaker than it reads: a change in an imported module would not invalidate a protected run.
- **Reproduction:** Compare each CODE tuple with the import graph.
- **Expected behaviour:** The hash covers the transitive first-party imports of the runner.
- **Actual behaviour:** Partial lists. Mitigation today: inference.py is pinned by the ORB frozen-hash test; stats.py and protocol.py are in the main hash, which still equals the registered value.
- **Proposed fix:** Report only (frozen files). Add a test, outside the frozen files, that pins the SHA-256 of every first-party module imported by each runner.
- **Test that will prevent regression:** Test: import-graph of each runner is a subset of the pinned file list.
- **Evidence:** VERIFIED BY INSPECTION; SUPPORTED BY HASH for today's state
- **Needs a frozen-code change:** yes — report only

## F-10 — P2

- **File:** `src/stage3/data.py ; src/stage3/protocol.py ; src/access.py ; evaluate_orb_v1.py`
- **Function:** build ; module level ; run
- **Line:** 112-121 ; 48 ; 33 ; 4 asserts
- **Description:** Safeguards are written as assert statements: the seven structural checks of the Stage 3 build (last session = T*, 170 months, 114/56 split, step A/B/C universe sizes and identities), the cutoff consistency checks, and the ORB evaluator's session-window check. python -O or PYTHONOPTIMIZE removes them.
- **Why it matters:** A safeguard that an environment variable can switch off without a message is not fail-closed.
- **Reproduction:** python3 -O -c "print(__debug__)" -> False; the checks are 'assert' lines.
- **Expected behaviour:** Checks raise an explicit exception in every interpreter mode.
- **Actual behaviour:** Skipped under -O.
- **Proposed fix:** Report only for the frozen files. Low-cost mitigation outside them: the verifier (F-05) repeats the structural checks with explicit raises; the runbook forbids -O.
- **Test that will prevent regression:** Run the verifier under python -O in a test.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** yes — report only

## F-11 — P2

- **File:** `src/registry/experiments.py`
- **Function:** log_trial
- **Line:** 112-121
- **Description:** The environment variable TRADING_LAB_NO_TRIAL_LOG (meant for tests) silently disables trial logging for any real run started from a shell where it is set. The runners do not check the return value.
- **Why it matters:** The trial count is the basis of the multiple-testing statements. A silent zero is worse than an error.
- **Reproduction:** TRADING_LAB_NO_TRIAL_LOG=1 python3 -c "from src.registry import experiments as E; print(E.log_trial('k',{},'d',{},'s'))" -> None
- **Expected behaviour:** A real run cannot proceed without a trial record; only the test harness can suppress it.
- **Actual behaviour:** Returns None; run continues and registers.
- **Proposed fix:** In experiments.py: suppress only when pytest is running (PYTEST_CURRENT_TEST present) or via an explicit function argument; otherwise raise if the variable is set.
- **Test that will prevent regression:** Test: with the variable set and no pytest marker, log_trial raises.
- **Evidence:** PROVEN (attack script)
- **Needs a frozen-code change:** no

## F-12 — P2

- **File:** `scripts/run_s2_mom.py`
- **Function:** _passed ; main
- **Line:** 59-62, 78-79
- **Description:** Two gates rest on hand-editable evidence. The pre-run check gate reads a local JSON file (all_passed, code_sha256) that carries no registered hash; 'checks' mode may be rerun at will. The Stage 2 gate tests only that the registry field stage2_rebuild.checks_passed equals 150; that field was written by a manual amendment, not by build_stage2.py.
- **Why it matters:** The gates prove that a file or a number exists, not that the check ran.
- **Reproduction:** Read lines 59-62 and 78-79; registry line 40 (amendment of 2026-10-05T20:51:33).
- **Expected behaviour:** The script that performs the check writes the evidence and its hash to the registry itself.
- **Actual behaviour:** Manual registration; unanchored check files. The manuscript builder also reads these two files.
- **Proposed fix:** Report only for the runner (frozen). Now: record the SHA-256 of the two pre_run_checks files in a registry amendment; add them to the verifier.
- **Test that will prevent regression:** Test: check files equal their registered hashes.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** yes — report only

## F-13 — P2

- **File:** `src/stage3/experiment.py`
- **Function:** _perturbed ; pre_run_checks
- **Line:** 77-89, 119-126
- **Description:** The real-data perturbation check scrambles returns and research-grade flags after t. Protocol B2 check 1 requires every price, flag, liquidity value and membership row after t to be changed. Liquidity and membership perturbation exists only in synthetic unit tests and in the UNIV-1 builder's own tests.
- **Why it matters:** The check that gated the registered runs is narrower than the frozen text says.
- **Reproduction:** Read _perturbed: only ln, lr, lraw, ok, bad are modified.
- **Expected behaviour:** The pre-run check perturbs universe rows too, or the protocol wording is matched by a recorded ruling.
- **Actual behaviour:** Returns and flags only.
- **Proposed fix:** Report only (frozen file). Record as a deviation or a reviewer ruling; cover the missing part in the verifier.
- **Test that will prevent regression:** Verifier test: scramble UNIV-1 rows dated after t; memberships up to t unchanged.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** yes — report only

## F-14 — P2

- **File:** `server.py`
- **Function:** add_symbol
- **Line:** 83-102
- **Description:** GET /api/add downloads a Yahoo history and overwrites data/india/<symbol>d1.csv in place, non-atomically, with no confirmation. The symbol is used in the file name after removing only '.NS', '.BO', '^', '&' (path separators and '..' are not rejected). State-changing GET; no authentication. fetch_data.py overwrites data files the same way.
- **Why it matters:** Research data files that registered legacy experiments identify by SHA-256 can be replaced from a browser tab. README note 1 documents that this already happened once (a figure became irreproducible after a refresh).
- **Reproduction:** Read lines 83-102.
- **Expected behaviour:** POST only; strict symbol pattern; refuse to overwrite an existing file (write a new dated file instead); atomic write.
- **Actual behaviour:** Overwrites silently.
- **Proposed fix:** Fix in server.py (not frozen): validate with a regular expression, use POST, refuse existing targets.
- **Test that will prevent regression:** Tests: '../x', 'a/b' rejected with 400; an existing file is not overwritten.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** no

## F-15 — P2

- **File:** `scripts/collect_intraday.sh ; update_intraday.py`
- **Function:** -
- **Line:** -
- **Description:** The launchd collector appends to 58 git-tracked data files in the research working tree every weekday, so the tree is permanently dirty and the registry's git_dirty flag is always true. The last run (2026-10-06 19:03) exited 1: BELm15.csv and CIPLAm15.csv were rejected because one overlapping bar disagreed by more than 0.2 %.
- **Why it matters:** git_dirty cannot distinguish 'collector ran' from 'code was edited'. Rejected holdout bars are lost for good if not recovered inside Yahoo's 60-day window (ORB v1 holdout completeness).
- **Reproduction:** tail logs/collector.log ; data/raw/collection_log.jsonl run 20261006T190331
- **Expected behaviour:** Collector output is separated from the code tree or committed by its own job; rejections raise an alert.
- **Actual behaviour:** Dirty tree; exit code 1 visible only in a log file.
- **Proposed fix:** Operational: review the two rejections; commit collector data separately; make environment() report code dirtiness and data dirtiness separately.
- **Test that will prevent regression:** holdout_status already reports health; add the last collector exit code to it.
- **Evidence:** VERIFIED BY INSPECTION (logs)
- **Needs a frozen-code change:** no

## F-16 — P2

- **File:** `src/stage2/archive.py`
- **Function:** fetch
- **Line:** 60-93
- **Description:** Any HTTP 200 response body is stored as a permanent raw file and recorded with its hash. There is no check that the body is a zip (bhavcopy) or JSON (corporate actions), no size check, no fsync. Raw files are never overwritten, so a truncated or HTML error body stays until someone edits the archive and the manifest by hand.
- **Why it matters:** A partial download poisons the append-only archive. It is detected later (the parser raises on a bad zip), so it is loud, but recovery is manual surgery on an 'append-only' record.
- **Reproduction:** Read lines 76-91.
- **Expected behaviour:** Validate the payload before recording status 200; otherwise treat as a transient failure.
- **Actual behaviour:** Recorded as a successful download.
- **Proposed fix:** Changing archive.py changes a hash embedded in the Stage 2 manifests (code_sha256), so treat as frozen: report only. Mitigation: the Stage 2 rebuild opens every file.
- **Test that will prevent regression:** Test with a fake opener returning HTML: nothing recorded.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** yes — report only

## F-17 — P2

- **File:** `src/stage3/step_e.py`
- **Function:** net_returns
- **Line:** 280-284
- **Description:** A portfolio-month with no ledger row gets cost 0 through fillna(0.0), and the guard only requires costed months to be a subset of gross months. The module's own header says no cost is ever set to zero.
- **Why it matters:** If holdings for one portfolio-month were missing or dropped, its net return would silently equal its gross return.
- **Reproduction:** Read lines 280-284.
- **Expected behaviour:** Raise when a (portfolio, month) has no cost row.
- **Actual behaviour:** Filled with 0. Not triggered: every one of the 170 months has a positive cost for W, L and the benchmark (verified).
- **Proposed fix:** Report only (frozen file). The verifier asserts 'every month has a positive cost'.
- **Test that will prevent regression:** Test: remove one month from the ledger -> error.
- **Evidence:** VERIFIED BY INSPECTION; non-occurrence PROVEN by the audit script
- **Needs a frozen-code change:** yes — report only

## F-18 — P2

- **File:** `evaluate_orb_v1.py`
- **Function:** run
- **Line:** 86-299
- **Description:** The single-use ORB v1 holdout evaluator has 26 % line coverage; its body is exercised only by two manual dry runs on development data (identical results). Outputs are written file by file and registered afterwards; a crash in between consumes the single use without a registry record (fail closed, but unrecoverable without a manual decision).
- **Why it matters:** It can run only once on the real holdout. A defect found on the day cannot be fixed without breaking the frozen hashes.
- **Reproduction:** coverage report; read lines 244-292.
- **Expected behaviour:** An end-to-end test of the evaluator on synthetic sessions, including the refusal and crash paths.
- **Actual behaviour:** Not tested end to end by the suite.
- **Proposed fix:** Add tests only (no change to the frozen evaluator or its frozen modules).
- **Test that will prevent regression:** Synthetic end-to-end test in a temporary repository.
- **Evidence:** PROVEN BY TEST (coverage measurement)
- **Needs a frozen-code change:** no

## F-19 — P3

- **File:** `src/stage3/ladder.py`
- **Function:** _hold ; run_ladder
- **Line:** 203-207, 254
- **Description:** The 'gap return already booked' set is kept per portfolio. A gap return booked by W in month m could be earned again by L in month m+1 if the stock moved between them. Occurrences in the registered runs: 0 (checked for every step, both samples).
- **Why it matters:** Possible double counting across portfolios of the same step.
- **Reproduction:** Audit script counter 'cross-portfolio re-count': 0.
- **Expected behaviour:** A booked row is consumed for every portfolio of the step, or the rule is documented.
- **Actual behaviour:** Per portfolio.
- **Proposed fix:** Report only (frozen). Note for the next protocol version.
- **Test that will prevent regression:** Synthetic test of a stock moving W -> L across a suspension.
- **Evidence:** PROVEN non-occurrence (audit script)
- **Needs a frozen-code change:** yes — report only

## F-20 — P3

- **File:** `src/stage3/ladder.py ; src/stage2/returns.py ; src/stage2/identity.py ; src/stage2/universe.py ; scripts/`
- **Function:** -
- **Line:** -
- **Description:** Duplicated rules and constants: the 'unadjustable event' pattern exists in returns.py and again in ladder.py; three union-find implementations with two entity-id conventions; Holm in inference.py and in the C2 runner; one-sided Newey-West test in step_e.py and the C2 runner; the same SHA-256 constants are typed into protocol.py, both later runners, build_stage2.py, the manuscript builder, several tests and the documents; two cost models (costs.py and step_e.py).
- **Why it matters:** A rule changed in one place only gives inconsistent results that no hash detects.
- **Reproduction:** grep.
- **Expected behaviour:** One authoritative implementation or constant, imported everywhere.
- **Actual behaviour:** Copies.
- **Proposed fix:** Tests that assert the copies are equal (pattern strings, hash constants versus registry). No frozen file needs to change.
- **Test that will prevent regression:** Equality tests.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** no

## F-21 — P3

- **File:** `src/stage3/experiment.py`
- **Function:** _describe
- **Line:** 162-170
- **Description:** Protocol section 14 defines the Sharpe-type ratio of long-only portfolios as the information ratio against the step's benchmark. The code reports mean/sd for every portfolio. The metric is not in the DEV-2 list of unexecuted analyses.
- **Why it matters:** A pre-registered reporting item is missing without a deviation entry.
- **Reproduction:** Read _describe.
- **Expected behaviour:** Information ratio reported, or a deviation recorded.
- **Actual behaviour:** mean_over_sd only (honestly named).
- **Proposed fix:** Add to the deviation log (researcher's decision).
- **Test that will prevent regression:** -
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** yes — report only

## F-22 — P3

- **File:** `src/stage3/experiment.py`
- **Function:** analyse
- **Line:** 271-273
- **Description:** Decision order: a significant estimate whose 90 % interval lies wholly inside +/-0.10 is labelled DETECTED_SIZE_UNCERTAIN; the protocol table can also be read as 'immaterial'. The rule is also evaluated for the confirmation sample (already disclosed in the registry). The flipped-threshold mutation survives the suite.
- **Why it matters:** Label ambiguity; untested labelling code.
- **Reproduction:** Read lines 271-273.
- **Expected behaviour:** A reviewer ruling and a table-driven test of all four labels.
- **Actual behaviour:** Not triggered: the primary result is INCONCLUSIVE.
- **Proposed fix:** Add tests of the four labels (no source change); record the ruling.
- **Test that will prevent regression:** Four-label test.
- **Evidence:** VERIFIED BY INSPECTION; mutation survivor
- **Needs a frozen-code change:** yes — report only

## F-23 — P3

- **File:** `src/stage3/protocol.py ; src/stage3/experiment.py`
- **Function:** NW_LAG
- **Line:** 36
- **Description:** The Newey-West lag is looked up by sample name, not computed from the number of months actually tested. If months were unpaired the lag would not follow the frozen formula. Both registered samples are fully paired (114, 56), where the constants equal the formula.
- **Why it matters:** Silent drift from the formula in an edge case.
- **Reproduction:** -
- **Expected behaviour:** Lag computed from n, or a guard that n equals the nominal sample size.
- **Actual behaviour:** Constant.
- **Proposed fix:** Report only (frozen).
- **Test that will prevent regression:** Assert n == nominal in the verifier.
- **Evidence:** VERIFIED BY INSPECTION; PROVEN equal for registered runs
- **Needs a frozen-code change:** yes — report only

## F-24 — P3

- **File:** `src/stage2/panel.py`
- **Function:** parse
- **Line:** 58-63
- **Description:** Numeric fields are coerced (malformed -> NaN) and rows whose date cannot be parsed are dropped from the date comparison, then stamped with the file's session date. Both are counted in QA only as missing prices.
- **Why it matters:** Malformed rows are accepted rather than classified with a reason.
- **Reproduction:** Read lines 58-63.
- **Expected behaviour:** An explicit 'unparseable rows' count per file.
- **Actual behaviour:** Coerced.
- **Proposed fix:** Report only (Stage 2 code hash is embedded in manifests).
- **Test that will prevent regression:** -
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** yes — report only

## F-25 — P3

- **File:** `src/stage3/data.py`
- **Function:** identity
- **Line:** 90
- **Description:** Delisting class is decided by a case-sensitive substring test for 'Voluntary' in free text copied from the NSE file. Current values are exactly 'Voluntary Delisting', 'Compulsory Delisting', 'Delisting - Liquidation' (checked).
- **Why it matters:** A differently spelled source value would silently fall into the -30 % class.
- **Reproduction:** -
- **Expected behaviour:** Exact match against an explicit list; unknown text raises.
- **Actual behaviour:** Substring.
- **Proposed fix:** Report only (frozen).
- **Test that will prevent regression:** Verifier asserts the set of observed types.
- **Evidence:** VERIFIED BY INSPECTION; values PROVEN on registered data
- **Needs a frozen-code change:** yes — report only

## F-26 — P3

- **File:** `src/registry/experiments.py`
- **Function:** environment ; record ; amend
- **Line:** 38-53, 75, 91
- **Description:** environment() swallows every exception from git and reports 'unknown'; timestamps are naive local time; git_dirty looks only at 'src' and '*.py'.
- **Why it matters:** Weak forensic metadata.
- **Reproduction:** -
- **Expected behaviour:** Explicit error or explicit 'git unavailable'; timezone-aware timestamps.
- **Actual behaviour:** As described.
- **Proposed fix:** Small change in experiments.py together with F-03/F-06.
- **Test that will prevent regression:** -
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** no

## F-27 — P3

- **File:** `src/stage3/experiment.py`
- **Function:** pre_run_checks (placebo)
- **Line:** 128-136
- **Description:** The placebo gate requires p > 0.05 for one fixed seed, so it fails for about 5 % of seeds by construction. Confirmation-sample value: p = 0.054.
- **Why it matters:** A gate with a built-in false-failure rate invites a seed change when it fails.
- **Reproduction:** data/stage3/s2_mom_v1/checks/pre_run_checks_oos.json
- **Expected behaviour:** A rule for what happens on failure, fixed in advance.
- **Actual behaviour:** Passed with the registered seed.
- **Proposed fix:** Disclosure only.
- **Test that will prevent regression:** -
- **Evidence:** SUPPORTED BY the saved check file
- **Needs a frozen-code change:** yes — report only

## F-28 — P3

- **File:** `README.md ; REPRODUCIBILITY.md ; METHODOLOGY.md ; CHANGELOG.md`
- **Function:** -
- **Line:** -
- **Description:** None of the four top-level documents mentions Stage 3 or S2-MOM-v1. REPRODUCIBILITY.md's procedure ('check out environment.git_commit') cannot work for S2-MOM-v1 (see F-01).
- **Why it matters:** A reader of the repository's front page cannot find or reproduce the main study.
- **Reproduction:** grep -n 'S2-MOM\|stage3' README.md REPRODUCIBILITY.md METHODOLOGY.md CHANGELOG.md -> no match.
- **Expected behaviour:** Documented procedure.
- **Actual behaviour:** Absent.
- **Proposed fix:** Write the section after F-01, F-05 and F-06 are done.
- **Test that will prevent regression:** -
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** no

## F-29 — P2

- **File:** `scripts/run_s2_mom.py ; src/stage3/data.py ; scripts/build_stage2.py`
- **Function:** sensitivity identity check ; build ; write_or_verify
- **Line:** 116-118 ; 148-151 ; 265-274
- **Description:** Reproduction is defined as byte identity of CSV and parquet files. That holds on this machine and library set; another numpy/pandas/pyarrow version or CPU can change the last digit or the parquet encoding, and the rebuild is then refused although the numbers agree.
- **Why it matters:** Fail-closed is right for protection, but it makes cross-machine verification fail for reasons unrelated to the science.
- **Reproduction:** -
- **Expected behaviour:** A second, tolerance-based comparison for verification purposes.
- **Actual behaviour:** Byte identity only.
- **Proposed fix:** Provide the tolerance-based verifier of F-05; keep byte identity for the protected runs.
- **Test that will prevent regression:** Golden test at 1e-9.
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** no

## F-30 — P2

- **File:** `src/stage3/data.py ; src/stage3/experiment.py`
- **Function:** load_inputs ; analyse ; run
- **Line:** 188-213 ; 39-41, 260-290
- **Description:** Any Python session can import the Stage 3 modules and compute any sample's results directly. load_inputs calls only verify_protocol(); there is no decision gate, no primary-before-confirmation order, no run-once guard and no trial log on this path.
- **Why it matters:** The protection of the confirmation sample 'comes from the execution order and the code hash' (protocol B3); the execution order is enforced only inside one script.
- **Reproduction:** By inspection of the function signatures; a notebook (Untitled.ipynb) lives in the repository root.
- **Expected behaviour:** The data loader refuses unless called through the registered runner, or logs a trial itself.
- **Actual behaviour:** Open.
- **Proposed fix:** Report only (frozen). Runbook rule; the verifier (F-05) is the one sanctioned read path and logs its own use.
- **Test that will prevent regression:** -
- **Evidence:** VERIFIED BY INSPECTION
- **Needs a frozen-code change:** yes — report only
