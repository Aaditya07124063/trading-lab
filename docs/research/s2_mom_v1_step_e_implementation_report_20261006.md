# S2-MOM-v1 — step E implementation and test report (2026-10-06)

**Step E was implemented and tested. It was NOT run.** No real historical cost, turnover, net return or break-even was calculated. Every test uses made-up holdings.

## 1. Reviewer decisions recorded (2026-10-06)
1. B2 — Evidence closure: PASS.
2. Cost-schedule closure: PASS.
3. IPFT stays inside the tax base, as the frozen "Exchange transaction charge + IPFT" line reads. The schedule is not reinterpreted.
4. The higher-cost depository treatment is accepted, with both caveats kept:
   - 2 Jul – 24 Dec 2012: ₹15 + ₹4.50. The lower amount (₹8 + ₹4.50) already appears in a form whose file was created in July 2012, so this may overstate the cost for part of the period.
   - 4 Jul 2014 – 8 Oct 2016: ₹13.5 carried back from the October 2016 capture under ruling 2. The date of the change from ₹12.5 is not known.
5. B3 and B4 remain OPEN. They do not block step E implementation or execution.
6. The A–D, sensitivity and confirmation results are frozen.

## 2. Files
| File | Status | SHA-256 |
|---|---|---|
| `src/stage3/step_e.py` | created (188 lines) | `250951a20e2029b41ba835b87f39429a87144d51625c74c77e39a9d7856e49fe` |
| `tests/test_s2mom_step_e.py` | created | `7db365f7116f56f4809264c05ba10b5fe90eedae33a2caed3d0b0fd961d44e10` |
| this report | created | — |
| `RESEARCH_LOG.md` | one entry added | — |

No other file was changed. The registered code (`src/stage3/costs.py`, `ladder.py`, `experiment.py`, `scripts/run_s2_mom.py`) is untouched, and the new module does not import it.

**Implementation hash:** the SHA-256 of `src/stage3/step_e.py` above.

## 3. Inputs the code is tied to
| Input | SHA-256 | How it is enforced |
|---|---|---|
| Dated schedule `config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json` | `47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f` | pinned in the code; a file with any other hash is refused |
| Frozen protocol | `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838` | checked on every load |
| Addendum 1 | `d12ccaa6fa23143f808b429d75c757a57a853afa42e961a94157d3b772dffefe` | checked on every load |
| Supplement 1 | `ab28fd1750db3e222819013ef70ff69c4b48d5d5757d51ec5c77e9b6232253b3` | checked on every load |

## 4. What the code does
- `load_schedule` — loads the approved schedule only; checks its hash, its parents, and that every component has a rate for every day of the sample with no gap or overlap.
- `period` — the one schedule period in force on a date. It raises if there is none; nothing is extrapolated.
- `order_cost` — every class 1 cost of one order, in rupees.
- `cost_ledger` — one row per order from a saved-holdings table.
- `monthly_costs` — the cost of each rebalance as a fraction of ₹1 crore.
- `net_of_class1` — gross return copied unchanged, minus the class 1 cost (scenario S0).

Rules applied:
| Rule | Implementation |
|---|---|
| ₹1 crore per portfolio at every rebalance, no compounding | the notional is a constant; no return or portfolio value enters the cost |
| One order per stock per rebalance | one ledger row per (rebalance, stock) |
| Order value | absolute (target weight − drifted weight) × ₹1 crore. Target = saved `begin_weight`; drifted = previous month's saved `end_weight` |
| Dated rates | the period in force on the trade date (the entry session `s_plus`); later periods are never read |
| STT | buy and sell |
| Stamp duty | buy only |
| Exchange charge and IPFT | two separate lines, each counted once |
| SEBI fee | both sides |
| Brokerage | per order: lower of rate × order value or the cap; zero from 1 Dec 2015 |
| Indirect tax | rate × (brokerage + exchange charge + IPFT + SEBI fee). Nothing else is taxed |
| Depository charge | once per stock whose target is below its drifted weight, whatever the size; tax already inside; not taxed again |
| No change in weight | no order, no charge |

Conventions taken from the registered code (`ladder.net_of_costs`): the first month of a sample is a full purchase from cash; nothing is charged for selling the last month's holdings.

