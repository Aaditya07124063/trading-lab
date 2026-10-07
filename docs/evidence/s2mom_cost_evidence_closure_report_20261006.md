# S2-MOM-v1 — cost-evidence closure report (2026-10-06)

**B2 status: OPEN. It cannot be declared closed.**

Inspection and evidence only. No cost schedule was created. No cost, turnover, net return or break-even was calculated. Step E was not implemented or run. No protocol, addendum, experiment code or result file was changed.

## 1. Supplement
- `docs/research/phase3a_momentum_protocol_addendum1_supplement1.md`
- SHA-256 `ab28fd1750db3e222819013ef70ff69c4b48d5d5757d51ec5c77e9b6232253b3`
- Registered in `registry/experiments.jsonl` under record `S2-MOM-v1`.
- Addendum 1 is byte-identical: `d12ccaa6fa23143f808b429d75c757a57a853afa42e961a94157d3b772dffefe`.
- The seven rulings are verbatim from the approved memo. The file also carries a short timing statement, a disclosure paragraph and an open-items paragraph, which were not part of the seven.

## 2. Newly archived evidence (2026-10-06)
All in `docs/evidence/s2mom_costs/`; full details in `MANIFEST.csv`.

| File | Source | Class | Date | SHA-256 | Relevance |
|---|---|---|---|---|---|
| `WB_CBEC_st14-2015.pdf` | tax department file, via an Internet Archive capture | official | 19 May 2015 | `6c9ab52e02bf08e69b9be6fef3179773adf7fc2773cb76db61bd9c1b667d9a30` | Fixes **1 June 2015** as the date the Finance Act 2015 service-tax provisions came into force. It gives the date, not the rate |
| `WB_CBEC_st27-2016.pdf` | same | official | 26 May 2016 | `278b5d3a0b91a03b9a0a5172a5e472ee015b5ff0c058ef1ffc23075b7236f30e` | Krishi Kalyan Cess rules in force **1 June 2016**. Date, not rate |
| `WB_CBEC_st28-2016.pdf` | same | official | 26 May 2016 | `caaf64be41ce1a347dc7f9d6cb6b210c8e736c3a13aadfc9da7d235611c3495f` | Krishi Kalyan Cess exemption alignment. Context only |
| `SEARCH_LOG_20261006.txt` | local record | search log | 2026-10-06 | in the manifest | Every attempt made today, with outcome |

The manifest now lists 43 files.

## 3. What the closure searches found, item by item

| Item sought | Attempts | Outcome |
|---|---|---|
| Service-tax rate notifications 2012 – June 2017 | Three official addresses did not respond. Internet Archive copies of the department's files were tried for five notifications | **Partly obtained.** Two commencement dates are now official (1 June 2015; 1 June 2016). **No archived document states a rate** (12.36%, 14%, 14.5%, 15%); the rates sit in Finance Acts that are not archived. The November 2015 cess notifications were not found |
| GST rate notification | Two addresses tried | **Not obtained.** One returned an error page, one returned an unrelated web page |
| SEBI instrument raising the fee to ₹20 | One guessed SEBI address tried | **Not obtained.** The address did not exist. No proper search for the instrument was made |
| Depository charge before October 2016 | Six Internet Archive index queries | **Search incomplete.** The archive's index answered "Temporarily Offline" to every query. This is an outage, not a negative result |
| Delivery brokerage, 2 July – 26 September 2012 | One Internet Archive index query | **Search incomplete**, same outage |
| Enacted Finance Act 2012 | Four addresses tried | **Not obtained.** No response, not found, or access refused |
| IPFT before April 2023; NSE circulars 2009–2020 | No new attempt beyond the circulars archived on 2026-10-05 | **Not searched further.** The circular numbers for that period are not known, and no index of NSE circulars was consulted |
| 2020 stamp-duty notification; SEBI 2020–21 halving instrument (optional) | Not attempted | Not obtained |

## 4. Unresolved inputs
| Input | Period | Why unresolved |
|---|---|---|
| Indirect tax rate | 2012-07-02 → 2016-10-08 | Dates partly official; no archived source for any rate |
| Indirect tax rate | 2017-07-01 → 2018-08-21 | No archived source |
| SEBI fee | from an unknown date in 2014-15 → 2017-03-31 | Date and instrument of the rise to ₹20 not archived |
| Depository charge | 2012-07-02 → 2016-10-08 | Not found; search incomplete because of an outage |
| Delivery brokerage | 2012-07-02 → 2012-09-26 | Not found; search incomplete because of an outage |
| IPFT amount | before 2023-04-01 | Not established; not searched further |
| Delivery STT | 2012-07-01 start | Supported by the Finance Bill memorandum (a proposal). The enacted Act is not archived |

