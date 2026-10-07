# Trading Lab — data flow and hash chain for S2-MOM-v1 (after remediation, 2026-10-07)

The forensic version of this file is kept unchanged in `docs/audit/forensic_20261007/DATA_FLOW.md`. `SYSTEM_ARCHITECTURE.md` describes every arrow in full. This file answers three shorter questions: which file feeds which, which hash protects which file, and where each file is stored.

## 1. Which hash protects which file

Read from the top. A file is trusted only if every link above it holds.

```
 src/registry/experiments.py
   GENESIS_SHA256 8fae608a…5f9d  ── pins lines 1-58 of the registry (history up to 2026-10-07 13:45)
        │
 registry/experiments.jsonl   (lines 59+ carry chain_prev_sha256 = SHA-256 of all bytes before them)
        │
        ├─ protocol_sha256 f1abd954…d838 ──────────▶ docs/research/phase3a_momentum_protocol.md
        ├─ addenda[5].sha256 ──────────────────────▶ Addendum 1, Supplements 1-4
        ├─ universe_sha256 2abf457a…9c42 ──────────▶ data/stage2/universe/univ1_pit_universe.parquet
        ├─ provenance.stage2_rebuild
        │     inputs_sha256 ───────────────────────▶ raw_manifest.jsonl ─▶ 5,560 raw files (per-line sha256)
        │     outputs_sha256 ──────────────────────▶ PANEL-1.1 / RET-1.1 / ID-1 / CA-2 manifests and tables
        ├─ provenance.blinded_precision_artifact_sha256 ─▶ results/s2_mom_v1/blinded_precision.json
        ├─ provenance.primary_run       code_sha256 f57c9321…  files_sha256 (5 files)
        ├─ provenance.sensitivity_run   code_sha256 f57c9321…  results_sha256
        ├─ provenance.confirmation_run  code_sha256 f57c9321…  files_sha256 (5 files)
        ├─ provenance.step_e_run        code_sha256 a6845d30…  files_sha256 (5 files)
        ├─ provenance.c2_run            code_sha256 505b2e4e…  spec_sha256, inputs_sha256 (6), files_sha256 (1)
        │
        └─ anchors                      (added by remediation; can only gain keys)
              stage3_manifest_sha256 6f08fd0f…1fe5 ─▶ data/stage3/s2_mom_v1/manifest.json
              │                                         ├─ outputs_sha256 ─▶ the 8 Stage 3 input files
              │                                         ├─ inputs_sha256  ─▶ UNIV-1, ID-1, ret1_1_manifest, 16 RET-1.1 files
              │                                         └─ code_sha256    ─▶ ladder.py, data.py, protocol.py
              stage3_check_files_sha256 ────────────▶ pre_run_checks_primary.json, pre_run_checks_oos.json,
              │                                         stage2_rebuild_20261005.log
              cost_schedules_sha256 ────────────────▶ delivery_nse_eq_s2mom.json, …_v1_dated.json (47a9bad4…)
              external_archive.manifest_sha256 ─────▶ release/s2_mom_v1/ARCHIVE_MANIFEST.json
              │                                         └─ files{5,637}.sha256 ─▶ raw archive, Stage 2 datasets, Stage 3 panel
              │  external_archive.tar_sha256 bb4b9659…1ac2 ─▶ any copy of the archive tar
              environment_files_sha256_v2 ──────────▶ release/s2_mom_v1/environment.yml, conda-osx-arm64.lock,
                                                        ENVIRONMENT.json, requirements-lock.txt   (supersedes environment_files_sha256)
```

Checked by: `src/registry/experiments.py` (registry), `src/registry/integrity.py::verify_stage3` (manifest chain), `scripts/release_archive.py verify` (archive), `scripts/reproduce_s2_mom_v1.py` (all of it, plus its own independent pins of the protocol, UNIV-1, schedule, C2 specification and the six result hashes).

Links that existed before remediation: protocol, addenda, UNIV-1, Stage 2 rebuild, the five run blocks. Links added by remediation: the pinned history and line chain, and everything under `anchors`.

## 2. Which file feeds which

