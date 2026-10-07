# S2-MOM-v1 — cost-evidence acquisition audit, stage 2 (2026-10-05)

**Scope:** evidence acquisition for Addendum 1 (`docs/research/phase3a_momentum_protocol_addendum1_costs.md`). Evidence only.

**Not done:** no cost schedule was created; no cost, turnover or net return was calculated; step E was not implemented or run; no protocol, addendum, code or result file was changed. **B2 is not closed.**

**Archive:** `docs/evidence/s2mom_costs/` — 39 source files (18 official, 21 broker primary), 5.3 MB. `MANIFEST.csv` gives, for every file, the source URL, source class, publication or capture date, retrieval date (2026-10-05) and full SHA-256. `SHA256SUMS` repeats the hashes. Hashes below are shortened; the manifest has them in full.

**Source classes**
- **OFFICIAL** — NSE, SEBI, Government of India, or an exchange notice reproducing a SEBI notification.
- **BROKER PRIMARY** — Zerodha's own pages, either served today or as captured on a past date by the Internet Archive. A capture proves what the page said on the capture date. It does not prove the date a rate began or ended.
- **SECONDARY** — anything else. Used below only to say where to look; never as evidence of a rate.

Period needed: 2012-07-02 to 2026-09-01.

---

## 1. Zerodha delivery brokerage

| Period | Rate | Evidence | Class | File and hash |
|---|---|---|---|---|
| capture 2012-09-27 | "0.1% or Rs 20 per executed order, whichever is lower" for delivery | pricing page | broker primary | `WAYBACK_zerodha_pricing_20120927020225.html` `62f6e36dfe94…` |
| capture 2013-01-04 | same | pricing page | broker primary | `…_20130104171836.html` `8d63ea94b1f0…` |
| captures 2014-01-09, 2015-02-06 | "Rs.20 per executed order or … .1% (delivery equity), whichever is lower" | pricing page | broker primary | `…_20140109010453.html` `1cf820285461…`; `…_20150206043100.html` `5b723a9c86c7…` |
| from 2015-12-01 | zero for equity delivery | announcement of 30 Nov 2015: "brokerage free starting 1st Dec 2015" | broker primary | `ZERODHA_zconnect_zero_brokerage_20151130.html` `0a72bc0fe7a1…` |
| captures 2016-10-09 … 2026-01-07; page today | "Zero Brokerage" | charges page | broker primary | 14 capture files and `ZERODHA_charges_page.html` `aae15a3dd992…` |

- **Gaps:** 2012-07-02 to 2012-09-26 has no capture (the earliest capture already shows the schedule). Nothing proves the schedule was unchanged between captures.
- **New point:** the 2015 announcement says the zero rate "is applicable only to retail, individual investors"; other account types "continue to pay 0.1% or Rs 20". The addendum does not say which account type the study assumes.
- **§13 fallback required?** No.

## 2. Zerodha sell-side depository charge

| Period | Charge per stock per sell day | Evidence | Class | File and hash |
|---|---|---|---|---|
| 2012-07-02 → 2016-10-08 | **not found**; the 2012–2015 pricing pages do not state it | — | — | — |
| captures 2016-10-09, 2017-03-17, 2018-08-22, 2019-05-06 | "₹13.5 per scrip (irrespective of quantity)"; tax is not mentioned | charges page | broker primary | `WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7…` and three more |
| captures 2020-02-17, 2021-01-02, 2022-01-17, 2023-01-03, 2024-03-01 | "₹13.5 + GST per scrip" | charges page | broker primary | `…_20200217130322.html` `c2ff785fb4ae…` and four more |
| capture 2024-09-17 | "₹13 + GST per scrip" | charges page | broker primary | `…_20240917083204.html` `256680064b73…` |
| captures 2024-10-08 … 2026-01-07; page today | "₹15.34 per scrip (₹3.5 CDSL fee + ₹9.5 Zerodha fee + ₹2.34 GST)" | charges page | broker primary | `…_20241008053010.html` `2095c01bc984…`; `ZERODHA_charges_page.html` `aae15a3dd992…` |

