# Trading Lab — reproducibility audit (2026-10-07)

## 1. What reproduces today, on the audit machine

| Item | Result | Label |
|---|---|---|
| Test suite, twice (real repo and a scratch copy without the raw archive and without git history) | 451 passed both times | PROVEN BY TEST |
| Test suite leaves the repository unchanged (6,975 files hashed before and after) | unchanged | PROVEN |
| Registered A–D monthly returns, δ, H1 statistics, step E costs, from the Stage 3 inputs with independent code | reproduce to ≤ 5e-16 | PROVEN by recomputation |
| Stage 3 inputs and code equal the Stage 3 manifest (`verify_provenance() == []`) | yes | SUPPORTED BY HASH |
| Stage 2 → Stage 3 rebuild (`scripts/build_stage3.py`) | not rerun in this audit | SUPPORTED BY HASH (manifest) |
| Raw NSE files → Stage 2 (`scripts/build_stage2.py`, ~7 min, ~10 GB RAM) | not rerun in this audit; 150/150 on 2026-10-05, log hash registered | SUPPORTED BY HASH + DOCUMENTATION |

## 2. What a second researcher cannot do today

1. **Check out the experiment.** The registry says `freeze_commit` and `environment.git_commit` = `7d4cb6d`. That commit holds the frozen protocol but none of `src/stage3/`, the three runners, their tests, the delivery cost schedule, the addendum and supplements, the Stage 3 inputs or the result files. They exist only as untracked files on one laptop (F-01). `REPRODUCIBILITY.md` tells the reader to "check out its `environment.git_commit`" — for S2-MOM-v1 that yields no experiment code (D-01).
2. **Install the same environment.** `requirements.txt` has eight unpinned names and omits `numpy`, `scipy` and `pyarrow`, all three imported by the experiment code. There is no lock file. The registry `environment` block of the primary, sensitivity, confirmation and step E runs records python, pandas, numpy, scikit-learn, yfinance, fastapi — **not scipy** (p-values, normal quantiles) and **not pyarrow** (parquet read/write, on which the byte-level hashes of Stage 2 and Stage 3 files depend). Only the C2 run recorded scipy (F-06).
3. **Get the data without the network.** `data/raw/nse_archive` (398 MB) and `data/stage2/datasets` (1 GB) are git-ignored. A clean clone must refetch 5,800+ files from NSE; each is hash-checked, so a changed or withdrawn file is detected, but availability is outside the project's control. `data/stage3/.../panel.parquet` is also git-ignored and must be rebuilt (F-05).
4. **Follow a documented S2-MOM procedure.** `README.md`, `REPRODUCIBILITY.md`, `METHODOLOGY.md` and `CHANGELOG.md` do not mention Stage 3 or S2-MOM-v1 (D-01).
5. **Rerun a registered mode.** By design each mode runs once and refuses when its output exists. There is no "verify" mode that recomputes and compares without writing. The only recompute-and-compare path is inside `sensitivity` (primary monthly series, byte-identical). So independent verification needs separate code — this audit's `verify.py` is that code, and it is not in the repository (F-05).

## 3. What can make two runs differ

| Cause | Effect | Present behaviour |
|---|---|---|
| Different numpy / pandas / pyarrow / scipy version, CPU or BLAS | last-digit float differences; different parquet bytes; different CSV text | hash comparisons fail **closed** (rebuild refused, sensitivity refused). No tolerance-based check exists, so a legitimate reproduction on another machine may be rejected (F-29) |
| `datetime.now()` | registry timestamps, `build.built_at`, ORB result folder name | excluded from hashed content (`manifest.json` separates `content` from `build`) — good |
| Random numbers | bootstrap, placebo | fixed seeds (`BOOTSTRAP_SEED = 20261005`; placebo seed derived from seed, date ordinal and step) — deterministic; no global random state is used (VERIFIED BY INSPECTION) |
| Dictionary / set / file-system order | — | every loop over a manifest or directory is sorted; rankings use a stable sort with an explicit tie-break (VERIFIED BY INSPECTION; `test_deterministic`, `test_deterministic_and_independent_of_row_order`) |
| Time zone / locale | none in Stage 2/3 (dates only); collector uses Asia/Kolkata explicitly | VERIFIED BY INSPECTION |
| A new NSE "lists" snapshot (`python -m src.stage2.archive lists`) | `identity._latest()` picks the newest file, so ID-1 inputs change | detected: raw-manifest hash and ID-1 hashes fail in `build_stage2.py` (fail loud) |
| The collector appending to `data/india/*m15.csv` every weekday | working tree is always dirty; `git_dirty` is always true and carries no information | not relevant to S2-MOM inputs (F-15) |
| `TRADING_LAB_NO_TRIAL_LOG` set in the shell | trial not logged | silent (F-11) |
| `python -O` / `PYTHONOPTIMIZE` | structural `assert` checks skipped | silent (F-10) |

