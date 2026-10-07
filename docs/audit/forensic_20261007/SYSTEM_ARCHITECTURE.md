# Trading Lab — system architecture (forensic audit, 2026-10-07)

Audit scope: the whole repository at `~/Projects/trading-lab`, HEAD `7d4cb6d` plus the uncommitted working tree.
Nothing in the repository was changed by this audit except the new folder `docs/audit/`.
Evidence labels used in every audit file: **PROVEN BY TEST** · **VERIFIED BY INSPECTION** · **SUPPORTED BY HASH** · **DOCUMENTATION ONLY** · **UNVERIFIED**.

## A. Repository tree (top level)

| Path | What it is | In git? |
|---|---|---|
| `src/` (`access.py`, `config.py`, `data_loader.py`, `datasets.py`, `backtest.py`, `signals.py`, `indicators.py`, `metrics.py`, `research.py`, `leaderboard.py`) | legacy daily engine + access boundary | yes |
| `src/intraday/` (13 files) | ORB v1 engine, inference, calendar, costs — frozen by hash | yes |
| `src/stage2/` (archive, panel, corporate_actions, identity, universe, returns) | NSE data foundation (PANEL-1, CA-2, ID-1, UNIV-1, RET-1.1) | yes |
| `src/stage3/` (protocol, data, ladder, stats, costs, experiment, step_e) | **S2-MOM-v1 experiment code** | **NO (untracked)** |
| `src/registry/` (experiments, data_registry) | append-only experiment registry, trial log, dataset registry | yes |
| `src/research_view.py` | read-only API view of the registry | **NO** |
| `scripts/` | builders, runners, one-off checks, launchd collector | partly (`build_stage3.py`, `run_s2_mom*.py` untracked) |
| `evaluate_orb_v1.py`, `run_*.py`, `paper_bot.py`, `fetch_data.py`, `update_intraday.py`, `server.py` | root-level entry points | yes (`server.py` modified) |
| `tests/` (28 files, 451 tests) | pytest suite | partly (7 S2-MOM/UI test files untracked) |
| `config/cost_schedules/` | cost schedules (ORB intraday: tracked; S2-MOM delivery: **untracked**) | partly |
| `data/india`, `data/gold`, `data/NIFTY_10Y.csv` | Yahoo/MT CSVs; the collector appends to `*m15.csv` daily | yes (58 files modified) |
| `data/raw/` | raw snapshots; `nse_archive` (398 MB) git-ignored | manifests only |
| `data/stage2/` | manifests + committed CSVs + UNIV-1 parquet; `datasets/` (1 GB) git-ignored | manifests only |
| `data/stage3/s2_mom_v1/` | Stage 3 inputs, manifest, pre-run check files | **NO**; `panel.parquet` git-ignored |
| `registry/` | `experiments.jsonl`, `trials.jsonl`, `datasets.json` | yes, **21 + 6 lines uncommitted** |
| `results/s2_mom_v1`, `results/s2_mom_v1_step_e`, `results/s2_mom_v1_c2` | **registered S2-MOM-v1 results** | **NO** |
| `docs/research/` | frozen protocol (tracked) + addendum, supplements 1-4, deviation log, guides (**untracked**) | partly |
| `docs/manuscript/s2_mom_v1/` | manuscript builder and outputs | **NO** |
| `web/` | static UI | partly |

## B. Executable entry points and protection class

PROTECTED = refuses unless protocol hash, registry record, input hashes and run-once conditions hold.

