# Pre-release checklist — S2-MOM-v1 (2026-10-08)

One controlled review before the researcher authorises commit and push. During this review nothing was committed, pushed, rerun or regenerated. No frozen protocol, registered result, cost schedule, research input, addendum, supplement or frozen code file was modified.

Labels: **PROVEN BY TEST** · **VERIFIED BY INSPECTION** · **SUPPORTED BY HASH** · **DOCUMENTATION ONLY** · **UNVERIFIED**.

## 1. Working tree

### 1.1 Staged

Before this review: **255 files**, 484,185 lines added, 70 deleted (209 text files, 46 binary). This review adds four files to `docs/audit/` (this checklist, `EXACT_COMMIT_CONTENTS.md`, `F01_CLOSURE_PLAN.md`, `remediation/coverage_summary.json`) and restages regenerated audit reports. The final list, with a SHA-256 for every file, is in `EXACT_COMMIT_CONTENTS.md`.

Each staged file was compared with the pre-remediation snapshot (`docs/audit/remediation/pre_remediation_snapshot.json`):

| Class | Files | Lines + / − | Meaning |
|---|---|---|---|
| EXPERIMENT | 162 | 414,369 / 0 | Never committed before. Content **byte-identical** to the snapshot: `src/stage3/`, the three runners, `build_stage3.py`, S2-MOM tests, cost schedules, addendum and supplements, deviation log, evidence, `data/stage3/` (except the panel), all 18 result files, manuscript |
| RESEARCHER | 2 | 216 / 0 | `RESEARCH_LOG.md`, `registry/trials.jsonl`: earlier uncommitted work, **byte-identical** to the snapshot |
| REMEDIATION: modified existing file | 8 | 496 / 70 | `.gitignore`, `CHANGELOG.md`, `EXPERIMENT_REGISTRY.md` (regenerated), `REPRODUCIBILITY.md`, `registry/experiments.jsonl` (3 lines appended), `requirements.txt` (2 comment lines), `src/registry/experiments.py`, `tests/test_access_boundary.py` (2 allow-list entries) |
| REMEDIATION: regenerated audit report | 8 | 1,580 / 0 | the forensic versions of these files are preserved byte-identical in `docs/audit/forensic_20261007/`; includes `scripts/audit_snapshot.py`, written by remediation before the snapshot was taken |
| REMEDIATION: new file | 57 | 65,287 / 0 | tooling, tests, release files, reports, evidence |
| REMEDIATION: preserved forensic copy | 18 | 2,237 / 0 | `docs/audit/forensic_20261007/*`, byte-identical to the originals |
| **Total** | **255** | **484,185 / 70** | All 70 deleted lines are in `src/registry/experiments.py` (69, the rewritten registry) and `EXPERIMENT_REGISTRY.md` (1, regenerated). No file is deleted or renamed. |

Label: SUPPORTED BY HASH (each file hashed and compared) · VERIFIED BY INSPECTION (classification).

### 1.2 Unstaged (tracked, modified)

| File | Owner | Note |
|---|---|---|
| `server.py` | researcher (UI work) | +22 lines; imports `src/research_view.py` |
| `web/index.html` | researcher (UI work) | the redesigned UI |
| `README.md` | researcher (UI line) + remediation (S2-MOM pointer paragraph) | belongs with the UI commit |
| `data/raw/collection_log.jsonl`, `data/raw/manifest.jsonl`, 58 files `data/india/*` | intraday collector (launchd) | not research evidence of S2-MOM-v1 |

### 1.3 Untracked

`web/classic.html`, `web/css/`, `web/js/` (11 files), `web/mock/` (UI work); `data/india/NSEd1.csv` (written by `/api/add`, legacy). Under research paths: **none** (`tests/test_version_control.py`). Label: PROVEN BY TEST.

### 1.4 Staged files that depend on unstaged files

| Staged file | Depends on | Effect |
|---|---|---|
| `tests/test_ui_api.py` | unstaged `server.py` (new `/api/research` and price endpoints), untracked `web/mock/` | 3 of its 4 tests fail without them |
| `src/research_view.py` | nothing unstaged; it is **used by** unstaged `server.py` | harmless alone, but it is part of the UI change |

Nothing else in the staged set depends on an unstaged or untracked file.

### 1.5 Is the staged set buildable and testable on its own?

Exported to a scratch directory exactly as staged (`git checkout-index`), with the external data added by copy-on-write:

