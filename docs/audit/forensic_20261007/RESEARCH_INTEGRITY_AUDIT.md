# Trading Lab — research-integrity audit of S2-MOM-v1 (2026-10-07)

## 1. Headline result: independent recomputation

The audit wrote a second implementation of the ladder from the frozen protocol text (B1.1–B1.4, §6–§10, §20–§22), with its own data structures, and ran it on the Stage 3 input files. It is kept outside the repository (audit scratch script `verify.py`); it wrote nothing into the project.

| Check | Result |
|---|---|
| Every registered file hash (blinded, primary ×5, sensitivity, confirmation ×5, step E ×5, C2) equals the registry | match |
| Protocol, addendum, supplements 1-4, cost schedule, UNIV-1, all 16 RET-1.1 files, all Stage 3 files equal their recorded hashes | match |
| Current runner code hash equals the registered primary = sensitivity = confirmation code hash; same for step E and C2 | match |
| Steps A, B, C, D — W, L, benchmark, rankable count, k — 456 primary + 224 confirmation step-months | **all reproduce; largest difference 5.4e-16** |
| δ series, both samples | reproduces (< 1e-9) |
| H1 mean, Newey-West SE, p-value, 90 % interval, both samples, against statsmodels HAC | reproduce (< 1e-9) |
| Newey-West lag equals `floor(4·(n/100)^(2/9))` for n = 114 and 56 | yes |
| Step E: cost of W, L and benchmark under S0–S4, every month, recomputed from saved holdings and the dated schedule | **reproduce; largest difference 1.1e-16** |
| Step E: H4 mean and one-sided p; gross columns copied unchanged; no month with zero cost | reproduce / true |
| Blinded-step δ hash equals the hash of the registered primary δ | yes |
| Stage 3 panel: no duplicate (entity, date); no return ≤ −100 %; no NaN/inf outside first observations; every research-grade row has a return; nothing after 2026-09-30 | true |

Label: the registered A–D and step E numbers are **PROVEN by independent recomputation** from the Stage 3 inputs, and **SUPPORTED BY HASH** back to the Stage 2 manifests. Not re-verified in this audit: the Stage 2 rebuild from raw NSE files (needs ~10 GB RAM; last run 2026-10-05, 150/150, log hash registered), the sensitivity and reverse-ladder numbers, the C2 numbers, and the manuscript text.

**No defect was found that changes a registered number.**

## 2. The 35 invariants

Question asked for each: *can a programmer accidentally violate this without the software raising an error or a test failing?* "Mutation" refers to `MUTATION_TEST_REPORT.md`.

| # | Invariant | Where enforced | Tests / evidence | Can it be broken silently? |
|---|---|---|---|---|
| 1 | Point-in-time universe | `universe.build`; `ladder.universes` | truncation, future-volume, future-delisting tests; hash | No (mutations killed) |
| 2 | Membership effective date (chosen at `t`, traded at `s⁺`) | `ladder.calendar` | calendar tests; mutation `s > t → >=` killed | No |
| 3 | Historical entity identity | `universe._components` (links effective ≤ t) | `test_future_symbol_not_used…` | **Yes in the suite** — "identity links from the future" survives; real data pinned by the UNIV-1 hash |
| 4 | Delisted entities kept | UNIV-1 from daily files; `delist_on` for universe C | `test_delisting_rule_applies_from_step_c_only…` | No |
| 5 | Survivor pool = ACTIVE_AT_CUTOFF | `data.identity` | `test_identity_refuses_a_grouping_mismatch`; synthetic world tests | No (mutation killed) |
| 6 | Liquidity ranking | `universe.build` | ties/top-N tests; hash | Partly — rank order killed; "mean instead of median" survives; real data pinned by hash |
| 7 | Trailing 63-session window | `universe.build` | truncation test | **Yes in the suite** — "63→64" and "min valid 50→49" survive; real data pinned by hash |
| 8 | Future-liquidity leakage | same | `test_future_high_volume…`, `test_d_…` | No |
| 9 | Future-identity leakage | same | `test_future_symbol…` | No |
| 10 | Future-return leakage | `run_ladder` formation slice | perturbation, truncation, "impossible future returns" tests; real-data pre-run checks | No (look-ahead mutations killed) |
| 11 | Formation window (m12, m1] | `run_ladder` | `test_formation_is_12_1…` | No |
| 12 | One-month skip | `calendar` (`SKIP_MONTHS`) | killed | No |
| 13 | Holding period (s⁺, s⁺⁺] | `_hold` | naive rule: killed. **Research-grade rule: dropping the exit session SURVIVES** | **Yes (step D)** — G-01 |
| 14 | Winner/loser cut-offs k = floor(0.30n + 0.5) | `sort_portfolios` | parametrised test | No |
| 15 | Equal weighting | `_hold` (`v.mean()`) | holdings and ladder tests | No (median mutation killed) |
| 16 | Missing observations (§20b neutral fill) | `_hold` | two tests | No (killed) |
| 17 | Special-session treatment | `wide` (`lr` zero unless OK), `treated` | span tests | **Partly** — "step D uses raw returns on every row" SURVIVES (G-02) |
| 18 | Corporate actions (validated only in D; every parsed factor in A–C) | `study_panel`, RET-1.1 | Stage 2 tests; `test_study_panel…` | Partly — same survivor as 17 |
| 19 | Research-grade return rules | RET-1.1 status precedence | Stage 2 tests | Partly — jump threshold 1.4→1.5, ex-date boundary and validation band 1.25→2.0 survive; real data pinned by the RET-1.1 hashes |
| 20 | Trading dates | `calendar` from the session list | tests | No |
| 21 | Session boundaries | `calendar` | tests | No |
| 22 | Cost-schedule dates | `step_e.period` (rate in force on the trade date) | boundary tests | No (killed) |
| 23 | Cost component application | `step_e.order_cost` | hand-calculation tests | No (killed) |
| 24 | Slippage | `cost_ledger` (band from UNIV-1 rank at the rebalance) | scenario tests | No (killed) |
| 25 | Portfolio denominator (₹1 crore at every rebalance) | `cost_ledger`, schedule conventions | `test_notional_is_never_compounded` | No |
| 26 | No reinvestment | same | same | No |
| 27 | Benchmark = all rankable, equal weight | `run_ladder` (`BM`) | placebo test compares BM sets | No |
| 28 | H3 → H4 conditional logic | `step_e.summarise` | `test_h4_and_break_even_only…` | No |
| 29 | Newey-West lag | `NW_LAG` constants | killed for PRIMARY | Partly — lag is tied to the sample name, not to the realised n (F-23) |
| 30 | Bootstrap configuration | `stats.bootstrap_test` | seeded/centred test | Partly — centring killed; a one-sided count survives (G-05) |
| 31 | Multiple-testing correction | C2 `holm`, `bh` | known-value test | No (killed) |
| 32 | Confirmation-period isolation | runner order; same-code check | gate-order test (earlier gates only) | **Partly** — the same-code gate exists but removing it survives (G-09); see also R-1 and L-01 |
| 33 | Holdout protection (ORB) | `access.py`, static scan | 23 tests | No |
| 34 | Frozen-protocol protection | `verify_protocol` (file + registry) | test | No (killed) |
| 35 | Registered-artifact protection | registry hashes; hash-pin tests | tests | Alteration: No. Loss: **Yes** (F-01). Registry rewrite: **Yes** (F-03) |

