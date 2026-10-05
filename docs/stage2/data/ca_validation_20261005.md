# Stage 2 — corporate-action validation (Phase 2D), methodology CA-2

**Run:** 2026-10-05.
**Status:** validation only. No prices were modified; no adjusted dataset was built; no experiments were run.
**Code:** `src/stage2/corporate_actions.py` (CA-2), `src/stage2/panel.py`. Tests: `tests/test_stage2_corporate_actions.py`.
**Outputs** (working tree, uncommitted):
- `data/stage2/validation/ca2_event_validation.csv` — SHA-256 `3045c358…8e`
- `data/stage2/validation/ca2_unexplained_jumps.csv` — SHA-256 `b0db620e…7e`

## 1. Inputs (all ≤ 2026-09-30)

| Input | Range | Volume |
|---|---|---|
| Price panel, scratch (not the 2C dataset): EQ rows of NSE CM bhavcopies from the raw archive (`data/stage2/raw_manifest.jsonl`) | 2005-01-03 → 2026-09-30. Legacy files to 2023-12-31, UDiFF from 2024-01-01 | 7,824,095 rows; 5,369 sessions; 4,435 symbols; **0 parse failures** |
| NSE corporate-action records: 32 archived yearly API responses, 1995–2026 | `to_date` capped at 30-09-2026; EQ series; ex-dates after the cutoff dropped | 42,383 records |

## 2. Method (CA-2)

1. **Parse** `subject` strictly:
   - bonus a:b → f = b/(a+b);
   - split X→Y → f = Y/X;
   - bonus and split together → product.
   - Abbreviations "Bon" and "Spl"/"Fv Spl" are accepted.
   - "Spl" is treated as a **special dividend** when written as "+ spl" or followed by div/dividend/int/&/@/%.
   - **Never adjusted:**
     - **any partial parse** (a split or bonus mentioned without a parseable ratio) → UNPARSED;
     - debenture, preference, NCRPS or DVR bonuses;
     - consolidations;
     - rights;
     - dividends;
     - schemes and demergers.
2. **Combine** all adjusting records of the same symbol and ex-date (product of factors).
3. **Compare with prices.** t0 = last EQ session before the ex-date; t1 = first EQ session within 10 days on or after it. raw = close(t1) / close(t0).
   - **VALIDATED:** |log(raw/f)| < log 1.25, and smaller than |log raw|.
   - **INCONCLUSIVE:** |log f| < log 1.25. A change this small cannot be separated from ordinary daily volatility.
   - **DISCREPANT:** otherwise.
   - **NO_PRICES:** with a reason.
   - Also recorded: whether NSE's PREVCLOSE on t1 equals close(t0) (unadjusted) or close(t0) × f (adjusted).
4. **Jumps:** any session-to-session close ratio above 1.4× or below 1/1.4× counts as *explained* only if an adjusting event for that symbol is within 10 days.

## 3. Results

### Events

| Category | Count |
|---|---|
| Adjusting NSE records | 1,415 |
| → combined symbol/ex-date events | 1,382 (33 combined two or more same-day records) |
| Pre-2006 events (not adjusted; NSE coverage incomplete) | 7 |
| Validated window (ex ≥ 2006-01-01) | **1,375** |
| **VALIDATED** | **1,082** |
| **INCONCLUSIVE** (small factor) | 47 |
| **DISCREPANT** (flagged) | **11** |
| NO_PRICES: no EQ session before ex (usually the record uses a *later* symbol — identity layer 2E) | 139 |
| NO_PRICES: no EQ session within 10 days after ex (suspended / other series / delisted) | 93 |
| NO_PRICES: symbol never in the EQ panel | 3 |
| UNPARSED subjects (never adjusted) | 6 |

**NSE PREVCLOSE on the ex-date** (1,140 priced events): **UNADJUSTED in 1,131**, adjusted in 1, other in 8. → PREVCLOSE must **not** be treated as adjusted, consistent with the 1997 evidence.

### The known events (Phase 2 requirement)