| Variant | Result | Label |
|---|---|---|
| The whole staged set | 958 passed, **3 failed** (`tests/test_ui_api.py`, see 1.4), 3 skipped (version-control guard: not a git checkout); reproduction PASS | PROVEN BY TEST |
| Staged set **minus** `src/research_view.py` and `tests/test_ui_api.py`, as a git repository (scratch, not the user's) | **960 passed, 0 failed, 0 skipped** | PROVEN BY TEST |
| The same, without the external data (what a fresh clone looks like before `materialize`) | 910 passed, 50 skipped (need the data), 0 failed; reproduction **FAIL, closed**: "missing input … panel.parquet" | PROVEN BY TEST |

Conclusion: commit the staged set without those two files, and commit them with the UI work (`EXACT_COMMIT_CONTENTS.md`, `F01_CLOSURE_PLAN.md`). Those two checks ran before this review added its four documentation files; the checks in section 6 ran on the final staged state.

### 1.6 Can any staged change alter a registered research result?

**No.**

1. All 18 registered result files are in class EXPERIMENT: byte-identical. SUPPORTED BY HASH.
2. All frozen research code is byte-identical (37 files pinned by `tests/test_frozen_code.py`). SUPPORTED BY HASH · PROVEN BY TEST.
3. The only changed code reachable from frozen code is `src/registry/experiments.py`. Frozen code uses it in three places:
   - `protocol.registration()` reads `current()`: the record of S2-MOM-v1 gains `anchors` and three history entries; the fields that frozen code reads (`protocol_sha256`, `decisions`, `pending_decisions`, `provenance`) are unchanged;
   - the runners call `amend()` and `log_trial()`: on the FINAL record a new registration is now refused;
   - `data.build()` calls `environment()`: its result goes only into the `build` block of the Stage 3 manifest, which `build()` does not rewrite when the content is unchanged.
   VERIFIED BY INSPECTION; the 58 historical lines fold to the pre-remediation view, PROVEN BY TEST (`test_registered_history_is_pinned_and_folds_to_the_pre_remediation_view`).
4. The reproduction recomputes the registered numbers from the staged code: PASS. PROVEN BY TEST.

### 1.7 Does any staged change modify frozen research evidence?

**No.** Protocol, Addendum 1, Supplements 1–4, cost schedules, Stage 2 tables, Stage 3 inputs, registered results, manuscript and the forensic audit files: all byte-identical (`scripts/audit_snapshot.py verify`: 6,299 of 6,299). The registry changed only by appending three lines; its first 58 lines are byte-identical. SUPPORTED BY HASH.

## 2. Mutation figures in the reports

`MUTATION_FINAL_REPORT.md` and `FINAL_RELEASE_GATE.md` now state the final campaign on its own line:

> **Final mutation campaign (run 3 — the only campaign in the score):** 198 generated · 198 executed · 196 non-equivalent killed · 2 equivalent · 0 survivors · 0 errored · 0 skipped or not applied.

The earlier remediation runs (run 0: disk full; run 1: stopped to change the method; run 2: complete but superseded) are in a separate table with their own counts and appear in no score column. The forensic campaign of 2026-10-07 is column 1 of the score table and is labelled as a different, earlier suite. VERIFIED BY INSPECTION. The generator refuses to write the report if a defined mutation is missing from the final run, appears twice, or is unknown. PROVEN BY TEST (it would raise).

## 3. Manuscript flag: Table A5 omits Supplements 2 and 3

**Question:** are those hashes required by the manuscript or the reproducibility specification?

**Finding: not required.** Classified **DOCUMENTATION ONLY, accepted (N-02)**. The manuscript was not changed.

Why:

1. No specification defines Table A5. The frozen protocol, Addendum 1, the supplements, the results guide and the C2 specification say nothing about it. The table is built from a curated list in `build_manuscript.py` ("SHA-256 values as registered (results guide, C2 specification, deviation log, RESEARCH_LOG.md)"). VERIFIED BY INSPECTION.
2. The release criteria of this remediation concern reproducibility and integrity. Neither depends on the table: both supplements are registered in the registry record (`addenda`) with their SHA-256, both files match, and the reproduction checks them on every run. SUPPORTED BY HASH · PROVEN BY TEST.
3. One sentence of the manuscript ("Hashes are in Appendix Table A5", after naming Supplements 1–4) reads as a promise the table does not keep. That is a presentation defect of a draft.
4. Fixing it means rebuilding the manuscript, which rewrites `manuscript.md`, `.html`, `.docx`, `.pdf` and `number_audit.csv`. Those files are frozen in this pre-release phase.

Recommended for the next manuscript revision: add the two entries to `REGISTERED` in `build_manuscript.py` and rebuild.

A second, related item found in this review: **N-06** (DOCUMENTATION ONLY, accepted). Section 15 of the manuscript says the code, results and manuscript "are not yet committed". True today; stale once F-01 is closed. Fix in the same revision.

## 4. F-01

See `F01_CLOSURE_PLAN.md`. Minimum: two commits and a tag, a push to the existing remote `origin`, the data archive packed onto an external disk, and verification of both copies. Nothing of it has been done.

## 5. Open decisions for the researcher before the push

1. **Visibility of the remote.** `origin` is `github.com/Aaditya07124063/trading-lab`. Whether it is public or private was not checked (no network access was used). The commit contains the manuscript, all registered results and third-party documents archived as cost evidence (`docs/evidence/s2mom_costs/`: SEBI, NSE, CBIC, Zerodha and Wayback captures). The repository already keeps third-party literature PDFs out of Git for copyright reasons (`.gitignore`). Decide whether these evidence files may go to that remote.
2. **Disk space.** 3.4 GB free. No external disk is mounted. The archive (1.55 GB) must go to an external disk or another machine.
3. **Scratch data.** Not deleted, by instruction: about 2 GB of copies from the forensic session (`/private/tmp/claude-501/…/478d767b…/scratchpad`), and this review's scratch export (`/private/tmp/claude-501/…/f8198df2…/scratchpad/staged`, 1.6 GB apparent, mostly copy-on-write clones that share blocks with the repository).

## 6. Checks run on the final staged state of this review

| Check | Result | Label |
|---|---|---|
| Full suite in the repository | 964 passed, 0 failed | PROVEN BY TEST |
| Frozen files | 6,299 of 6,299 byte-identical | SUPPORTED BY HASH |
| Manuscript verification (saved artifacts only) | 59 PASS, 1 FLAG (N-02, accepted), 3 INFO | VERIFIED BY INSPECTION |
| Reproduction | PASS; 117 quantities, 8,257 numbers, all within tolerance; largest difference 6.7e-14 | PROVEN BY TEST |
| External data archive files | 5,637 files identical to the archive manifest | SUPPORTED BY HASH |
| Research experiments rerun | none; trial log byte-identical to the snapshot | SUPPORTED BY HASH |
| Staged after this review | 258 files (255 + 3 new documents of this review); commit 1 of the plan: 256 | VERIFIED BY INSPECTION |
