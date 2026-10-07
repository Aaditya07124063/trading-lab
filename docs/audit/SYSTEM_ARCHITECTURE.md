# Trading Lab — authoritative system map for S2-MOM-v1 (after remediation, 2026-10-07)

This file replaces the forensic version of the same name. The forensic version is kept unchanged in `docs/audit/forensic_20261007/SYSTEM_ARCHITECTURE.md` (repository tree, entry-point table, dependency list). This version is the map of the research chain: every stage, and for every arrow the nine facts the release standard asks for.

Words used below:

- **Frozen** = a registered hash covers the file. It must not change. `scripts/audit_snapshot.py verify` and `scripts/reproduce_s2_mom_v1.py` both fail if it does.
- **Mutable** = may change. A change is visible in Git.
- **Append-only** = may only grow; old bytes are pinned.
- **Root of trust** = `registry/experiments.jsonl`. Its first 58 lines are pinned by a SHA-256 inside `src/registry/experiments.py`; every later line carries the SHA-256 of all bytes before it.

```
 1 RAW DATA  (NSE web files)
     │  arrow 1
 2 RAW ARCHIVE            data/raw/nse_archive/            (5,560 files, outside Git, in the external archive)
     │  arrow 2
 3 RAW MANIFEST           data/stage2/raw_manifest.jsonl   (Git)
     │  arrow 3
 4 STAGE 2 PARSING / QA   PANEL-1.1, CA-2, ID-1            data/stage2/
     │  arrow 4
 5 RET-1.1                data/stage2/datasets/ret1_1/     (16 yearly files, external archive)
     │  arrow 5
 6 UNIV-1                 data/stage2/universe/univ1_pit_universe.parquet (Git)
     │  arrow 6
 7 STAGE 3 INPUT MANIFEST data/stage3/s2_mom_v1/manifest.json  ◀── anchored in the registry
     │  arrow 7
 8 FROZEN PROTOCOL        docs/research/phase3a_momentum_protocol.md (+ Addendum 1, Supplements 1-4)
     │  arrow 8
 9 A/B/C/D LADDER         src/stage3/ladder.py
     │  arrow 9
10 STATISTICS             src/stage3/stats.py, experiment.py
     │  arrow 10
11 STEP E COSTS           src/stage3/step_e.py
     │  arrow 11
12 C2 ANALYSES            scripts/run_s2_mom_c2.py
     │  arrow 12
13 REGISTERED RESULTS     results/s2_mom_v1*/  +  registry/experiments.jsonl, trials.jsonl
     │  arrow 13
14 MANUSCRIPT             docs/manuscript/s2_mom_v1/
     │  arrow 14
15 REPRODUCTION PACKAGE   Git commit + release/s2_mom_v1/ARCHIVE_MANIFEST.json + scripts/reproduce_s2_mom_v1.py
     │  arrow 15
16 RELEASE GATE           docs/audit/FINAL_RELEASE_GATE.md
```

## Arrow 1 — RAW DATA → RAW ARCHIVE

| | |
|---|---|
| Input | NSE bhavcopy zips, corporate-action JSON, list files (HTTP). |
| Output | One file per URL under `data/raw/nse_archive/`. |
| Responsible code | `src/stage2/archive.py::fetch` |
| Validation | Session date ≤ research cutoff. A URL already in the manifest is never fetched again. 5xx/429 raise and record nothing. 404 is recorded as "no session". |
| Invariant | A raw file is never overwritten (`.part` then rename onto a path that did not exist). |
| Failure behaviour | Network error after 4 tries: message, nothing recorded, a rerun resumes. **Gap (F-16, report-only frozen):** any HTTP 200 body is stored without checking that it is a zip or JSON; a bad body is detected later, by the parser. |
| Hash / provenance | SHA-256 per file, written at download time. Since remediation: every file is also listed in `release/s2_mom_v1/ARCHIVE_MANIFEST.json`, whose hash is anchored in the registry. All 5,560 raw files have the same hash in both records (checked 2026-10-07). |
| Tests | `tests/test_stage2_archive.py` (3); `tests/test_release_archive.py` (11); `tests/test_version_control.py::test_every_ignored_research_file_is_in_the_external_archive_manifest`. |
| Mutable or frozen | Frozen (append-only by design). |

