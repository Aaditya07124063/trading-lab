# Stage 2 data foundation — NSE source-coverage audit (Phase 2A)

**Audited:** 2026-10-03, by direct requests to NSE servers. Raw responses were inspected but no dataset was built during the audit.
**Cutoff:** nothing dated after **2026-09-30** is requested for research (`src/access.py`).

**Licence / usage:** NSE archive files are published publicly on nseindia.com. NSE's website terms apply; redistribution rights are not established. Raw files are therefore kept **outside git**; only checksums, manifests and derived metadata are committed.

## 1. Daily equity bhavcopy (CM segment)

| Source | URL pattern | Verified coverage | Fields |
|---|---|---|---|
| **Legacy CM bhavcopy** | `https://nsearchives.nseindia.com/content/historical/EQUITIES/{YYYY}/{MON}/cm{DD}{MON}{YYYY}bhav.csv.zip` | **1995-01-02 → 2024-07-05** (none found in Jan or Jul 1994; last file 2024-07-05) | `SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, TOTTRDVAL, TIMESTAMP`; **`TOTALTRADES, ISIN` from 2011-06-22** |
| **UDiFF CM bhavcopy** | `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{YYYYMMDD}_F_0000.csv.zip` | **2024-01-01 →** present (none in any month of 2023) | `TradDt, BizDt, Sgmt, Src, FinInstrmTp, FinInstrmId, ISIN, TckrSymb, SctySrs, …, OpnPric, HghPric, LwPric, ClsPric, LastPric, PrvsClsgPric, …, TtlTradgVol, TtlTrfVal, TtlNbOfTxsExctd, SsnId, NewBrdLotQty, …` |

- **Format overlap 2024-01-01 → 2024-07-05.** On 2024-03-01 all 1,782 EQ rows were identical across formats (OPEN, CLOSE, PREVCLOSE, volume, value, trades and ISIN all exactly equal). Units are therefore the same: value in ₹ (TOTTRDVAL = TtlTrfVal). The builder re-checks **every** overlap day.
- **Timestamp semantics:** one file per trading session (end of day). A weekday with no file (HTTP 404) is a non-trading day per NSE's archive; it is recorded, never imputed.
- **Delisted securities are present.** Example: `SATYAMCOMP` (EQ) appears on 2008-01-01. The archive is a point-in-time list of what traded each day, so it is survivorship-free by construction.
- **Series:** EQ plus others (BE, N*, W*, …). The research panel uses **EQ only**, as decided.

## 2. Corporate actions

| Source | Access | Verified coverage |
|---|---|---|
| NSE corporate actions | `https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date=DD-MM-YYYY&to_date=DD-MM-YYYY` (needs a session cookie from nseindia.com; JSON) | **Records per year: 81–247 for 1995–2004, then 829 (2005), 1,156 (2006) and 1,500–2,700 per year from 2007.** Bonus/split records: 0–2 per year before 2006, then 15–130 per year from 2006 |

- **Fields:** `symbol, comp, series, isin, faceVal, subject, exDate, recDate, bcStartDate, bcEndDate, ndStartDate, ndEndDate, caBroadcastDate, ind`.
- **`subject` is free text** and can combine events, e.g. "Bonus 1:1 /Dividend- Rs 29 Per Share" or "Face Value Split (Sub-Division) - From Rs 2 Per Share To Rs 1 Per Share".
- **Conclusion:** NSE corporate-action evidence is **comprehensive only from 2006**.
  - Adjusted price series are built only for **2006-01-01 → 2026-09-30**.
  - Earlier prices are kept raw and flagged "corporate-action coverage incomplete".
- **Without** an NSE record:
  - **RELIANCE bonus, November 1997.** Price evidence: 354.15 → 182.65 on 1997-11-05. NSE corporate-action evidence: **UNKNOWN**. It falls outside the adjusted window.
- **Found** in NSE records:
  - RELIANCE bonus 1:1, ex 2017-09-07;
  - RELIANCE bonus 1:1, ex 2024-10-28;
  - RELIANCE rights 1:15 @ ₹1,247 premium, ex 2020-05-13;
  - HDFCBANK split ₹10→₹2, ex 2011-07-14;
  - HDFCBANK split ₹2→₹1, ex 2019-09-19;
  - HDFCBANK bonus 1:1, ex 2025-08-26;
  - INFY bonus 1:1, ex 2018-09-04;
  - TCS bonus 1:1, ex 2006-07-28, 2009-06-16 and 2018-05-31.

## 3. Identity and listing evidence (current snapshots; entries dated after 2026-09-30 are ignored)

| File | URL | Content |
|---|---|---|
| Symbol changes | `https://nsearchives.nseindia.com/content/equities/symbolchange.csv` | company, old symbol, new symbol, date |
| Name changes | `https://nsearchives.nseindia.com/content/equities/namechange.csv` | symbol, previous name, new name, date |
| Delisted | `https://nsearchives.nseindia.com/content/equities/delisted.csv` | symbol, company, delisted date, type |
| Listed equities | `https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv` | symbol, name, series, listing date, paid-up value, lot, ISIN, face value |

## 4. Index closes (NSE `ind_close_all_DDMMYYYY.csv`)

| Item | Verified |
|---|---|
| URL | `https://nsearchives.nseindia.com/content/indices/ind_close_all_{DDMMYYYY}.csv` |
| First file found | **2012-02-21** (none in Sep 2011 – Jan 2012; none at the March/September samples of 1995–2011) |
| NIFTY 50 naming | "S&P CNX Nifty" (2012) → "CNX Nifty" (2013–2015) → "Nifty 50" (2016+). This needs a name-map, with evidence |
| Sector indices (Bank, IT, Pharma, Auto, FMCG, Metal, …) | about 9–10 in 2012, rising to 37 by 2026 |
| **India VIX** | first present in the week of **2014-05-19** (absent at 2014-03-03 and in the weekly scan up to then) |
| Index count per file | 30 (2012) → 146 (2026) |

**Implication:** market-context series from this source cover only **2012+** (VIX 2014+). The pre-2012 context would need another verified source; none is assumed.

## 5. Not available / not verified
- Dividend-adjusted (total-return) prices: no NSE adjusted-price file was found. Dividend **records** exist in the corporate-action source (2006+ comprehensive) but are not applied (§2G limitation).
- Pre-2006 corporate actions: incomplete (above).
- Index history before 2012-02-21 from this archive.
