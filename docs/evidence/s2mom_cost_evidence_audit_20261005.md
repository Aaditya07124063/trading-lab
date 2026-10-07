# S2-MOM-v1 — cost-evidence acquisition audit (2026-10-05)

**Purpose:** find out whether the cost evidence required by frozen §13 can be obtained without changing the frozen methodology. Audit only.

**What this is not:** it is not archived evidence, and it sets no rate. Nothing found here was copied into the archive. No cost and no return was calculated. No protocol, code or result file was changed.

**Period every rate must cover:** 2012-07-02 (first trade) to 2026-09-01 (last trade).

**How sources are labelled**
- **ARCHIVED** — a copy is in `docs/evidence/` today.
- **LOCATED-OFFICIAL** — an official document was opened and read on 2026-10-05, but is not archived.
- **LOCATED-BROKER** — a broker's own page was opened and read, not archived.
- **SECONDARY** — reported by a non-official page or a search summary only. Not evidence.
- **NOT FOUND** — not located in this audit.

A page that was read but not copied is **not** archived evidence. "Current rate evidenced" and "historical rate evidenced" are kept apart throughout.

## 1. Status of the eight inputs

| # | Input | Rate expected by frozen §13 | Current rate | History 2012–2026 |
|---|---|---|---|---|
| 1 | Delivery STT, buy | 0.100% | LOCATED-BROKER (Zerodha charges page: "0.1% on buy & sell"). Not archived | SECONDARY only. Official document NOT FOUND |
| 2 | Delivery STT, sell | 0.100% | same | same |
| 3 | Stamp duty, delivery buy | 0.015% | LOCATED-OFFICIAL in search results (PIB release, 30 Jun 2020), page itself not opened; LOCATED-BROKER (0.015% on the buy side). Not archived | From 2020-07-01: as left. Before: state-wise, no single national rate (SECONDARY) |
| 4 | Brokerage, delivery | 0 | LOCATED-BROKER ("Zero Brokerage"). Not archived | LOCATED-BROKER in search results for the 2015 change; page not opened |
| 5 | Depository charge per stock sold | no number in §13 | LOCATED-BROKER: ₹15.34 per scrip per sell day. Not archived | NOT FOUND |
| 6 | Exchange transaction charge + IPFT | 0.00307% each side | **ARCHIVED** (NSE/FA/73061, 27 Feb 2026) | 2021–2026 LOCATED-OFFICIAL (three NSE circulars, not archived); 2012–2020 NOT FOUND |
| 7 | SEBI turnover fee | 0.0001% each side | ARCHIVED only as a note about two broker pages (`cost_sources.md`). No official source archived | Partly LOCATED-OFFICIAL (SEBI board memorandum, March 2019). Exact effective dates NOT FOUND |
| 8 | GST | 18% of brokerage + exchange + SEBI | ARCHIVED only as the same note | SECONDARY only |

**No input has archived evidence covering the whole period. Only input 6 has an archived official source, and only for the current rate.**

## 2. Rate timelines, where established

Each line gives the label of its support. Nothing below is taken from memory.

### 2.1 Delivery STT (inputs 1, 2)
| Period | Rate, buy and sell | Support |
|---|---|---|
| to 2012-06-30 | 0.125% | SECONDARY |
| 2012-07-01 → present | 0.100% | SECONDARY for the change (Finance Act 2012; an NSE circular is described but was not found); LOCATED-BROKER for the current rate |

- No change to the delivery rate after 2012-07-01 was found. That is absence of a finding, not proof.
- The whole study period (from 2012-07-02) lies after the reported change.
- **To archive:** the Finance Act 2012 provision amending the STT schedule (Chapter VII, Finance (No. 2) Act 2004), or the tax department's dated STT rate table, or the NSE circular of mid-2012. Plus one official statement of the rate in force in 2026.

### 2.2 Stamp duty, delivery buy (input 3)
| Period | Rate | Support |
|---|---|---|
| 2012-07-02 → 2020-06-30 | No single national rate; charged by the client's state | SECONDARY |
| 2020-07-01 → present | 0.015% on the buyer | LOCATED-OFFICIAL in search results: Ministry of Finance press release, PIB PRID 1635399, 30 Jun 2020 |