## Arrow 2 — RAW ARCHIVE → RAW MANIFEST

| | |
|---|---|
| Input | The downloaded file. |
| Output | One line in `data/stage2/raw_manifest.jsonl`: kind, url, path, session, status, bytes, sha256, retrieved_at (8,166 lines: 5,560 files, 2,606 "no session"). |
| Responsible code | `src/stage2/archive.py::fetch` |
| Validation | Written only after the file is on disk. |
| Invariant | One line per URL, never edited. |
| Failure behaviour | No line without a file. |
| Hash / provenance | SHA-256 of the manifest itself (`7dea91c9…`) is in the registry (`provenance.stage2_rebuild.inputs_sha256`). The file is in Git. |
| Tests | `tests/test_stage2_archive.py`; real-data cross-check in `tests/test_release_archive.py::test_real_archive_manifest_matches_the_working_tree_when_data_is_present`. |
| Mutable or frozen | Frozen for the registered study (append-only if new sessions are fetched for a later study). |

## Arrow 3 — RAW MANIFEST → STAGE 2 PARSING / QA

| | |
|---|---|
| Input | Raw files named by the manifest. |
| Output | PANEL-1 / PANEL-1.1 yearly parquet, CA-2 event tables, ID-1 identity tables, their manifests (`data/stage2/panel`, `validation`, `identity`). |
| Responsible code | `src/stage2/panel.py`, `corporate_actions.py`, `identity.py`; driver `scripts/build_stage2.py`. |
| Validation | Each raw file's SHA-256 equals the manifest before parsing. Row dates must equal the file's session. QA counts problems and removes nothing. Only strictly parsed bonus/split subjects get a factor. Identity links need explicit evidence. |
| Invariant | Nothing is repaired. Nothing after the cutoff is read. |
| Failure behaviour | Hash or date mismatch raises. **Gaps (F-24, report-only frozen):** malformed numbers become NaN and are counted as missing prices. |
| Hash / provenance | Per-file hashes in `panel1_1_manifest.json`, `PHASE2_MANIFEST.json`; those manifest hashes are in the registry (`stage2_rebuild.outputs_sha256`). The rebuild log `stage2_rebuild_20261005.log` (150 of 150 checks) is now anchored in the registry. |
| Tests | `tests/test_stage2_panel.py`, `test_stage2_corporate_actions.py`, `test_stage2_identity.py`; `tests/test_s2mom_mutation_kills.py::test_corporate_action_validation_band_is_25_percent`. |
| Mutable or frozen | Frozen. A Stage 2 rebuild is a stop condition of this remediation and was not needed. |

## Arrow 4 — STAGE 2 PARSING / QA → RET-1.1

| | |
|---|---|
| Input | PANEL-1.1 rows, ID-1 entities, CA-2 events, special-session list. |
| Output | 16 yearly files `data/stage2/datasets/ret1_1/ret1_1_<year>.parquet`: `ret_raw`, `event_factor`, `ret_adj`, `return_status`, `research_grade`, `ret_research`. |
| Responsible code | `src/stage2/returns.py::build` |
| Validation | Panel after the cutoff is refused. An event attaches to the first row with `prev_date < ex_date ≤ date`. Status precedence is fixed. |
| Invariant | Only `OK` and `ADJUSTED_VALIDATED` rows are research-grade. A move above 1.4× with no validated event is `UNEXPLAINED_JUMP`. |
| Failure behaviour | Cutoff breach raises. A flagged row is kept and labelled, never dropped. |
| Hash / provenance | `ret1_1_manifest.json` (per-file hashes, in Git) → its hash is in the Stage 3 manifest → the Stage 3 manifest hash is in the registry. Files also in the external archive manifest (two independent records agree, tested). |
| Tests | `tests/test_stage2_returns.py`; `tests/test_s2mom_mutation_kills.py::test_ret1_jump_threshold_is_40_percent`, `::test_ret1_event_is_attached_to_the_first_row_on_or_after_its_ex_date`. |
| Mutable or frozen | Frozen. |

## Arrow 5 — RET-1.1 → UNIV-1

(UNIV-1 is built from the same PANEL-1.1 and ID-1 as RET-1.1; it is listed here in the order of the release chain.)

