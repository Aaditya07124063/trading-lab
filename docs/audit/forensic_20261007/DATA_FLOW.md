# Trading Lab — data-flow graph for S2-MOM-v1 (audit 2026-10-07)

Each arrow lists: module/function · input → output · validation · invariant · failure behaviour · tests · provenance/hash. Evidence label at the end of each block.

```
 NSE archive (network)
   │ 1 fetch
   ▼
 data/raw/nse_archive + raw_manifest.jsonl
   │ 2 parse / QA
   ▼
 PANEL-1, PANEL-1.1 ──3──▶ CA-2 events ──4──▶ ID-1 identity
   │                                             │
   │ 5 UNIV-1 (point-in-time universe)           │
   │ 6 RET-1.1 (daily returns, status)  ◀────────┘
   ▼
 Stage 3 inputs (panel, sessions, identity, calendar, universes)   7 build
   │ 8 load + verify
   ▼
 ladder A–D (strategy → portfolio)                                  9
   │
   ├─10─▶ statistics (Newey-West, bootstrap, decisions)
   │
   ▼
 results/s2_mom_v1 (monthly, delta, holdings, events, JSON)        11 write + register
   │ 12 step E (costs from saved holdings)
   │ 13 C2 (late analyses from saved files)
   ▼
 registry/experiments.jsonl + trials.jsonl                          14
   │ 15
   ▼
 research_view (API) · manuscript builder
```

## 1. INPUT — `src/stage2/archive.py::fetch`
- In: URL. Out: one raw file + one manifest record (`kind, url, path, session, status, bytes, sha256`).
- Validation: session ≤ research cutoff; a URL already in the manifest is never refetched; 5xx/429 raise and are not recorded; 404 is recorded as "no session".
- Invariant: a raw file is never overwritten (`.part` + rename onto a path that did not exist).
- Failure: network error after 4 tries → message, nothing recorded, rerun resumes.
- **Gap:** any HTTP 200 body is stored permanently, with no check that it is a zip/JSON (F-16). No fsync. No lock for two collectors.
- Tests: `tests/test_stage2_archive.py` (3 tests; 40 % coverage). Hash: SHA-256 per file.
- Label: VERIFIED BY INSPECTION; partly PROVEN BY TEST.

## 2. VALIDATION — `src/stage2/panel.py::parse`, `build_year`, `qa`, `calendar_check`
- In: zip bytes. Out: EQ rows `date symbol isin series open high low close last prevclose volume value trades source source_sha256`.
- Validation: session ≤ cutoff; row dates must equal the file's session; overlap days compared field by field; QA counts (duplicates, impossible OHLC, non-positive price, missing price, negative volume) are **counted, never removed** — by design ("nothing is repaired").
- **Gaps:** numeric fields use `errors="coerce"` (malformed → NaN, counted as missing price); unparseable row dates are dropped before the date comparison, so such rows are accepted under the file's session (F-24). Only the first zip member is read.
- Failure: date mismatch → `ValueError`. Tests: `tests/test_stage2_panel.py` (93 %). Hash: yearly parquet hashes in `panel1_manifest.json`, rebuilt and compared by `build_stage2.py` step 2.
- Label: PROVEN BY TEST (rules); SUPPORTED BY HASH (real data, 150/150 on 2026-10-05).

## 3. TRANSFORMATION — `src/stage2/corporate_actions.py::load_events`, `parse_subject`, `classify`, `validate`
- In: archived NSE JSON. Out: events with `kind`, `factor` (bonus/split only), validation status.
- Invariant: only strictly parsed bonus/split subjects get a factor; anything ambiguous is `UNPARSED`, never adjusted. Ex-dates after the cutoff are dropped.
- Tests: `tests/test_stage2_corporate_actions.py` (96 %). Hash: `ca2_*.csv` in `PHASE2_MANIFEST.json`.
- Label: PROVEN BY TEST; SUPPORTED BY HASH.