- **To archive:** that PIB release; the notifications of 30 March 2020 it cites; the Indian Stamp Act schedule as amended by the Finance Act 2019.
- For the earlier period a single historical rate does not exist. See 4.

### 2.3 Brokerage, delivery (input 4)
| Period | Rate at Zerodha | Support |
|---|---|---|
| to 2015-11-30 | lower of 0.1% or ₹20 per order | SECONDARY (search summary of a Zerodha post) |
| 2015-12-01 → present | zero | LOCATED-BROKER in search results (Z-Connect post of 30 Nov 2015, not opened); current page read |

- **Specification gap:** frozen §13 says "0 … discount-broker delivery" and names no broker. Brokerage is specific to a broker. The evidence above is for one broker.
- A per-order rupee fee before December 2015 cannot be turned into a rate without an order size.

### 2.4 Depository charge per stock sold (input 5)
| Period | Fee | Support |
|---|---|---|
| current | ₹15.34 per scrip per sell day = ₹3.50 CDSL fee + ₹9.50 Zerodha fee + ₹2.34 GST | LOCATED-BROKER (Zerodha charges page, read 2026-10-05) |
| 2012–? | — | NOT FOUND |

- Broker-specific, like brokerage. The depository's own part is ₹3.50; the rest is the broker's.
- **To archive:** the broker charges page with date; the depository (CDSL) tariff circular; dated history of both.

### 2.5 Exchange transaction charge, NSE cash market (input 6)
Until 30 Sep 2024 the charge was **slab-based on the trading member's monthly turnover**. Figures are ₹ per lakh of traded value, each side, lowest slab (up to ₹1,250 crore a month) to highest slab.

| Period | Transaction charge | Support |
|---|---|---|
| 2012 → Dec 2020 | — | NOT FOUND |
| Jan 2021 → 2023-03-31 | 3.45 … 3.20 | LOCATED-OFFICIAL: NSE/FA/56129 (24 Mar 2023) gives these as the "existing" charges and cites NSE/FA/46730 (18 Dec 2020) for the increase; start date not read from 46730 |
| 2023-04-01 → 2024-03-31 | 3.25 … 3.00 | LOCATED-OFFICIAL: NSE/FA/56129 |
| 2024-04-01 → 2024-09-30 | 3.22 … 2.97 | LOCATED-OFFICIAL: NSE/FA/61137 (14 Mar 2024) |
| 2024-10-01 → Feb 2026 | uniform 2.97 (+ 0.10 IPFT = 3.07) | LOCATED-OFFICIAL: NSE/FA/64232 (27 Sep 2024); ARCHIVED: table in NSE/FA/73061 |
| from the 2026 revision | 3.0699 + 0.0001 IPFT = 3.07 | ARCHIVED: NSE/FA/73061 (its effective date is stated in `cost_sources.md`, not found in the PDF text extraction) |

- The investor-protection (IPFT) contribution also changed over time; its history was not established.
- **Specification gap:** before October 2024 there is no single rate; it depends on which slab the broker was in. Frozen §13 gives one number.
- **To archive:** NSE/FA/46730, NSE/FA/56129, NSE/FA/61137, NSE/FA/64232, and the circulars for 2012–2020.

### 2.6 SEBI turnover fee (input 7)
| Period | Fee per crore of turnover | Support |
|---|---|---|
| 2007-08 onwards | "substantially decreased"; amount not stated | LOCATED-OFFICIAL: SEBI board memorandum, March 2019 |
| 2014-15 | "revised upwards"; amount not stated | same |
| before the 2017 change | ₹20 | same |
| after the Board decision of 14 Jan 2017 | ₹15 | same; the date it took effect NOT FOUND |
| after the March 2019 proposal | ₹10 | same (proposal); the amending notification and its effective date NOT FOUND |

- A temporary reduction during 2020–21 is mentioned in a search summary only (SECONDARY).
- **To archive:** the SEBI fee-amendment notifications of 2014-15, 2017 and 2019, and one official statement of the current fee.