| | |
|---|---|
| Input | EQ panel rows, ID-1 segments and links. |
| Output | `data/stage2/universe/univ1_pit_universe.parquet`: one row per (selection date, entity) with liquidity, valid sessions, status, rank. |
| Responsible code | `src/stage2/universe.py::build` |
| Validation | Panel after the cutoff refused. Liquidity = median traded value over the 63 sessions ending at t. At least 50 valid sessions. Identity uses only links effective on or before t. |
| Invariant | Nothing after t decides membership at t. Ties break by entity id. |
| Failure behaviour | Cutoff breach raises. |
| Hash / provenance | `2abf457a…9c42`: pinned in `src/stage3/protocol.py`, in the registry record (`universe_sha256`), in the Stage 3 manifest and in `scripts/reproduce_s2_mom_v1.py`. Four independent places must agree. |
| Tests | `tests/test_stage2_universe.py`; `tests/test_s2mom_mutation_kills.py::test_univ1_liquidity_window_is_63_sessions_and_needs_50_valid_ones`, `::test_univ1_liquidity_is_the_median_not_the_mean`. |
| Mutable or frozen | Frozen. |

## Arrow 6 — UNIV-1 → STAGE 3 INPUT MANIFEST

| | |
|---|---|
| Input | RET-1.1 files, UNIV-1, ID-1. |
| Output | Eight Stage 3 input files (`research/panel.parquet`, `sessions.csv`, `identity.csv`, `gap_rows.csv`, `primary/` and `oos/` `calendar.csv` + `universes.csv`) and `manifest.json` with input hashes, output hashes, code hashes, counts. |
| Responsible code | `src/stage3/data.py::build` (frozen); checked from outside by `src/registry/integrity.py::verify_stage3`, `validate_stage3`. |
| Validation | Frozen builder: protocol hash, every RET-1.1 hash, UNIV-1 hash, ID-1/RET-1.1 grouping, seven structural `assert`s. **New, outside frozen code:** the same seven checks and 40 more as explicit raises in `validate_stage3` (works under `python -O`). |
| Invariant | An existing output that differs is never overwritten. The last session is T\* = 2026-09-30. 114 + 56 months. Every universe has exactly 200 stocks. Step A's list is the same in every month. |
| Failure behaviour | Any mismatch raises (`ValueError` in the builder; `ProvenanceError` / `ValidationError` in the verifier). |
| Hash / provenance | **Closed by remediation (F-02):** registry `anchors.stage3_manifest_sha256` = `6f08fd0f…1fe5` → `manifest.json` → `outputs_sha256` → the eight files; `inputs_sha256` → Stage 2 files; `code_sha256` → three code files. The manifest is not trusted because it agrees with its own folder: it must first equal the registry anchor. |
| Tests | `tests/test_provenance_chain.py` (24, including: rewritten manifest, modified input, modified manifest, missing manifest, duplicate entry, path traversal, unexpected file, symlink); `tests/test_failure_injection.py` (43 value attacks on `validate_stage3`); `tests/test_s2mom_mutation_kills.py::test_load_inputs_refuses_a_stage3_file_that_differs_from_the_manifest`. |
| Mutable or frozen | Frozen. |

## Arrow 7 — STAGE 3 INPUT MANIFEST → FROZEN PROTOCOL

| | |
|---|---|
| Input | The manifest's `protocol_sha256`; the protocol file; the registry record. |
| Output | Permission to compute: the constants of the experiment (`src/stage3/protocol.py`). |
| Responsible code | `src/stage3/protocol.py::verify_protocol`, `require_ready` (frozen); `scripts/reproduce_s2_mom_v1.py::check_protocol`. |
| Validation | Protocol file SHA-256 = constant in code = registry `protocol_sha256` = manifest `protocol_sha256`. Addendum 1 and Supplements 1–4: file = registry `addenda[].sha256`. Every reviewer decision recorded. |
| Invariant | The protocol text is `f1abd954…d838`. In the registry, `protocol_sha256` is an identity field: it cannot be replaced in any state except through explicit revalidation. |
| Failure behaviour | `ProtocolMismatch` / `NotReady` (frozen code); `RegistryError` on any attempt to amend the hash; reproduction FAIL. |
| Hash / provenance | Registry record (root of trust), plus three independent pins (protocol.py, reproduce script, manuscript Table A5). |
| Tests | `tests/test_stage3_infra.py::test_h_runner_refuses_a_changed_protocol_or_registry_record`, `::test_protocol_file_matches_the_frozen_hash_and_constants`; `tests/test_registry_state_machine.py` (protocol hash replacement refused in every state; allowed only after REQUIRES REVALIDATION with the explicit flag); failure injection "modify the protocol", "modify protocol hash (registry)". |
| Mutable or frozen | Frozen. Changing it is a stop condition. |