| Event | NSE record | factor | raw close ratio | Status | PREVCLOSE |
|---|---|---|---|---|---|
| RELIANCE bonus 1:1, ex 2024-10-28 | yes | 0.5 | 0.5024 | **VALIDATED** | unadjusted |
| HDFCBANK split ₹2→₹1, ex 2019-09-19 | yes | 0.5 | 0.5033 | **VALIDATED** | unadjusted |
| HDFCBANK bonus 1:1, ex 2025-08-26 | yes | 0.5 | 0.4956 | **VALIDATED** | unadjusted |
| TCS bonus 1:1, ex 2018-05-31 | yes | 0.5 | 0.4954 | **VALIDATED** | unadjusted |
| INFY bonus 1:1, ex 2018-09-04 | yes | 0.5 | 0.5140 | **VALIDATED** | unadjusted |
| **RELIANCE bonus, Nov 1997** | **no NSE record** (0 in 1997) | — | — | **UNKNOWN** (outside panel window; price evidence 354.15 → 182.65 only) | — |
| *Additional:* RELIANCE 2017-09-07 bonus; HDFCBANK 2011-07-14 split ₹10→₹2; TCS 2006-07-28 and 2009-06-16 bonuses | yes | 0.5 / 0.2 / 0.5 / 0.5 | 0.4972 / 0.2008 / 0.4887 / 0.5002 | all **VALIDATED** | unadjusted |

### The 11 DISCREPANT events (flagged, unchanged)

DIAPOWER 2013-08-26, DVL 2021-08-05, GOLDIAM 2026-07-10, HINDCON 2023-11-10, JINDALSTEL 2008-01-21, JMTAUTOLTD 2014-07-30, KWALITY 2010-06-15, LAKSHVILAS 2006-11-17, MINDACORP 2015-01-05, SUMEETINDS 2025-10-03, VKSPL 2013-02-27. Likely causes (not acted on):
- the rights leg not modelled (LAKSHVILAS);
- a convention or text ambiguity (JMTAUTOLTD "5:2", KWALITY "5:7");
- same-day large market moves (JINDALSTEL, 21 Jan 2008 crash);
- PREVCLOSE "OTHER" cases suggesting a different effective date (HINDCON, MINDACORP, SUMEETINDS, VKSPL).

### Unexplained price jumps (beyond 1.4× either way)

| | Count |
|---|---|
| All jumps | 4,791 |
| Explained by an adjusting event within 10 days | 1,044 |
| **Unexplained** | **3,747** |
| → after a gap of more than 1 session (security absent from EQ: suspension or series move) | 2,485 |
| → companies (ISIN INE), consecutive sessions | 957 |
| → no ISIN (before 2011-06-22) | 232 |
| → fund/ETF units (ISIN INF), e.g. 1:10 unit splits of GOLDADD, SILVERADD, PSUBANK | 73 |

Of the 957 company jumps:
- **865 have no NSE corporate-action record of any kind within 10 days**;
- 58 have only an "OTHER" record nearby;
- 18 are rights;
- 10 are schemes or demergers (ABFRL, ARVIND, IDFC, PEL, ADANIENT, ABIRLANUVO);
- 6 have only a dividend nearby.

## 4. Methodological issues discovered

1. **The NSE corporate-action API is incomplete even after 2006.** Per-symbol queries return **no records at all** for HEG (2023–2026) or TIPSINDLTD (2022–2024), although their prices show split-like moves (HEG 2024-10-18 at 0.19×; TIPSINDLTD 2023-04-21 at 0.096×). TATAMOTORS 2025-10-14 (0.60×) also has no record.
   - These are **not** inferred from prices. They stay flagged.
   - A second verified source is needed before adjusted returns can be trusted for all names.
2. **Demergers, schemes and rights are not adjusted** (no defensible rule established yet). They cause real discontinuities.
3. **The EQ series contains ETFs and fund units** (ISIN prefix INF from 2011-06-22). Their unit splits are not in the equity corporate-action feed. The instrument type must be resolved in 2E/2F (no ISIN exists before 2011-06-22).
4. **Corporate-action records often use the current symbol** for old events (139 NO_SESSION_BEFORE_EX). Identity linking (2E) is needed.
5. **The CA-1 → CA-2 changes were made after seeing the first results.** They are evidence and parsing corrections; no price was touched:
   - combining same-day records;
   - abbreviation parsing;
   - special-dividend disambiguation;
   - no adjustment on partial parses;
   - an INCONCLUSIVE status for small factors.

   CA-1 results for the record: 1,080 validated, 67 discrepant, 237 no prices. All CA-2 rule changes are unit-tested and documented in the module header.
6. A robustness bug (duplicate index labels in jump detection) was found by the tests and fixed; the real-run results were identical.

## 5. Boundary confirmation

- Maximum session read: **2026-09-30**. The parser refuses later sessions (tested). Corporate-action requests are capped at 30-09-2026, and later ex-dates are dropped (tested).
- No holdout file (`data/india/*m15.csv`) was read.
- ORB v1 and its methodology are unchanged (frozen-hash tests pass).
