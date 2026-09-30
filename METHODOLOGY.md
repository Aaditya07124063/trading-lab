# Methodology

Authoritative description of how the lab produces evidence. Changes to this
file are recorded in [RESEARCH_LOG.md](RESEARCH_LOG.md). Study-specific rules
live in versioned protocols under [docs/protocols/](docs/protocols/).

## Data
RAW → VALIDATION → CLEAN → EXPERIMENT DATASET.
- **Raw** files under `data/` are never modified. New intraday downloads are
  first stored untouched in `data/raw/<provider>/<dataset>/<timestamp>.csv`
  (checksummed in `data/raw/manifest.jsonl`); working files only gain new bars.
- **Validation** (`src/validation/daily.py`, `src/intraday/data.py`) *flags*;
  it never deletes. Extreme moves are often genuine.
- **Clean** = raw minus *reviewed* exclusions in `data/metadata/exclusions.csv`
  (instrument, dates, original values, rule, classification, evidence,
  replacement status, affected experiments). Computed at load time
  (`src/datasets.py`), checksummed, reproducible.
- Cross-validation source: NSE bhavcopy archive (`docs/evidence/`).
- Provenance and licences: [DATA_REGISTRY.md](DATA_REGISTRY.md). Yahoo data is
  for exploratory development only; publication suitability is not established.

## Price basis and cash
- Yahoo daily prices are split/bonus-adjusted, not dividend-adjusted; dividends
  are excluded for strategies AND benchmarks alike.
- Legacy daily experiments: idle cash earns 0%. This is a known bias against
  timing strategies and will be replaced by a documented risk-free series
  (pending - see roadmap).
- Intraday: flat between trades; cash earns 0% intraday (negligible over
  hours; stated explicitly).

## Execution (no look-ahead, enforced in code and tests)
- Daily: signal at close T → fill at open T+1.
- Intraday: strategy sees bars up to the one that just closed; fill at next bar
  open, same session only; entry cutoff; square-off at the 15:15 bar close;
  sessions without a 15:15 bar are not traded.

## Samples and holdout
- Intraday studies split sessions chronologically: development 50% /
  validation 25% / final 25%.
- The final periods of the 2026-04..2026-09 intraday data are **EXPOSED —
  VIEWED FOR RESEARCH/DIAGNOSTIC PURPOSES; NO PARAMETER TUNING PERFORMED.**
- **Clean prospective holdout:** intraday bars from `HOLDOUT_START`
  (2026-10-01, `src/config.py`) onward. Loaders drop them unless a protocol
  whose status is `FROZEN` is named; evaluated once, after freezing.

## Experiments and multiple testing
- Every serious experiment is appended to `registry/experiments.jsonl`
  (fields: [EXPERIMENT_REGISTRY.md](EXPERIMENT_REGISTRY.md)); corrections are
  appended amendments, never edits.
- Every backtest run (CLI or web) is appended to `registry/trials.jsonl`, so
  the number of tests is known for multiple-testing corrections.

## Reporting
- No verdict labels from raw return margins. Results report return,
  volatility, Sharpe, drawdown, costs, benchmark difference, OOS status and -
  once implemented - confidence intervals and tests with stated assumptions.
- Claims follow the specification's claim discipline: "under the tested
  sample and assumptions, the strategy produced ...".
