# Failure-injection report — Phase 7 (2026-10-07)

Every attack below was made on a **scratch copy** or on **synthetic frames**. The real repository was not touched.
Suite: `tests/test_failure_injection.py`. Table source: `docs/audit/remediation/failure_injection_results.json`, written by `python3 tests/test_failure_injection.py OUT.json` on the final code.

## 1. Method

Two layers are attacked separately, so that one cannot hide behind the other.

1. **File layer.** A scratch copy of the registered artifacts (registry, protocol, Stage 3 inputs, results, code, environment files) is made. One thing is broken. The verification steps of `scripts/reproduce_s2_mom_v1.py` are run on the copy. The attack counts as rejected only if the verdict is FAIL **and** the message names the expected reason.
2. **Value layer.** An attacker who could make every hash valid would still have to pass the value checks. A complete, valid set of synthetic Stage 3 frames is built (170 months, 510 universes of 200 stocks). One defect is inserted. `integrity.validate_stage3` must raise with the expected message.

A third group checks the validators of the registered monthly and step E files, the numerical comparison of the reproduction, and interrupted writes (these are pytest cases, not rows of the JSON table).

Outcome classes, as the brief requires: **A = rejected**; **B = allowed operation that cannot change a result** (shown, not assumed).

## 2. Result

| Layer | Attacks | Rejected (A) | Allowed (B) | Silently accepted |
|---|---|---|---|---|
| Files (scratch copy, whole verification) | 46 | 46 | 0 | 0 |
| Values (hash-valid synthetic inputs) | 43 | 43 | 0 | 0 |
| Registered monthly file validator | 10 | 10 | 0 | 0 |
| Step E file validator | 6 | 6 | 0 | 0 |
| Numerical comparison (NaN, inf, shape, tolerance, label) | 5 | 5 | 0 | 0 |
| Interrupted writes (archive pack, registry summary) | 2 | 2 | 0 | 0 |
| Reordered panel rows | 1 | 0 | 1 | 0 |
| **Total** | **113** | **112** | **1** | **0** |

Rows of the table rejected for the expected reason: 89 of 89.

## 3. The attacks required by the brief

| Required attack | Where it is covered | Outcome |
|---|---|---|
| corrupt one input | files: 2 variants | rejected |
| corrupt one manifest entry | files | rejected |
| rewrite the manifest | files | rejected |
| delete one input | files (also: delete the manifest, delete a registered output) | rejected |
| duplicate one input | files; duplicate manifest key in `tests/test_provenance_chain.py` | rejected |
| add an unexpected file | files: inputs folder and results folder | rejected |
| modify one result | files | rejected |
| modify protocol hash | files: protocol file, a supplement, and a forged registry amendment | rejected |
| modify code hash | files: ladder, C2 runner, and a forged registry amendment | rejected |
| modify registry state | files: forged FINAL → PLANNED with a valid chain; in-place rewrite of history | rejected |
| duplicate registry record | files: record and amendment | rejected |
| alter confirmation status | files: confirmation result file, C2 file, forged registry headline | rejected |
| alter environment metadata | files: specification file, registry record, manifest build block | rejected |
| insert NaN | files (result file); values (naive return, research return, rank); monthly validator; comparison | rejected |
| insert +inf | files (step E file); values; monthly validator; comparison | rejected |
| insert -inf | files (input); values; monthly validator | rejected |
| duplicate monthly row | files (delta file); values (calendar); monthly validator; step E validator | rejected |
| reorder rows | files (calendar: rejected by hash); values (calendar order: rejected); panel rows: **class B**, section 5 | rejected / B |
| alter a date | files; values (exit before entry, holiday, unparseable, missing) | rejected |
| alter entity id | files; values (panel, universe) | rejected |
| alter return value | files (registered delta); the independent recomputation compares all 680 step-months | rejected |
| alter cost | files (schedule; step E output); cost-function agreement test | rejected |
| remove a required column | files; values (panel, calendar); monthly validator; step E validator | rejected |
| change column type | files; values (returns, date, rank as text); monthly validator | rejected |
| truncate an output | files (results JSON, holdings CSV) | rejected |
| interrupt a write if safely testable | files (half-written registry line); interrupted archive pack and registry summary leave no final file | rejected |