## Arrow 8 — FROZEN PROTOCOL → A/B/C/D LADDER

| | |
|---|---|
| Input | Stage 3 matrices, calendar, universes A/B/C, protocol constants. |
| Output | One row per (month, step): W, L, BM, WML, counts; holdings; audit events. `delta = (WML_A − WML_D) × 100`. |
| Responsible code | `src/stage3/ladder.py` (frozen). Independent second implementation: `scripts/reproduce_s2_mom_v1.py::ladder`. |
| Validation | Missing price in the panel stops the run. Universe entity missing from the panel stops the run. **Gap (F-07, report-only frozen):** `wide()` itself does not reject duplicates, inf, or returns ≤ −100%; `validate_stage3` now rejects them before any calculation in the reproduction path. |
| Invariant | 12-1 formation over (m12, m1]; entry at the close of the first session after t; holding (s_plus, s_pp]; k = floor(0.30 n + 0.5); ties by entity; equal weights; WML = W − L; step D uses research-grade returns only; delisting rule from step C only. |
| Failure behaviour | `ValueError`. A month that cannot be computed is kept with its reason, never as a zero. |
| Hash / provenance | Code hash `f57c9321…a1d1` (seven files) in the registry for primary, sensitivity and confirmation. |
| Tests | Golden hand-computed world: `tests/test_s2mom_mutation_kills.py` part 1 (8 tests + 7 boundary cases); `tests/test_stage3_ladder.py` (33); two-implementation agreement: `tests/test_reproduction.py::test_independent_ladder_agrees_with_the_frozen_ladder_on_a_random_world`. Mutation matrix: `MUTATION_FINAL_REPORT.md`. |
| Mutable or frozen | Frozen. |

## Arrow 9 — A/B/C/D LADDER → STATISTICS

| | |
|---|---|
| Input | Monthly series, delta. |
| Output | H1 (mean, Newey–West SE, t, two-sided p, 90% interval, label), bootstrap p, ladder table, step differences. |
| Responsible code | `src/stage3/stats.py`, `src/stage3/experiment.py::analyse` (frozen). Independent: `reproduce_s2_mom_v1.py::nw_test`. |
| Validation | Series shorter than lag + 2 raises. **Gap (F-07):** NaN in gives NaN out in frozen code; the reproduction comparison refuses any NaN or inf. |
| Invariant | Lag = floor(4 (n/100)^(2/9)) = 4 (114 months), 3 (56). Two-sided normal p. Bootstrap: seed 20261005, 10,000 resamples, null-centred, both tails. Label table of §27. |
| Failure behaviour | Raise on a short series; otherwise fail-open on NaN inside frozen code (guarded from outside). |
| Hash / provenance | Same code hash as arrow 8. `src/intraday/inference.py` (resampler) is pinned by the ORB frozen-hash test, not by the S2-MOM code hash (F-09, accepted risk; listed in `findings.json`). |
| Tests | `tests/test_s2mom_mutation_kills.py` parts 2–3 (hand Newey–West, both bootstrap tails, 12-row label table, one-sided economic flags); `tests/test_stage3_infra.py` (statsmodels cross-check). |
| Mutable or frozen | Frozen. |

## Arrow 10 — STATISTICS → STEP E COSTS