| # | Reads | Writes | Code |
|---|---|---|---|
| 1 | NSE web | `data/raw/nse_archive/*`, `data/stage2/raw_manifest.jsonl` | `src/stage2/archive.py` |
| 2 | raw archive | `data/stage2/datasets/panel1_1/*`, `data/stage2/panel/*` | `src/stage2/panel.py` |
| 3 | raw archive (corporate actions) | `data/stage2/validation/ca2_*.csv` | `src/stage2/corporate_actions.py` |
| 4 | panel, NSE lists | `data/stage2/identity/id1_*.csv` | `src/stage2/identity.py` |
| 5 | panel, ID-1 | `data/stage2/universe/univ1_pit_universe.parquet` | `src/stage2/universe.py` |
| 6 | panel, ID-1, CA-2 | `data/stage2/datasets/ret1_1/*.parquet`, `data/stage2/returns/*` | `src/stage2/returns.py` |
| 7 | RET-1.1, UNIV-1, ID-1 | `data/stage3/s2_mom_v1/*` (8 files + manifest) | `src/stage3/data.py::build` |
| 8 | Stage 3 inputs | `data/stage3/s2_mom_v1/checks/pre_run_checks_*.json` | `scripts/run_s2_mom.py checks` |
| 9 | Stage 3 inputs | `results/s2_mom_v1/blinded_precision.json` | `… blinded` |
| 10 | Stage 3 inputs | `results/s2_mom_v1/primary_*` (5 files) | `… primary` |
| 11 | Stage 3 inputs, primary files | `results/s2_mom_v1/sensitivity_results.json` | `… sensitivity` |
| 12 | Stage 3 inputs | `results/s2_mom_v1/confirmation_*` (5 files) | `… confirmation` |
| 13 | step D holdings + monthly (both samples), UNIV-1, cost schedule | `results/s2_mom_v1_step_e/*` (5 files) | `scripts/run_s2_mom_step_e.py` |
| 14 | monthly + delta (both samples), primary results, step E results | `results/s2_mom_v1_c2/c2_results.json` | `scripts/run_s2_mom_c2.py` |
| 15 | registered result JSON files | `docs/manuscript/s2_mom_v1/*` | `build_manuscript.py` |
| 16 | everything above, read-only | nothing | `scripts/reproduce_s2_mom_v1.py`, `scripts/verify_manuscript.py` |

Rows 8–14 each ran once and are registered. None was run again during remediation: the trial log still has exactly five `s2_mom_v1` entries (primary, sensitivity, confirmation, step E, C2), and the reproduction fails if it finds a sixth.

## 3. Where each file is stored

| Kind | Where | In Git | In the external archive |
|---|---|---|---|
| Research code, runners, tests | `src/`, `scripts/`, `tests/` | yes (staged; commit deferred) | no |
| Protocol, addendum, supplements, deviation log, specifications | `docs/research/` | yes | no |
| Cost schedules and their evidence | `config/cost_schedules/`, `docs/evidence/s2mom_costs/` | yes | no |
| Registry and trial log | `registry/` | yes | no |
| Registered results (18 files, 63 MB) | `results/s2_mom_v1*/` | yes | no |
| Stage 2 manifests, ID-1, UNIV-1, validation tables | `data/stage2/` (except `datasets/`) | yes | no |
| Stage 3 inputs except the panel, manifest, check files, rebuild log | `data/stage3/s2_mom_v1/` | yes | no |
| Stage 3 daily panel (53 MB) | `data/stage3/s2_mom_v1/research/panel.parquet` | no | yes |
| Stage 2 datasets (1.0 GB) | `data/stage2/datasets/` | no | yes |
| Raw NSE archive (398 MB) | `data/raw/nse_archive/` | no | yes |
| Archive manifest, environment specification | `release/s2_mom_v1/` | yes | — |
| Manuscript | `docs/manuscript/s2_mom_v1/` | yes | no |

Rule enforced by `tests/test_version_control.py`: no file under a research path may be untracked, and every ignored file under a research path must be listed in the archive manifest. A file that is "just ignored" fails the suite.

To restore the external files on another machine:

1. Clone the repository.
2. Obtain `s2-mom-v1-data-baa0b47040101031.tar` (1,552,240,640 bytes).
3. `python3 scripts/release_archive.py materialize <path to the tar>` — checks the tar hash, then every file hash, and never overwrites an existing file.
4. `python3 scripts/reproduce_s2_mom_v1.py`.

## 4. Trust boundaries (untrusted → trusted) and what stands at each

| Boundary | Check | Fails how |
|---|---|---|
| NSE response → raw archive | cutoff, HTTP status, hash recorded | raises; **content type not checked (F-16)** |
| raw file → Stage 2 | SHA-256 = raw manifest | raises |
| Stage 2 file → Stage 3 | SHA-256 = RET-1.1 manifest, UNIV-1 pin | raises |
| Stage 3 file → ladder | registry anchor → manifest → file; then `validate_stage3` (values) | `ProvenanceError`, `ValidationError` |
| protocol, schedule → code | SHA-256 pinned in code, registry and reproduction script | `ProtocolMismatch`, `CostScheduleError`, FAIL |
| result file → reader | SHA-256 = registry `files_sha256` | `NotReady`, FAIL |
| registry line → current view | pinned history, chain, state machine, protected fields | `RegistryError` |
| archive tar → working tree | tar hash, member list, per-file hash, no overwrite | `ArchiveError` |
| environment → run | pinned versions; `python -O` refused by the reproduction | FAIL, or a visible "DIFFERS" note |
| command line → runner | fixed words only; no path or date arguments | usage text, exit ≠ 0 |
