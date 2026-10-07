# S2-MOM-v1 — delivery cost schedule: audit report (2026-10-06)

**B2 — Evidence closure: PASS, subject to the approved readings above. Cost-schedule closure: PENDING until the schedule contains no empty rate.**

"The approved readings above" are the two readings approved by the reviewer on 2026-10-06: the Krishi Kalyan Cess bracket (1 Jun – 8 Oct 2016) and the education-cess rates (Jul 2012 – May 2015). The schedule below contains no empty rate; whether that closes the second half of B2 is the reviewer's call.

This step created the schedule file, its tests and this report only. No turnover, cost, net return or break-even was calculated. Step E was not implemented or run. No experiment was run or rerun. The frozen protocol, Addendum 1, Supplement 1, the registered code and every result file are unchanged. Nothing was committed.

## 1. The schedule

- Path: `config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json`
- SHA-256: `47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f`
- Sample covered: 2012-07-02 to 2026-09-01, every component, no gap and no overlap.
- Account: Zerodha, retail individual account (Addendum rule 1, Supplement ruling 1).
- Date rule: Each rate applies to trade dates from `from` to `to`, both inclusive. A stated effective date is used where an archived document gives one; between two differing dated captures the higher-cost value applies (Supplement ruling 2). No interpolation.
- Timing: Specified after the gross primary, sensitivity and confirmation results were known and before any cost, turnover or net return was computed. It changes no part of steps A-D.

The older file `config/cost_schedules/delivery_nse_eq_s2mom.json` (single rates, five of them empty) is the format read by the registered experiment code. It was **not** edited and is **not** the Addendum 1 schedule. See caveat 8 in section 5.

## 2. Every rate and date range

Hashes are the first 12 characters; the schedule file holds them in full. "Flag" shows whether the row is evidence, a §13 fallback or an approved assumption.

### Securities transaction tax, buy — and the same for sell
Tax treatment: not taxed.

| From | To | Rate | Flag | Evidence (file, hash) | Note |
|---|---|---|---|---|---|
| 2012-07-02 | 2026-09-01 | 0.1% = 0.1% | **FALLBACK** | `NSE_FATAX73524.pdf` `f4cbd1f917f8`<br>`NSE_FATAX63809.pdf` `e72218a4aaff`<br>`NSE_static_sebi_fees_stt_page.html` `a9c261eed75c`<br>`SEARCH_LOG_20261006.txt` `e2bc86c0e112`<br>`SEARCH_LOG_20261006b.txt` `1647f7fb4e8b` | Enacted Finance Act 2012 not obtained: nine addresses over two passes and three archive-index queries (SEARCH_LOG_20261006.txt, SEARCH_LOG_20261006b.txt). Frozen §13 fallback: current rate for the whole sample. Supporting only, not relied on: Finance Bill 2012 memorandum and broker lists show 0.1% from 1 Jul 2012. |

### NSE transaction charge (each side)
Tax treatment: in the tax base.

| From | To | Rate | Flag | Evidence (file, hash) | Note |
|---|---|---|---|---|---|
| 2012-07-02 | 2020-12-31 | 3.25 ₹ per lakh = 0.00325% | evidence | `NSE_FAAC13028_20090907.pdf` `5c018e6a880f`<br>`NSE_FA46730.pdf` `a9ff85ab4dee` | Lowest monthly-turnover slab = highest rate (Addendum rule 2). Transaction charge only; IPFT is the separate component `ipft`. Set from 1 Oct 2009; given as 'existing' in Dec 2020. The 1 Aug 2020 - 31 Mar 2021 scheme for stocks outside NIFTY 50 / Next 50 is NOT applied (Supplement ruling 3). |
| 2021-01-01 | 2023-03-31 | 3.45 ₹ per lakh = 0.00345% | evidence | `NSE_FA46730.pdf` `a9ff85ab4dee`<br>`NSE_FA56129.pdf` `ec260386adbc` | Lowest monthly-turnover slab = highest rate (Addendum rule 2). Transaction charge only; IPFT is the separate component `ipft`. The January 2021 increase was made to the transaction charge itself; it is recorded here once and is NOT an IPFT amount (Supplement ruling 6). |
| 2023-04-01 | 2024-03-31 | 3.25 ₹ per lakh = 0.00325% | evidence | `NSE_FA56129.pdf` `ec260386adbc`<br>`NSE_FA61137.pdf` `e01c5b6c76d2` | Lowest monthly-turnover slab = highest rate (Addendum rule 2). Transaction charge only; IPFT is the separate component `ipft`. January 2021 increase rolled back from 1 Apr 2023. |
| 2024-04-01 | 2024-09-30 | 3.22 ₹ per lakh = 0.00322% | evidence | `NSE_FA61137.pdf` `e01c5b6c76d2` | Lowest monthly-turnover slab = highest rate (Addendum rule 2). Transaction charge only; IPFT is the separate component `ipft`. |
| 2024-10-01 | 2026-02-28 | 2.97 ₹ per lakh = 0.00297% | evidence | `NSE_FA64232.pdf` `85b816208f33`<br>`NSE_FA73061_2026-02-27_transaction_charges.pdf` `6085601a2617` | Uniform rate from 1 Oct 2024 (Rs 297 per crore). Transaction charge only. |
| 2026-03-01 | 2026-09-01 | 3.0699 ₹ per lakh = 0.0030699% | evidence | `NSE_FA73061_2026-02-27_transaction_charges.pdf` `6085601a2617` | Uniform rate Rs 306.99 per crore. Transaction charge only. |