| | |
|---|---|
| Input | Saved step D holdings and monthly files of both samples, UNIV-1 ranks, the dated cost schedule. |
| Output | `results/s2_mom_v1_step_e/`: order ledger, monthly costs and net returns under S0–S4, H3, H4 (primary only), break-even. |
| Responsible code | `src/stage3/step_e.py`, `scripts/run_s2_mom_step_e.py` (frozen). Independent: `reproduce_s2_mom_v1.py::step_e_costs`. |
| Validation | Five inputs hash-pinned in the runner. Schedule byte-checked with its parent documents. Rank guard for W and L. A missing period, rate or month raises. |
| Invariant | Rates in force on the entry session. Tax on brokerage + exchange + IPFT + SEBI fee only. Net = gross − cost. Gross is copied, never recomputed. No cost is zero. |
| Failure behaviour | `CostScheduleError` / `NotReady`. **Gap (F-17, report-only frozen):** a month without a ledger row would be costed at 0 inside `net_returns`; `validate_step_e` and the registered-file test now reject any zero cost. |
| Hash / provenance | Step E code hash `a6845d30…cc54`; schedule `47a9bad4…a10f` pinned in code, anchored in the registry, pinned in the reproduction script. |
| Tests | `tests/test_s2mom_step_e.py`, `test_s2mom_step_e_scenarios.py`, `test_s2mom_cost_schedule.py`; `tests/test_s2mom_mutation_kills.py` part 7; `tests/test_reproduction.py::test_independent_step_e_costs_agree_with_the_frozen_cost_ledger`. |
| Mutable or frozen | Frozen. |

## Arrow 11 — STEP E COSTS → C2 ANALYSES

| | |
|---|---|
| Input | Six registered result files (monthly and delta of both samples, primary results, step E results). |
| Output | `results/s2_mom_v1_c2/c2_results.json`: H2d, Holm, Benjamini–Hochberg, two halves, pooled block, skewness, worst month. |
| Responsible code | `scripts/run_s2_mom_c2.py` (frozen). Independent arithmetic in the reproduction script. |
| Validation | Specification and six inputs hash-checked before any read. Recomputed delta must equal the registered delta file. The primary block must reproduce the registered primary results to 1e-9. |
| Invariant | No backtest is rerun. Late execution is stated in the output itself ("not blind and not confirmatory"). |
| Failure behaviour | `NotReady`. Output directory appears only when complete (`.partial` then rename). Runs once. |
| Hash / provenance | C2 code hash `505b2e4e…b3fa`, specification hash, six input hashes and the run environment are in the registry. |
| Tests | `tests/test_s2mom_c2.py`; reproduction recomputes H2d, Holm, BH and five block deltas. |
| Mutable or frozen | Frozen. |

## Arrow 12 — C2 ANALYSES → REGISTERED RESULTS

| | |
|---|---|
| Input | The 18 result files. |
| Output | Registry record `S2-MOM-v1` (state FINAL) with every file hash; six trial-log lines, one per registered mode. |
| Responsible code | `src/registry/experiments.py` (rewritten in remediation: state machine, hash chain, fail-closed reader). |
| Validation | Every read validates the whole file: JSON, duplicate ids, duplicate lines, orphan amendments, pinned history (58 lines), hash chain, legal transition, protected fields. Every write holds a file lock, re-validates, appends one line, fsyncs. |
| Invariant | PLANNED → READY → EXECUTING → REGISTERED → FINAL. FINAL → SUPERSEDED / INVALID / REQUIRES REVALIDATION only. In FINAL only `status` may change and `anchors` may gain keys. Recorded hashes never change without explicit revalidation. |
| Failure behaviour | `RegistryError`; nothing is written. A truncated last line makes the registry unreadable on purpose (fail closed) with a clear message. |
| Hash / provenance | Pinned genesis hash `8fae608a…5f9d` (58 lines) + per-line chain. The registry file is in Git. |
| Tests | `tests/test_registry_state_machine.py` (235): all 156 state pairs, 11 protected-field attacks on FINAL, 13 parser attacks, 10 forged-amendment attacks with a valid chain, 6 history rewrites, 12 attacks on a copy of the real registry. |
| Mutable or frozen | Append-only. Result files: frozen. |

## Arrow 13 — REGISTERED RESULTS → MANUSCRIPT

| | |
|---|---|
| Input | Registered result JSON files; `manuscript.template.md`. |
| Output | `manuscript.md` / `.html` / `.docx` / `.pdf`, `number_audit.csv` (565 numbers), `claim_audit.md`. |
| Responsible code | `docs/manuscript/s2_mom_v1/build_manuscript.py` (not changed). Independent check: `scripts/verify_manuscript.py`. |
| Validation | Builder: stops if a registered hash differs; 699 consistency checks. Verifier: every audited number re-read from the registered file, rounding checked, every printed hash checked against disk and registry, required disclosures present. |
| Invariant | No result number is typed by hand. No derived number. |
| Failure behaviour | Builder stops. Verifier prints FLAG and exits 1; it never edits the manuscript. |
| Hash / provenance | Table A5 of the manuscript (26 hashes). One open flag: Supplements 2 and 3 are referenced but their hashes are not in Table A5 (`MANUSCRIPT_VERIFICATION_REPORT.md`). |
| Tests | `tests/test_manuscript_verification.py`. |
| Mutable or frozen | Mutable (the manuscript is a draft); the numbers in it are frozen by their sources. |