| # | Command | Writes | Class | Notes |
|---|---|---|---|---|
| 1 | `scripts/run_s2_mom.py checks\|blinded\|primary\|sensitivity\|confirmation` | `data/stage3/.../checks`, `results/s2_mom_v1`, registry, trials | PROTECTED | gaps: F-02, F-08, F-09, F-12 |
| 2 | `scripts/run_s2_mom_step_e.py execute` | `results/s2_mom_v1_step_e`, registry, trials | PROTECTED | five hash-pinned inputs; `.partial` directory + rename |
| 3 | `scripts/run_s2_mom_c2.py execute` | `results/s2_mom_v1_c2`, registry, trials | PROTECTED | six hash-pinned inputs |
| 4 | `scripts/build_stage3.py` | `data/stage3/s2_mom_v1` | PARTIALLY | build-or-verify; structural checks are `assert` (F-10); manifest unanchored (F-02) |
| 5 | `scripts/build_stage2.py` | `data/stage2/datasets`, Phase 2.1 files (once) | PARTIALLY | verify-only against manifests; 0 % test coverage |
| 6 | `python -m src.stage2.archive bhavcopy\|bhavcopy-weekends\|corporate-actions\|lists` | `data/raw/nse_archive`, `raw_manifest.jsonl` | PARTIALLY | network; cutoff guard; no content validation (F-16) |
| 7 | `python -m src.stage3.protocol` | registry (first registration) | PARTIALLY | duplicate id refused |
| 8 | `python -m src.registry.experiments` | `EXPERIMENT_REGISTRY.md` | UNPROTECTED (derived file) | |
| 9 | `python -m src.registry.data_registry` | `registry/datasets.json`, `DATA_REGISTRY.md` | UNPROTECTED (derived) | 0 % coverage |
| 10 | `evaluate_orb_v1.py [--dry-run-dev]` | `results/orb_v1_holdout\|dryrun/<stamp>`, registry, trials | PROTECTED | authorization artifact, single use, clean tree; 26 % coverage (F-18) |
| 11 | `run_orb_v1_dev_validation.py` | `results/orb_v1_dev` (overwrites) | PARTIALLY | development data only |
| 12 | `update_intraday.py [--dry-run] [--only ...]`, `scripts/collect_intraday.sh`, launchd `com.tradinglab.intraday-collector` | `data/india/*m15.csv`, `data/raw/yahoo`, logs | writer tier | runs weekdays 18:30; last run exit 1 (F-15) |
| 13 | `uvicorn server:app` | `/api/add` → `data/india/*d1.csv`; `/api/leaderboard/save`; trial log | PARTIALLY | F-14 |
| 14 | `paper_bot.py` | `results/paper_state.json`, `paper_diary.csv` | UNPROTECTED (legacy) | non-atomic |
| 15 | `run_experiments.py`, `run_intraday.py`, `run_ml.py`, `run_momentum.py`, `fetch_data.py` | leaderboard, `results/intraday`, data CSVs | UNPROTECTED (legacy) | `fetch_data.py` overwrites data files |
| 16 | `scripts/holdout_status.py` | nothing | read-only | fixed output fields |
| 17 | `scripts/orb_v1_power.py`, `verify_exit_bar_semantics.py`, `verify_ssrn5198458_bootstrap.py`, `seed_legacy_registry.py` | one-off outputs | UNPROTECTED (one-off) | 0 % coverage |
| 18 | `docs/manuscript/s2_mom_v1/build_manuscript.py [export]` | manuscript files in its own folder | PARTIALLY | checks 27 registered hashes; reads two unregistered check files |
| 19 | **Direct import**, e.g. `from src.stage3 import data, experiment; experiment.analyse(data.load_inputs("OOS"), ...)` | nothing | **UNPROTECTED** | computes any sample with no decision gate, no run-once guard, no trial log (L-01) |

## C. Dependencies (versions on the audit machine)

Python 3.13.5 (Anaconda, `/opt/anaconda3/bin/python3`). pandas 2.2.3 · numpy 2.1.3 · scipy 1.15.3 · pyarrow 19.0.0 · scikit-learn 1.6.1 · yfinance 1.5.1 · fastapi 0.139.2 · uvicorn 0.51.0 · requests 2.32.3 · httpx 0.28.1 · pytest 8.3.4 · statsmodels 0.14.4 (tests only). Manuscript export also needs `markdown`, `lxml`, `python-docx`, `matplotlib`, Google Chrome. See `DEPENDENCY_AUDIT.md`.

## D–F. Data inputs, intermediate artifacts, outputs