### NSE investor-protection contribution, IPFT (each side)
Tax treatment: in the tax base.

| From | To | Rate | Flag | Evidence (file, hash) | Note |
|---|---|---|---|---|---|
| 2012-07-02 | 2023-03-31 | 0.01 ₹ per crore = 0.0000001% | **FALLBACK** | `NSE_FA73061_2026-02-27_transaction_charges.pdf` `6085601a2617`<br>`NSE_FA56129.pdf` `ec260386adbc`<br>`NSE_FA46730.pdf` `a9ff85ab4dee`<br>`SEARCH_LOG_20261006b.txt` `1647f7fb4e8b` | No NSE document states the contribution for any date before the circular of 24 Mar 2023 (documented failed search). Supplement ruling 6: §13 fallback = current amount. The 'existing' amount named in March 2023 is not used as evidence for earlier dates. The January 2021 transaction-charge increase is NOT added here. |
| 2023-04-01 | 2026-02-28 | 10 ₹ per crore = 0.0001% | evidence | `NSE_FA56129.pdf` `ec260386adbc`<br>`NSE_FA73061_2026-02-27_transaction_charges.pdf` `6085601a2617` | Stated separately from the transaction charge: Rs 10 per crore (297 + 10 = 307 in the 2026 circular). |
| 2026-03-01 | 2026-09-01 | 0.01 ₹ per crore = 0.0000001% | evidence | `NSE_FA73061_2026-02-27_transaction_charges.pdf` `6085601a2617` | Stated separately: Rs 0.01 per crore (306.99 + 0.01 = 307). |

### SEBI turnover fee (each side)
Tax treatment: in the tax base.

| From | To | Rate | Flag | Evidence (file, hash) | Note |
|---|---|---|---|---|---|
| 2012-07-02 | 2014-05-22 | 10 ₹ per crore = 0.0001% | evidence | `SEBI_PR_payment_of_fees_amendment_2014.html` `7608634ec8a6`<br>`WAYBACK_zerodha_chargelist_20120504125926.xls` `b4bccc8b0574`<br>`WAYBACK_zerodha_chargelist_20121225060108.xls` `ae240f3dd100`<br>`WAYBACK_zerodha_charge-list_20140504002448.html` `166b556a2c73`<br>`SEBI_stock_brokers_amendment_regs_commondocs.pdf` `6b48fde69507` | SEBI press release: fee raised 'from Rs. 10'. Broker lists of May 2012, Dec 2012, May 2014 agree. |
| 2014-05-23 | 2017-03-31 | 20 ₹ per crore = 0.0002% | evidence | `SEBI_payment_of_fees_amendment_regs_2014.pdf` `4a78abbe563f`<br>`SEBI_PR_payment_of_fees_amendment_2014.html` `7608634ec8a6` | Gazette 23 May 2014, in force on publication. |
| 2017-04-01 | 2019-03-31 | 15 ₹ per crore = 0.00015% | evidence | `SEBI_gazette_fees_amendment_2017.pdf` `4b826aaa6189`<br>`THC_SEBI_stock_brokers_regulations_1992_consolidated.pdf` `f18f452b08c7` | Gazette 6 Mar 2017, in force 1 Apr 2017. |
| 2019-04-01 | 2026-09-01 | 10 ₹ per crore = 0.0001% | evidence | `CSE_notice_SEBI_turnover_fees_2019.htm` `99ebdca9a5ce`<br>`NSE_static_sebi_fees_stt_page.html` `a9c261eed75c` | SEBI notification of 22 Mar 2019, in force 1 Apr 2019. The June 2020 - March 2021 halving is NOT applied: no SEBI instrument fixing its dates is archived (Supplement ruling 5). This is the higher-cost reading. |

