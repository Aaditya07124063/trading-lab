# ORB research protocol — v1

**Status:** FROZEN
**Version:** 1.0 · frozen 2026-10-03 on the explicit approval of Aaditya Adhikari (2026-10-03).
**Body:** §1–9 copied verbatim from `docs/protocols/ORB_v1_pre_freeze_audit_20261001.md` (audit commit `dcd323e`, code audited at `13e4664`).
**Freeze rule:** this file is never edited after freezing (apart from the one-time annotation of the freeze commit on the line below); any change creates `ORB_v2.md`. The superseded DRAFT of 2026-09-30 is preserved in git history.
**Freeze commit:** (recorded in the follow-up commit)

The holdout (first 250 standard NSE sessions from 2026-10-01) may be evaluated only once, with `python3 evaluate_orb_v1.py`, after explicit authorisation.

---

## 1. Complete frozen-protocol candidate

**Question and hypothesis**
- **1.1 Question.** Does the predefined ORB strategy produce positive mean daily net returns, after realistic costs and slippage, as an equal-weighted portfolio across the frozen NIFTY 50 universe? *FROZEN*
- **1.2 Hypothesis.** H1: μ > 0; H0: μ ≤ 0. μ = expected daily portfolio net return R_t (§4) at the primary cost scenario. One-sided, **α = 0.05**. *FROZEN*

**Universe, data and holdout**
- **1.3 Universe.** NIFTY 50 constituents frozen 2026-10-01 08:26 IST (`NIFTY50_frozen_20261001.json`; raw-file SHA-256 verified at every run). N = 50; never updated or substituted. *FROZEN*
- **1.4 Data.** Yahoo 15-min OHLCV (bar-start, IST) from the logged append-only collector. *FROZEN*
- **1.5 Development data.** All bars < 2026-10-01. Exposed; every result on them is DIAGNOSTIC (§10).
- **1.6 Holdout.** The **first 250 standard NSE sessions on or after 2026-10-01** (§5).
  - Locked in code until the protocol is FROZEN.
  - Evaluated **once**, after the collection has reached session 250. *FROZEN*

**Strategy and execution**
- **1.7 Opening range.** Bars 09:15 and 09:30 (09:15–09:45). OR_HIGH = max high; OR_LOW = min low. *FROZEN*
- **1.8 Signal.** The first **completed** bar at or after 09:45 whose **close** is above OR_HIGH (long) or below OR_LOW (short). One signal per stock per day. *FROZEN*
- **1.9 Entry.** **Open of the next bar** (earliest 10:00). No fill after the 14:30 bar open. One trade per stock per day. *FROZEN*
- **1.10 Exit (X2).** **Open of the 15:00 bar.**
  - Never used: 15:00 high/low/close; any 15:15 data; the closing-auction price.
  - No overnight positions. *FROZEN*
  - Implementation constraint, documented, **not** a research rule: SEBI CAS from 2026-08-03 (CTS ends 15:15 for F&O stocks); broker MIS square-off 15:12 (Zerodha) / 15:10 (Upstox). X2 precedes all of them.
- **1.11 Sizing.** K = ₹1,00,000 fixed per stock per session; integer shares; entry fill + entry charges ≤ K; no leverage; **no reinvestment**. *FROZEN*

**Costs**
- **1.12 Costs.** Zerodha NSE equity-intraday schedule of 2026-09-30.
  - Brokerage: min(₹20, 0.03 %).
  - STT: 0.025 % sell.
  - Exchange: 0.00307 %. SEBI: 0.0001 %.
  - Stamp: 0.003 % buy.
  - GST: 18 % on brokerage + exchange + SEBI.
  - Deterministic. *FROZEN*
- **1.13 Slippage.** Primary **5 bps per side**, adverse, both legs. *FROZEN*
  - Sensitivity: 0 / 2 / 10 / 20 bps, GROSS, U-5, K = ₹10 lakh. *REPORTING*

**Comparisons and statistics**
- **1.14 Benchmarks.** A: open-to-close long (09:15 open → 15:00 open, same sessions, K and costs). B: long-only ORB. *CONTEXT ONLY*
- **1.15–1.21** Statistics, baselines, multiple testing, DSR, verdict: see §3. *FROZEN* unless marked otherwise.
- **1.22 Power / MDE.** See §8. Computed from development data only.
- **1.23 Regimes.** See §6. *EXPLORATORY*

