# Stage 2 research architecture — proposed (DESIGN ONLY, not implemented)

**Date:** 2026-10-03
**Constraints:**
- ORB v1 (protocol, rules, evaluator, holdout data, status/protection, universe, costs, statistics, portfolio definition) is untouched.
- No October 2026+ data is read.
- No new experiments, no ORB tuning, no ML.

## 0. Inspected facts that shape the design

| Fact | Consequence |
|---|---|
| 15-min data before the cutoff: 4 stocks from 2026-04-23, 46 from 2026-08-03 (42 sessions) | Stage 2 **historical** research must be **daily-frequency**. Intraday Stage 2 is data-starved, so it is postponed |
| Daily files: RELIANCE/TCS/HDFCBANK/INFY (decades, with reviewed exclusions), NIFTY50 (2007+), SENSEX; NIFTY50d1 ends 2026-07-17 | Four hand-picked survivors cannot support cross-sectional research. A **survivorship-free daily panel** is needed |
| Validated NSE sources already used: CM bhavcopy archives (EQ series), index-close archives, holiday master | The official bhavcopy panel includes delisted names, so it is point-in-time by construction |
| Shared core exists: cost model, fixed-notional maths, null-centred stationary bootstrap, Holm, DSR, registries, calendar | Stage 2 **reuses** these and adds only daily-frequency pieces |
| `load_intraday(holdout_protocol=…)` opens the holdout whenever ORB_v1.md is FROZEN (true now) | Stage 2 must have its **own** cutoff-enforcing loader. The holdout gate needs the authorisation requirement (holdout_ops_design §A.3) |
| Dashboard `/api/add` + `/api/backtest` can fetch and test daily data up to today | The dashboard must enforce the research cutoff, or Stage 2 must not use it |
| Legacy daily experiments (EMA, momentum on 4 stocks, RandomForest ML) exist in the registry | Status LEGACY / not evidence. Stage 2 starts its own pre-registered program |

## A. Proposed architecture

### A1. Separation (four zones)

| Zone | Code | Data | Status |
|---|---|---|---|
| **1. Frozen ORB v1** | `src/intraday/{orb,engine,inference,portfolio,calendar,bhavcopy_check,regimes,data}.py`, `evaluate_orb_v1.py`, `docs/protocols/ORB_v1.md` | — | **Read-only.** A *frozen-code guard test* pins the SHA-256 of these files at the freeze commit. Any edit fails CI, so Stage 2 adds new modules instead of editing these |
| **2. Prospective holdout** | collector, `holdout_status.py`, VPS deployment | 15-min data ≥ 2026-10-01 | Collected, never analysed. Opened only by the authorised evaluator |
| **3. Stage 2 historical research** | `src/stage2/**`, `docs/stage2/**`, `run_stage2.py` | Daily panel ≤ **2026-09-30** (research cutoff) | Active |
| **4. Paper / live execution** | `paper_bot.py` (dormant), future `src/execution/` | Live | **Postponed.** Never imports Stage 2 or ORB research code paths that read holdout data |

### A2. Stage 2 module structure (minimum new code; reuse the core)

```
src/stage2/
  data.py         cutoff-enforced loaders (RESEARCH_CUTOFF = 2026-09-30; raises on any later date)
                  daily panel from stored NSE bhavcopies; PIT liquidity universe
  universe.py     point-in-time universe rule (e.g. top-N EQ by trailing 63-day median traded value)
  engine.py       daily cross-sectional engine: target weights at close t -> trade at open t+1,
                  fixed notional, delivery-cost schedule, integer shares; reuses intraday cost formulas
  experiment.py   ExperimentSpec (JSON) -> run(spec) -> read-only artifacts + manifest + registry record
  strategies/     one small module per family: signal(panel_up_to_t, params) -> weights_t
docs/stage2/protocols/S2-<family>-v1.md     pre-registered, DRAFT -> FROZEN (same discipline as ORB)
config/cost_schedules/zerodha_nse_eq_delivery_<date>.json   (new; delivery costs differ: STT both sides, DP charge)
results/stage2/<experiment_id>/             read-only artifacts + manifest.json
registry/experiments.jsonl                  shared, append-only (adds a "stage" field)
data/stage2/                                stored bhavcopy extracts + checksums (data/raw/nse_bhavcopy cache)
tests/test_stage2_*.py                      incl. cutoff guard, no-holdout-import guard, frozen-code guard
```

### A3. Generic experiment interface

```
strategy module:  PARAMS_SCHEMA = {...}
                  def signal(panel: Panel, t: date, params) -> pd.Series   # weights, sum |w| <= 1
                  # receives ONLY panel rows dated <= t (the engine slices; strategies cannot look ahead)
experiment:       spec = ExperimentSpec.load("docs/stage2/specs/<id>.json")
                  result = run(spec)   # engine -> portfolio daily returns -> inference -> baselines
```