### Stamp duty, buy
Tax treatment: not taxed.

| From | To | Rate | Flag | Evidence (file, hash) | Note |
|---|---|---|---|---|---|
| 2012-07-02 | 2020-06-30 | 0.015% = 0.015% | **FALLBACK** | `NSE_static_stamp_duty_page.html` `670216ea1d4f`<br>`ZERODHA_bulletin_uniform_stamp_duty_20200701.html` `871057fc1efc`<br>`PIB_stamp_duty_PRID1635399_20200630.html` `a94e6043b555` | An official release states no single rate existed before 1 Jul 2020 (state rates, both sides). Supplement ruling 7: §13 fallback as written = current rate, buyer only. DISCLOSURE: it omits the seller's side that applied then; may favour the strategy. No state rate is used. |
| 2020-07-01 | 2026-09-01 | 0.015% = 0.015% | evidence | `NSE_static_stamp_duty_page.html` `670216ea1d4f`<br>`ZERODHA_bulletin_uniform_stamp_duty_20200701.html` `871057fc1efc`<br>`PIB_stamp_duty_PRID1635399_20200630.html` `a94e6043b555` | Uniform scheme from 1 Jul 2020; 0.015% on the buyer, delivery. |

### Indirect tax on charges (service tax, then GST)
Tax treatment: applied to brokerage + exchange charge + IPFT + SEBI fee.

| From | To | Rate | Flag | Evidence (file, hash) | Note |
|---|---|---|---|---|---|
| 2012-07-02 | 2015-05-31 | 12.36% | **APPROVED READING** | `WB_CBEC_st-act-ason24oct2013_20150829.pdf` `ef4f4b35418c`<br>`WB_CBEC_finact2015_20150528.pdf` `33e73c90d8c3`<br>`WAYBACK_zerodha_chargelist_20120504125926.xls` `b4bccc8b0574`<br>`WAYBACK_zerodha_chargelist_20121225060108.xls` `ae240f3dd100`<br>`WAYBACK_zerodha_charge-list_20140504002448.html` `166b556a2c73` | Service tax 12% is OFFICIAL (section 66B). The education cess (2% of the tax) and higher education cess (1% of the tax) rates are NOT from an official file: they rest on three agreeing dated Zerodha charge lists (approved reading, 2026-10-06). Official files prove only that the cesses existed until removed by the Finance Act 2015. 12 x 1.03 = 12.36. |
| 2015-06-01 | 2015-11-14 | 14% | evidence | `WB_CBEC_finact2015_20150528.pdf` `33e73c90d8c3`<br>`WB_CBEC_st14-2015.pdf` `6c9ab52e02bf` | Finance Act 2015 s.108 (14%), s.153 and s.159 (education cesses removed); in force 1 Jun 2015 by Notification 14/2015-ST. |
| 2015-11-15 | 2016-05-31 | 14.5% | evidence | `WB_CBEC_st21h-2015_20151123.pdf` `41fcf099114c`<br>`WB_CBEC_st22h-2015_20151123.pdf` `d14727f37541`<br>`WB_CBEC_faq-sbc_20161022.pdf` `09c94bafb603` | 14% + Swachh Bharat Cess 0.5% from 15 Nov 2015. |
| 2016-06-01 | 2016-10-08 | 15% | **BRACKET ASSUMPTION** | `WB_CBEC_st27-2016.pdf` `278b5d3a0b91`<br>`WB_CBEC_st28-2016.pdf` `caaf64be41ce`<br>`WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`WB_CBEC_faq-sbc_20161022.pdf` `09c94bafb603`<br>`SEARCH_LOG_20261006b.txt` `1647f7fb4e8b` | EVIDENCE-BASED BRACKET ASSUMPTION, not direct official-rate evidence (approved reading, 2026-10-06). The Krishi Kalyan Cess start date, 1 Jun 2016, is official. Its 0.5% rate is not in any archived official file. The 15% total is taken from the Zerodha capture of 9 Oct 2016 and applied from the official start date under Supplement ruling 2 (higher of 14.5% and 15%). |
| 2016-10-09 | 2017-06-30 | 15% | evidence | `WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`WAYBACK_zerodha_charges_20170317010757.html` `7da660e59125`<br>`WB_CBEC_st-act-ason-01apr2017_20170611.pdf` `f170777f5ede` | 15% shown in the broker captures of 9 Oct 2016 and 17 Mar 2017 (broker primary); basic rate 14% official at 1 Apr 2017. Service tax ended 30 Jun 2017. |
| 2017-07-01 | 2026-09-01 | 18% | evidence | `CBIC_GST_notfn8_2017_integrated_tax_rate.pdf` `1f2d7ff6b922`<br>`CBIC_GST_notfn11_2017_central_tax_rate.pdf` `a8051c8882b8` | GST 18% on financial and related services from 1 Jul 2017. |

