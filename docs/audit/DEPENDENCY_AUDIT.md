# Trading Lab — dependency and supply-chain audit (2026-10-07)

No package was upgraded, installed into, or removed from the research environment by this audit. (The `coverage` tool was installed into a scratch folder outside the project and outside the Python environment.)

## 1. Exact versions on the audit machine (record these first)

Interpreter: `/opt/anaconda3/bin/python3`, Python 3.13.5, macOS 27.0 arm64.

| Package | Version | Declared in `requirements.txt` | Imported by | Recorded in registry `environment` |
|---|---|---|---|---|
| pandas | 2.2.3 | yes (unpinned) | everything | yes |
| numpy | 2.1.3 | **no** | Stage 2, Stage 3, intraday | yes |
| scipy | 1.15.3 | **no** | `src/stage3/stats.py`, `step_e.py`, `src/intraday/inference.py`, C2 runner | **only in the C2 run** |
| pyarrow | 19.0.0 | **no** | every `read_parquet` / `to_parquet` (Stage 2, Stage 3, step E) | **no** |
| scikit-learn | 1.6.1 | yes | `run_ml.py` (legacy) | yes |
| yfinance | 1.5.1 | yes | collector, `/api/add`, `fetch_data.py` | yes |
| fastapi | 0.139.2 | yes | `server.py` | yes |
| uvicorn | 0.51.0 | yes | running the server | no |
| requests | 2.32.3 | yes | `/api/search` | no |
| httpx | 0.28.1 | yes | FastAPI test client | no |
| pytest | 8.3.4 | yes | tests | no |
| statsmodels | 0.14.4 | **no** | `tests/test_stage3_infra.py` (Newey-West cross-check) | no |
| matplotlib, markdown, lxml, python-docx | not checked | **no** | `docs/manuscript/s2_mom_v1/build_manuscript.py` | no |

## 2. Findings

1. **Nothing is pinned and there is no lock file** (`requirements.txt` is eight bare names). `pip install -r requirements.txt` on another day gives a different environment. Reproducibility risk: byte-level hashes of parquet and CSV files, and last-digit float values, depend on numpy / pandas / pyarrow versions (F-06, F-29).
2. **Three packages used by the registered experiment are not declared:** numpy, scipy, pyarrow. They arrive today only because Anaconda ships them.
3. **The registered runs do not record scipy or pyarrow.** `experiments.environment()` lists five packages chosen for the legacy engine. For primary, sensitivity, confirmation and step E the scipy and pyarrow versions are documented nowhere in the registry. They are recorded in this file as of 2026-10-07; whether the same versions were installed on 2026-10-05/06 is **UNVERIFIED** (very likely, since results still reproduce bit for bit).
4. **A test-only dependency is undeclared:** statsmodels. Without it one Stage 3 test fails.
5. **Declared but unused by the research path:** scikit-learn (legacy `run_ml.py`), yfinance and requests (collector and web UI only). Not harmful; they should live in a separate "app" requirement set so the research environment stays small.
6. **Deprecation in use:** Starlette warns that using `httpx` with its test client is deprecated (one warning in every test run). No effect on results.
7. **Global environment.** The lab runs in the base Anaconda environment, shared with every other project on the machine. A `conda update` for another project changes the research environment without any record.
8. **Network at run time.** `yfinance` and `requests` call Yahoo; `urllib` calls NSE. No research runner (Stage 3, step E, C2) touches the network — VERIFIED BY INSPECTION of imports (`test_g_stage3_code_cannot_reach_collector_intraday_or_orb_files` pins the import list).
9. **No vendored or copied third-party code. No post-install scripts. No private index.** Supply-chain exposure is the ordinary PyPI/conda exposure of the packages above.

## 3. Recommended remediation (no upgrade)

1. Write `requirements-research.txt` with the exact versions in the table (pandas, numpy, scipy, pyarrow, pytest, statsmodels) and `requirements-app.txt` for the rest; keep `requirements.txt` as an include of both. Pin with `==`.
2. Add scipy and pyarrow to `experiments.environment()` (this file is not part of any registered code hash).
3. Record, by a registry amendment with a reason, the environment observed on 2026-10-07 for the already registered runs, labelled "observed after the fact".
4. Create a project virtual environment and point the launchd collector at it.
