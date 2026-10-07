# S2-MOM-v1 — Supplement 4 to Addendum 1: scope of the formation-rank guard (ruling 21)

**Status:** APPROVED by the reviewer on 2026-10-06. Registered. Its SHA-256 is recorded in `registry/experiments.jsonl` (record `S2-MOM-v1`) and in `RESEARCH_LOG.md`.

**Parents:**
- Frozen protocol `docs/research/phase3a_momentum_protocol.md`, SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`.
- Addendum 1 `docs/research/phase3a_momentum_protocol_addendum1_costs.md`, SHA-256 `d12ccaa6fa23143f808b429d75c757a57a853afa42e961a94157d3b772dffefe`.
- Supplement 1 `docs/research/phase3a_momentum_protocol_addendum1_supplement1.md`, SHA-256 `ab28fd1750db3e222819013ef70ff69c4b48d5d5757d51ec5c77e9b6232253b3`.
- Supplement 2 `docs/research/phase3a_momentum_protocol_addendum1_supplement2.md`, SHA-256 `6c373c5ff0db321cb753fff7a08db078ff29ca2c3f2f0cfbe8c0fb1431e6a888`.
- Supplement 3 `docs/research/phase3a_momentum_protocol_addendum1_supplement3.md`, SHA-256 `682191de462bac3b5d2901995be8d20d355bb4d6146fd87a3f02ed8c6c2580ce`.

This supplement is a separate file. No parent is edited, and all five hashes are unchanged.

**Purpose.** It formally registers ruling 21, which the reviewer approved on 2026-10-06 during the review of the step E implementation. It makes no other methodological change.

**Timing.** Specified after the gross primary, sensitivity and confirmation results were known, after Supplements 2 and 3 were registered, and after step E was implemented and tested on made-up data only. Specified **before** any real cost, turnover, net return, break-even cost or H4 result was computed, and before any UNIV-1 rank was read for a step E purpose. Step E has not been run.

## 1. What this supplement clarifies

Supplement 3, section 3.1 ("Guard on the formation rank") reads: "For every held stock, at its selection date: `UNIV-1 rank == holdings.liquidity_rank`."

Ruling 21 fixes the scope of the words "every held stock". The rest of Supplement 3 stands as written, including section 3.2 on exit orders and ruling 20 on the identifier join.

## 2. Ruling 21 — Formation-rank guard scope

1. The formation-rank equality guard applies **only** to W and L selected/held stocks.
2. For every W/L stock:
   - the saved formation `liquidity_rank` must equal the corresponding UNIV-1 rank at the formation/selection date;
   - a missing, empty or null saved rank is a hard failure;
   - a missing, duplicate, malformed or invalid UNIV-1 key or rank is a hard failure;
   - a mismatch is a hard failure before any step E cost calculation.
3. The benchmark is **not** subject to the formation-rank equality guard.
   - The benchmark's saved `liquidity_rank` is ignored for this guard.
   - Benchmark slippage still requires a strict UNIV-1 lookup at the relevant trading rebalance.
   - A missing row, a malformed or duplicate key, or an invalid rank in that lookup remains a hard failure.
4. This is a scope clarification of Supplement 3 §3.1. It changes no step E formula, rate, cost convention, portfolio definition, slippage scenario, H3/H4 rule, break-even rule, or A–D result.
5. The clarification is applied identically to the primary and the confirmation sample.
6. No benchmark formation-rank equality requirement may be introduced elsewhere.

## 3. Reason

The guard proves that the join returns the UNIV-1 row the registered run used when it selected a stock into W or L. The benchmark is not a W/L ranked-stock selection portfolio. Requiring benchmark rows to carry a matching `liquidity_rank` would impose the W/L selection invariant on a different portfolio construction.

## 4. What does not change

- **No A–D calculation and no existing result changes.**
- The join of ruling 20 is unchanged for every portfolio, the benchmark included: holdings `(t, entity)` → UNIV-1 `(selection_date = t, entity_id = entity)`; no other identifier and no other date.
- The slippage band of every order, the benchmark's included, still comes from the UNIV-1 rank at the selection date of the rebalance at which the order trades (Supplement 2 ruling 11; Supplement 3 §3.2).
- The five approved inputs of ruling 19 and their hashes are unchanged.
- Rulings 1–20 stand.

## 5. References

- Supplement 3, sections 3.1 and 3.2, and section 1 for the ruling numbers.
- Supplement 2, ruling 11 (slippage) and ruling 14 (costed portfolios).
- The step E implementation that applies this ruling: `src/stage3/step_e.py` (`RANK_GUARDED`, `check_formation_ranks`, `rank_at`, `band`), SHA-256 `17e1908270bf544878164ed6b0704af5ba74a7a440055684f78b0cc56c397554` when this supplement was written.
- The record of the ruling at the time it was given: `docs/research/s2_mom_v1_step_e_full_implementation_report_20261006.md`, section 3a, and the entry of 2026-10-06 in `RESEARCH_LOG.md`.

## 6. What remains open

- **B3 and B4 remain OPEN** and are separate from this supplement.
- Step E is implemented and tested but has not been run. No real cost, turnover, net return, break-even or H4 result has been calculated.
- Execution of step E needs separate, explicit authorisation.