### 2.7 GST / service tax on brokerage and charges (input 8)
| Period | Rate | Support |
|---|---|---|
| 2012-07-02 → 2015-05-31 | service tax 12.36% | SECONDARY |
| 2015-06-01 → 2015-11-14 | 14% | SECONDARY |
| 2015-11-15 → 2016-05-31 | 14.5% | SECONDARY |
| 2016-06-01 → 2017-06-30 | 15% | SECONDARY |
| 2017-07-01 → present | GST 18% | SECONDARY; current rate also in the archived note |

- **Specification gap:** frozen §13 names "GST". Before July 2017 the tax was service tax, a different levy.
- **To archive:** the official rate notifications for each date.

## 3. Exact evidence still missing
1. An official document for the delivery STT rate from 2012-07-01, and for its rate in 2026.
2. The PIB release and notifications for the uniform stamp duty; anything official on what applied before July 2020.
3. A dated broker schedule for delivery brokerage, and — first — which broker the study assumes.
4. A dated depository tariff and broker schedule for the depository charge, with history.
5. NSE circulars for 2012–2020, and archived copies of the four located circulars; IPFT history.
6. SEBI notifications with effective dates for 2014-15, 2017 and 2019.
7. Official service-tax and GST rate notifications.

## 4. Is the frozen §13 fallback available?
Frozen wording: "Where a historical rate cannot be evidenced, the current rate is applied to the whole sample and labelled as an assumption."

| Input | Fallback available? | Why |
|---|---|---|
| STT buy / sell | **No** | History appears obtainable from statute; it has simply not been archived |
| Stamp duty, 2020-07-01 on | **No** | Obtainable |
| Stamp duty, before 2020-07-01 | **Yes, once documented** | No single national rate existed, so a historical rate in the protocol's sense cannot be evidenced |
| Brokerage | **Not yet** | Obtainable for a named broker; the broker is not named in §13 |
| Depository charge | **Undetermined** | Current value located; history not searched to exhaustion |
| Exchange charge | **Undetermined** | 2021–2026 obtainable; 2012–2020 not found; slab dependence is a separate gap |
| SEBI fee | **No** | Obtainable from SEBI notifications |
| GST | **No** | Obtainable from official notifications |

The fallback also needs archived evidence of the current rate. Today that exists for the exchange charge only.

## 5. Points that evidence alone cannot settle
These need a reviewer ruling. No ruling is made here.
1. **Which broker** the brokerage and depository charge refer to (§13 names none).
2. **Which slab** of the exchange charge applies before October 2024.
3. **Service tax before July 2017:** §13 says "GST".
4. **Per-order brokerage before December 2015:** needs an order size; §13 fixes a notional only "to convert the flat depository fee".
5. **Whether the 0.1% STT, 0.015% stamp duty and zero brokerage "expected" in §13 are meant as constants** or as placeholders to be replaced by a dated history where history differs.

## 6. Circular-number reference
- `cost_sources.md` cites the slab-to-uniform circular as **NSE/FA/64232**.
- The archived NSE/FA/73061 cites it as **NSE/FA/64323**.
- The circular itself, opened on NSE's site, prints "Download Ref No: NSE/FA/64232, Date: September 27, 2024". The address for 64323 returns "not found".
- So the non-archived primary document supports the note, and the archived circular's cross-reference appears to be the one in error. Because the supporting document is not archived, **the discrepancy is recorded here as unresolved and no file was corrected.** An earlier statement in this session that the note was wrong is withdrawn.

## 7. Sources opened or seen on 2026-10-05 (none archived)
- NSE circulars NSE/FA/56129, NSE/FA/61137, NSE/FA/64232 — `nsearchives.nseindia.com/content/circulars/FA<number>.pdf`
- SEBI board memorandum, March 2019 — `sebi.gov.in/sebi_data/meetingfiles/mar-2019/1553244864312_1.pdf`
- Zerodha charges page — `zerodha.com/charges/`
- Seen in search results, not opened: PIB PRID 1635399; Zerodha Z-Connect "Zerodha going Zero brokerage"; pages describing STT, stamp duty and service-tax history.