- One engine and one inference path serve every family. Families differ only in `signal()`.
- Factor research is `signal()` returning long-short ranks. Regime research is a pre-specified **conditioning** layer applied to existing signals (reporting).
- ML later plugs in as a `signal()` whose fit uses only the training window (walk-forward), with no interface change.

## B. Research workflow (per study)

1. **Question and literature note** (`docs/stage2/literature/`), with source-supported claims marked separately from our inference.
2. **Pre-registered protocol** (DRAFT): hypothesis, universe rule, data period and splits, parameters (from literature, not search), costs, benchmark, baselines, statistics, verdict rule, power/MDE from the development split only.
3. **Implementation + tests on synthetic data**, then a **dry run on the development split only**.
4. **Freeze the protocol** (your approval) → run the **test split once** → read-only artifacts → registry FINAL.
5. **Optional prospective holdout** for the study, starting after its freeze and evaluated only after its pre-registered end, and only after the ORB v1 final evaluation (§D, R7).
6. **Report every result** (positive, negative, inconclusive) in `RESEARCH_LOG.md` and the experiment registry.

## C. Experiment schema (extends the existing `REQUIRED` fields)

```json
{
  "experiment_id": "S2-MOM-20261015-001",
  "stage": "stage2", "family": "momentum", "status": "PLANNED|DIAGNOSTIC|FINAL|...",
  "protocol_file": "docs/stage2/protocols/S2-MOM-v1.md", "protocol_sha256": "...",
  "research_question": "...", "hypothesis": "...", "null_hypothesis": "...",
  "universe": {"rule": "top-100 EQ by trailing 63d median traded value", "snapshot_sha256": "..."},
  "data": {"source": "NSE CM bhavcopy", "cutoff": "2026-09-30",
           "dataset_checksums": {"<file>": "<sha256>"}},
  "splits": {"development": ["2005-01-01","2016-12-31"], "validation": ["2017-01-01","2020-12-31"],
             "test": ["2021-01-01","2026-09-30"], "test_viewed": false},
  "strategy": {"module": "src/stage2/strategies/momentum.py", "params": {"lookback": 252, "skip": 21}},
  "execution": {"signal": "close t", "fill": "open t+1", "sizing": "fixed notional", "capital": 5000000},
  "cost_model": {"schedule": "zerodha_nse_eq_delivery_<date>.json", "sha256": "...", "slippage_bps": 5},
  "benchmark": "equal-weight universe buy-and-hold (context)",
  "statistics": {"primary": "null-centred stationary bootstrap, PW block, one-sided alpha 0.05",
                 "family_correction": "Holm", "dsr": "reporting only"},
  "random_baselines": ["random-sign", "random-portfolio (same turnover/exposure)"],
  "seeds": {"bootstrap": 0, "baselines": 0},
  "artifacts": {"dir": "results/stage2/<id>/", "manifest_sha256": "..."},
  "git_commit": "...", "git_dirty": false, "environment": {"python": "...", "packages": {}},
  "viewed_before_finalization": "...", "parent_experiment": null, "variant_of": null,
  "trial_count_at_run": 0
}
```

- `variant_of` and `trial_count_at_run` make the **program-wide** multiple-testing count explicit, which feeds the DSR and the family definitions.

## D. Data-boundary rules (Stage 2)

| # | Rule | Enforcement |
|---|---|---|
| R1 | **Research cutoff 2026-09-30** for every instrument and frequency. Until the ORB v1 final evaluation, all post-cutoff market data is reserved for collectors and locked evaluators | `src/stage2/data.py` raises on any later row. Dashboard endpoints get the same cutoff **[change to server.py, approval needed]** |
| R2 | Stage 2 never imports `evaluate_orb_v1`, never passes `holdout_protocol`, never reads `results/orb_v1_*`, `holdout_mirror/` or collection logs | Guard test (static scan of `src/stage2`, `run_stage2.py`) |
| R3 | Frozen ORB v1 files are never edited | Frozen-code SHA-256 guard test |
| R4 | Chronological splits (development / validation / test) are fixed in the protocol **before** any data is viewed. Test is viewed **once**, after freeze | Spec field `test_viewed`; the runner refuses test-split runs unless the protocol is FROZEN |
| R5 | Parameters come from literature or the development split only. Every variant run is registered (`variant_of`), and no silent best-of selection | Registry + trial log; DSR uses the program-wide count |
| R6 | Point-in-time everything: universe membership, liquidity filters, corporate-action adjustments and regimes use only data ≤ t | Engine slices panel ≤ t; unit tests with a planted future shock |
| R7 | Stage 2 prospective holdouts may *collect* after their own freeze, but are *evaluated* only after their pre-registered end **and** after the ORB v1 final evaluation | Same authorisation-file gate pattern |
| R8 | The legacy ML/EMA/4-stock momentum experiments stay LEGACY and are not reused as evidence | Registry status |