## 4. TRANSFORMATION — `src/stage2/identity.py::segments`, `links`, `entities`, `end_status`
- Invariant: segments are linked only with explicit evidence (same ISIN, NSE symbol-change file, ISIN introduction, ISIN change with a corporate-action record). `end_status` ∈ {ACTIVE_AT_CUTOFF, DELISTED_EVIDENCED, ENDED_UNEXPLAINED}.
- **Coupling:** three separate union-find implementations with two different entity-id conventions (smallest id here; earliest segment in `returns.entity_map` and `universe._components`). Stage 3 `data.identity()` checks the two groupings are a bijection and raises otherwise (A-01).
- Tests: `tests/test_stage2_identity.py` (94 %). Hash: `id1_*.csv` in `PHASE2_MANIFEST.json` and again in the Stage 3 manifest.
- Label: PROVEN BY TEST; SUPPORTED BY HASH.

## 5. RESEARCH DATA — `src/stage2/universe.py::build` (UNIV-1)
- In: EQ panel, segments, links. Out: one row per (selection_date, entity): liquidity median, valid sessions, status, rank.
- Invariants: window = the 63 sessions ending at `t` inclusive; identity uses only links effective ≤ `t`; ties by entity id; panel after cutoff refused.
- Tests: `tests/test_stage2_universe.py` (truncation, future delisting, future volume, future symbol; 95 %). Mutations of the window, link date, rank order, fund-unit rule: see `MUTATION_TEST_REPORT.md`.
- Hash: `2abf457a…9c42`, pinned in code and registry; rebuilt bit-identically by `build_stage2.py` step 6.
- Label: PROVEN BY TEST; SUPPORTED BY HASH.

## 6. RESEARCH DATA — `src/stage2/returns.py::build` (RET-1.1)
- Out per row: `ret_raw`, `event_factor`, `ret_adj`, `return_status`, `research_grade`, `ret_research`.
- Invariants: an event attaches to the first row with `prev_date < ex_date ≤ date`; status precedence is fixed; only OK / ADJUSTED_VALIDATED are research-grade.
- **Gap:** a segment missing from ID-1 silently becomes its own entity (`.fillna(segment_id)`); caught later by Stage 3 `identity()`.
- Tests: `tests/test_stage2_returns.py` (95 %). Hash: per-year hashes in `ret1_1_manifest.json`; that manifest's hash is in the registry (`stage2_rebuild.outputs_sha256`).
- Label: PROVEN BY TEST; SUPPORTED BY HASH.

## 7. RESEARCH DATA → STRATEGY INPUTS — `src/stage3/data.py::build`
- Validation: `verify_protocol()`; every RET-1.1 file hash; UNIV-1 hash; ID-1/RET-1.1 grouping bijection; seven structural `assert`s (last session = T\*, 170 months, 114/56 split, step A list = UNIV-1 MEMBER at T\*, step C = UNIV-1 MEMBER, step B has 200).
- Invariant: build-or-verify — an existing output that differs is never overwritten.
- **Gaps:** the structural checks are `assert` statements (disabled by `python -O`, F-10); `manifest.json` is written non-atomically and is not anchored in the registry or in code (F-02); the whole function has **0 % test coverage** (F-04).
- Label: VERIFIED BY INSPECTION; SUPPORTED BY HASH (self-referential only).

## 8. LOAD — `src/stage3/data.py::load_inputs`
- Validation: `verify_protocol()`; every Stage 3 file against `manifest.json`; cutoff ≤ research cutoff; no row after T\*.
- Then `ladder.wide()` builds date × entity matrices.
- **Gaps:** `wide()` does not reject duplicate (date, entity) rows, returns ≤ −100 %, ±inf, NaN on a research-grade row, or an unknown class value (F-07). The registered panel was checked in this audit and has none of these. **0 % test coverage** of `load_inputs` (F-04).
- Label: UNVERIFIED by the suite; verified on the registered data by the audit script.

