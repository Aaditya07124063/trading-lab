# ORB v1 — pre-freeze audit (2026-10-01 decisions, audited 2026-10-02)

**Status:** AUDIT — ORB v1 is **NOT FROZEN**.
- `docs/protocols/ORB_v1.md` is still the 2026-09-30 DRAFT.
- On approval, §A below replaces its body and the status line becomes `FROZEN (commit <hash>, date)`.
- Stage 2 has not started.
- No holdout performance has been computed.

**Supersedes:** `ORB_v1_final_review_20261001.md` wherever they differ (OPEN-1, 2, 4–12 resolved by the 2026-10-01 approvals).

**Code at audit:** `8d21e3e`.

---

## A. Frozen-protocol candidate

| # | Element | Rule |
|---|---|---|
| A1 | Question | Does the predefined ORB strategy produce positive mean daily net returns, after realistic costs and slippage, as an equal-weighted portfolio across the frozen NIFTY 50 universe? |
| A2 | Hypothesis | **H1:** μ > 0 vs **H0:** μ ≤ 0. μ = expected daily portfolio net return R_t (A12) at the primary cost scenario. One-sided, α = 0.05. |
| A3 | Universe | NIFTY 50 constituents frozen 2026-10-01 08:26 IST.<br>File `data/metadata/universe/NIFTY50_frozen_20261001.json`; raw-file SHA-256 verified at run time.<br>N = 50; never updated; never substituted. |
| A4 | Data | Yahoo 15-min OHLCV, bar-start IST, from the append-only logged collector (provider unchanged).<br>Validation by `load_intraday`; hard errors stop the run (A24-7). |
| A5 | Development | All bars < 2026-10-01. Status EXPOSED / DIAGNOSTIC (LEGACY-014/015, ORBV1-20261001-001, ORBV1-20261002-001). |
| A6 | Holdout | The **first 250 standard NSE sessions on or after 2026-10-01** (A13-6).<br>2026 contributes 61 (2026-10-01..2026-12-31); 189 fall in 2027.<br>Evaluated **once**, after all 250 are collected.<br>Data stay locked (`load_intraday`) until FROZEN. |
| A7 | Opening range | 09:15 and 09:30 bars. OR_HIGH = max high; OR_LOW = min low. |
| A8 | Breakout | The first **completed** bar at or after 09:45 whose **close** is above OR_HIGH (long) or below OR_LOW (short). One signal per stock per day. |
| A9 | Entry | **Open of the next bar** after the signal bar (earliest 10:00). No fill after 14:30. One trade per stock per day. |
| A10 | Exit (X2) | **Open of the 15:00 bar.**<br>Never used: the 15:00 high/low/close, the 15:15 bar, the closing-auction price.<br>No overnight positions. |
| A11 | Sizing | K = ₹1,00,000 per stock per session. qty = largest integer with qty × entry_fill + entry charges ≤ K. No leverage, no reinvestment. |
| A12 | Portfolio | **R_t = Σ_{i=1}^{50} NetPnL_{i,t} / (50 × 1,00,000)** over every holdout session t, including zero-trade sessions (§D). |
| A13 | Missing data | §E. |
| A14 | Corporate events | §E-8. |
| A15 | Costs | Zerodha NSE equity-intraday schedule `zerodha_nse_eq_intraday_20260930.json`.<br>Brokerage: min(₹20, 0.03 %) per order. STT: 0.025 % sell. Exchange: 0.00307 %. SEBI: 0.0001 %. Stamp: 0.003 % buy. GST: 18 % on brokerage + exchange + SEBI. |
| A16 | Slippage | **Primary: 5 bps per side**, adverse, on entry and exit.<br>Sensitivity: 0 / 2 / 10 / 20 bps, GROSS, U-5, and K = ₹10 lakh. |
| A17 | Benchmarks | **Context only.**<br>A: open-to-close long, 09:15 open → 15:00 open, same sessions, costs and K.<br>B: long-only ORB.<br>Neither enters the verdict. |
| A18 | Random baselines | §C3. |
| A19–21 | Statistics, CIs, multiple testing | §C. |
| A22 | Power | §F. |
| A23 | Regimes | Exploratory. Definitions in `src/intraday/regimes.py`. **Index-close source: OPEN (§I-1)**; not run until approved. |
| A24 | Robustness | The sensitivities listed in A16 and §C5. None can change the verdict or the protocol. |
| A25 | Reporting | Everything in `summary.json` (§G), whatever the result. All deviations stated. Negative and inconclusive results get equal prominence. |
| A26 | Reproducibility | §H. |
| A27 | Verdict labels | §C4. Reporting categories only; no scoring. |