### Zerodha delivery brokerage (each side)
Tax treatment: in the tax base.

| From | To | Rate | Flag | Evidence (file, hash) | Note |
|---|---|---|---|---|---|
| 2012-07-02 | 2015-11-30 | lower of 0.1% or ₹20 per order | evidence | `WAYBACK_zerodha_chargelist_20120504125926.xls` `b4bccc8b0574`<br>`WAYBACK_zerodha_demat_form_20120504125220.pdf` `f7bbf2eb4cc7`<br>`WAYBACK_zerodha_pricing_20120927020225.html` `62f6e36dfe94`<br>`WAYBACK_zerodha_chargelist_20121225060108.xls` `ae240f3dd100`<br>`WAYBACK_zerodha_pricing_20130104171836.html` `8d63ea94b1f0`<br>`WAYBACK_zerodha_pricing_20140109010453.html` `1cf820285461`<br>`WAYBACK_zerodha_charge-list_20140504002448.html` `166b556a2c73`<br>`WAYBACK_zerodha_pricing_20150206043100.html` `5b723a9c86c7` | Lower of 0.1% of order value or Rs 20 per executed order. Captures of 4 May 2012 and 27 Sep 2012 agree, so the rate holds between them (covers 2 Jul - 26 Sep 2012). Some captures say 'per trade'; the tariff sheet says 'per executed order'; the Addendum fixes one order per stock. |
| 2015-12-01 | 2026-09-01 | zero | evidence | `ZERODHA_zconnect_zero_brokerage_20151130.html` `0a72bc0fe7a1`<br>`WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`ZERODHA_charges_page.html` `aae15a3dd992` | Zero for equity delivery from 1 Dec 2015, the date stated in the broker's announcement. Applies to retail individual accounts only (Supplement ruling 1). DISCLOSURE: ruling 1 may favour the strategy; other account types kept paying. |

### Sell-side depository charge, per stock per sell day
Tax treatment: tax already included as billed; never taxed again.

| From | To | Rate | Flag | Evidence (file, hash) | Note |
|---|---|---|---|---|---|
| 2012-07-02 | 2012-12-24 | ₹21.9102 (₹19.5 + 12.36% tax) | **APPROVED READING** | `WAYBACK_zerodha_demat_form_20120504125220.pdf` `f7bbf2eb4cc7`<br>`WAYBACK_zerodha_ilfs_demat_form_20121225052153.pdf` `6f03dee81cb2`<br>`WB_NSDL_policy_2010-0029_settlement_fee_20131028.pdf` `932a1f380984`<br>`WB_CBEC_st-act-ason24oct2013_20150829.pdf` `ef4f4b35418c`<br>`WB_CBEC_finact2015_20150528.pdf` `33e73c90d8c3`<br>`WAYBACK_zerodha_chargelist_20120504125926.xls` `b4bccc8b0574`<br>`WAYBACK_zerodha_chargelist_20121225060108.xls` `ae240f3dd100`<br>`WAYBACK_zerodha_charge-list_20140504002448.html` `166b556a2c73` | Rs 15 broker + Rs 4.50 NSDL. Capture of 4 May 2012 (Rs 15 + depository fee) and capture of 25 Dec 2012 (Rs 8 + depository fee) differ: ruling 2 applies the higher to every date between. CAVEAT: this may overstate the charge for part of the period. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2012-12-25 | 2014-07-03 | ₹14.045 (₹12.5 + 12.36% tax) | **APPROVED READING** | `WAYBACK_zerodha_ilfs_demat_form_20121225052153.pdf` `6f03dee81cb2`<br>`WAYBACK_zerodha_blog_poa_demat_20150620.html` `1f0e7d7c7de0`<br>`WAYBACK_zerodha_ilfsdemat_20140703122832.pdf` `1969f54936ab`<br>`WB_NSDL_policy_2010-0029_settlement_fee_20131028.pdf` `932a1f380984`<br>`WB_NSDL_fee_payable_by_participants_20130818.html` `6825fa90f405`<br>`WB_CBEC_st-act-ason24oct2013_20150829.pdf` `ef4f4b35418c`<br>`WB_CBEC_finact2015_20150528.pdf` `33e73c90d8c3`<br>`WAYBACK_zerodha_chargelist_20120504125926.xls` `b4bccc8b0574`<br>`WAYBACK_zerodha_chargelist_20121225060108.xls` `ae240f3dd100`<br>`WAYBACK_zerodha_charge-list_20140504002448.html` `166b556a2c73` | Rs 8 broker + Rs 4.50 NSDL. Captures of 25 Dec 2012 and 3 Jul 2014 agree; broker statement of 19 Mar 2013 gives Rs 12.5. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2014-07-04 | 2015-05-31 | ₹15.1686 (₹13.5 + 12.36% tax) | **APPROVED READING** | `WAYBACK_zerodha_ilfsdemat_20140703122832.pdf` `1969f54936ab`<br>`WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`WB_NSDL_fees_and_charges_to_DPs_20170708.pdf` `bc45eddb4e0d`<br>`WB_CBEC_st-act-ason24oct2013_20150829.pdf` `ef4f4b35418c`<br>`WB_CBEC_finact2015_20150528.pdf` `33e73c90d8c3`<br>`WAYBACK_zerodha_chargelist_20120504125926.xls` `b4bccc8b0574`<br>`WAYBACK_zerodha_chargelist_20121225060108.xls` `ae240f3dd100`<br>`WAYBACK_zerodha_charge-list_20140504002448.html` `166b556a2c73` | Captures of 3 Jul 2014 (Rs 12.5) and 9 Oct 2016 (Rs 13.5) differ: ruling 2 applies the higher to every date between. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2015-06-01 | 2015-11-14 | ₹15.39 (₹13.5 + 14% tax) | evidence | `WAYBACK_zerodha_ilfsdemat_20140703122832.pdf` `1969f54936ab`<br>`WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`WB_NSDL_fees_and_charges_to_DPs_20170708.pdf` `bc45eddb4e0d`<br>`WB_CBEC_finact2015_20150528.pdf` `33e73c90d8c3`<br>`WB_CBEC_st14-2015.pdf` `6c9ab52e02bf` | Captures of 3 Jul 2014 (Rs 12.5) and 9 Oct 2016 (Rs 13.5) differ: ruling 2 applies the higher to every date between. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2015-11-15 | 2016-05-31 | ₹15.4575 (₹13.5 + 14.5% tax) | evidence | `WAYBACK_zerodha_ilfsdemat_20140703122832.pdf` `1969f54936ab`<br>`WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`WB_NSDL_fees_and_charges_to_DPs_20170708.pdf` `bc45eddb4e0d`<br>`WB_CBEC_st21h-2015_20151123.pdf` `41fcf099114c`<br>`WB_CBEC_st22h-2015_20151123.pdf` `d14727f37541`<br>`WB_CBEC_faq-sbc_20161022.pdf` `09c94bafb603` | Captures of 3 Jul 2014 (Rs 12.5) and 9 Oct 2016 (Rs 13.5) differ: ruling 2 applies the higher to every date between. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2016-06-01 | 2016-10-08 | ₹15.525 (₹13.5 + 15% tax) | **BRACKET ASSUMPTION** | `WAYBACK_zerodha_ilfsdemat_20140703122832.pdf` `1969f54936ab`<br>`WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`WB_NSDL_fees_and_charges_to_DPs_20170708.pdf` `bc45eddb4e0d`<br>`WB_CBEC_st27-2016.pdf` `278b5d3a0b91`<br>`WB_CBEC_st28-2016.pdf` `caaf64be41ce`<br>`WB_CBEC_faq-sbc_20161022.pdf` `09c94bafb603`<br>`SEARCH_LOG_20261006b.txt` `1647f7fb4e8b` | Captures of 3 Jul 2014 (Rs 12.5) and 9 Oct 2016 (Rs 13.5) differ: ruling 2 applies the higher to every date between. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2016-10-09 | 2017-06-30 | ₹15.525 (₹13.5 + 15% tax) | evidence + **ruling 4 assumption** | `WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`WAYBACK_zerodha_charges_20170317010757.html` `7da660e59125`<br>`WAYBACK_zerodha_charges_20180822091806.html` `9bdbe5edb345`<br>`WAYBACK_zerodha_charges_20190506071501.html` `0331ea42e374`<br>`WAYBACK_zerodha_charges_20200217130322.html` `c2ff785fb4ae`<br>`WB_CBEC_st-act-ason-01apr2017_20170611.pdf` `f170777f5ede` | RULING 4 ASSUMPTION: captures of 9 Oct 2016 to 6 May 2019 show Rs 13.5 per scrip without mentioning tax; Supplement ruling 4 treats it as before tax and adds the tax in force (higher-cost reading). The next capture, 17 Feb 2020, says Rs 13.5 + GST. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2017-07-01 | 2020-02-16 | ₹15.93 (₹13.5 + 18% tax) | evidence + **ruling 4 assumption** | `WAYBACK_zerodha_charges_20161009084026.html` `cd66fee700c7`<br>`WAYBACK_zerodha_charges_20170317010757.html` `7da660e59125`<br>`WAYBACK_zerodha_charges_20180822091806.html` `9bdbe5edb345`<br>`WAYBACK_zerodha_charges_20190506071501.html` `0331ea42e374`<br>`WAYBACK_zerodha_charges_20200217130322.html` `c2ff785fb4ae`<br>`CBIC_GST_notfn8_2017_integrated_tax_rate.pdf` `1f2d7ff6b922`<br>`CBIC_GST_notfn11_2017_central_tax_rate.pdf` `a8051c8882b8` | RULING 4 ASSUMPTION: captures of 9 Oct 2016 to 6 May 2019 show Rs 13.5 per scrip without mentioning tax; Supplement ruling 4 treats it as before tax and adds the tax in force (higher-cost reading). The next capture, 17 Feb 2020, says Rs 13.5 + GST. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2020-02-17 | 2024-09-16 | ₹15.93 (₹13.5 + 18% tax) | evidence | `WAYBACK_zerodha_charges_20200217130322.html` `c2ff785fb4ae`<br>`WAYBACK_zerodha_charges_20220117095119.html` `964292b4e465`<br>`WAYBACK_zerodha_charges_20240301020050.html` `cd4467daab82`<br>`WAYBACK_zerodha_charges_20240917083204.html` `256680064b73`<br>`CBIC_GST_notfn8_2017_integrated_tax_rate.pdf` `1f2d7ff6b922`<br>`CBIC_GST_notfn11_2017_central_tax_rate.pdf` `a8051c8882b8` | Rs 13.5 + GST in the captures of 17 Feb 2020 to 1 Mar 2024. Capture of 17 Sep 2024 shows Rs 13 + GST: ruling 2 keeps the higher Rs 13.5 up to 16 Sep 2024. Tax included as billed: the indirect tax in force in this period; no further tax is added. |
| 2024-09-17 | 2026-09-01 | ₹15.34 (₹13 + 18% tax) | evidence | `WAYBACK_zerodha_charges_20240917083204.html` `256680064b73`<br>`WAYBACK_zerodha_charges_20241008053010.html` `2095c01bc984`<br>`WAYBACK_zerodha_charges_20241102213954.html` `0aea1fc02640`<br>`ZERODHA_charges_page.html` `aae15a3dd992`<br>`CBIC_GST_notfn8_2017_integrated_tax_rate.pdf` `1f2d7ff6b922`<br>`CBIC_GST_notfn11_2017_central_tax_rate.pdf` `a8051c8882b8` | Rs 13 + GST (capture 17 Sep 2024) = Rs 15.34 as billed (Rs 3.5 CDSL + Rs 9.5 Zerodha + Rs 2.34 GST; captures from 8 Oct 2024 and the page today). Tax included as billed: the indirect tax in force in this period; no further tax is added. |

