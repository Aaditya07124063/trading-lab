# Stage 2 — Phase 2 data foundation: final report (2026-10-05)

> **Phase 2.1 (2026-10-05):** special sessions, reproducibility and large residuals were addressed in `phase2_1_fixes_20261005.md`. That document supersedes the calendar statements in §2–3 and the RET-1 status table in §8 for RET-1.1. RET-1 itself is unchanged.
>
> **Approved decisions (2026-10-05):** large-residual threshold fixed at 10% (predefined diagnostic rule); `SPECIAL_SESSION_SPAN` rows stay outside research-grade; weekday special sessions are left unclassified (calendar-source limitation); the 2012-11-11 file is kept. "Research-grade" means passing predefined data-quality rules, not proof that the market history is error-free. See the "Review decisions" section of that document.

**Scope:** data foundation only. No strategy experiments, no ML, no performance studies. Nothing after 2026-09-30 was read, and no ORB holdout file was read.

**Detailed reports:**
- `source_coverage_20261003.md` (2A)
- `ca_validation_20261005.md` (2D)
- `identity_20261005.md` (2E)
- `universe_20261005.md` (2F)
- `returns_20261005.md` (2G)

**Consolidated manifest:** `data/stage2/PHASE2_MANIFEST.json`.

## 1. Historical coverage obtained

- **Raw NSE CM bhavcopy archive:** 2005-01-03 → 2026-09-30.
  - Legacy format to 2024-07-05; UDiFF from 2024-01-01.
  - 5,494 files (4,816 legacy + 678 UDiFF), 396 MB, outside git, SHA-256 in `raw_manifest.jsonl`.
- **PANEL-1** (normalised EQ panel, raw values unchanged): 2005-01-03 → 2026-09-30.
- **Verified period** (ISIN-bearing; UNIV-1 and RET-1): **2011-06-22 → 2026-09-30**.
- **Pre-2011-06-22 data:** preserved, but not represented as point-in-time verified.

## 2–3. Securities and sessions

| Item | Count |
|---|---|
| Panel rows | 7,824,095 |
| Sessions | 5,369 (verified period: 3,768) |
| Symbols | 4,435 |
| 2E entities | 5,861 (all eras) |
| Verified-period entities | 3,683 |
| UNIV-1 members | 687 distinct entities, 200 per date, 181 monthly dates |

**Calendar check:**
- 5,673 weekdays = 5,369 sessions + 304 recorded non-trading days. **0 days were never attempted.**
- The 2026 non-trading days exactly match NSE's stored holiday list.

## 4. Delisted securities retained

- **All** delisted and ended entities are retained historically.
- 206 delistings are evidenced by NSE `delisted.csv`. That list only covers 2002 → Nov 2020.
- 2,986 entities ended without a recorded reason.
- 126 UNIV-1 member entities later ended (21 evidenced delistings, 105 unexplained). Their membership is kept on every earlier date.

## 5. Symbol / ISIN transitions (evidence links, ID-1)

| Link type | Count |
|---|---|
| SYMBOL_CHANGE | 599 |
| ISIN_SAME | 495 |
| ISIN_CHANGE_CA | 439 (25 via a record filed under a later symbol) |
| ISIN_INTRO | 1,427 |
| Return rows crossing an evidenced identity transition | 934 |

**Unresolved:**
- 89 ISIN changes with no NSE record;
- 2 symbol changes whose ISINs conflict;
- 1,892 pre-2011 symbol gaps.

## 6–7. Corporate actions (CA-2; adjustments only from 2006, when NSE records become comprehensive)

**Validated:**
- 1,082 of 1,375 bonus/split events (2006+) validated directly.
- 104 more validated after identity resolution of records filed under a later symbol.
- All six known-event fixtures validated, except RELIANCE 1997: **UNKNOWN** (no NSE record; outside the window).
- 825 return rows carry a validated adjustment (RET-1).

**Unresolved:**
- 47 inconclusive (small factors);
- 11 discrepant;
- 235 without usable prices (114 later resolved by identity; 25 remain unresolved);
- 6 UNPARSED subjects (never adjusted).

