# S2-MOM-v1 — Supplement 3 to Addendum 1: step E input boundary and identifier join

**Status:** APPROVED by the reviewer on 2026-10-06. Registered. Its SHA-256 is recorded in `registry/experiments.jsonl` (record `S2-MOM-v1`) and in `RESEARCH_LOG.md`.

**Parents:**
- Frozen protocol `docs/research/phase3a_momentum_protocol.md`, SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`.
- Addendum 1 `docs/research/phase3a_momentum_protocol_addendum1_costs.md`, SHA-256 `d12ccaa6fa23143f808b429d75c757a57a853afa42e961a94157d3b772dffefe`.
- Supplement 1 `docs/research/phase3a_momentum_protocol_addendum1_supplement1.md`, SHA-256 `ab28fd1750db3e222819013ef70ff69c4b48d5d5757d51ec5c77e9b6232253b3`.
- Supplement 2 `docs/research/phase3a_momentum_protocol_addendum1_supplement2.md`, SHA-256 `6c373c5ff0db321cb753fff7a08db078ff29ca2c3f2f0cfbe8c0fb1431e6a888`.

This supplement is a separate file. No parent is edited, and all four hashes are unchanged.

**Nature.** This is an input-boundary and implementation-methodology amendment only. **It changes no A–D calculation and no existing result.** It adds no scenario and no parameter. It does not change any rate, formula, test or sample of the frozen protocol, Addendum 1, Supplement 1 or Supplement 2.

**Timing.** Specified after the gross primary, sensitivity and confirmation results were known, after Supplement 2 was registered, and after a key-only compatibility check of identifiers (section 4). Specified **before** any real cost, turnover, net return, break-even cost or H4 result was computed, and before any UNIV-1 rank was read for a step E purpose.

## 1. Ruling numbers

- Rulings 1–7 are in Supplement 1. Rulings 8–16 are in Supplement 2.
- The reviewer refers to two decisions as **Ruling 17** and **Ruling 18**. Both are already registered in Supplement 2, inside ruling 11 as amended, and are not restated differently here:
  - **Ruling 17** = the slippage rate is set by the stock's UNIV-1 rank at the selection date of the rebalance at which the order trades, including the sale of a stock that has left the portfolio.
  - **Ruling 18** = a stock ranked above 500, or unranked, at that date takes the frozen 201–500 rate of the same scenario, as a labelled assumption.
- Rulings 19 and 20 are new and are recorded below.

## 2. Ruling 19 — Step E sample scope and input boundary

Step E covers **both** the primary sample and the confirmation sample.

The approved data inputs are exactly these five:

| # | Path | SHA-256 |
|---|---|---|
| 1 | `results/s2_mom_v1/primary_holdings.csv` | `3887995763861a2ed17e280f1f975c6fd716dab4923c954d3ca70b91c2d93748` |
| 2 | `results/s2_mom_v1/primary_monthly.csv` | `f7c8d3ab5a0ef7a08b6a0ca8a12bf26a1f901006c21637cf7886e297b97bb372` |
| 3 | `results/s2_mom_v1/confirmation_holdings.csv` | `96bb174ed2942e7b93630ae445d11817551a44e15b90e5454272ddb79aa825b0` |
| 4 | `results/s2_mom_v1/confirmation_monthly.csv` | `4d88f385375ad681f85be739b292097e2e898acb6acb71013230c67415a43ce3` |
| 5 | `data/stage2/universe/univ1_pit_universe.parquet` | `2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42` |

Rules of the boundary:

- All five inputs are **read-only**.
- **All five are hash-checked before any of them is read.** If any hash differs, the runner refuses to execute and calculates nothing.
- The step E runner has **one** entry in the access-boundary allow-list, covering these five paths and no other. There is no separate approval for the UNIV-1 input.
- UNIV-1 is used as registered. It is not rebuilt and not recomputed.
- No raw market data is read. No file outside this list is read as data.
- `data/stage2/identity/id1_segments.csv` and the RET-1.1 return files are **not** required and are not read.

The dated cost schedule and the parent documents are not data inputs. They continue to be hash-checked on every load, as already implemented and registered.

## 3. Ruling 20 — Identifier join

- The deterministic join is: **holdings `(t, entity)` → UNIV-1 `(selection_date = t, entity_id = entity)`**.
- `segment_at_selection` is **not** the join key.
- No identifier inference and no alternate mapping is permitted. No other identifier and no other date is ever tried.
- The UNIV-1 lookup must be unique. A duplicate key or a null key in UNIV-1 is a **hard failure**.

### 3.1 Guard on the formation rank

For every held stock, at its selection date:

`UNIV-1 rank == holdings.liquidity_rank`

A mismatch is a **hard failure before any cost calculation**. The guard proves that the join returns the row the registered run used.

### 3.2 Exit orders

- The guard of 3.1 applies to the rank at which a stock was held. It is **not** applied to exit orders: the exit-time rank is not compared with the saved `liquidity_rank`.
- For an exit order the runner looks up, independently, the UNIV-1 rank at the selection date of the exit rebalance (Ruling 17).

| UNIV-1 row at the exit rebalance | Slippage rate |
|---|---|
| rank 1–200 | 1–200 rate |
| rank 201–500 | 201–500 rate |
| rank above 500 | 201–500 rate, fallback under Ruling 18, counted and reported |
| row present, no rank (unranked) | 201–500 rate, fallback under Ruling 18, counted and reported |
| **no row, or more than one row** | **hard failure** |

- A missing or duplicate exit lookup is never replaced by another identifier or another date.
- **Clarification of Supplement 2, ruling 11.** Its words "with no UNIV-1 rank" mean a stock that has a UNIV-1 row at that date whose rank is empty. A stock with no UNIV-1 row at that date is not covered by the fallback; it stops the run.

## 4. The key-only compatibility check behind ruling 20

Done on 2026-10-06, after all five input hashes were verified. It read identifier columns only: `step`, `t`, `portfolio`, `entity` from the holdings files, and `selection_date`, `entity_id`, `segment_at_selection` from UNIV-1. No rank, weight, return or price was read. Nothing was calculated except counts of matching keys.

| Step D; W, L and benchmark | Primary | Confirmation |
|---|---|---|
| Distinct held stocks found in UNIV-1 `entity_id` | 502 of 502 | 389 of 389 |
| Held (date, stock) pairs found at the same date | 21,405 of 21,405 | 10,491 of 10,491 |
| Exit (date, stock) pairs found at the exit rebalance | 3,120 of 3,120 | 1,667 of 1,667 |

- `(selection_date, entity_id)` is unique in UNIV-1: no duplicate and no null in 318,208 rows.
- `segment_at_selection` has nulls, is not unique per date, and matches only part of the holdings.
- The check matched identifier strings. It did not read ranks, so it does not show whether an exit row carries a rank, and it does not replace the guard of 3.1.

## 5. What remains open

- **B3 and B4 remain OPEN** and are separate from this supplement.
- Step E is not implemented for rulings 8–20 and has not been run. No runner exists and no access-boundary entry has been added. No real cost, turnover, net return, break-even or H4 result has been calculated.
- Execution of step E needs separate, explicit authorisation.