## Arrow 14 — MANUSCRIPT → REPRODUCTION PACKAGE

| | |
|---|---|
| Input | The Git tree; the external data files. |
| Output | (a) a Git commit holding all code, tests, configuration, registry, results, manifests and documents; (b) `release/s2_mom_v1/ARCHIVE_MANIFEST.json` — 5,637 external files with SHA-256, archive id `s2-mom-v1-data-baa0b47040101031`, deterministic tar SHA-256 `bb4b9659…1ac2`; (c) the environment contract: `release/s2_mom_v1/environment.yml`, `conda-osx-arm64.lock`, `ENVIRONMENT.json` (Conda, osx-arm64; pip is not supported) and `requirements-lock.txt` (version pins for reference). |
| Responsible code | `scripts/release_archive.py` (manifest / verify / pack / materialize). |
| Validation | `verify`: every file present and identical, nothing extra. `materialize`: tar hash first, then every member against the manifest; never overwrites; refuses unknown members and path traversal. |
| Invariant | No research-critical file is untracked. Every git-ignored research file is in the archive manifest. The archive bytes depend on the files only (sorted names, fixed metadata), so any copy can be verified anywhere. |
| Failure behaviour | `ArchiveError`; nothing written. A partial archive never carries the final name. |
| Hash / provenance | Archive manifest hash and tar hash anchored in the registry (`anchors.external_archive`). Environment files anchored (`anchors.environment_files_sha256_v2`, which supersedes the first anchor). |
| Tests | `tests/test_release_archive.py` (11), `tests/test_version_control.py` (3), `tests/test_environment.py` (9), `tests/test_frozen_code.py` (41). |
| Mutable or frozen | The commit: immutable once made. The archive: frozen. **Open action for the researcher:** the commit is not made yet (by instruction) and the archive has not been copied off this laptop. |

## Arrow 15 — REPRODUCTION PACKAGE → RELEASE GATE

| | |
|---|---|
| Input | Everything above. |
| Output | PASS / FAIL of `python3 scripts/reproduce_s2_mom_v1.py`; the tables of `FINAL_RELEASE_GATE.md`. |
| Responsible code | `scripts/reproduce_s2_mom_v1.py`, `scripts/mutation_campaign.py`, `tests/test_failure_injection.py`, `scripts/audit_snapshot.py`. |
| Validation | Eight steps: environment, protocol, registry, manifest chain, registered outputs and input validation, independent recomputation, comparison at 1e-9, repository unchanged. |
| Invariant | It registers nothing and writes nothing in the repository. Any failed step is a FAIL; there is no partial pass. `python -O` is refused. |
| Failure behaviour | Exit code 1 and the name of the broken link. |
| Hash / provenance | The script pins the published result hashes itself, so the registry, the files and the script must all agree. |
| Tests | `tests/test_reproduction.py` (17, including a clean-process run), `tests/test_failure_injection.py` (46 file attacks, 43 value attacks). |
| Mutable or frozen | Mutable tooling; its own mutations are tested (45 mutations in group "release tooling"). |

## Where a gap is still open

There is no unexplained gap in the chain, but four links are weaker than the rest. They are listed here so that nobody has to find them again.

1. **Arrow 1.** A non-zip HTTP 200 body would be archived (F-16). Detected at arrow 3. Report-only.
2. **Arrows 8–9.** The frozen code can be imported and called directly, without the runner's gates (F-30 / L-01). The registry now refuses to register such a result on a FINAL experiment, and the trial log check in the reproduction flags an extra logged run, but an unlogged private computation cannot be prevented by code. Accepted risk; runbook rule.
3. **Arrow 14.** One laptop still holds the only copy until the commit is pushed and the archive is copied (F-01: mechanism in place, action open).
4. **Arrow 13.** The manuscript's PDF is compared by extracted text only.