## 4. Clean-room reproduction procedure (as it has to be done today)

This is the procedure the audit recommends documenting in `REPRODUCIBILITY.md` once F-01 and F-06 are fixed. Steps marked ⚠ do not work from a clean clone today.

1. **Environment.** macOS arm64 or Linux x86-64. Python 3.13.5. `python3 -m venv .venv && . .venv/bin/activate`.
2. **Dependencies.** ⚠ Install exactly: pandas 2.2.3, numpy 2.1.3, scipy 1.15.3, pyarrow 19.0.0, pytest 8.3.4, statsmodels 0.14.4 (tests), fastapi 0.139.2, httpx 0.28.1, requests 2.32.3, yfinance 1.5.1, scikit-learn 1.6.1. No lock file exists yet.
3. **Source.** ⚠ `git clone` and check out the commit that contains `src/stage3/` and the runners. No such commit exists yet.
4. **Tests.** `python3 -m pytest` → 451 passed.
5. **Raw data.** `python3 -m src.stage2.archive bhavcopy 2005-01-01 2026-09-30`; `… bhavcopy-weekends 2005-01-01 2026-09-30`; `… corporate-actions 1995 2026`. Do **not** run `lists` (it would add a new snapshot); the four list files of the original retrieval date must be obtained from the original archive, because NSE serves only the current version. ⚠ This is a real limit: ID-1 cannot be rebuilt from a fresh download.
6. **Stage 2.** `python3 scripts/build_stage2.py` → "ALL CHECKS PASSED", exit 0 (150 checks). Needs ~10 GB memory.
7. **Stage 3 inputs.** `python3 scripts/build_stage3.py` → "built / verified identical"; then compare `data/stage3/s2_mom_v1/manifest.json` `content` with the registered copy. ⚠ The registered copy is not anchored (F-02).
8. **Verification of results, without rerunning a registered mode.** Run an independent recomputation (the audit's `verify.py`) and compare with `results/s2_mom_v1/*_monthly.csv`, `*_delta.csv`, `*_results.json`, `results/s2_mom_v1_step_e/*_monthly.csv` at a tolerance of 1e-9.
9. **Hash verification.** Compare every file under `results/s2_mom_v1*` with `provenance.*.files_sha256` in `registry/experiments.jsonl`; `GET /api/research` and `tests/test_s2mom_*` do this.

## 5. Dependence on machine state

| Depends on | Where | Risk |
|---|---|---|
| Absolute path `/Users/aadityaadhikari/Projects/trading-lab` and `/opt/anaconda3/bin/python3` | `scripts/collect_intraday.sh`, the launchd plist | collector only |
| Global Anaconda packages (no virtual environment) | everything | a `conda update` changes the research environment silently (F-06) |
| Untracked files | all of S2-MOM-v1 | F-01 |
| Git-ignored files that the runner needs | `panel.parquet`, RET-1.1 parquet (for `with_ret_status`), raw archive | F-05 |
| Shell environment | `TRADING_LAB_NO_TRIAL_LOG`, `PYTHONOPTIMIZE` | F-10, F-11 |
| Google Chrome, `markdown`, `lxml`, `python-docx`, `matplotlib` | manuscript export only | undeclared |