## 3. Fallbacks and assumptions in the schedule

| # | Input | Period | Kind | What is assumed |
|---|---|---|---|---|
| 1 | Delivery STT, buy and sell | whole sample | §13 fallback | Current rate 0.1% each side. The enacted Finance Act 2012 was not obtained after a documented search |
| 2 | IPFT | 2012-07-02 → 2023-03-31 | §13 fallback (ruling 6) | Current amount ₹0.01 per crore. No NSE document states the amount for those dates |
| 3 | Stamp duty | 2012-07-02 → 2020-06-30 | §13 fallback (ruling 7) | Current 0.015% on the buyer only. It omits the seller's side and the state rates that applied then; may favour the strategy |
| 4 | Indirect tax | 2012-07-02 → 2015-05-31 | approved reading | 12% is official. The 2% and 1% cess rates come from three agreeing Zerodha lists, not from an official file |
| 5 | Indirect tax | 2016-06-01 → 2016-10-08 | approved bracket assumption | Official start date of the Krishi Kalyan Cess, with the 15% total taken from the Zerodha capture of 9 Oct 2016. Not direct official-rate evidence |
| 6 | Depository charge | 2016-10-09 → 2020-02-16 | ruling 4 | ₹13.5 is treated as before tax and the tax in force is added |
| 7 | Depository charge | 2012-07-02 → 2012-12-24 and 2014-07-04 → 2016-10-08 | ruling 2 | Two dated captures differ, so the higher amount applies between them |
| 8 | Depository charge | every period that sits on rows 4 or 5 | inherited | The tax inside the billed amount carries the same assumption |
| 9 | SEBI fee | 2020-06 → 2021-03 | ruling 5 | The temporary halving is not applied; no instrument is archived. Higher-cost reading |
| 10 | Exchange charge | 2020-08-01 → 2021-03-31 | ruling 3 | The temporary lower-rate scheme for stocks outside NIFTY 50 / Next 50 is not applied. Higher-cost reading |
| 11 | Brokerage | from 2015-12-01 | ruling 1 | Zero rate of a retail individual account; may favour the strategy |