- **Gaps:** nothing before October 2016. The dates on which the wording changed are only bracketed by captures. For 2016–2019 it is not established whether "₹13.5" included tax.
- The depository's own tariff documents were not archived (a uniform ₹3.50 from 1 Oct 2024 is reported by secondary sources only).
- **§13 fallback required?** Possibly, for 2012-07 to 2016-10. Not yet available: the search made here was limited to the broker's pricing and charges pages; one wider archive query failed.

## 3. Delivery STT (buy and sell)

| Period | Rate | Evidence | Class | File and hash |
|---|---|---|---|---|
| to 2012-06-30 | 0.125% each side ("existing") | Memorandum to the Finance Bill 2012 | official (a proposal document) | `GOI_FinanceBill2012_memorandum_direct_taxes.pdf` `1899459535ce…` |
| from 2012-07-01 | 0.1% purchaser, 0.1% seller: "effective from the 1st day of July, 2012" | same | official (a proposal document) | same |
| September 2024 | 0.1% purchaser, 0.1% seller, "No Change" | NSE/FATAX/63809 | official | `NSE_FATAX63809.pdf` `e72218a4aaff…` |
| from 2026-04-01 and up to 2026-03-31 | 0.1% and 0.1%, "No Change" | NSE/FATAX/73524 | official | `NSE_FATAX73524.pdf` `f4cbd1f917f8…` |
| captures 2021–2026 | "0.1% on buy & sell" | charges page | broker primary | capture files |

- **Gaps:** the enacted Finance Act 2012 is not archived (the memorandum is the proposal). No archived official document covers 2012-07 to 2024-08 continuously; the two NSE circulars show the rate at their dates and that those revisions left it unchanged.
- **§13 fallback required?** No.

## 4. Stamp duty, delivery buy

| Period | Rate | Evidence | Class | File and hash |
|---|---|---|---|---|
| 2012-07-02 → 2020-06-30 | **no single rate**: "multiple rates for the same instrument"; "stamp duty was payable by both seller and buyer" | Ministry of Finance press release, 30 Jun 2020 | official | `PIB_stamp_duty_PRID1635399_20200630.html` `a94e6043b555…` |
| same period | "view stamp charges for different states" | charges page captures 2016-10 … 2020-02 | broker primary | capture files |
| from 2020-07-01 | uniform scheme in force "from … 1st July, 2020" (the release does not print the rate) | same press release | official | same |
| from 2020-07-01 | 0.015% on the buy side, delivery | Zerodha bulletin of 1 Jul 2020 | broker primary | `ZERODHA_bulletin_uniform_stamp_duty_20200701.html` `871057fc1efc…` |
| current | 0.015%, buyer, "transfer of security other than debenture on delivery basis" | NSE stamp-duty page | official (undated page) | `NSE_static_stamp_duty_page.html` `670216ea1d4f…` |

- **Gaps:** the notification that fixes 0.015% and the amended schedule of the Stamp Act are not archived.
- **§13 fallback required?** Yes for 2012-07-02 to 2020-06-30: an official source states that no single rate existed. Note for whoever applies it: before July 2020 the duty fell on both sides; the current rate falls on the buyer only.

## 5. NSE cash-market transaction charge (lowest-turnover slab = highest rate), ₹ per lakh of traded value, each side