## 9. STRATEGY → PORTFOLIO — `src/stage3/ladder.py::calendar`, `universes`, `run_ladder`, `_hold`, `paired_delta`
- Schema out: monthly rows (`t, holding_month, sample, step, status, n_universe, n_rankable, k, holding_sessions, W, L, BM, WML`, counts) and holdings with begin/end weights and audit events.
- Invariants and their tests: see `RESEARCH_INTEGRITY_AUDIT.md`.
- Label: PROVEN BY TEST (95 % coverage, 33 tests) **and independently re-implemented in the audit: all 680 step-months match to 5e-16**.

## 10. STATISTICS — `src/stage3/stats.py`, `src/stage3/experiment.py::analyse`
- `newey_west_lrv` (Bartlett, autocovariances / n), `mean_test` (normal reference), `bootstrap_test` (null-centred stationary bootstrap, seed 20261005), §27 decision.
- **Gap:** NaN in → NaN out with no error; the decision then falls through to `INCONCLUSIVE` (F-07).
- Tests: cross-checked against statsmodels in the suite and again in the audit (H1 mean, SE, p to 1e-9 in both samples).
- Label: PROVEN BY TEST; independently recomputed.

## 11. RESULTS — `scripts/run_s2_mom.py::main`, `_write`
- Order: gates → compute → `_write(results.json)` (refuses if the file exists) → CSVs → `log_trial` → `amend`.
- **Gaps:** exists-check then `write_text` is not atomic and not exclusive; CSVs are written with plain `to_csv`; a crash after the JSON is written leaves a readable, unregistered result with **no trial-log entry** (F-08). The run-once guard is untested (F-04).
- Label: VERIFIED BY INSPECTION.

## 12. COSTS — `src/stage3/step_e.py`, `scripts/run_s2_mom_step_e.py`
- Reads five hash-pinned inputs; schedule byte-checked with its parent documents; costs per order from the rate in force on the trade date; output directory appears only when complete (`.partial` → rename).
- **Gap:** `net_returns` fills a missing portfolio-month cost with 0 (F-17) — not triggered (every month has a positive cost, verified).
- Label: PROVEN BY TEST (97 %); **independently recomputed in the audit from holdings + schedule: max difference 1e-16**.

## 13. LATE ANALYSES — `scripts/run_s2_mom_c2.py`
- Six hash-pinned inputs; recomputed δ must match the registered δ file; the primary block must reproduce the registered primary results to 1e-9.
- Label: PROVEN BY TEST (91 %).

## 14. REGISTRY — `src/registry/experiments.py`
- `record` refuses a duplicate id and an unknown status; `amend` refuses an unknown id/status only.
- **Gap:** no state machine, no protected fields, shallow replace of nested fields, no lock, no checksum chain (F-03). 54 % coverage.
- Label: VERIFIED BY INSPECTION; weaknesses PROVEN by the audit attack script on a scratch copy.

## 15. PRESENTATION — `src/research_view.py`, `docs/manuscript/s2_mom_v1/build_manuscript.py`
- `research_view` re-hashes registered files and reports mismatches; computes nothing; 100 % coverage.
- The manuscript builder fills numbers only from registered files, checks 27 hashes and runs 699 consistency checks. It also reads the two `pre_run_checks_*.json` files, which carry no registered hash (F-12).
- Label: PROVEN BY TEST (view); VERIFIED BY INSPECTION (manuscript builder; its numbers were not re-audited line by line).

## Components that should be connected but are not

1. Stage 3 `manifest.json` ↔ registry: the registry stores only the manifest's path (F-02).
2. Pre-run check files ↔ registry: the gate reads a local JSON file with no registered hash (F-12).
3. Stage 2 rebuild ↔ runner: the "150 of 150" fact is a hand-entered registry field; the runner tests the integer only (F-12).
4. Step E / C2 code hash ↔ `stats.py`, `protocol.py`: both import them, neither hashes them (F-09).
5. Git ↔ experiment code: the registered code is not in any commit (F-01).
6. `REPRODUCIBILITY.md` ↔ Stage 3: no documented procedure (D-01).