Rows 1–5 carry `assumption: true` and a non-evidence `basis` in the file. Rows 6–8 carry `assumption: true` on the depository periods. Rows 9–11 are approved rulings, stated in the notes of the periods they affect.

## 4. Verification of the ten points

| Point | Result | How it is fixed in the file |
|---|---|---|
| IPFT never double-counted | Confirmed | `exchange_txn` holds the circulars' transaction charge only (3.25, 3.45, 3.25, 3.22, 2.97, 3.0699 ₹ per lakh). `ipft` is its own component. Test: charge + IPFT = ₹307 per crore on both sides of 1 Mar 2026, as NSE/FA/73061 tabulates |
| January 2021 increase not added as IPFT | Confirmed | The ₹0.20 per lakh rise sits in `exchange_txn` from 2021-01-01. `ipft` has no period starting in January 2021 and is the same on 2020-12-31 and 2021-01-01 |
| Exchange charge and IPFT separate | Confirmed | Two components, each with its own periods, units and evidence |
| Tax only on the frozen base | Confirmed, with caveat 1 | `indirect_tax_base` = brokerage, exchange charge, IPFT, SEBI fee. STT, stamp duty and the depository charge are outside it |
| Depository charge follows the retail-individual reading | Confirmed | Built from Zerodha's retail schedules and the depository's own fee; one billed amount per period |
| ₹1 crore portfolio convention | Confirmed | `notional_rs_per_portfolio` = 10,000,000; reset at every rebalance |
| One order per stock per rebalance | Confirmed | `orders_per_stock_per_rebalance` = 1 |
| Order value = absolute weight change × ₹1 crore | Confirmed | `order_value` = "abs(target weight - drifted weight) x notional_rs_per_portfolio" |
| Sell-side charge exactly as specified | Confirmed | dp_charge billed_rs once per stock sold per rebalance, whatever the size of the reduction; tax already included; never taxed again. A sale is: target weight below drifted weight; any reduction counts |
| No compounding | Confirmed | `compounding` = false. The schedule holds rates only; it contains no balance and no path |