| Period | Charge | Evidence | Class | File and hash |
|---|---|---|---|---|
| to 2009-09-30 | 3.50 (flat) | NSE/F&A/13028, 7 Sep 2009 | official | `NSE_FAAC13028_20090907.pdf` `5c018e6a880f…` |
| 2009-10-01 → 2020-12-31 | 3.25 | set by NSE/F&A/13028 "with effect from 1st October 2009"; given as the "existing" charge by NSE/FA/46730 (18 Dec 2020) | official | same; `NSE_FA46730.pdf` `a9ff85ab4dee…` |
| captures 2016-10 … 2020-02 | 0.00325% | charges page | broker primary | capture files |
| 2021-01-01 → 2023-03-31 | 3.45 | NSE/FA/46730 | official | `NSE_FA46730.pdf` `a9ff85ab4dee…` |
| 2023-04-01 → 2024-03-31 | 3.25 | NSE/FA/56129, 24 Mar 2023 | official | `NSE_FA56129.pdf` `ec260386adbc…` |
| 2024-04-01 → 2024-09-30 | 3.22 | NSE/FA/61137, 14 Mar 2024 | official | `NSE_FA61137.pdf` `e01c5b6c76d2…` |
| 2024-10-01 → 2026-02-28 | 2.97, uniform | NSE/FA/64232, 27 Sep 2024 | official | `NSE_FA64232.pdf` `85b816208f33…` |
| from 2026-03-01 | 3.0699 | NSE/FA/73061, 27 Feb 2026 | official | `docs/evidence/NSE_FA73061_2026-02-27_transaction_charges.pdf` (archived earlier) |

- **Gap:** no document between October 2009 and December 2020 was found, so continuity of 3.25 across 2012–2016 rests on the two end points being equal. Broker captures show 0.00325% from 2016.
- **Temporary scheme:** NSE/FA/46225 (`2918e89609d1…`) sets, for 1 Aug 2020 to 31 Mar 2021, a separate structure (2.75 up to ₹7,500 crore; 1.75 above) for EQ stocks **other than** NIFTY 50 and NIFTY Next 50 constituents, debt ETFs and stocks under graded surveillance. Applying it would need point-in-time index membership. See 10.
- The circular number NSE/FA/64232 is confirmed by the document itself, now archived. The cross-reference "NSE/FA/64323" printed in NSE/FA/73061 does not correspond to a retrievable circular. The discrepancy is resolved in favour of 64232; the note in `cost_sources.md` was correct and was not edited.
- **§13 fallback required?** No.

## 6. IPFT contribution — included in the charge, separate, or unknown

| Period | Relationship | Amount | Evidence | File and hash |
|---|---|---|---|---|
| 2012-07-02 → 2023-03-31 | **Separate** from the transaction charge. The circulars of 2009 and 2020 state transaction charges only | ₹0.01 per crore is called the "existing" contribution in March 2023. **The date it began is not established**, so the amount for earlier years is unknown | NSE/FA/56129 | `NSE_FA56129.pdf` `ec260386adbc…` |
| 2023-04-01 → 2026-02-28 | **Separate; to be added** | ₹10 per crore ("from existing Rs.0.01 per crore … to Rs.10 per crore"); the 2026 circular tabulates 297 + 10 = 307 | NSE/FA/56129; NSE/FA/73061 | as above; `docs/evidence/NSE_FA73061_2026-02-27_transaction_charges.pdf` |
| from 2026-03-01 | **Separate; to be added** | ₹0.01 per crore (306.99 + 0.01 = 307) | NSE/FA/73061 | `docs/evidence/NSE_FA73061_2026-02-27_transaction_charges.pdf` |

- The January 2021 increase (NSE/FA/46730) was "to augment the IPFT corpus" but was made **to the transaction charge itself**. It is already inside the 3.45 and must not be added again.
- No circular found states a charge that already includes IPFT. Double counting is avoided by taking the transaction charge and the contribution from the separate columns of the circulars.
- Broker pages: from April 2023 to January 2026 the captures show 0.00325%, 0.00322% and 0.00297%, which equal the transaction charge **without** the ₹10 contribution; the page today shows 0.00307%. Whether the broker billed the contribution to clients in 2023–2026 is **unknown**.

## 7. SEBI turnover fee, cash segment, per crore