**NSE's corporate-action source is incomplete** (e.g. HEG 2024, TIPSINDLTD 2023 have no records). Of 865 company jumps with no same-symbol record, 47 were explained by identity evidence and **818 remain flagged**.

## 8. Exclusions and reasons

**PANEL-1 QA:**
- 0 duplicate symbol-dates;
- 0 impossible OHLC;
- 0 non-positive or missing prices;
- 0 bad volume or value;
- 0 identity conflicts;
- 1,708,333 pre-2011 rows without an ISIN (format, not an error).
- **Format discrepancy:** the legacy and UDiFF files differ on 3 stock-days, ISIN only: BDL and SDBL on 2024-05-24, KAMOPAINTS on 2024-06-14. They look like split ex-dates where UDiFF already shows the new ISIN. UDiFF is used per the rule; this is documented and not resolved.

**UNIV-1 exclusion rows:**

| Reason | Rows |
|---|---|
| NOT_TRADED_ON_SELECTION_DATE | 23,580 |
| INSUFFICIENT_HISTORY | 19,684 |
| FUND_UNIT | 18,915 |
| NON_EQUITY_ISIN | 526 |

**RET-1 non-research-grade rows** (99.24% of rows are research-grade):

| Status | Rows |
|---|---|
| MULTI_SESSION_GAP | 41,283 |
| FIRST_OBSERVATION | 3,683 |
| UNEXPLAINED_JUMP | 914 |
| EVENT_UNADJUSTABLE | 316 |
| EVENT_INCONCLUSIVE | 44 |
| EVENT_DISCREPANT | 4 |

- 125 UNIV-1 member entities have at least one unresolved discontinuity somewhere in their history (list provided).
- Within members' holding periods, 129 of 738,765 rows (0.017%) are not research-grade.

## 9. Universe methodology (UNIV-1, approved and frozen 2026-10-05)

- **Data:** verified period, EQ series only.
- **Rebalance:** last session of each month; membership effective from the next session.
- **Exclusions:** fund/ETF ISINs (INF) and non-INE ISINs.
- **Minimum history:** at least 50 valid sessions out of the trailing 63.
- **Liquidity:** median daily traded value over the trailing 63 sessions, with missing days counted as 0.
- **Selection:** top 200; ties broken by lower `entity_id`.
- **Identity:** point-in-time, using only links effective on the selection date; the entity ID is its earliest listing.
- **Never used:** future information, current index lists, or anything from strategy results.

## 10. Index / VIX coverage (NSE `ind_close_all`)

- First file **2012-02-21**; nothing in Sep 2011 – Jan 2012 or at the 1995–2011 samples.
- NIFTY 50 naming changed: "S&P CNX Nifty" → "CNX Nifty" → "Nifty 50".
- Sector indices: about 9–10 in 2012, rising to 37 in 2026.
- **India VIX** from the week of **2014-05-19**.
- Only the 2026 NIFTY 50 history (184 closes) is stored as evidence (ORB regime source). **No market-context dataset has been built yet.**

## 11. Dataset checksums

All in `data/stage2/PHASE2_MANIFEST.json`:
- the raw manifest SHA-256;
- 22 PANEL-1 and 16 RET-1 generated files (outside git; rebuildable);
- the UNIV-1 dataset, which is **tracked in git** as the frozen universe (corrected in Phase 2.1; the original text wrongly said outside git);
- 16 committed metadata files.

**UNIV-1 dataset SHA-256:** `2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42`.

## 12. Tests

233 pass (124 before Phase 2), including:

| Area | Tests |
|---|---|
| Corporate actions | 29 |
| Identity | 10 |
| Universe | 10 |
| Returns | 15 |
| Panel | 6 |

Phase 1 boundary and frozen-ORB hash tests still pass.

Mutation checks:
- the point-in-time universe window shifted into the future → caught;
- adjustment applied without validation → caught, after strengthening one test.

## 15. Confirmations

- No data after 2026-09-30 was read: every builder refuses later dates, and this is tested.
- No ORB holdout file or performance was read or computed.
- No ML was trained and no Stage 2 strategy experiment was run.
- ORB v1 is unchanged; protocol SHA-256 `9c9cc1fc…`.