Note: the sell-side charge rule is in Addendum 1 (rule 6); Supplement 1 adds ruling 4 on its tax. Both are applied.

## 5. Unresolved caveats

1. **IPFT inside the tax base.** Frozen §13 taxes "brokerage + exchange + SEBI", and its exchange line reads "Exchange transaction charge + IPFT". The schedule therefore taxes IPFT. If the reviewer reads the base as excluding IPFT, one line of the file changes. The effect is on a contribution of ₹0.01 to ₹10 per crore.
2. **Depository charge, 2 Jul – 24 Dec 2012.** The higher amount (₹15 + ₹4.50) applies under ruling 2. The lower amount (₹8 + ₹4.50) already appears in a form whose file was created in July 2012, so the higher amount may overstate the cost for part of this period. File dates are not effective dates, so the ruling is applied as written.
3. **Depository charge, 4 Jul 2014 – 8 Oct 2016.** ₹13.5 is carried back from the October 2016 capture under ruling 2. The switch from ₹12.5 to ₹13.5 is not dated.
4. **Depository fee component.** The depository's ₹4.50 is the NSDL fee. The ₹13.5 of 2016 implies a different depository fee (₹5.5); the depository's own document for that is not archived. The billed total comes from the broker's page, so no rate depends on it.
5. **Swachh Bharat Cess notifications** are archived in Hindi; the English statement of the same rate and date is the department's FAQ.
6. **Brokerage wording.** Some captures say "per trade", the tariff sheet says "per executed order". Addendum rule 4 fixes one order per stock, so the cap is ₹20 per stock traded.
7. **Asymmetry disclosure of Addendum 1 section 5** stands: flat rupee charges weigh more on the benchmark, which holds more stocks. It is not quantified here, because nothing was calculated.
8. **Two schedule files exist.** The registered code reads the older file and refuses to compute while it has empty rates. Addendum 1 says step E must be new code. The new code must read the dated file; the older file should stay as it is unless the reviewer says otherwise.
9. **Not obtained (optional):** the 2020 stamp-duty rate notification and the SEBI 2020–21 halving instrument.