**Implementation constraint (documented, not a research rule):**
- NSE CAS (SEBI circular, 16 Jan 2026): continuous trading for F&O stocks ends at 15:15; auction 15:15–15:35.
- Broker MIS square-off for CAS stocks: Zerodha 15:12, Upstox 15:10.
- X2 (15:00) precedes the CTS end and both broker cut-offs.
- **FUTURE SENSITIVITY (not v1):** a closing-auction exit.

## B. Remaining assumptions (explicit)

1. Yahoo 15-min bars faithfully represent NSE trades (validated against the bhavcopy only via range, presence and volume).
2. A fill at a bar's open plus 5 bps adverse slippage approximates an executable market order. Slippage is assumed, not measured.
3. Shorts are borrowable intraday (MIS) for all 50 F&O stocks.
4. The cost schedules of 2026-09-30 stay valid through the holdout. Any published change is recorded as an amendment but **not applied** to the frozen evaluation; the effect is reported as a deviation.
5. The NSE CM holiday master is complete and correct for the calendar (amendments: §E-6).
6. Idle cash earns 0 %.
7. The sign-flip baseline holds costs at their actual values (direction-flipped charges differ only at second order).
8. DSR assumptions are listed in §C6.

## C. Exact statistical methodology (`src/intraday/inference.py`)