| Period | Fee | Evidence | Class | File and hash |
|---|---|---|---|---|
| regulations as amended to about 2015 | ₹10 (0.0001%) | SEBI Stock Brokers Regulations, consolidated | official; as-of date unclear | `SEBI_stock_brokers_amendment_regs_commondocs.pdf` `6b48fde69507…` |
| "2014-15" | "revised upwards" (amount not stated) | SEBI board memorandum, March 2019 | official | `SEBI_board_memo_fees_mar2019.pdf` `ed3f87f2f37f…` |
| before the decision of 14 Jan 2017 | ₹20 | same memorandum; captures 2016-10-09 and 2017-03-17 show ₹20 | official; broker primary | same; capture files |
| 2017-04-01 → 2019-03-31 | ₹15 (0.00015%) | Gazette of 6 Mar 2017, in force 1 Apr 2017; consolidated regulations footnote | official | `SEBI_gazette_fees_amendment_2017.pdf` `4b826aaa6189…`; `THC_SEBI_stock_brokers_regulations_1992_consolidated.pdf` `f18f452b08c7…` |
| from 2019-04-01 | ₹10 (0.00010%) | SEBI notification of 22 Mar 2019, reproduced in an exchange notice: "shall come into force with effect from April 01, 2019" | official (reproduction) | `CSE_notice_SEBI_turnover_fees_2019.htm` `99ebdca9a5ce…` |
| June 2020 → March 2021 | proposal to charge 50% of the fee; capture of 2021-01-02 shows ₹5 | SEBI board memorandum, July 2020 | official (a proposal); broker primary | `SEBI_board_memo_fee_relaxation_jul2020.pdf` `fcc397d8893b…` |
| current | ₹10 | NSE page | official (undated page) | `NSE_static_sebi_fees_stt_page.html` `a9c261eed75c…` |

- **Gaps:** the date and instrument of the rise to ₹20, and so the fee for 2012-07 to about 2016; the instrument and exact dates of the 2020–21 halving.
- The exchange notice's own heading says "w.e.f. April 3, 2019"; the regulation text it reproduces says 1 April 2019. The regulation text is taken as the evidence; the difference is recorded.
- **§13 fallback required?** No; the missing items are obtainable SEBI instruments.

## 8. Indirect tax before 1 July 2017 (service tax and cesses)

| Period | Rate | Evidence | Class | File and hash |
|---|---|---|---|---|
| captures 2016-10-09 and 2017-03-17 | "Service tax 15% on (brokerage + transaction charges)" | charges page | broker primary | `WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7…`; `…_20170317010757.html` `7da660e59125…` |
| 2012-07-02 → 2016-10-08 | 12.36%, 14%, 14.5% at various dates per **secondary sources only** | — | not evidence | **not archived** |

- **Gaps:** no official notification is archived. The official tax site did not respond during this audit. The documents to obtain are the service-tax rate notification of May 2015, the cess notifications of November 2015 and the 2016 Finance Act provision.
- **§13 fallback required?** Not available: the history is obtainable.

## 9. GST from 1 July 2017

| Period | Rate | Evidence | Class | File and hash |
|---|---|---|---|---|
| captures 2018-08-22 … 2022-01-17 | "GST 18% on (brokerage + transaction charges)" | charges page | broker primary | capture files |
| captures 2023-01-03 … 2026-01-07; page today | "GST 18% on (brokerage + SEBI charges + transaction charges)" | charges page | broker primary | capture files; `ZERODHA_charges_page.html` `aae15a3dd992…` |

- **Gaps:** no official GST rate notification is archived; nothing archived covers 2017-07 to 2018-08.
- **Base:** until at least January 2022 the broker's stated base did not include the SEBI fee. Addendum rule 3 fixes the frozen §13 base (brokerage + exchange + SEBI) for all dates, so no new decision is needed; the difference is recorded.
- **§13 fallback required?** Not available: obtainable.

---

## 10. Evidence matrix

IPFT column: I = included in the stated charge; S = stated separately; U = relationship or amount unknown; — = not applicable.