| Layer | Artifact | Location | Integrity anchor |
|---|---|---|---|
| Raw | NSE bhavcopy zips (legacy + UDiFF), corporate-action JSON, equities lists | `data/raw/nse_archive/` (git-ignored) | SHA-256 per file in `data/stage2/raw_manifest.jsonl`; prefix hash in `PHASE2_MANIFEST.json` |
| Stage 2 | PANEL-1 / PANEL-1.1 yearly parquet | `data/stage2/datasets/` (git-ignored) | `panel1_manifest.json`, `panel1_1_manifest.json` |
| Stage 2 | CA-2 validation CSVs, ID-1 CSVs | `data/stage2/validation`, `identity` | `PHASE2_MANIFEST.json` |
| Stage 2 | UNIV-1 `univ1_pit_universe.parquet` | `data/stage2/universe` | SHA-256 pinned in code (4 places) and in the registry |
| Stage 2 | RET-1.1 yearly parquet | `data/stage2/datasets/ret1_1` (git-ignored) | `ret1_1_manifest.json` (hash recorded in registry `stage2_rebuild`) |
| Stage 3 | `research/panel.parquet` (git-ignored), `sessions.csv`, `identity.csv`, `gap_rows.csv`, `primary|oos/{calendar,universes}.csv` | `data/stage3/s2_mom_v1` | `manifest.json` — **not anchored anywhere** (F-02) |
| Stage 3 | `checks/pre_run_checks_{primary,oos}.json`, `stage2_rebuild_20261005.log` | `data/stage3/s2_mom_v1/checks` | log hash in registry; check files unanchored (F-12) |
| Results | blinded, primary (5 files), sensitivity, confirmation (5 files) | `results/s2_mom_v1` | registry `provenance.*.files_sha256` |
| Results | step E (5 files) | `results/s2_mom_v1_step_e` | registry `step_e_run.files_sha256` |
| Results | C2 (1 file) | `results/s2_mom_v1_c2` | registry `c2_run` |
| Presentation | manuscript md/html/pdf/docx, number audit, figures | `docs/manuscript/s2_mom_v1` | none (regenerated) |
| ORB | `data/india/*m15.csv`, cost schedules, calendar, index closes | various | `FROZEN_SHA256` in `tests/test_access_boundary.py`; per-run manifest |

## G–I. Configuration, environment variables, CLI arguments

- **Configuration in code:** `src/config.py` (`BASE_DIR`, `HOLDOUT_START`), `src/access.py` (`RESEARCH_CUTOFF`), `src/stage3/protocol.py` (all frozen S2-MOM constants, decisions, seed), `src/stage3/step_e.py` (schedule hash, supplement hashes), `src/stage2/*` (WINDOW 63, MIN_VALID 50, TOP_N 200, JUMP 1.4, LARGE_RESIDUAL 0.10).
- **Configuration in files:** `config/cost_scenarios.json`, `config/cost_schedules/*.json`, `data/metadata/*.json`, `data/metadata/exclusions.csv`.
- **Environment variables read:** exactly one — `TRADING_LAB_NO_TRIAL_LOG` (`src/registry/experiments.py:114`). If set, **no trial is logged** (F-11). `PYTHONOPTIMIZE` / `python -O` silently removes every `assert`-based guard (F-10). Stage 3 code is tested never to read the environment.
- **CLI arguments:** `run_s2_mom.py <mode>`; `run_s2_mom_step_e.py execute`; `run_s2_mom_c2.py execute`; `evaluate_orb_v1.py [--dry-run-dev]`; `update_intraday.py [--dry-run] [--only SYM...]`; `src.stage2.archive <cmd> <start> <end>`; `build_manuscript.py [export]`. No runner accepts a path, date range, seed or parameter override. Unknown arguments exit non-zero (tested in the audit).

## J. External providers

NSE archives (`nsearchives.nseindia.com`, `www.nseindia.com` API) — Stage 2 raw data, bhavcopy cross-check, index closes. Yahoo Finance via `yfinance` / `query2.finance.yahoo.com` — intraday collector, `/api/add`, `/api/search`, `fetch_data.py`. Internet Archive — archived cost evidence (already stored in `docs/evidence/s2mom_costs`). No broker API. No credentials anywhere (see `THREAT_MODEL.md`).

## K. Storage, caches, logs

`registry/*.jsonl` (append-only by convention) · `logs/` (git-ignored) · `data/raw/collection_log.jsonl`, `data/raw/manifest.jsonl` · `data/india/backups/` (git-ignored) · `results/` · `.pytest_cache`. No database. No cache is read by research code.

## L–M. Test suites and verification mechanisms

451 tests, 26 s, all pass; the suite leaves every repository file byte-identical (checked by hashing 6,975 files before and after). No CI. Verification scripts: `scripts/build_stage2.py` (150 checks), `scripts/build_stage3.py` (rebuild-and-compare), `run_s2_mom.py checks`, `build_manuscript.py` (699 consistency checks). See `TEST_COVERAGE_AUDIT.md`.