## 6. Validation

File: `tests/test_s2mom_cost_schedule.py`. It reads the schedule file and the evidence archive only.

Result on 2026-10-06: **40 passed, 0 failed** (`python3 -m pytest tests/test_s2mom_cost_schedule.py`). The whole repository suite also passes: 359 passed, 0 failed.

| Required check | Test | Result |
|---|---|---|
| No missing rates | `test_no_missing_rate`, `test_all_required_components_present` | pass |
| No overlapping periods; no gaps | `test_no_gap_no_overlap_whole_sample` (9 components) | pass |
| Correct effective-date boundaries | `test_effective_date_boundaries` (18 boundaries, last day before and first day after), `test_constant_inputs` | pass |
| Correct units | `test_units` | pass |
| Correct tax bases | `test_tax_base_is_the_frozen_one`, `test_dp_charge_includes_exactly_the_tax_in_force_once`, `test_education_cess_period_is_12_percent_plus_3_percent_of_it` | pass |
| IPFT non-double-counting | `test_ipft_is_separate_and_never_double_counted` | pass |
| January 2021 non-double-counting | `test_january_2021_increase_is_in_the_transaction_charge_only` | pass |
| Fallbacks and assumptions marked | `test_every_fallback_and_assumption_is_marked` | pass |
| Conventions of Addendum 1 | `test_conventions_match_addendum_1` | pass |
| Reproducibility from archived evidence and fallback metadata | `test_reproducible_from_archived_evidence` (every cited file exists and matches its hash and the manifest; parent protocol, addendum and supplement hashes match), `test_schedule_is_the_audited_file` (the file hash is pinned) | pass |

Not covered by a test: that each number was read correctly from its source document. That was checked by reading the documents; the notes in section 2 say where each number comes from.

## 7. Remaining blockers before Step E may be executed

1. Reviewer acceptance of this schedule, including caveat 1 (IPFT in the tax base) and caveats 2 and 3 (how ruling 2 dates the depository charge).
2. A reviewer statement on whether the second half of B2 ("no empty rate") is now closed.
3. Step E is not implemented. Addendum 1 requires new code that reads the saved holdings and this dated schedule; the registered code is not to be changed. That code needs its own authorisation and tests.
4. B3 and B4 remain open. Frozen §32 asked for them to be closed before returns are computed; DEV-1 records that this order was already broken once. The reviewer must say whether step E waits for them.
5. Explicit, separate authorisation to execute Step E.

## 8. Unchanged

Compared with a snapshot taken before this step (85 files: results, registered code, scripts, configuration, protocol documents, stage 3 data, tests, registry): every file is byte-identical. Two files were added inside those folders: the schedule and its test file. All registry-recorded hashes of result files, the protocol, Addendum 1 and Supplement 1 still match.