## E. Research order and December 2026 milestones

**Recommended order** (each step justified by data availability and literature strength, not expected returns):
1. **Data foundation:**
   - survivorship-free NSE daily panel from bhavcopies;
   - PIT liquidity universe;
   - delivery cost schedule;
   - corporate-action handling. Proposal: daily return = ClsPric / PrvsClsgPric − 1, since NSE adjusts the previous close on ex-dates. **To verify empirically on known splits/bonuses before use.**
2. **Descriptive baselines and regime description:** no strategy; a market-state "atlas" that later studies can condition on.
3. **Cross-sectional momentum (12-1):** the strongest literature, with Indian evidence to review. First pre-registered Stage 2 study.
4. **Short-term reversal (1 week / 1 month):** the mean-reversion family; the opposite horizon; highly cost-sensitive, a good test of the cost machinery.
5. **Breakout, daily (52-week high, Donchian):** connects to ORB as "breakout across horizons".
6. **Price-based factors (low volatility, beta):** factor research without fundamentals.
7. **Regime conditioning** of 3–6: exploratory, pre-specified conditioning variables.
8. **ML:** last, after linear baselines, with walk-forward fits and the full registry.

**By December 2026 (Trading Lab v1):**

| Week | Milestone |
|---|---|
| Oct (now → mid-Oct) | Approve designs. Holdout ops deployed on the VPS. Stage 2 skeleton + guard tests (cutoff, no-holdout import, frozen-code hash) |
| Oct–Nov | Bhavcopy panel: 2005→2026-09-30, checksums, validation, corporate-action verification. PIT universe. Delivery costs. Daily engine + tests |
| Nov | Momentum literature note + protocol S2-MOM-v1 (DRAFT) with dev-split power/MDE; dry run on development |
| Late Nov | Freeze S2-MOM-v1 (your approval) → single test-split evaluation → report |
| Dec | Reversal protocol (S2-REV-v1) drafted and, if time permits, frozen and evaluated. Paper outline + methods chapter (shared ORB/Stage 2 methodology) |

**Explicitly postponed until after December 2026:**
- ML of any kind;
- intraday Stage 2 (insufficient pre-cutoff 15-min data);
- fundamental factors (no licensed fundamentals);
- regime-conditional strategies as confirmatory claims;
- paper/live trading and broker integration;
- Stage 2 prospective holdouts' evaluation;
- the ORB v1 final evaluation (about Oct 2027, on your authorisation);
- any publication claims.

## F. Risks and controls

| Risk | Control |
|---|---|
| Holdout leakage through shared loaders or the dashboard | R1/R2 guards; authorisation gate; dashboard cutoff |
| Accidental edits to frozen ORB code while building Stage 2 | Frozen-code SHA-256 test; Stage 2 adds modules only |
| Survivorship bias | Bhavcopy panel (includes delisted names); PIT liquidity universe rather than today's index list |
| Corporate-action errors in daily returns | Verify the PrvsClsgPric approach on known events; flag-and-exclude rules pre-registered; no silent repair |
| Specification search / p-hacking across families | Pre-registered protocols; program-wide trial count; Holm within families; DSR reporting |
| Costs understated (delivery vs intraday) | Separate delivery schedule from published sources; slippage grid; break-even reporting |
| Data-source drift or outages (NSE archive format changes) | Stored raw files + checksums; parsing tests per format era |
| Scope creep before December | Milestone table; postponed list; one family frozen at a time |
| Over-interpreting a single historical test split | Report as historical out-of-sample only; prospective holdouts later |

## G. How the paper connects the experiments

**Working thesis:** *Do simple, well-documented price-based trading rules survive realistic Indian costs, point-in-time universes and pre-registered, out-of-sample testing?*

- **Part I (prospective):** ORB v1, intraday, NIFTY 50, a 250-session forward holdout. The cleanest test, pre-registered before data existed.
- **Part II (historical out-of-sample):** daily momentum, reversal, breakout and low-volatility on a survivorship-free NSE panel, each pre-registered before its test split was viewed.
- **Shared methods chapter:**
  - fixed-notional portfolios;
  - published Indian cost schedules and break-even slippage;
  - null-centred dependence-aware bootstrap;
  - random baselines;
  - the program-wide multiple-testing ledger (registry), plus the DSR.
- **Contribution claims stay evidential:** what survives and what doesn't. Null results are reported with equal weight. No novelty claim beyond the documented gaps (see `docs/literature/ORB_research_gap_analysis.md`).