**C1 Primary test**
- **Data:** x = (R_1 … R_n), n = 250.
- **Block length:** b = Politis–White (2004) automatic expected block length for the stationary bootstrap, with the Patton–Politis–White (2009) correction, computed **on x itself by the pre-specified algorithm** (approved). If it returns 1, 1 is used. b is reported. It is never chosen by hand.
- **Resampling:** stationary bootstrap (Politis–Romano 1994) with geometric blocks of mean b, circular wrap. B = 10,000 resamples, seed 20261001. Resample means m\*_1..m\*_B; centred deviations δ_b = m\*_b − x̄.
- **p-value:** p = (1 + #{δ_b ≥ x̄}) / (B + 1). This is **null-centred**; it is not the SSRN 5198458 construction, and a test guards against that construction.

**C2 Uncertainty and effect size**
- Bootstrap SE = sd(δ); t_boot = x̄ / SE.
- One-sided 95 % lower bound = x̄ − q₀.₉₅(δ). One-sided 95 % upper bound = x̄ − q₀.₀₅(δ). Two-sided 95 % CI = [x̄ − q₀.₉₇₅(δ), x̄ − q₀.₀₂₅(δ)].
- Effect size: mean in bps/day and annualised Sharpe (√252).
- Economic significance (reported separately): gross mean, every cost component, net mean, break-even slippage.

**C3 Random baselines (family 2, confirmatory secondary, Holm α = 0.05)**
- **E — fair-coin random direction (primary randomised-direction baseline, approved):**
  - Each actual ORB trade keeps its stock, session, entry and exit times and quantity.
  - Its gross P&L is multiplied by an independent fair coin s_j = ±1; actual costs are subtracted unflipped.
  - The ORB long/short mix is **not** used.
- **D — random entry:**
  - For every actual ORB trade (same stock and session), the entry bar is drawn uniformly from the **10:00–14:30 IST** bar opens (19 bars). These are the only times an ORB entry can fill under A8–A9; 09:45 is impossible because the earliest signal is the 09:45 close.
  - Fair-coin direction; exit at 15:00 open; the engine's exact sizing, slippage and charges (verified equal to the engine to ₹1e-12).
- **Both:** B = 10,000, seed 20260930, statistic = mean R_t. p = (1 + #{draws ≥ observed}) / (B + 1). Then Holm across {E, D}.
- **Direction-matched secondary baseline:** not implemented (optional; omitted).

**C4 Verdict (reporting category)**
- **POSITIVE:** p < 0.05 and the one-sided lower bound > 0.
- **NEGATIVE:** the one-sided upper bound < 0.
- **INCONCLUSIVE:** otherwise.
- There is no minimum-economic-effect threshold in the verdict (approved). An additional **DATA-LIMITED** flag applies if more than 10 % of stock-sessions are non-tradable.

**C5 Exploratory and sensitivity**
- **Family 3:** 50 per-stock tests (stock i's NetPnL/K per session, same C1 method, automatic b per series, B = 2,000), Holm.
- Block-length ½× / 2×; cost grid; ₹10 lakh; long-only B; benchmark A; excluding bhavcopy-flagged stock-sessions.

**C6 Deflated Sharpe ratio (reporting only, never in the verdict)**
- **Question:** if the best of N independent configurations had been selected, what is the probability that this configuration's true per-period Sharpe exceeds the Sharpe a zero-skill selection would show?
- **Formula** (Bailey & López de Prado 2014):

  DSR = Φ((SR̂ − SR₀) √(T−1) / √(1 − γ₃SR̂ + (γ₄−1)/4·SR̂²)),
  where SR₀ = √V · [(1−γ)Φ⁻¹(1−1/N) + γ Φ⁻¹(1−1/(Ne))].

- **Inputs:**
  - N = number of distinct ORB strategy definitions registered in `registry/experiments.jsonl` (currently 3);
  - V = 1/(T−1), the null sampling variance (the cross-trial Sharpe variance is unknown);
  - γ₃, γ₄ = sample skew and kurtosis.
- **Assumptions:** independent trials; i.i.d. returns (no autocorrelation adjustment).

## D. Exact portfolio mathematics

- **Per trade:** fill_in = O_in(1 + d·s), fill_out = O_out(1 − d·s), where s = slippage_bps/10⁴ and d = +1 for long, −1 for short.
- **Quantity:** qty = max integer with qty·fill_in + charges(entry side, qty·fill_in) ≤ K.
- **NetPnL:** d·qty·(fill_out − fill_in) − charges(entry) − charges(exit).
- **charges:** the brokerage, STT, exchange, SEBI, stamp and GST formulas of A15.
- **Portfolio return:** R_t = Σ_i NetPnL_{i,t} / (50 · 1,00,000).
- **NetPnL_{i,t} = 0** when there is no signal, the entry is refused, the session is non-tradable, or there is no data.
- **Idle capital:** 0 % return. **No reinvestment:** K is the same every day.
- **Primary statistic:** x̄ = (1/n) Σ_t R_t over all n = 250 calendar sessions.

## E. Exact missing-data rules (depend on bar existence only, never on prices)

1. **Complete-session rule.** A stock-session is tradable iff all 24 bars from 09:15 to 15:00 exist. Otherwise it is non-tradable: NetPnL = 0, listed in `non_tradable.csv`. This covers missing opening-range, confirmation, intermediate and 15:00 bars.
2. **The 15:15 bar** is never required or used.
3. **No forward-fill, interpolation or substitution** of any price.
4. **Whole stock-session missing:** non-tradable, 0.
5. **DATA-LIMITED** if more than 10 % of the 12,500 stock-sessions are non-tradable.
6. **Calendar.** A standard session is a Mon–Fri date not in NSE's CM trading-holiday master for that year (`src/intraday/calendar.py`; 2026 stored with source and SHA-256).
   - Weekend and holiday special sessions (e.g. Muhurat 2026-11-08) are excluded by construction.
   - **The 2027 master must be stored, with its NSE source, when NSE publishes it, before 2027 sessions are counted.** The code raises an error for an unstored year.
   - If NSE amends the list by circular, the stored file is updated from that official source with a dated log entry. Dates are never edited by hand or by result.
7. **Hard validation errors** (duplicate or out-of-order timestamps, impossible OHLC) stop the evaluation for investigation and documentation. Nothing is dropped silently. See §I-3.
8. **Corporate events.**
   - Intraday returns are adjustment-free; stored bars are as-collected (existing bars win).
   - Suspension or delisting → non-tradable.
   - Demergers and mergers: no successor is added.
   - Symbol changes are mapped only with stored NSE evidence.
   - Index changes are ignored.
9. **Bhavcopy cross-check** (`src/intraday/bhavcopy_check.py`). Data quality only.
   - **Checks per stock-session against the EQ row of NSE's CM bhavcopy:**
     - **C1 RANGE:** every 15-min high ≤ HghPric·(1+10⁻⁴) and every low ≥ LwPric·(1−10⁻⁴).
     - **C2 PRESENCE:** Yahoo bars versus an NSE row with positive volume.
     - **C3 VOLUME:** Yahoo/NSE day volume within [0.50, 1.05].
     - **C0 UNAVAILABLE:** the bhavcopy could not be fetched.
   - **Not checked:** the 09:15 open, because NSE's OpnPric is the pre-open auction price (dev median gap 12 bps).
   - **Thresholds:** set from development data quality (716/716 inside the range; volume ratio 0.76–1.00), not from performance.
   - **On discrepancy:** one row is logged to `bhavcopy_flags.csv`. Prices are unchanged and the primary analysis is unchanged. The only use is the "excluding flagged stock-sessions" sensitivity.
   - **Storage:** bhavcopy zips are cached in `data/raw/nse_bhavcopy/`, with checksums in the manifest.

## F. Power / MDE (development data only; `scripts/orb_v1_power.py`)

**Inputs (development data):**

| Item | Value |
|---|---|
| Series | 42 development sessions (2026-08-03..09-30) of R_t at Z-5 |
| Mean | removed; never used |
| sd | 16.32 bps/day (90 % CI 13.85–19.99, χ²) |
| Skew / kurtosis | 2.17 / 11.9 |
| Politis–White block | 1.0 (no detectable autocorrelation) |
| Long-run sd σ_LR | 16.04 bps/day |

**Calculation:** analytical, MDE = (z₀.₉₅ + z₀.₈₀)·σ_LR/√n, for the one-sided α = 0.05 test at 80 % target power. Checked by simulating **the actual primary test** (automatic block, B = 999, 300 replications) at μ = MDE.

| n | MDE (bps/day) | Range over sd 90 % CI | Simulated power, normal | Simulated power, resampled dev returns | Simulated size at μ = 0 |
|---|---|---|---|---|---|
| 250 | **2.52** | 2.18–3.14 | 0.78 | 0.82 | 0.027–0.053 |
| 500 | 1.78 | 1.54–2.22 | 0.77 | 0.78 | 0.043–0.050 |

Monte Carlo SE ≈ 0.02–0.03.

**Statement:**
- Under the stated assumptions (variance and dependence of the holdout equal to the development estimates; independent days; stationarity), the minimum detectable true mean is about **2.5 bps/day of ₹50 lakh** for n = 250, with power of about 0.8 (simulated 0.78–0.82).
- **Extrapolation caveat:** σ comes from 42 sessions in a mostly low-volatility period. If holdout volatility or dependence is higher, the MDE scales up proportionally.

## G. Exact evaluation procedure (`evaluate_orb_v1.py`; no tuning options)

1. Load the protocol. Refuse unless `**Status:** FROZEN`.
2. Refuse unless the working tree is clean for src, *.py, config and docs/protocols.
3. Sessions = first 250 standard sessions from 2026-10-01 (§E-6).
4. Load the universe; verify the raw-file SHA-256.
5. Load the 50 files through the FROZEN gate. Refuse if any ends before session 250. Keep only calendar sessions.
6. Run the strategy (A7–A11) under every cost scenario and at ₹10 lakh; long-only B; benchmark A.
7. Portfolio R_t (§D) and the non-tradable list (§E).
8. Primary test (§C1–C2) → label (§C4).
9. E and D (§C3) + Holm; family 3; deflated Sharpe; break-even slippage; block ½× / 2×.
10. Bhavcopy check (§E-9) and its sensitivity.
11. Write `summary.json`, `portfolio_daily.csv`, `trades.csv`, `non_tradable.csv`, `bhavcopy_flags.csv` to a new timestamped directory under `results/orb_v1_holdout/` (never overwrite).
12. `manifest.json`: SHA-256 of every input (universe, cost files, calendar, 50 data files, bhavcopies) and output; protocol SHA-256; git commit and dirty flag; environment.
13. Make all artifacts read-only.
14. Register the experiment (status FINAL) and log the trial.

The only CLI option is `--dry-run-dev`, which runs the same pipeline on the 42 development sessions and writes to `results/orb_v1_dryrun/`.

## H. Reproducibility

| Item | Value |
|---|---|
| Protocol | Version = SHA-256 of `ORB_v1.md` at freeze, plus the commit on its status line |
| Seeds | 20261001 (primary), 20260930 (baselines) |
| Code | `8d21e3e` at audit; the freeze commit is recorded |
| Environment | Python and package versions in every manifest / experiment record |
| Data | Append-only raw snapshots and `data/raw/manifest.jsonl`. **At freeze:** register the 46 prospective-universe m15 files in `registry/datasets.json` from the collector's existing manifest checksums and provenance (no content read; universe unchanged) |
| Determinism | Development validation and dry run are bit-for-bit identical apart from timestamps |

## Audit checklist

| Area | Check | Result / evidence |
|---|---|---|
| Protocol | Every rule deterministic | PASS, except the regime source (§I-1), which is excluded from the run until approved |
| Protocol | No unresolved ambiguity | Not fully: §I lists 4 items |
| Protocol | Frozen vs exploratory separated | PASS (§A, §C5) |
| Execution | Exit at 15:00 bar OPEN | PASS: `test_exit_is_1500_open_not_1515_close`; dry-run exits 1,810/1,810 at 15:00 |
| Execution | No future data | PASS: spy/look-ahead tests; 15:00 h/l/c and 15:15 ignored; regime labels t−1 |
| Execution | Next-bar-open entry | PASS: `test_entry_still_next_bar_open_after_close_confirmation` |
| Execution | No overnight positions | PASS: `test_no_overnight_position_and_flat_at_exit` |
| Portfolio | ₹1 lakh fixed per stock, no reinvestment | PASS: `test_fixed_notional_sizing_does_not_compound`; max dev notional ₹99,969 |
| Portfolio | ₹50 lakh denominator; idle = 0 | PASS: `test_portfolio_return_is_on_fixed_total_capital` |
| Costs | Approved schedule; 5 bps primary; grid | PASS: `cost_scenarios.json` primary Z-5 asserted; hand reconciliation (7.09 bps/day charges) |
| Statistics | One-sided α = 0.05, null-centred dependence-aware bootstrap, CIs, effect size | PASS: size/power/guard tests |
| Statistics | Power/MDE wording | PASS: §F |
| Statistics | Multiple testing; D 10:00–14:30; fair-coin E; DSR reporting-only | PASS |
| Data | Frozen universe | PASS: hash verified at run time; file unchanged since `fc3b26d` |
| Data | Point-in-time holdout; no synthetic prices; missing-bar rules; corporate events; calendar; bhavcopy | PASS: tests + §E. Bhavcopy dry run: 0 flags / 2,100 |
| Holdout | Starts 2026-10-01; 250 standard sessions; locked | PASS: loader gate, evaluator refuses (tested), calendar errors for unstored 2027 |
| Holdout | No observation used for tuning | PASS (§J) |
| Holdout | Evaluator cannot optimise | PASS: CLI options = {--help, --dry-run-dev} (tested) |
| Reproducibility | Protocol hash, checksums, experiment ID, commit, environment, read-only artifacts | PASS: dry run ORBV1-20261002-001, manifest with 98 input checksums |

## Test results

- **`pytest`: 120 passed** (80 pre-existing + 40 ORB v1).
- **Dry run** (`results/orb_v1_dryrun/20261002T180543/`, development data, DIAGNOSTIC): identical to the earlier development validation.
  - Net −16.30 bps/day; label NEGATIVE on development data.
  - E p = 0.68; D p = 0.70.
  - Block length 1.0; DSR 0.001.
  - 0 non-tradable stock-sessions; 0 bhavcopy flags.
  - **Not evidence; nothing was changed in response.**

## I. Remaining ambiguity (needs your decision before freeze)

1. **Regime index-close source (OPEN-3, not covered by the 2026-10-01 approvals).**
   - Options: NSE / NSE Indices official NIFTY 50 daily close, stored as evidence (recommended); Yahoo ^NSEI daily; or the last 15-min bar.
   - The expanding-median start also needs fixing (recommendation: the first stored date).
   - Until decided, the evaluator reports regimes as NOT RUN.
2. **2027 holiday master:** not yet published by NSE. It must be stored when published (procedural; the rule is fixed).
3. **Hard data-validation errors in holdout files** (§E-7). Choose between:
   - (a) stop, investigate and document (current behaviour);
   - (b) treat that stock as non-tradable for the affected sessions under a pre-stated rule.

   Recommendation: (b), limited to the sessions containing the defect, logged. It avoids an indefinite block while keeping the result deterministic.
4. **Bhavcopy tolerances** (C1 1 bp; C3 [0.50, 1.05]) were set from development data quality. Approve or adjust before freeze.

## J. Holdout integrity confirmation

- No bar dated 2026-10-01 or later was loaded into any analysis. Both `load_intraday` and the evaluator enforce this; the dry run used only 2026-08-03..09-30.
- No October return, signal or trade was computed or viewed.
- The 18:30 collector run appended 2026-10-01/02 bars to the data files, which is its normal append-only job. Those changes are **uncommitted and were not read**; only the dry run's checksum step hashed whole files.
- No protocol element, parameter, cost, test, baseline or rule was chosen or changed using holdout data or development performance.
- The frozen universe, collector, provider and cost model are unchanged.