## 4. Full table

### 4.1 File layer

| # | Attack | What was done | Outcome | Message (first 150 characters) |
|---|---|---|---|---|
| 1 | corrupt one input | flip one character of primary/calendar.csv | REJECTED | ProvenanceError: data/stage3/s2_mom_v1/primary/calendar.csv does not match its recorded SHA-256 |
| 2 | corrupt one input (append a byte) | append a newline to research/identity.csv | REJECTED | ProvenanceError: data/stage3/s2_mom_v1/research/identity.csv does not match its recorded SHA-256 |
| 3 | corrupt one manifest entry | change one hash inside the manifest | REJECTED | ProvenanceError: Stage 3 manifest does not match the SHA-256 anchored in the registry |
| 4 | rewrite the manifest | edit an input and make the manifest agree with it | REJECTED | ProvenanceError: Stage 3 manifest does not match the SHA-256 anchored in the registry |
| 5 | delete one input | delete research/gap_rows.csv | REJECTED | ProvenanceError: missing input (or a symlink): data/stage3/s2_mom_v1/research/gap_rows.csv |
| 6 | delete the manifest | delete manifest.json | REJECTED | ProvenanceError: Stage 3 manifest is missing |
| 7 | duplicate one input | copy oos/calendar.csv to a second file | REJECTED | ProvenanceError: unexpected file(s) in the Stage 3 input folder: ['oos/calendar (1).csv'] |
| 8 | add an unexpected file (inputs) | drop a new csv into the input folder | REJECTED | ProvenanceError: unexpected file(s) in the Stage 3 input folder: ['research/extra.csv'] |
| 9 | add an unexpected file (results) | drop a second results file beside the registered ones | REJECTED | Fail: unregistered file(s) in results/s2_mom_v1: ['primary_results_v2.json'] |
| 10 | modify one result | change one digit of primary_monthly.csv | REJECTED | Fail: results/s2_mom_v1/primary_monthly.csv does not match its registered SHA-256 |
| 11 | modify the protocol | edit one character of the frozen protocol | REJECTED | Fail: docs/research/phase3a_momentum_protocol.md does not have its pinned SHA-256 |
| 12 | modify a supplement | edit Supplement 2 | REJECTED | Fail: docs/research/phase3a_momentum_protocol_addendum1_supplement2.md does not match the registry |
| 13 | modify protocol hash (registry) | append an amendment that replaces protocol_sha256 | REJECTED | RegistryError: S2-MOM-v1 is FINAL: protected field 'protocol_sha256' is immutable (only status and new anchors may be appended) / Fail: the environmen |
| 14 | modify code hash (ladder) | add a comment to src/stage3/ladder.py | REJECTED | Fail: the code behind primary_run differs from its registered code hash |
| 15 | modify code hash (C2 runner) | add a comment to scripts/run_s2_mom_c2.py | REJECTED | Fail: the code behind c2_run differs from its registered code hash |
| 16 | modify code hash (registry) | append an amendment that replaces the registered code hash | REJECTED | RegistryError: S2-MOM-v1 is FINAL: protected field 'provenance' is immutable (only status and new anchors may be appended) / Fail: the environment spe |
| 17 | modify registry state | append FINAL -> PLANNED with a valid hash chain | REJECTED | RegistryError: illegal transition FINAL -> PLANNED for S2-MOM-v1 (allowed: ['INVALID', 'REQUIRES REVALIDATION', 'SUPERSEDED']) / Fail: the environment |
| 18 | modify registry state (in place) | rewrite the historical PLANNED -> FINAL line | REJECTED | RegistryError: the first 58 registry lines (registered history) are missing or were rewritten / Fail: the environment specification is not anchored in |
| 19 | duplicate registry record | append a copy of the S2-MOM-v1 record | REJECTED | RegistryError: registry line 62 duplicates an earlier record / Fail: the environment specification is not anchored in the registry |
| 20 | duplicate registry amendment | append a copy of the last amendment | REJECTED | RegistryError: registry line 62 duplicates an earlier record / Fail: the environment specification is not anchored in the registry |
| 21 | delete a registry amendment | remove the last line (the newest anchor) | REJECTED | Fail: release/s2_mom_v1/ENVIRONMENT.json: environment specification does not match the registry anchor |
| 22 | delete all remediation amendments | remove every line after the pinned history (all anchors) | REJECTED | Fail: the environment specification is not anchored in the registry / Fail: the cost schedule is not anchored in the registry with its pinned SHA-256  |
| 23 | alter confirmation status (result file) | change the saved confirmation label | REJECTED | Fail: results/s2_mom_v1/confirmation_results.json does not match its registered SHA-256 |
| 24 | alter confirmation status (C2 file) | change H2d NOT CONFIRMED/CONFIRMED text | REJECTED | Fail: results/s2_mom_v1_c2/c2_results.json does not match its registered SHA-256 |
| 25 | alter confirmation status (registry) | append an amendment that rewrites the results headline | REJECTED | RegistryError: S2-MOM-v1 is FINAL: protected field 'results' is immutable (only status and new anchors may be appended) / Fail: the environment specif |
| 26 | alter environment metadata (specification) | change a pinned version in ENVIRONMENT.json | REJECTED | Fail: release/s2_mom_v1/ENVIRONMENT.json: environment specification does not match the registry anchor |
| 27 | alter environment metadata (registry) | append an amendment that replaces the recorded environment | REJECTED | RegistryError: S2-MOM-v1 is FINAL: protected field 'environment' is immutable (only status and new anchors may be appended) / Fail: the environment sp |
| 28 | alter environment metadata (manifest build block) | edit the environment recorded in the Stage 3 manifest | REJECTED | ProvenanceError: Stage 3 manifest does not match the SHA-256 anchored in the registry |
| 29 | insert NaN (result file) | write NaN into a monthly return | REJECTED | Fail: results/s2_mom_v1/confirmation_monthly.csv does not match its registered SHA-256 |
| 30 | insert +inf (step E file) | write inf into a cost | REJECTED | Fail: results/s2_mom_v1_step_e/primary_step_e_monthly.csv does not match its registered SHA-256 |
| 31 | insert -inf (input) | write -inf into a universe rank | REJECTED | ProvenanceError: data/stage3/s2_mom_v1/primary/universes.csv does not match its recorded SHA-256 |
| 32 | duplicate monthly row | repeat one row of primary_delta.csv | REJECTED | Fail: results/s2_mom_v1/primary_delta.csv does not match its registered SHA-256 |
| 33 | reorder rows | swap two rows of oos/calendar.csv | REJECTED | ProvenanceError: data/stage3/s2_mom_v1/oos/calendar.csv does not match its recorded SHA-256 |
| 34 | alter a date | move one exit session by a day | REJECTED | ProvenanceError: data/stage3/s2_mom_v1/primary/calendar.csv does not match its recorded SHA-256 |
| 35 | alter entity id | rename one stock in a universe | REJECTED | ProvenanceError: data/stage3/s2_mom_v1/oos/universes.csv does not match its recorded SHA-256 |
| 36 | alter return value | change one digit of a registered monthly delta | REJECTED | Fail: results/s2_mom_v1/confirmation_delta.csv does not match its registered SHA-256 |
| 37 | alter cost (schedule) | change one STT rate in the approved schedule | REJECTED | Fail: config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json does not have its pinned SHA-256 |
| 38 | alter cost (step E output) | change one registered cost | REJECTED | Fail: results/s2_mom_v1_step_e/confirmation_step_e_monthly.csv does not match its registered SHA-256 |
| 39 | remove a required column | drop the last column of research/identity.csv | REJECTED | ProvenanceError: data/stage3/s2_mom_v1/research/identity.csv does not match its recorded SHA-256 |
| 40 | change column type | quote every rank as text | REJECTED | ProvenanceError: data/stage3/s2_mom_v1/oos/universes.csv does not match its recorded SHA-256 |
| 41 | truncate an output | cut primary_results.json in half | REJECTED | Fail: results/s2_mom_v1/primary_results.json does not match its registered SHA-256 |
| 42 | truncate an output (holdings) | drop the last 1000 bytes of the holdings file | REJECTED | Fail: results/s2_mom_v1/confirmation_holdings.csv does not match its registered SHA-256 |
| 43 | interrupted registry write | leave a half-written last line | REJECTED | RegistryError: registry ends in a truncated line (interrupted write?) - refusing to read it / Fail: the environment specification is not anchored in t |
| 44 | unregistered rerun | log a second primary run in the trial log | REJECTED | Fail: trial log: expected exactly one run of each of ['primary', 'sensitivity', 'confirmation', 'step_e', 'c2'], found ['primary', 'sensitivity', 'con |
| 45 | delete a registered output | delete sensitivity_results.json | REJECTED | FileNotFoundError: [Errno 2] No such file or directory: '/var/folders/0b/stgbdkfs7ss1p8c_108yzf440000gn/T/tmphnj97jzy/a44/results/s2_mom_v1/sensitivit |
| 46 | symlink an input | replace sessions.csv by a link to identical bytes elsewhere | REJECTED | ProvenanceError: missing input (or a symlink): data/stage3/s2_mom_v1/research/sessions.csv |

### 4.2 Value layer

| # | Defect inserted into otherwise valid inputs | Outcome | Message |
|---|---|---|---|
| 1 | insert NaN (naive return) | REJECTED | panel: missing naive return on a row that is not a first observation |
| 2 | insert NaN (research return of an OK row) | REJECTED | panel: research-grade row without a research return |
| 3 | insert +inf | REJECTED | panel.r_naive: infinite value |
| 4 | insert -inf | REJECTED | panel.r_raw: infinite value |
| 5 | return of -100% | REJECTED | panel.r_naive: return of -100% or less |
| 6 | return below -100% | REJECTED | panel.r_rg: return of -100% or less |
| 7 | unknown row class | REJECTED | panel: unknown class ['WEIRD'] |
| 8 | research return on a flagged row | REJECTED | panel: research return on a row that is not research-grade |
| 9 | duplicate panel row | REJECTED | panel: duplicate (date, entity) row |
| 10 | panel row on a non-session date | REJECTED | panel: row on a date that is not a market session |
| 11 | panel row after the cutoff | REJECTED | panel: row on a date that is not a market session |
| 12 | alter entity id (panel) | REJECTED | panel: entity that is not in the identity table |
| 13 | second FIRST row | REJECTED | panel: a FIRST row is not the entity's first row |
| 14 | change column type (returns as text) | REJECTED | panel.r_naive: not a float column (object) |
| 15 | change column type (date as text) | REJECTED | panel.date: not a date column (object) |
| 16 | remove a required column (panel) | REJECTED | panel: columns ['date', 'entity', 'r_naive', 'r_rg', 'cls', 'raw_ok'] != ['date', 'entity', 'r_naive', 'r_rg', 'r_raw', 'cls', 'raw_ok'] |
| 17 | extra column (panel) | REJECTED | panel: columns ['date', 'entity', 'r_naive', 'r_rg', 'r_raw', 'cls', 'raw_ok', 'note'] != ['date', 'entity', 'r_naive', 'r_rg', 'r_raw', 'cls', 'raw_o |
| 18 | remove a required column (calendar) | REJECTED | primary/calendar: columns ['t', 'm12', 'm1', 's_plus', 'holding_month', 'sample'] != ['t', 'm12', 'm1', 's_plus', 's_pp', 'holding_month', 'sample'] |
| 19 | duplicate session | REJECTED | sessions: duplicate or unsorted dates |
| 20 | last session is not T* | REJECTED | sessions: last session 2026-09-29 is not T* 2026-09-30 |
| 21 | reorder calendar rows | REJECTED | oos/calendar: duplicate or unsorted month |
| 22 | duplicate monthly calendar row | REJECTED | primary/calendar: 115 months, protocol B3 says 114 |
| 23 | 113 primary months | REJECTED | primary/calendar: 113 months, protocol B3 says 114 |
| 24 | alter a date (exit before entry) | REJECTED | primary/calendar: m12 < m1 < t < s_plus < s_pp violated |
| 25 | alter a date (holiday) | REJECTED | primary/calendar: a date that is not a market session |
| 26 | alter a date (unparseable) | REJECTED | oos/calendar.t: not a date column (time data "31/12/2021" doesn't match format "%Y-%m-%d", at position 0. You might want to try:
    - passing `format |
| 27 | missing date | REJECTED | oos/calendar.s_pp: missing date |
| 28 | wrong sample label | REJECTED | oos/calendar: wrong sample label |
| 29 | wrong holding month | REJECTED | primary/calendar: holding month is not the month after t |
| 30 | alter entity id (universe) | REJECTED | primary/universes: entity that is not in the identity table |
| 31 | duplicate universe member | REJECTED | primary/universes: duplicate (t, key, entity) |
| 32 | 199-stock universe | REJECTED | oos/universes: a universe does not have exactly 200 stocks |
| 33 | change column type (rank as text) | REJECTED | oos/universes.rank: not a numeric column (object) |
| 34 | insert NaN (rank) | REJECTED | oos/universes.rank: NaN or infinite value |
| 35 | insert inf (rank) | REJECTED | oos/universes.rank: NaN or infinite value |
| 36 | rank below 1 | REJECTED | oos/universes: rank below 1 |
| 37 | step A stock outside the survivor pool | REJECTED | primary/universes: step A/B stock outside the survivor pool |
| 38 | step A list changes over time | REJECTED | oos/universes: step A universe is not the same list at 2026-07-31 |
| 39 | unknown universe key | REJECTED | primary/universes: keys are not exactly A, B, C |
| 40 | unknown delisting class | REJECTED | identity: unknown delisting class |
| 41 | duplicate identity row | REJECTED | identity: missing or duplicate entity_id |
| 42 | survivor pool flag inconsistent | REJECTED | identity: survivor pool != ACTIVE_AT_CUTOFF |
| 43 | gap row that is not a flagged row | REJECTED | gap_rows: a gap row is not a flagged panel row |

## 5. The one class B case

**Reordering the rows of the panel.** If the bytes of the file change, the hash layer rejects it (file-layer case "reorder rows"). The question for the value layer is different: does row order carry information? It does not. The test `test_reordering_panel_rows_is_an_allowed_operation_that_cannot_change_a_result` shuffles every row, validates the frames, builds the matrices and shows that every matrix is identical cell for cell. Reordering the **calendar** is different: month order is checked and a swap is rejected.

## 6. What was not attacked

1. Stage 2 raw files and datasets were not corrupted file by file in this suite (1.4 GB). They are covered by the manifest chain (`tests/test_provenance_chain.py`, synthetic) and by the archive verifier (`tests/test_release_archive.py`, synthetic).
2. A simultaneous, consistent rewrite of the registry history **and** of the pinned history hash in code was not attempted: it is a deliberate edit of two tracked files, visible in Git, and outside what local code can prevent (`THREAT_MODEL.md`, section 1).
3. Removing only the newest registry line is detected through the environment anchor (the superseded anchor then no longer matches the files). Removing lines that nothing depends on would not be detected by local code (finding N-03).
4. Power loss during a registry append cannot be simulated safely. Its result is tested: a half-written last line makes the registry unreadable with a clear message.
5. The frozen runners' own non-atomic writes (F-08) cannot occur again for S2-MOM-v1 because every mode has run; they were not exercised.

## 7. Status

No silent acceptance of a corrupted research input was found among these attacks. This is evidence about the attacks listed, not a proof that no other corruption exists.