## 3. Research-integrity risks (for the researcher's decision; none is a code change request)

**R-1. Primary-sample results use confirmation-period data through §22.** A stock with no price at an exit session in 2012–2021 is valued by looking forward to the research cutoff (2026-09-30) to decide "trades again later" versus "never trades again", and to book the realised gap return. This is the registered decision `exit_gap_lookahead = TO_RESEARCH_CUTOFF` and it affects returns, not selection. It means the primary sample is not computable from data up to December 2021 alone. Status: decided, registered, tested (`test_only_the_section_22_row_can_reach_past_the_exit_session`). It should be stated in the manuscript's limitations if it is not already. DOCUMENTATION ONLY for the disclosure.

**R-2. A series change is treated as "not trading".** The study reads EQ rows only (§5). A stock moved to another NSE series has no EQ row, so the ladder treats it as untraded, and §22 books the whole close-to-close move over the gap into one month. Registered counts in step D: 16 (W), 4 (L), 23 (benchmark) booked gap returns in the primary sample, of which 5, 3 and 8 are on rows flagged as not research-grade. The Stage 2 documentation says a gap can mean "suspension/other series"; the frozen protocol §30 does not list this as a threat. No new analysis was run here. Recommendation: disclose.

**R-3. Step D books raw gap returns on flagged rows.** Decision `exit_gap_return_step_d = REALISED_RAW_GAP_RETURN`: the corrected specification can book an unadjusted multi-month return. The code stops only when a parsed factor sits on the resumption row. Counted and saved in the events files. Decided and registered.

**R-4. Code changed between the blinded step and the primary run.** `blinded_code_sha256 = ddebf8ce…`, primary `code_sha256 = f57c9321…`. The change (mode split) is recorded in `RESEARCH_LOG.md` line 357, and the δ hash stored by the blinded step equals the hash of the registered primary δ, so the estimand did not move. SUPPORTED BY HASH. It is not in the deviation log.

**R-5. The real-data perturbation check is narrower than B2 check 1.** The protocol says "randomly change every price, flag, liquidity value and membership row dated after t". `experiment._perturbed` scrambles returns and research-grade flags only; liquidity and membership rows are perturbed only in the synthetic unit tests. The UNIV-1 builder has its own leakage tests. PARTIAL (F-13).

**R-6. The placebo gate depends on one seed.** It requires p > 0.05 for a random ranking, so it fails for about one seed in twenty by construction. The confirmation-sample value was p = 0.054. It passed, with the pre-registered seed; had it failed, the protocol gives no rule other than "stop".

**R-7. The §27 label is applied by code outside its scope and its ordering is ambiguous.** Already corrected in the registry for the confirmation sample (metadata correction 6). In addition, a significant estimate whose 90 % interval lies wholly inside ±0.10 would be labelled `DETECTED_SIZE_UNCERTAIN`, while the protocol table also allows "immaterial". Not triggered (F-22).

**R-8. §14 asks for an information ratio for long-only portfolios.** The code reports `mean_over_sd` for every portfolio. It is named honestly in the result files; the information ratio was not computed and is not in the DEV-2 list (D-04).

## 4. What is enforced only by documentation

1. "Called only by the runner" (`experiment.analyse`, `load_inputs`) — L-01.
2. "Each mode runs once" — enforced by file existence, not by the registry.
3. "Code is developed on synthetic and permuted data only" (B3 step 1) — cannot be checked.
4. "Every specification that is run is written to `registry/trials.jsonl`" — only runs that reach the end of a runner, with the environment variable unset.
5. "The registry is append-only and never edited" — a file-system convention.
6. "Stage 2 rebuild passed 150 of 150" — a hand-written registry amendment plus a log file whose hash is registered.
7. "Raw files are never modified" — convention; detected only when `build_stage2.py` is rerun.
