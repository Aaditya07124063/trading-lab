# S2-MOM-v1 — C2 analysis specification: seven pre-registered analyses executed late

**Status:** APPROVED by the reviewer on 2026-10-07. Written and hashed before any of the analyses below was computed. Its SHA-256 is recorded in the runner (`scripts/run_s2_mom_c2.py`), in `registry/experiments.jsonl` (record `S2-MOM-v1`) and in `RESEARCH_LOG.md`.

**Parent protocol:** `docs/research/phase3a_momentum_protocol.md`, frozen, SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`. This file is separate. The frozen protocol, its addendum and supplements, the cost schedule and every registered result file are not edited.

## 1. Timing statement (travels with every result that uses this file)

**These analyses were pre-registered in the frozen protocol but executed late, after the primary, sensitivity, confirmation and step E results were already known.** They are not blind and not confirmatory. No backtest is rerun: every number is computed from the saved, registered result files listed in section 3.

Known when this was written: every registered figure of S2-MOM-v1, including the mean of each ladder step, the primary estimand, the step differences, the sensitivity results, the confirmation results and the step E results. In particular the means of `W_A` and `W_D` were known, so the sign and size of the H2d estimate were known; its standard error was not.

Not computed when this was written: the H2d standard error, t-statistic and p-value; any Holm-adjusted p-value; any Benjamini–Hochberg q-value; any figure for a half of the primary sample; any pooled standard error or t-statistic; any skewness; any worst month.

Choices made after results were known, all by rule and none by inspection of an outcome:
- the lag for the two halves (section 5);
- the Benjamini–Hochberg family (section 7);
- the skewness estimator (section 8).

## 2. Scope

Computed (reviewer decision of 2026-10-07):
1. H2d (frozen §3).
2. Holm adjustment of H2a–H2d (frozen §17).
3. Benjamini–Hochberg q-values (frozen §17).
4. The two halves of the primary sample (frozen B3, §16 R-half).
5. The pooled 170 months, gross A–D and δ only, descriptive, appendix only (frozen B3, §16 R-pool).
6. Skewness (frozen §14).
7. Worst monthly return (frozen §14).

Not computed here, by the same decision: step-D capacity; H5 and its robustness; R-JK; R-skip; R-bp; R-wt; R-entry; R-cost; R-mono; R-ext; holding periods longer than one month; the deflated Sharpe ratio; H4 under the sensitivity treatments; the stationary bootstrap for any test other than H1; the middle portfolio; the monotonicity figure; halves of the confirmation sample; turnover at steps A–C; any pooled step E (net) figure. These are disclosed in the deviation log (DEV-2).

## 3. Inputs (read-only; all six hash-checked before any is read)

| # | Path | SHA-256 | Used for |
|---|---|---|---|
| 1 | `results/s2_mom_v1/primary_monthly.csv` | `f7c8d3ab5a0ef7a08b6a0ca8a12bf26a1f901006c21637cf7886e297b97bb372` | monthly W, L, BM, WML of steps A–D, primary |
| 2 | `results/s2_mom_v1/confirmation_monthly.csv` | `4d88f385375ad681f85be739b292097e2e898acb6acb71013230c67415a43ce3` | the same, confirmation |
| 3 | `results/s2_mom_v1/primary_delta.csv` | `2efa04351a6bca10fbf1e6a96d6c5240fb0f2570420185250750b77d5c4fecc9` | integrity guard on δ |
| 4 | `results/s2_mom_v1/confirmation_delta.csv` | `a462455acb343910a02206ab6af50582eaedef20b0ed6cec81a88f73cbc58b75` | integrity guard on δ |
| 5 | `results/s2_mom_v1/primary_results.json` | `fe7e95ba97482d6d53faba543d860e4f0d1e50cfa0312d669e910346d41ef857` | registered p-values of H2a, H2b, H2c; integrity guards |
| 6 | `results/s2_mom_v1_step_e/step_e_results.json` | `675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0` | registered one-sided p-values of H3 and H4, primary |

If any hash differs the runner refuses and calculates nothing. No other file is read as data. No raw market data, no RET-1.1, no UNIV-1, no holdings file and no cost schedule is read. The backtest and ladder code (`src/stage3/ladder.py`, `experiment.py`, `data.py`, `step_e.py`) is not called.

The only registered code that is reused is the frozen statistics function `src.stage3.stats.mean_test` (imported, not modified), so the Newey–West calculation is the registered one.

## 4. Series and units

- Monthly files: one row per (`holding_month`, `step`), `step` ∈ {A, B, C, D}; columns `W`, `L`, `BM`, `WML` are monthly returns as fractions. Rows are ordered by `holding_month`.
- Every reported figure is in **percent per month** = 100 × the fraction.
- `X_k(t)` = column `X` of step `k` in holding month `t`.
- `δ(t) = 100 × (WML_A(t) − WML_D(t))` (frozen §2).
- Step differences on WML: `A−B`, `B−C`, `C−D`, each `100 × (WML_i(t) − WML_j(t))`.
- H2d series: `h(t) = 100 × (W_A(t) − W_D(t))`.

## 5. Samples and Newey–West lags

Lag rule of frozen §15: `floor(4 · (T/100)^(2/9))`.

| Block | Holding months | T | Lag | Source |
|---|---|---|---|---|
| `primary` | 2012-07 → 2021-12 | 114 | 4 | input 1 |
| `confirmation` | 2022-01 → 2026-08 | 56 | 3 | input 2 |
| `primary_half_1` | 2012-07 → 2017-03 | 57 | 3 | input 1 |
| `primary_half_2` | 2017-04 → 2021-12 | 57 | 3 | input 1 |
| `pooled` | 2012-07 → 2026-08 | 170 | 4 | inputs 1 and 2, concatenated in date order |

- The halves are the frozen ones of B3. Frozen §15 lists lags only for T = 114, 170 and 56; the lag for T = 57 is the frozen formula applied: `4 · 0.57^(2/9) = 3.53`, floor 3.
- The confirmation sample is **not** split.
- The pooled block is descriptive only and is never called confirmatory (frozen B3). It covers gross A–D returns and δ. No pooled step E, net-return, cost, H3, H4 or break-even figure is computed.
- Each block is analysed on its own months; no observation outside the block enters its autocovariances.

## 6. Tests

**Mean test (all blocks).** `mean_test(x, lag)` of `src/stage3/stats.py`: mean; Newey–West standard error (Bartlett kernel, autocovariances divided by n); `t = mean / se`; two-sided p and 90% interval from the standard normal distribution (registered reviewer decision 5).

**H2d.** H0: mean of `h` ≤ 0. H1: mean of `h` > 0 (frozen §3, one-sided).
- Primary sample (the test): lag 4. `p_one_sided = 1 − Φ(t)`. Raw decision at α = 0.05; the decision that counts is the Holm one (section 7).
- Confirmation sample: the same statistic with lag 3, reported with the confirmation status of frozen B3:
  - `CONFIRMED` — same sign as the primary mean and one-sided p < 0.05;
  - `CONSISTENT, NOT CONFIRMED` — same sign, p ≥ 0.05;
  - `NOT CONFIRMED` — opposite sign.
- H2d is not computed for the halves or the pooled block.

## 7. Multiple testing (primary sample only)

**Holm (frozen §17: H2a–H2d, family α = 0.05).** The four p-values:

| Hypothesis | p-value used | Source |
|---|---|---|
| H2a (`A−B`) | two-sided, as registered | input 5, `step_differences_pct["A-B"].p_two_sided` |
| H2b (`B−C`) | two-sided, as registered | input 5, `["B-C"]` |
| H2c (`C−D`) | two-sided, as registered | input 5, `["C-D"]` |
| H2d | one-sided | section 6 |

Sort ascending `p_(1) ≤ … ≤ p_(m)`, m = 4. `adj_(i) = max over j ≤ i of min(1, (m − j + 1) · p_(j))`. Rejected if `adj < 0.05`.

**Benjamini–Hochberg (frozen §17: "q-values are shown beside every secondary p-value").** The family is the six secondary tests that were executed, in the primary sample: H2a, H2b, H2c (two-sided, input 5), H2d (one-sided, section 6), H3 and H4 (one-sided, input 6, `samples.primary.H3.p_one_sided` and `.H4.p_one_sided`). m = 6. `q_(i) = min over j ≥ i of min(1, m · p_(j) / j)`.
- H1 is the primary test and is not in the family.
- H5 is a pre-registered secondary test that was not executed. It is absent from the family; with it, m would have been 7. This is disclosed with every q-value.
- The q-values are shown for information. They decide no hypothesis; the frozen decision rules are Holm for H2 and the fixed sequence for H3 → H4.

## 8. Descriptive statistics (every block; steps A–D; W, L, BM, WML)

For each series `x` in percent:
- `n`; `mean_pct`; `sd_pct` (sample standard deviation, divisor n − 1, as registered); `t_nw` and `p_two_sided` from the mean test with the block's lag;
- `skewness`: adjusted Fisher–Pearson sample skewness, `G1 = sqrt(n(n−1)) / (n−2) · m3 / m2^1.5` with `m_k` the k-th central moment divided by n (`scipy.stats.skew(x, bias=False)`);
- `worst_month_pct`: the minimum of `x`; `worst_month`: its `holding_month` (the earliest if tied).

For the worst month of WML the figure is the worst winner-minus-loser month, not a portfolio loss that could be realised.

Also for every block: the mean test of δ and of the three step differences (two-sided, block lag).

Steps A, B and C are biased by construction (frozen B1.5 guard); their figures measure error and are not evidence about momentum.

## 9. Missing values and integrity guards (fail closed; nothing is imputed)

The runner stops, writes nothing and registers nothing if:
- an input hash differs;
- a monthly file does not have exactly the steps A–D for exactly the expected months (114 or 56), or has a duplicate (`holding_month`, `step`), a `status` other than `OK`, or a missing value in `W`, `L`, `BM` or `WML`;
- the recomputed `δ(t)` differs from the `delta` column of input 3 or 4 by more than 1e-9 in any month;
- for the primary block, the recomputed mean or t of δ, `A−B`, `B−C` or `C−D`, or the mean of any ladder series, differs from input 5 by more than 1e-9;
- the output directory, or a partial one, already exists.

Empty count columns of the monthly files (for example `W_filled_stock_days`) are not read.

## 10. Output

One file, in a new directory outside the registered results: `results/s2_mom_v1_c2/c2_results.json`. No existing file is changed. Deterministic: no randomness, no clock, no environment field in the file.

Schema:

```
{
 "statement": str,                        # the timing statement of section 1
 "spec_sha256": str,
 "inputs_sha256": {path: sha256},
 "blocks": {
   <block>: {                             # primary, confirmation, primary_half_1, primary_half_2, pooled
     "months": [first, last], "n": int, "lag": int,
     "delta": {n, mean, se_nw, t, p_two_sided, lag, ci90, distribution},
     "step_differences_pct": {"A-B": {...}, "B-C": {...}, "C-D": {...}},     # same fields as delta
     "ladder": {<step>: {<portfolio>: {n, mean_pct, sd_pct, t_nw, p_two_sided,
                                        skewness, worst_month_pct, worst_month}}}
   }
 },
 "H2d": {
   "primary":      {n, mean, se_nw, t, p_two_sided, lag, ci90, distribution, p_one_sided},
   "confirmation": {... same ...},
   "confirmation_status": "CONFIRMED" | "CONSISTENT, NOT CONFIRMED" | "NOT CONFIRMED"
 },
 "holm": {"family_alpha": 0.05, "m": 4,
          <H2a|H2b|H2c|H2d>: {"p": float, "sided": "two"|"one", "p_holm": float, "rejected": bool}},
 "benjamini_hochberg": {"m": 6, "note": str,
          <H2a|H2b|H2c|H2d|H3|H4>: {"p": float, "sided": "two"|"one", "q": float}}
}
```

## 11. Execution and registration

- Code: `scripts/run_s2_mom_c2.py` (one file); tests on made-up series in `tests/test_s2mom_c2.py`.
- Command: `python3 scripts/run_s2_mom_c2.py execute`, run once. It refuses if the output exists.
- The runner checks the SHA-256 of this specification and of the frozen protocol before anything else.
- Registered only after the output is complete and hashed: one registry amendment (`provenance.c2_run`: specification hash, code hash, input hashes, output hash, environment) and one line in `registry/trials.jsonl`.
- A rerun is permitted only after a genuine execution error, and must be recorded.