**Reporting and reproducibility**
- **1.24 Robustness.** Sensitivities in 1.13 and §3.5. They can never change the verdict or the protocol. *REPORTING*
- **1.25 Reporting.** Everything in `summary.json`, whatever the result.
  - All deviations stated.
  - "250 sessions collected" is reported separately from "usable stock-sessions".
  - Negative and inconclusive results get equal prominence.
- **1.26 Reproducibility.** See §9.
- **1.27 Verdict labels.** See §3.4. Reporting categories, no scoring.

## 2. Remaining assumptions

1. Yahoo bars represent NSE trades. The bhavcopy checks only range, presence and volume.
2. A fill at a bar's open plus 5 bps adverse slippage approximates an executable market order. Slippage is assumed, not measured.
3. Intraday shorts are available for all 50 (F&O) stocks.
4. The 2026-09-30 cost schedules apply throughout. A published change is reported as a deviation and is not applied.
5. NSE's CM holiday master is correct. NSE amendments are applied from the official source with a dated log entry.
6. Idle cash earns 0 %.
7. Baseline E holds costs at their actual values.
8. DSR assumptions are in §3.6.
9. The power assumptions are in §8.

## 3. Exact statistical methodology (`src/intraday/inference.py`)

**3.1 Primary test** on x = (R_1..R_250):
- **Block length:** b = **Politis–White (2004) automatic** stationary-bootstrap block length, with the Patton–Politis–White (2009) correction, computed on x by the fixed algorithm. If it returns 1, then 1. Reported; never hand-picked.
- **Resampling:** stationary bootstrap (Politis–Romano 1994), mean block b, circular. B = 10,000, seed 20261001. δ_b = m\*_b − x̄.
- **p-value:** **p = (1 + #{δ_b ≥ x̄}) / (B + 1)** (null-centred).

**3.2 Uncertainty and effect size**
- Bootstrap SE = sd(δ); t_boot = x̄ / SE.
- One-sided 95 % lower bound = x̄ − q₀.₉₅(δ). Upper bound = x̄ − q₀.₀₅(δ).
- Two-sided 95 % CI.
- Mean in bps/day; annualised Sharpe (√252).
- **Economic significance, reported separately:** gross mean, each cost component, net mean, break-even slippage.

**3.3 Family 2 (confirmatory secondary): Holm at α = 0.05 across {E, D}**
- **E — fair-coin random direction (primary randomised-direction baseline):**
  - Each actual ORB trade keeps its stock, session, entry and exit times and quantity.
  - Gross P&L × independent fair coin ±1; actual costs are subtracted unflipped.
  - The ORB long/short mix is **not** used.
- **D — random entry:**
  - For each actual ORB trade (same stock-session), the entry bar is drawn uniformly from the **10:00–14:30 IST** bar opens (19 bars).
    - 09:45 is not an executable ORB entry time: the earliest signal is the 09:45 bar's close, which fills at 10:00.
    - Random entry obeys the strategy's own entry constraints.
  - Fair-coin direction; exit at 15:00 open; the engine's exact sizing, slippage and charges (verified equal to the engine to ₹1e-12).
- **Both:** B = 10,000, seed 20260930, statistic = mean R_t, p = (1 + #{draws ≥ observed}) / (B + 1).
- **If there are zero ORB trades:** baselines undefined, p := 1.
- **Not implemented:** a direction-matched secondary baseline (optional).

**3.4 Verdict (reporting category)**
- **POSITIVE:** p < 0.05 and lower bound > 0.
- **NEGATIVE:** upper bound < 0.
- **INCONCLUSIVE:** otherwise.
- No economic threshold in the verdict.
- An additional **DATA-LIMITED** flag if more than 10 % of the 12,500 stock-sessions are untradable.

**3.5 Exploratory and sensitivity**
- **Family 3:** 50 per-stock tests (same method; automatic b per series; B = 2,000), Holm.
- Block ½× / 2×; cost grid; ₹10 lakh; long-only; benchmark A; regimes.

**3.6 Deflated Sharpe (REPORTING ONLY, never in the verdict)**
- **Question:** if the best of N independent ORB configurations had been selected, what is the probability that this configuration's true per-period Sharpe exceeds the Sharpe a zero-skill selection would show?
- **Formula:** DSR = Φ((SR̂ − SR₀)√(T−1) / √(1 − γ₃SR̂ + (γ₄−1)/4·SR̂²)), with SR₀ = √V[(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne))].
- **Inputs:**
  - N = distinct ORB strategy definitions in `registry/experiments.jsonl` (currently 3);
  - V = 1/(T−1);
  - γ₃, γ₄ = sample skew and kurtosis.
- **Assumptions:** independent trials; i.i.d. returns. Undefined (reported null) if the variance is 0.

## 4. Exact portfolio mathematics

- **Per trade (d = +1 long, −1 short; s = 5 × 10⁻⁴):**
  - fill_in = O_in(1 + d·s); fill_out = O_out(1 − d·s).
  - qty = max integer with qty·fill_in + charges_entry ≤ 1,00,000.
  - NetPnL = d·qty·(fill_out − fill_in) − charges_entry − charges_exit.
- **Portfolio:** **R_t = Σ_{i=1}^{50} NetPnL_{i,t} / 50,00,000.**
  - NetPnL_{i,t} = 0 for no signal, refused entry, untradable stock-session, or no data.
  - Idle capital earns 0. K is the same every day (no reinvestment).
- **Primary statistic:** x̄ = (1/250) Σ_{t=1}^{250} R_t.

## 5. Exact holdout definition and missing-data rules

**5.1 Session calendar.** `src/intraday/calendar.py`.
- A standard session is a Mon–Fri date not in NSE's CM trading-holiday master for its year (`docs/evidence/nse_calendar/`, stored with source and SHA-256).
- Weekend and holiday special sessions (e.g. Muhurat 2026-11-08) are excluded by construction.
- **2027 rule (frozen procedure, not dates):**
  - The official 2027 master is stored with its checksum when NSE publishes it.
  - The code refuses to count 2027 sessions until then (tested).
  - NSE amendments are applied from the official source with a dated log entry. Never by hand, never by result.

**5.2 Holdout.** Sessions 1..250 = the first 250 standard sessions on or after 2026-10-01.
- 2026 contributes 61 (2026-10-01..12-31); the remaining 189 fall in 2027.
- **"Collected"** (universe-level): the collection has reached session 250. The evaluator refuses otherwise.
- **"Usable"** (per stock-session): reported separately. Untradable stock-sessions follow 5.3–5.6 and do not block the evaluation.

**5.3 Complete-session rule.** A stock-session is tradable iff all 24 bars 09:15..15:00 exist. Otherwise it is untradable: NetPnL = 0, reason "missing bars: …" or "no data". The 15:15 bar is never required.

**5.4 Malformed data** (approved 2026-10-02; `split_defective`).
- **Defects:** a duplicate timestamp, an out-of-order timestamp, a bar off the session grid, missing OHLC, or impossible OHLC.
- **Effect:** marks **only the affected stock-session** untradable, with the exact reason ("malformed data: …") in `non_tradable.csv`.
- A row with an unparseable timestamp belongs to no session. It is counted per stock and reported.
- The source file is never repaired, filled or altered. One malformed stock-session never blocks the 250-session evaluation.

**5.5 No synthetic data.** No forward-fill, interpolation, substitution or synthetic fill, anywhere.

**5.6 Corporate events.**
- Intraday returns are adjustment-free; stored bars are as-collected.
- Suspension or delisting → untradable.
- Demergers and mergers: no successor is added.
- Symbol changes are mapped only with stored NSE evidence.
- Index changes are ignored.

**5.7 Bhavcopy validation — DATA-QUALITY FLAGS ONLY.** `src/intraday/bhavcopy_check.py`.
- **Checks per stock-session against the EQ row of NSE's CM bhavcopy:**
  - **C1 RANGE:** every 15-min high ≤ HghPric·(1 + **1 bp**) and every low ≥ LwPric·(1 − 1 bp).
  - **C2 PRESENCE:** Yahoo bars versus an NSE row with positive volume.
  - **C3 VOLUME:** Yahoo/NSE day volume within **[0.50, 1.05]**.
  - **C0 UNAVAILABLE:** bhavcopy not obtainable, preserved as an explicit flag.
- **Not checked:** the 09:15 open, because NSE's OpnPric is the pre-open auction price.
- **Effect:** flags are written to `bhavcopy_flags.csv` and counted in `summary.json`.
- **They never modify, exclude, repair or alter any observation or calculation.** The earlier "excluding flagged" sensitivity has been removed.

## 6. Regime labels — EXPLORATORY / REPORTING ONLY

- **Source:** the official NSE NIFTY 50 daily close from NSE's `ind_close_all_DDMMYYYY.csv` archive.
  - History: all 184 standard sessions 2026-01-01..2026-09-30, stored in `docs/evidence/nse_index/nifty50_official_close_2026.csv` with a per-file SHA-256.
  - The history matches the stored calendar exactly. The 2026 days without a file are exactly NSE's listed holidays.
  - Holdout-session closes are fetched and hashed (manifest) at evaluation.
- **Labels for session t (data up to t−1 only; tested):**
  - vol20 = sd of the 20 daily returns ending t−1; HIGH if above its expanding median (from the first stored date), else LOW;
  - trend = sign of the 20-session return ending t−1.
- **Reported:** mean R_t, n and SE per label.
- **If any official close is unavailable:** "NOT RUN" with the reason. No substitute source.
- **Never affects the primary result.**

## 7. Exact evaluation procedure (`evaluate_orb_v1.py`; CLI options = {--help, --dry-run-dev})

**Refusals:**
1. Unless `ORB_v1.md` reads `**Status:** FROZEN`.
2. If src, *.py, config, docs/protocols or docs/evidence have uncommitted changes.
3. If the collection has not reached session 250.

**Run:**
4. Sessions per §5.2.
5. Universe hash check.
6. Load the 50 files through the FROZEN gate (the only holdout-gate caller in the repository). Apply §5.3–5.4.
7. Strategy under every cost scenario and at ₹10 lakh; long-only; benchmark A.
8. R_t (§4) and untradable stock-sessions with reasons.
9. Primary test → verdict; family 2 (E, D, Holm); family 3; DSR; break-even slippage; block ½× / 2×.
10. Bhavcopy flags (§5.7).
11. Regimes (§6).

**Outputs:**
12. Write `summary.json`, `portfolio_daily.csv`, `trades.csv`, `non_tradable.csv` (with reasons) and `bhavcopy_flags.csv` to a new timestamped directory. Never overwrite.
13. `manifest.json`: SHA-256 of every input (universe, cost files, calendar, 50 data files, bhavcopies, index history and fetched closes) and every output; protocol SHA-256; git commit and dirty flag; environment.
14. All files made read-only.
15. Experiment registered (FINAL; dry runs DIAGNOSTIC) and trial logged.

## 8. Power / MDE — under stated assumptions, no overclaim (`scripts/orb_v1_power.py`)

**Inputs (development data only):**

| Item | Value |
|---|---|
| Series | 42 sessions of R_t at Z-5, 2026-08-03..09-30 |
| Mean | removed; never used |
| sd | 16.32 bps/day (90 % χ² CI 13.85–19.99) |
| Skew / kurtosis | 2.17 / 11.9 |
| Politis–White block | 1.0 |
| Long-run sd | 16.04 bps/day |

**Method:**
- Test: the one-sided α = 0.05 null-centred stationary bootstrap of §3.1.
- Target power: 0.80.
- **Analytical** MDE = (z₀.₉₅ + z₀.₈₀)·σ_LR/√n.
- **Simulation check:** the actual test (B = 999, 300 replications) at μ = MDE.

| n | MDE (bps/day) | Range over sd CI | Simulated power (normal / resampled dev returns) | Simulated size |
|---|---|---|---|---|
| 250 | **2.52** | 2.18–3.14 | 0.78 / 0.82 | 0.03–0.05 |
| 500 | 1.78 | 1.54–2.22 | 0.77 / 0.78 | 0.04–0.05 |

**Statement:**
- **Under the assumptions** that holdout daily variance and dependence equal the development estimates (no detected autocorrelation), with stationarity, a true mean of about 2.5 bps/day (on ₹50 lakh) would be detected with probability ≈ 0.8 (simulated 0.78–0.82, Monte Carlo SE ≈ 0.02) at n = 250.
- The estimate rests on 42 sessions from a period labelled entirely low-volatility. With higher holdout volatility or dependence, the MDE scales up proportionally.
- This is an MDE under assumptions, **not** a guarantee of detection.

## 9. Reproducibility

| Item | Value |
|---|---|
| Protocol | SHA-256 of `ORB_v1.md` recorded in every manifest; freeze commit on the status line |
| Seeds | 20261001 (primary), 20260930 (baselines) |
| Code | Commit and dirty flag in every manifest; environment (Python, packages) in the manifest and registry |
| Data | Append-only collector with raw snapshots and `data/raw/manifest.jsonl`. **At freeze:** register the 46 prospective-universe files in `registry/datasets.json` from the collector's existing checksums and provenance (approved; no content read) |
| Raw caches | Bhavcopy and index raw files are cached locally (git-ignored), with SHA-256 in the manifests and evidence files |
| Determinism | Development validation and both dry runs give identical primary numbers |