| INPUT | PERIOD | RATE | SOURCE | OFFICIAL? | ARCHIVED? | HASH | IPFT | FALLBACK REQUIRED? |
|---|---|---|---|---|---|---|---|---|
| Brokerage, delivery | 2012-07-02 → 2012-09-26 | not evidenced | — | — | no | — | — | undetermined |
| Brokerage, delivery | 2012-09-27 → 2015-11-30 | lower of 0.1% or ₹20 per executed order | pricing captures; 2015 announcement | broker primary | yes | `62f6e36dfe94…` | — | no |
| Brokerage, delivery | 2015-12-01 → 2026-09-01 | zero (retail individual accounts) | announcement; captures | broker primary | yes | `0a72bc0fe7a1…` | — | no |
| Depository charge | 2012-07-02 → 2016-10-08 | not found | — | — | no | — | — | undetermined |
| Depository charge | 2016-10-09 → 2019-05-06 (captures) | ₹13.5 per scrip; tax not stated | captures | broker primary | yes | `cd66fee700c7…` | — | no |
| Depository charge | 2020-02-17 → 2024-03-01 (captures) | ₹13.5 + GST | captures | broker primary | yes | `c2ff785fb4ae…` | — | no |
| Depository charge | 2024-09-17 (capture) | ₹13 + GST | capture | broker primary | yes | `256680064b73…` | — | no |
| Depository charge | 2024-10-08 → today (captures) | ₹15.34, tax included | captures; page | broker primary | yes | `2095c01bc984…` | — | no |
| STT buy and sell | 2012-07-01 → 2026-09-01 | 0.1% each side | Finance Bill 2012 memorandum; NSE/FATAX/63809; NSE/FATAX/73524 | official (start is a proposal document) | yes | `1899459535ce…` | — | no |
| Stamp duty, buy | 2012-07-02 → 2020-06-30 | no single rate; both sides; by state | Ministry of Finance release | official | yes | `a94e6043b555…` | — | **yes** |
| Stamp duty, buy | 2020-07-01 → 2026-09-01 | 0.015% buyer | NSE page; Zerodha bulletin | official; broker primary | yes | `670216ea1d4f…` | — | no |
| Exchange charge | 2012-07-02 → 2020-12-31 | ₹3.25 per lakh | NSE/F&A/13028; NSE/FA/46730 | official | yes | `5c018e6a880f…` | S, amount U before Mar 2023 | no |
| Exchange charge | 2021-01-01 → 2023-03-31 | ₹3.45 per lakh | NSE/FA/46730 | official | yes | `a9ff85ab4dee…` | S, amount U before Mar 2023 | no |
| Exchange charge | 2023-04-01 → 2024-03-31 | ₹3.25 per lakh | NSE/FA/56129 | official | yes | `ec260386adbc…` | S: + ₹10 per crore | no |
| Exchange charge | 2024-04-01 → 2024-09-30 | ₹3.22 per lakh | NSE/FA/61137 | official | yes | `e01c5b6c76d2…` | S: + ₹10 per crore | no |
| Exchange charge | 2024-10-01 → 2026-02-28 | ₹2.97 per lakh | NSE/FA/64232 | official | yes | `85b816208f33…` | S: + ₹10 per crore | no |
| Exchange charge | 2026-03-01 → 2026-09-01 | ₹3.0699 per lakh | NSE/FA/73061 | official | yes (earlier) | `6085601a2617…` | S: + ₹0.01 per crore | no |
| SEBI fee | 2012-07-02 → date unknown (2014-15) | ₹10 per crore (regulations as amended to ~2015) | consolidated regulations | official | yes | `6b48fde69507…` | — | no |
| SEBI fee | date unknown → 2017-03-31 | ₹20 per crore | SEBI memorandum; captures | official; broker primary | yes | `ed3f87f2f37f…` | — | no |
| SEBI fee | 2017-04-01 → 2019-03-31 | ₹15 per crore | Gazette 6 Mar 2017 | official | yes | `4b826aaa6189…` | — | no |
| SEBI fee | 2019-04-01 → 2026-09-01 | ₹10 per crore (halved June 2020 – March 2021 per a proposal) | SEBI notification via exchange notice; SEBI memorandum | official | yes | `99ebdca9a5ce…` | — | no |
| Indirect tax | 2012-07-02 → 2016-10-08 | not evidenced | secondary only | no | no | — | — | not available |
| Indirect tax | 2016-10-09 → 2017-06-30 | service tax 15% (captures 2016-10, 2017-03) | captures | broker primary | yes | `cd66fee700c7…` | — | no |
| Indirect tax | 2017-07-01 → 2018-08-21 | not evidenced | secondary only | no | no | — | — | not available |
| Indirect tax | 2018-08-22 → 2026-09-01 | GST 18% | captures; page | broker primary | yes | `9bdbe5edb345…` | — | no |