## N. Registry interactions

`experiments.record()` (first registration), `experiments.amend()` (every later change), `experiments.log_trial()`, `experiments.current()` (fold), `experiments.write_md()`. Callers: the three S2-MOM runners, `src.stage3.protocol.__main__`, `evaluate_orb_v1.py`, `run_orb_v1_dev_validation.py`, `server.py`, legacy runners, `scripts/seed_legacy_registry.py`. Read by `src/access.final_evaluation_unused`, `src/research_view.py`, tests, the manuscript builder.

## O. Hash mechanisms

| Mechanism | Covers | Enforced by |
|---|---|---|
| `PROTOCOL_SHA256` | frozen protocol file | `verify_protocol()` on every runner start, every loader call |
| registry `protocol_sha256` | same, second copy | `verify_protocol()` |
| `UNIV1_SHA256` | UNIV-1 parquet | `load_univ`, `verify_provenance`, step E `INPUTS`, `build_stage2` |
| `ret1_1_manifest.json` | RET-1.1 yearly files | `load_ret` (per file) |
| Stage 3 `manifest.json` `outputs_sha256` / `inputs_sha256` / `code_sha256` | Stage 3 files; four Stage 2 inputs; three code files | `load_inputs`, `verify_provenance` |
| `code_sha()` in each runner | 7 files (main), 2 files (step E), 1 file (C2) | confirmation and sensitivity require the primary run's code hash |
| registry `files_sha256` | every registered result file | sensitivity mode; step E/C2 `INPUTS` (hard-coded copies); tests; `research_view`; manuscript builder |
| `SCHEDULE_SHA256`, `PARENTS`, `SUPPLEMENTS` | cost schedule, protocol, addendum, supplements 1-3 | `step_e.load_schedule` |
| `FROZEN_SHA256` (tests) | ORB v1 protocol, code, config, evidence | pytest only |
| ORB authorization artifact | protocol hash + git-committed state | `holdout_authorized()` |

## P. Architectural problems

| ID | Problem | Where | Consequence | Finding |
|---|---|---|---|---|
| A-01 | Three union-find implementations and two entity-id conventions for the same identity rule | `identity.entities` (smallest id), `returns.entity_map` and `universe._components` (earliest segment) | Stage 3 has to reconcile them at load time; a change in one is not a change in the others | F-20 |
| A-02 | Two cost models side by side | `src/stage3/costs.py` + `ladder.net_of_costs` + `experiment.step_e` (first design, flat schedule) and `src/stage3/step_e.py` (the one that was run) | the unused one stays importable and still drives the "pending" text in the primary result files | F-20 |
| A-03 | The same rule text in two modules | "unadjustable event" pattern in `stage2/returns.py` and `stage3/ladder.py`; Holm in `intraday/inference.py` and the C2 runner; one-sided test in `step_e.py` and the C2 runner | silent divergence if one copy is edited | F-20 |
| A-04 | Registered hash constants are typed by hand in at least seven places | `protocol.py`, `run_s2_mom_step_e.py`, `run_s2_mom_c2.py`, `build_stage2.py`, `build_manuscript.py`, tests, documents | the registry is the root of trust but is not the single source | F-20 |
| A-05 | Protection lives in the runner script, not in the data-access layer | `run_s2_mom.py::main` holds the gates; `data.load_inputs` and `experiment.*` are open | every other caller bypasses the gates | F-30 |
| A-06 | Runners mix computation, file writing and registration with no transaction boundary | `run_s2_mom.py` lines 96-107; `evaluate_orb_v1.py` lines 244-292 | crash windows between "result readable" and "result registered" | F-08, F-18 |
| A-07 | Research working tree is also the collector's output directory and the web app's data directory | `data/india` | tree always dirty; a web endpoint can overwrite a research input | F-14, F-15 |
| A-08 | Layer separation is otherwise good | ingestion (`stage2/archive`), validation (`panel`, `corporate_actions`), research data (`universe`, `returns`), strategy (`stage3/ladder`), statistics (`stats`), costs (`step_e`), registry, presentation (`research_view`, manuscript) are separate modules with one-way imports, enforced for Stage 3 by an import allow-list test | — | — | — |
