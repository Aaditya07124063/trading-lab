# Phase 3B — final pre-run audit for S2-MOM-v1 (2026-10-05)

**Frozen protocol:** `docs/research/phase3a_momentum_protocol.md`, SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`, freeze commit `7d4cb6d`. Not changed. Section numbers refer to it.

**State:** the experiment has NOT been run. No real research result exists. This audit changed no code and no data.

**Verdict:** the primary experiment is **not yet authorisable**. Three items block it (section 4). Most secondary and robustness work does **not** block it.

---

## 1. Primary experiment requirements

"Blocking" = stops the primary run today.

| Requirement | Required before primary run? | Implemented? | Tested? | Blocking? | Evidence / file |
|---|---|---|---|---|---|
| Protocol registration | Yes (header) | Yes | Yes | No | `registry/experiments.jsonl`, id `S2-MOM-v1`, status PLANNED |
| Protocol SHA-256 check | Yes | Yes | Yes | No | `src/stage3/protocol.py` `verify_protocol`; runner refuses a changed file or record |
| Reviewed interpretations recorded | Yes | Yes | Yes | No | registry amendment; `require_ready` refuses any other value |
| Global cutoff 2026-09-30 | Yes (§5) | Yes | Yes | No | `src/stage3/data.py` `_cut`; `src/access.py` |
| Primary / OOS boundaries (114 + 56 months; exit sessions 2022-01-03 and 2026-09-01) | Yes (B3) | Yes | Yes | No | `ladder.calendar`; builder asserts; pre-run checks |
| 12-1 formation, skip month | Yes (§7–§8) | Yes | Yes | No | `ladder.run_ladder`; hand-checked test |
| One-session delayed entry | Yes (§9) | Yes | Yes | No | same |
| One-month non-overlapping holding | Yes (§9) | Yes | Yes | No | same |
| Top / bottom 30%, `k = floor(0.30·n + 0.5)`, ties by entity | Yes (§10, B1.1) | Yes | Yes | No | `ladder.sort_portfolios` |
| Equal weighting | Yes (§10) | Yes | Yes | No | `ladder._hold` |
| Step A: fixed survivor list at 2026-09-30 | Yes (B1.2) | Yes | Yes | No | `ladder.universes`; builder asserts it equals UNIV-1 members at that date |
| Step B: same pool, liquidity at each date | Yes (B1.3) | Yes | Yes | No | `ladder.top200` |
| Step C: UNIV-1 point-in-time universe | Yes (B1.4) | Yes | Yes | No | builder asserts it equals UNIV-1 members at all 170 dates |
| Step D: RET-1.1 research-grade returns | Yes (§20–§21) | Yes | Yes | No | `ladder.study_panel`, `wide`; RET-1.1 files hash-checked on load |
| Special-session exclusion | Yes (§20a) | Yes | Yes | No | `ladder._hold`; test |
| §20(b) fill (simple mean; stock kept; logged) | Yes | Yes | Yes | No | `ladder._hold`; audit events |
| §22 missed-exit treatment (literal) | Yes | Yes | Yes | No | `ladder._hold`; tests incl. "only the §22 row reaches past the exit" |
| Step E cost model | **No for the primary estimand** (δ is gross). Yes for step E and H4 | Yes | Yes (synthetic rates) | **Yes, as the runner is built today** — see 4.3 | `src/stage3/costs.py`; five rates have no archived evidence |
| Paired A/D estimand δ(t) | Yes (§2) | Yes | Yes | No | `ladder.paired_delta`; real-data pairing 114/114 and 56/56 |
| Newey–West, lag 4, two-sided, standard normal | Yes (§15) | Yes | Yes (matches `statsmodels`) | No | `src/stage3/stats.py` |
| Stationary bootstrap, 10,000 resamples | Yes (§15) | Yes | Yes | No | `stats.bootstrap_test`; resampler reused from `src/intraday/inference.py` |
| Bootstrap seed 20261005 | Yes | Yes | Yes | No | `protocol.BOOTSTRAP_SEED`; registry |
| Leakage tests (perturbation, truncation, placebo) on the real pipeline | Yes (B2, §25) | Yes | Yes | No — **passed** | `data/stage3/s2_mom_v1/checks/` |
| Access boundary; collector / ORB isolation | Yes (§19) | Yes | Yes | No | code scan test; file-open design; existing boundary tests |
| Input hashes | Yes (§4) | Yes | Yes | No | `data/stage3/s2_mom_v1/manifest.json`; `data.verify_provenance` |
| Code hash | Yes (B3 step 2) | Yes | Yes | No | runner `code_sha()`; checks are void if code changes |
| Reproducibility manifest; deterministic rebuild | Yes | Yes | Yes | No | `scripts/build_stage3.py` (rebuild byte-identical) |
| **Stage 2 rebuild passes all 150 checks** | **Yes (§4, §25)** | Yes (script exists) | Not re-run since Phase 2.1 | **Yes** | Needs disk space — section 5 |
| **Blinded precision step generated and registered** | **Yes (§15)** | Yes | Yes (synthetic) | **Yes — needs your authorisation to generate** | `scripts/run_s2_mom.py blinded` |
| Primary diagnostics: unpaired months, rankable counts, fill / gap / delisting counts, audit events | Yes | Yes | Yes | No | check artifacts; `*_events.csv` at run time |
| **Sensitivity runs that label the primary result: R-span, R-gap, R-miss, R-delist** | **Yes (§25)** | **No** | No | **Yes** | See 2 and 4.2 |
| Holdings and end-weights saved with the primary run | Needed so later analyses need no second run | **No** (kept in memory only) | — | **Yes (small)** | See 4.2 |

## 2. Secondary and robustness scope

**One rule of the frozen protocol drives this section.** B3 says "Protocol and code are frozen and hashed" before the primary run, and "No change is allowed between steps 3 and 4"; §25 says a code-hash change between the primary and confirmation runs means "report nothing".

Consequence: an analysis may be added after the primary result only if
1. it does not decide how the primary result is labelled, and
2. it is written as a **new file** that reads the registered outputs, leaving the hashed pipeline files byte-identical.

Anything that needs a change to the hashed pipeline files can be done before the primary run or after the confirmation run, **never between them**.

| Item | Class | Reason |
|---|---|---|
| Sensitivity comparison (R-span, R-gap, R-miss, R-delist) | **A** | §25: if H1 changes sign or significance under any of them, the primary result is reported as "not reliable". They decide the label of H1, and they are pipeline variants, so they cannot be added between the two runs |
| Saving holdings and end-weights at the primary run | **A** | Without it, turnover, costs and capacity would need a second primary run |
| Reliability labels (under 100 rankable stocks in any month, or average under 150; more than 5% of W or L stock-days filled) | **B** | Fixed thresholds applied to registered counts; no discretion. The counts are already known from the pre-run checks: minimum 180 and mean 188 rankable stocks; 198 fill events in total, far below 5% |
| Confirmation classification (confirmed / consistent / not confirmed) | **B** | A fixed three-way rule applied to two registered results |
| Holm correction | **B** | Arithmetic on registered p-values |
| Benjamini–Hochberg q-values | **B** | Same |
| Long-only inflation test H2d (W_A − W_D) | **B** | Computed from the registered monthly series |
| One-sided existence test H3 | **B** | Same |
| Survival test H4 | **B** | Needs costs and saved holdings; blocked by cost evidence, not by the primary run |
| Investable total distortion (A − E) | **B** | Same as H4 |
| Capacity | **B** | Descriptive; needs saved holdings |
| Turnover for steps A–C | **B** | Needs saved holdings |
| Information ratio | **B** | From the registered monthly series |
| Deflated Sharpe ratio | **B** | Needs the final trial count, which exists only after every specification has run |
| Reverse-order ladder (R-order) | Done | Implemented and tested; runs with the primary |
| R-half, R-pool, R-mono | **B** | Computed from the registered monthly series |
| R-JK, R-skip, R-bp, R-wt, R-entry | **B, with a timing limit** | New pipeline runs with other parameters. Allowed after the primary result only as new files; if they need a change to the hashed pipeline files, only after the confirmation run |
| R-cost (brokerage 0.03%; estimated spreads) | **B** | Cost variants on saved holdings |
| Liquidity band 201–500 (H5) | **B, with the same timing limit** | A new universe and a new pipeline run |
| Tables | **B** | Rendering of registered outputs |
| Figures | **B** | Same |
| R-ext (public IIMA factor) | **C** | The protocol makes it conditional on archiving that file |
| Regime analysis; prospective months; futures-based short leg; IIMA alpha | **C** | Outside the protocol |

**Caution on class B.** These analyses are fixed in §16–§17, so adding them later does not change the protocol. But code written after the primary result is seen can still drift toward it. Two safeguards: write each one against the protocol text, and register it in `registry/trials.jsonl` when it runs.

## 3. Cost evidence acquisition list

Nothing is assumed. No external search was made. Trades in the study fall between **2012-07-02 and 2026-09-01**, so that is the period every rate must cover.

| Input | Period needed | Authoritative source type | One source for the whole period? | Did the rate change? | Exact missing evidence |
|---|---|---|---|---|---|
| Delivery STT, buy | 2012-07-02 → 2026-09-01 | The Finance Act provisions on securities transaction tax and each amending Finance Act; or the tax department's rate table; or exchange circulars announcing each rate | Only if it is a dated rate history. A current rate page does not cover the past | **Not established.** The protocol records a reported change taking effect on 2012-07-01, the first day of the sample; unverified | A dated statement of the delivery-purchase rate for every sub-period, including confirmation of what applied on 2012-07-02 |
| Delivery STT, sell | same | same | same | Not established | Same, for delivery sales |
| Stamp duty, delivery buy | 2012-07-02 → 2026-09-01 | Government notification of stamp-duty rates on securities; exchange circulars; for earlier years, the state schedules that applied | **No.** The protocol states a uniform national rate from July 2020 and state-wise rates before; unverified | Yes, per the protocol's own note | (a) the notification and effective date of the uniform rate; (b) what applied from 2012-07 to that date. A single national figure may not exist for (b) |
| Brokerage, delivery | same | The charge schedule of the broker the study assumes, with dated history | No. It is specific to a broker and a date | Not established | The broker assumed, and its delivery brokerage for each sub-period |
| Depository charge per stock sold | same | Depository tariff and the broker's schedule, with dated history | No | Not established | The rupee fee per stock sold for each sub-period, including taxes on it |

Already archived (current rates only): exchange transaction charge + IPFT, SEBI turnover fee, GST (`docs/evidence/cost_sources.md`, NSE circular FA/73061). **Their history is not archived either.**

**A point for your decision, not resolved here.** You instruct that current rates must not be used as historical rates. The frozen §13 says: "Where a historical rate cannot be evidenced, the current rate is applied to the whole sample and labelled as an assumption." Your instruction is stricter than the frozen fallback. If full history cannot be found for some input (stamp duty before 2020 is the likely case), one of the two must give way. No rate has been used so far, so nothing has to be undone.

## 4. What blocks primary authorisation

### 4.1 Stage 2 rebuild (protocol §4, §25)
`python3 scripts/build_stage2.py` must pass all 150 checks before the study runs. Not possible at about 1.3 GB free. See section 5.

### 4.2 Two pieces of pipeline code
1. The four sensitivity treatments R-span, R-gap, R-miss, R-delist, and the comparison of H1 across them.
2. Saving holdings and end-weights when the primary run executes.

Both touch the hashed pipeline files. After they are added, the Stage 3 manifest must be refreshed and the pre-run checks run again, because the checks are tied to the code hash.

### 4.3 Costs — one of two ways
- (a) archive the five missing rates with history (section 3), or
- (b) take step E out of the primary run mode, so the gross primary experiment (H1 on δ) can run and step E and H4 follow when the evidence is archived. This is a change to the runner only; the protocol is untouched, because δ is gross.

### 4.4 Your authorisation
- to generate the blinded precision artifact (it computes δ internally and outputs dispersion only);
- then, separately, to run the primary sample.

## 5. Stage 2 rebuild requirement

- **Current state:** about 1.3 GB free. The macOS update staging area (`/System/Volumes/Update`, 16 GB, last written 18:51 today) is unchanged. Nothing was deleted or cleaned.
- **What the rebuild needs:** it writes almost nothing to the project (Phase 2 artifacts are rebuilt in memory). Its need is memory: peak footprint about 10.9 GB on a machine with 8 GB of RAM, so macOS must create swap files on the same disk.
- **Observed:** it passed three times today with about 11 GB free, and swap grew to 3 GB.
- **Minimum:** not measured below 11 GB. A reasoned floor is about **6 GB free** (observed swap of 3 GB, plus room for it to grow, plus working margin). **Recommended: at least 8 GB free.** Below that I would not start it.
- It should run with other large applications closed.

## 6. Placebo — diagnostic metadata only

| Sample | Random-ranking placebo, p-value of the random WML mean | Rule (fixed) | Outcome |
|---|---|---|---|
| Primary | 0.4725 | p > 0.05 | pass |
| OOS | 0.054 | p > 0.05 | pass |

These describe **random** portfolios. They are not evidence for or against the momentum hypothesis. The threshold was not changed and will not be.

## 7. §22 special cases — counts only

| Case | Count |
|---|---|
| Member-months with no price at the exit session | 70 (51 primary, 19 OOS) |
| … that trade again later | 41 |
| … that never trade again | 29 member-months, 28 entities |
| Resumption rows flagged in RET-1.1 | 12 of 41 (2 with a scheme/demerger record, 10 beyond the 1.4× bound) |
| Never-resumed entities with no delisting evidence, receiving −30% | 26 of 28 |
| Never-resumed entities with a voluntary delisting, receiving 0% | 2 of 28 |
| Primary-sample cases whose resumption falls after 2022-01-03 | 2 |

The frozen behaviour is retained exactly. No return of these cases was calculated for this report or disclosed.

## 8. Summary

**Blocking**
1. Stage 2 rebuild check (disk space).
2. Sensitivity treatments R-span, R-gap, R-miss, R-delist.
3. Saving holdings at the primary run.
4. Costs: archive five rates, or take step E out of the primary run mode.
5. Generation of the blinded precision artifact (needs authorisation).

**Not blocking** (class B or C): Holm, Benjamini–Hochberg, H2d, H3, H4, H5, investable total distortion, capacity, turnover A–C, information ratio, reliability labels, confirmation classification, deflated Sharpe ratio, R-half, R-pool, R-mono, R-JK, R-skip, R-bp, R-wt, R-entry, R-cost, tables, figures, and everything optional.

**Minimum work before primary authorisation**
1. Free at least 8 GB of disk (the macOS update), then run the Stage 2 rebuild and confirm 150 of 150.
2. Add the four sensitivity treatments and the saving of holdings; test on synthetic data.
3. Decide 4.3 (a) or (b).
4. Refresh the Stage 3 manifest and rerun the pre-run checks under the final code hash.
5. Authorise and generate the blinded precision artifact; record its hash.
6. Authorise the primary run.

---

## 9. Update after the final implementation pass (2026-10-05, later)

No protocol text changed. The experiment has still NOT been run.

### 9.1 Blocking items — status now
| Item | Status |
|---|---|
| Sensitivity treatments R-span, R-gap, R-miss, R-delist | **Done and tested.** Six labelled variants: `R_SPAN`, `R_GAP`, `R_MISS_RAW`, `R_MISS_ZERO`, `R_DELIST_ZERO`, `R_DELIST_MINUS100`. Each reruns step D only and pairs it with the primary step A |
| Fixed "not reliable" labels (§25) | **Done and tested.** Rankable minimum 100 and mean 150; more than 5% of W or L stock-days filled; change of sign or significance of H1 or H3 under any treatment |
| Saving holdings and end-weights | **Done and tested.** Written with each run as `*_holdings.csv` |
| Costs in the primary run | **Resolved by the protocol text** (9.3). Step E reports `COST-EVIDENCE-PENDING` |
| Stage 2 rebuild, 150 of 150 | **NOT run.** Free disk still about 1.3 GB; macOS update staging unchanged. **Still blocking** |
| Blinded precision artifact | Not generated. Not yet ready for authorisation, because the Stage 2 rebuild has not passed |

### 9.2 The primary calculation did not change
A SHA-256 fingerprint of the internal A–D monthly output and W/L memberships was taken before and after the code change, for both samples. Only the hash was looked at.

| Sample | Fingerprint | Before = after |
|---|---|---|
| Primary | `23ab567a…53f07` | yes |
| OOS | `1a1a3d0c…ff35` | yes |

### 9.3 Cost mode, checked against the frozen text
- No sentence of the protocol requires step E to execute in the same run as the gross primary estimand.
- §2 defines the estimand on gross returns. B1.4 defines step E as "Step D net, under each scenario". §3 makes H4 a secondary test "tested only if H3 is rejected". §32 (blocker B2) says the missing cost evidence affects "Step E; H4; anchor 1 of §27. **Not** the primary estimand".
- "The primary historical sample is run once" (B3) is kept: the pipeline runs once and saves the holdings; step E is a deduction applied to those saved holdings, not a second run.
- So the runner no longer needs cost evidence to start the primary mode. It then writes step E, H4 and the H4 sensitivity as `COST-EVIDENCE-PENDING`, lists the missing inputs, and computes nothing cost-dependent. The cost functions themselves still refuse any missing rate; nothing can become zero.

### 9.4 Frozen §13 fallback
Each cost input now carries a `basis`:
- `HISTORICAL_EVIDENCE` — archived evidence covers 2012-07-02 → 2026-09-01;
- `CURRENT_RATE_ASSUMPTION` — the frozen §13 fallback. It needs archived evidence of the current rate, the period it is assumed for, and a written reason why history could not be evidenced. Every cost output lists these as assumptions; they are never presented as historical fact.

Current state: exchange charge, SEBI fee and GST are labelled `CURRENT_RATE_ASSUMPTION` for the whole period (only the current schedule is archived; no external search has been made). The five delivery inputs remain null and block every cost calculation.

### 9.5 Interpretations made while implementing the treatments (for your confirmation)
- **R-span** ("use the raw two-session return"): applied to every special-session span row, 10,495 rows in the study's entities. One of them is not a clean row in RET-1.1; the literal text makes no exception, so it is included.
- **R-gap** ("when no event is on the row"): "event" is read as RET-1.1 reads it — a parsed bonus/split factor or an unadjustable record (rights, scheme, consolidation and the like). A dividend alone is not an event, as everywhere else in price-return data. 1,130 of 1,192 gap rows qualify. The 1.4× jump bound is not applied, because the frozen sentence does not mention it.
- **R-miss** ("raw return; zero"): two variants, for flagged days in the holding month only. Formation eligibility is unchanged.
- **R-delist** ("0% for all; −100% for all non-voluntary"): two variants; voluntary delistings stay at 0% in the second.
- **H4 under sensitivity:** pending with the cost evidence.

### 9.6 Placebo diagnostics (metadata only)
- primary p = 0.4725
- OOS p = 0.054

Both exceed the fixed 5% rejection threshold; the OOS placebo is close to the threshold and is treated only as a diagnostic. Neither is evidence for or against the primary momentum hypothesis.

Identical values were obtained when the checks were rerun under the final code hash. No threshold was changed and nothing was tuned.

### 9.7 What remains before primary authorisation
1. Free disk space (at least 8 GB recommended), then the Stage 2 rebuild with 150 of 150, recording peak memory, swap and free disk before and after.
2. Then: authorise the blinded precision artifact.
3. Then: authorise the primary run.

---

## 10. Reviewer rulings after the read-only consistency audit (2026-10-05)

None of these touches the primary A–D calculation. Its fingerprint is unchanged (10.4).

### 10.1 R-span — kept as implemented (sensitivity-only interpretation)
- Frozen §16: "R-span — Special-session spans use the raw two-session return." Frozen §20(a) for the primary: "PRIMARY: excluded."
- The sensitivity rule is class-based. Every `SPECIAL_SESSION_SPAN` row takes the raw two-session return in R-span; the protocol names no exception, so none is added.
- 10,495 span rows; 10,494 are inside the 1.4× bound. The one beyond it, **ZEETELE 2024-01-23, stays included in R-span.**
- **That row does not affect the primary A–D result:** in the primary, all span rows are excluded for every stock.

### 10.2 R-gap — "event" is an implementation interpretation, not literal §16 wording
- Frozen §16: "R-gap — Multi-session gaps use the raw gap return when no event is on the row." The sentence does not define "event".
- Operational definition in force: **event = a parsed bonus/split factor OR an unadjustable record. A dividend-only record is not an event.**
- The 1.4× bound is not applied to R-gap, because the frozen sentence does not name it.
- Audit counts:

| Gap rows | Count |
|---|---|
| Total | 1,192 |
| No event | 1,130 |
| … no record at all | 1,085 |
| … dividend-only record | 45 |
| With an event | 62 |
| … parsed factor | 3 |
| … unadjustable record | 59 |

### 10.3 Fill threshold — fixed
- Frozen §25: "more than 5% of stock-days in W or L filled under §20(b)".
- W and L are now tested **separately**. The label fails if W is above 5% **or** L is above 5%. Exactly 5% does not fail. The two are never combined into one denominator.
- Code: `src/stage3/experiment.py`, `fill_shares` and `reliability`. No other reliability logic changed.

### 10.4 After the fix
- Tests: 317 passed (241 baseline + 76 Stage 3), 0 failed.
- Real-data pre-run checks rerun under the new code hash: all passed for both samples; placebo diagnostics unchanged (primary p = 0.4725, OOS p = 0.054; diagnostics only).
- Primary A–D fingerprints unchanged: primary `23ab567a…53f07`, OOS `1a1a3d0c…ff35`.
- Cost inputs: the five delivery inputs remain missing (null). Exchange charge, SEBI fee and GST remain **provisional** current-rate assumptions: frozen §13 permits that treatment only once it is established that their history cannot be evidenced, which has not been done. No cost is computed anywhere.