## 11. B2 status

**B2 remains OPEN.**

**Requirements now met by archived evidence**
- Exchange transaction charge, lowest-turnover slab, 2009 to 2026: official circulars.
- IPFT relationship and amount from 2023-04-01: official circulars.
- SEBI fee from 2017-04-01: official instruments.
- Stamp duty from 2020-07-01, and the official statement that no single rate existed before.
- Delivery STT at 2012-07-01 (proposal document), 2024 and 2026: official.
- Zerodha delivery brokerage from 2012-09-27, and the zero rate from 2015-12-01: broker primary.
- Zerodha depository charge wording from 2016-10-09: broker primary.

**Still open**
1. Depository charge 2012-07 to 2016-10; the dates of its later changes; whether ₹13.5 included tax in 2016–2019.
2. Brokerage 2012-07-02 to 2012-09-26.
3. The enacted Finance Act 2012 (STT).
4. The stamp-duty rate notification of 2020.
5. SEBI fee 2012 to 2017: the date and instrument of the rise to ₹20; the 2020–21 halving instrument.
6. IPFT amount before March 2023.
7. Official service-tax notifications 2012–2017 and an official GST rate notification.
8. The delivery cost schedule file itself, which this audit does not create.

**Rates with no defensible evidence at all**
- Depository charge before October 2016.
- Indirect tax rate before October 2016 and between July 2017 and August 2018.
- SEBI fee between about 2014 and October 2016 (the change date is unknown).
- IPFT amount before March 2023.

## 12. Ambiguities that need another methodological decision

None is resolved here.

1. **Account type.** Zero delivery brokerage applies to retail individual accounts only. The addendum names the broker, not the account type.
2. **Dating of broker evidence.** Captures bracket a change; they do not date it. A rule is needed for which rate applies between two captures that differ.
3. **Temporary exchange-charge scheme, August 2020 to March 2021.** For stocks outside NIFTY 50 and NIFTY Next 50 the rate was lower and stock-specific. Rule 2 says "the lowest monthly-turnover slab in force … which is the highest rate"; for these stocks the scheme's lowest slab is not the highest rate. Applying the scheme also needs point-in-time index membership, which is not archived.
4. **Depository charge 2016–2019.** The page gives "₹13.5 per scrip" without saying whether tax is included; rule 6 says "tax included as billed".
5. **Temporary halving of the SEBI fee, June 2020 to March 2021.** Whether to apply it, and on what evidence, since only the proposal is archived.
6. **IPFT before April 2023.** The amount is evidenced only as "existing" in March 2023. Whether to apply it to earlier years, or treat it as unknown.
7. **Stamp-duty fallback.** The frozen fallback applies the current buyer-only rate to years in which duty fell on both sides at state rates. No decision is required to apply it, but it should be acknowledged.

## 13. What was not possible
- The official tax-notification site did not respond; three downloads failed and were discarded.
- One wider Internet Archive query for 2012–2016 depository-charge pages timed out.
- The depository's own tariff circulars were not located.