**Traceability.** Each ledger row carries: sample, step, portfolio, selection date, holding month, trade date, stock, drifted weight, target weight, weight change, notional, side, order value, the eight cost lines, the tax base, the tax rate, the total, the cost as a fraction of the portfolio, the start date of the schedule period behind every component, and the list of fallbacks and assumptions that applied.

**Refusals.** The code raises, and calculates nothing, when: the schedule file differs from the approved hash; a parent document differs; a period or rate is missing; a trade date is outside the schedule; holding months are not consecutive; a month is not "OK"; a weight is missing; a stock appears twice.

## 5. Tests
`tests/test_s2mom_step_e.py`: **40 tests, 40 passed, 0 failed.**
With the schedule tests: 80 passed. Whole repository: **399 passed, 0 failed.**

| Required test | Test function |
|---|---|
| Schedule loading | `test_loads_only_the_approved_schedule`, `test_parent_documents_are_checked` |
| Effective-date boundaries | `test_rate_change_on_before_and_after_its_effective_date` (8 cases) |
| No gaps, no overlaps | `test_no_gap_no_overlap` (9 components) |
| Buy vs sell | `test_buy_order_by_hand`, `test_sell_order_by_hand` |
| STT; stamp duty buyer only | `test_stt_both_sides_stamp_duty_buyer_only_dp_seller_only` |
| Brokerage | `test_brokerage` |
| Exchange + IPFT; no double-counting of IPFT | `test_exchange_charge_and_ipft_are_separate_and_counted_once` |
| January 2021 not double-counted | `test_january_2021_increase_is_counted_once_in_the_exchange_charge` |
| SEBI | `test_sebi_fee` |
| Indirect tax base | `test_indirect_tax_base_and_rates` |
| Depository sell-side charge | `test_depository_charge_once_per_stock_sold_whatever_the_size` |
| ₹1 crore notional; absolute-weight-change sizing | `test_ledger_orders_weights_and_notional` |
| Zero weight change | `test_zero_weight_change_makes_no_order` |
| Deterministic repeat | `test_deterministic_and_independent_of_row_order` |
| Fallback flags | `test_fallback_and_assumption_flags_travel_with_each_order` |
| Traceability | `test_every_cost_is_traceable` |

| Adversarial test | Test function |
|---|---|
| Future information cannot change a past cost | `test_future_information_cannot_change_a_past_cost` (every later schedule period corrupted; later months added) |
| New rate on its effective date; one day before and after | `test_rate_change_on_before_and_after_its_effective_date` |
| No cost when a period is missing | `test_no_cost_when_a_schedule_period_is_missing`, `test_holdings_that_cannot_be_costed_raise` |
| No compounding of the notional | `test_notional_is_never_compounded` |
| Gross A–D returns not modified | `test_gross_returns_are_copied_never_changed`, `test_registered_result_files_are_byte_identical`, `test_module_is_separate_from_the_registered_code_and_writes_nothing` |

## 6. Not implemented, on purpose
1. **A runner that reads the saved files and writes outputs.** The repository's access-boundary test forbids research code from calling `read_csv` unless the file is on an allow-list inside `tests/test_access_boundary.py`. That file is a safety guard, so it was not edited. The module therefore takes the holdings as a table passed in by the caller. A runner needs one allow-list line approved by the reviewer.
2. **Slippage scenarios S1–S4, the break-even cost and the test H4.** The request was for class 1 delivery costs. The break-even also needs a decision: frozen §13 defines it as a single one-way cost, while S1–S4 use two rank bands with different slippage.

## 7. Remaining blockers before step E may be executed
1. Reviewer approval of the allow-list line and a small runner script (point 6.1).
2. Reviewer decision on whether execution covers class 1 costs only (S0), or also S1–S4, break-even and H4 (point 6.2). The second needs more code and tests.
3. Reviewer statement on which steps and portfolios to cost. Frozen §13 names W and the benchmark at step D; frozen §23 reports turnover for W, L and the benchmark at every ladder step.
4. Explicit, separate authorisation to execute.

## 8. Unchanged
- 122 files compared with a snapshot taken before this step (results, all of `src/`, scripts, configuration, protocol documents, stage 3 data, tests, registry): none changed. Two files were added: the module and its tests.
- The ten registered result files match the hashes in the registry (also checked by a test on every run).
- `results/s2_mom_v1/` still holds the same 12 files.
- The dated schedule, Addendum 1, Supplement 1 and the frozen protocol match the hashes in section 3.
- Nothing was committed.