## 5. Fallback inputs
The approved condition for the fallback is a **documented failed search** plus archived current-rate evidence.

| Input and period | Search status | Fallback that would apply | Archived current-rate evidence | Fallback usable now? |
|---|---|---|---|---|
| Stamp duty, 2012-07-02 → 2020-06-30 | Not needed: an official document states no single rate existed | 0.015% on the buyer | `NSE_static_stamp_duty_page.html`; `ZERODHA_bulletin_uniform_stamp_duty_20200701.html` | **Yes** (ruling 7) |
| Depository charge, 2012-07-02 → 2016-10-08 | Incomplete (outage) | ₹15.34 per stock per sell day, tax included | `ZERODHA_charges_page.html` | **No** — the search has not failed, it has not been completed |
| Delivery brokerage, 2012-07-02 → 2012-09-26 | Incomplete (outage) | zero (current retail rate) | `ZERODHA_charges_page.html` | **No**, same reason. Note: the current rate is zero, while the first capture, one day after this period, shows a non-zero rate. Applying the fallback here would lower the cost |
| IPFT before 2023-04-01 | Not carried out | ₹0.01 per crore | `docs/evidence/NSE_FA73061_2026-02-27_transaction_charges.pdf` | **No** — no documented search yet |
| Indirect tax, 2012-07 → 2016-10 and 2017-07 → 2018-08 | Official sites unreachable; archive copies partly found | 18% | captures from 2018-08 | **No** — the history is obtainable in principle, so the fallback condition is not met |
| SEBI fee, 2014-15 → 2017-03 | One address tried | ₹10 per crore | `NSE_static_sebi_fees_stt_page.html` | **No** — obtainable in principle; no adequate search |

## 6. Explicit verifications
| Check | Result |
|---|---|
| IPFT is not double-counted | Confirmed in the evidence tables: the transaction charge and the IPFT contribution are taken from separate columns of the NSE circulars; no archived circular states a charge that already includes IPFT |
| The January 2021 increase is not added again as IPFT | Confirmed: NSE/FA/46730 raises the transaction charge itself to ₹3.45; it is recorded once, as a transaction charge. Supplement ruling 6 states this |
| No capture is treated as an effective date | Confirmed: every capture is recorded as "capture" with its date; effective dates appear only where an archived document states them (1 Dec 2015 brokerage; NSE and SEBI instruments). Supplement ruling 2 governs |
| No silent retail-individual assumption | Confirmed: the account type is an explicit approved ruling (supplement ruling 1), with its possible favourable effect disclosed |
| No historical state stamp-duty rate invented | Confirmed: no state rate is recorded anywhere. The pre-July-2020 period uses the frozen fallback as written (ruling 7) |

## 7. B2 determination
**B2 is NOT closed.** The closing test is: every required input has archived defensible evidence for its period, or a documented failed search with the approved fallback and archived current-rate evidence.

It fails for:
1. indirect tax before October 2016 and for July 2017 to August 2018;
2. the SEBI fee between 2014-15 and March 2017;
3. the depository charge before October 2016;
4. delivery brokerage for 2 July to 26 September 2012;
5. the IPFT amount before April 2023.

For items 3 and 4 the search was cut short by an outage, so the fallback cannot honestly be invoked. For items 1, 2 and 5 no adequate search has been made.

It is met for: the NSE transaction charge 2009–2026; IPFT from April 2023; the SEBI fee from April 2017; stamp duty for the whole period (evidence from July 2020, approved fallback before); delivery brokerage from 27 September 2012; the depository charge from 9 October 2016; delivery STT, subject to the proposal-document caveat.

## 8. Remaining blockers before the cost schedule may be created
1. Repeat the Internet Archive queries for earlier Zerodha pages when the index is available; archive what is found, or record a completed failed search.
2. Obtain official rate evidence for service tax (2012 – June 2017) and GST (from July 2017): the Finance Acts of 2012, 2015 and 2016, the November 2015 cess notifications, and the 2017 GST rate notification.
3. Obtain the SEBI instrument that set the ₹20 fee, with its date.
4. Carry out and record a search for the IPFT contribution before April 2023.
5. Obtain the enacted Finance Act 2012, or accept in writing that the memorandum plus the 2024 and 2026 NSE circulars suffice for delivery STT.
6. Then: your authorisation to create the schedule.

## 9. Unchanged
The frozen protocol, Addendum 1, ORB v1, all experiment code and all registered result files are byte-identical to their recorded hashes. See the verification in `RESEARCH_LOG.md`, entry of 2026-10-06.
