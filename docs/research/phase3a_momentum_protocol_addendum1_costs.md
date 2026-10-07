# S2-MOM-v1 — Addendum 1: cost specification for step E

**Status:** APPROVED by the reviewer on 2026-10-05. Registered. Its SHA-256 is recorded in `registry/experiments.jsonl` (record `S2-MOM-v1`) and in `RESEARCH_LOG.md`.

**Parent protocol:** `docs/research/phase3a_momentum_protocol.md`, frozen, SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`. This addendum is a separate file. The frozen protocol is not edited and its hash is unchanged.

## 1. When this was specified

This addendum was specified **after** the gross primary, sensitivity and confirmation results of S2-MOM-v1 were computed, registered and known, and **before** any cost, turnover or net-return figure was computed.

- Known when it was written: the gross monthly returns of steps A–D, the primary estimand, the sensitivity results and the chronological confirmation results.
- Not computed when it was written: any cost, any turnover figure, any net return, any break-even cost, step E, and the survival test H4.

Every result that uses this addendum must carry this statement.

## 2. What this addendum does not change

**It changes no part of steps A–D.** Universes, identity, return rules, formation, holding, ranking, weights, the primary estimand, the samples and the statistical tests are exactly as frozen. Costs are a deduction applied afterwards to the holdings saved by the registered runs. The registered primary, sensitivity and confirmation results are not altered.

It does not change the slippage scenarios S0–S4 of frozen §13, the benchmark rule ("the benchmark pays costs on its own turnover"), or the test H4.

## 3. Why it is needed

Frozen §13 leaves six points open, so that two faithful implementations could produce different net results from the same holdings. They are set out in the Step E decision memo and proposal of 2026-10-05. The six rules below close them. They were chosen on grounds that do not depend on results: the least researcher discretion, the strongest reproducibility, and the conservative option where two were otherwise defensible.

## 4. The six rules

### Rule 1 — Broker
Class 1 costs are those billed by **Zerodha** on NSE cash-market delivery trades, taken from its **dated delivery schedule**.

Zerodha is the primary cost schedule of the lab's ORB v1 protocol, which was frozen before any S2-MOM-v1 result existed. The broker is therefore not a choice made in the light of these results.

### Rule 2 — Exchange transaction charge before 1 October 2024
Before 1 October 2024 the NSE cash-market transaction charge depended on the trading member's monthly turnover. For every trade date before 1 October 2024, the charge is the rate of the **lowest monthly-turnover slab in force on that date, which is the highest rate**. From 1 October 2024 it is the uniform rate in force on the trade date. Any separately stated investor-protection contribution in force on the trade date is added.

### Rule 3 — Indirect tax on charges
The line "GST" in frozen §13 is read as **the indirect tax on charges in force on the trade date**:
- before 1 July 2017: service tax, including the cesses applicable on that date;
- from 1 July 2017: GST.

The tax base is the one stated in frozen §13 for all dates: brokerage + exchange charge + SEBI fee.

### Rule 4 — Notional and order convention
- The notional is **₹1 crore per portfolio**, as frozen §13 states. It is not a per-stock amount. The amount per stock is ₹1 crore divided by the number of stocks the portfolio holds, so it differs between portfolios and months.
- Each portfolio is valued at ₹1 crore **at every rebalance**. The notional is not compounded.
- Each stock traded at a rebalance is **one order**.
- **Order value = the absolute change in the stock's weight × ₹1 crore**, where the change is target weight minus drifted weight.
- This notional applies to every fee stated in rupees: any per-order brokerage and the sell-side charge of rule 6.

### Rule 5 — Dated schedules and the fallback
Every class 1 input follows its **dated schedule**, built from archived official or primary sources. The single "expected" rates in the table of frozen §13 are expectations to be verified, not fixed constants.

Where a historical rate cannot be evidenced after a **documented search**, the fallback of frozen §13 applies: "the current rate is applied to the whole sample and labelled as an assumption." Each use of the fallback must record the input, the period, the search made and the archived evidence of the current rate.

Where the fallback is used, frozen §13's description of S0 as "the only scenario with no assumption" is qualified: every fallback assumption is listed with each result that uses it.

A rate is never set to zero for lack of evidence.

### Rule 6 — Sell-side account and depository charge, and what counts as a sale
- The charge is **the total amount billed by Zerodha per stock per sell day**, with **tax included as billed**. No further tax is added to it.
- It is dated from the broker's and the depository's schedules under rule 5.
- A stock is **sold** at a rebalance if its **target weight is below its drifted weight**. Any reduction counts, however small.
- The charge is applied **once per stock per rebalance**, whatever the size of the reduction.

Frozen §10 resets every portfolio to equal weights at each rebalance, so reductions occur by design. No threshold is introduced, because a threshold would be a new strategy rule.

## 5. Disclosure — asymmetry between the benchmark and the winner and loser portfolios

A flat charge per stock sold, applied to a notional of ₹1 crore per portfolio, weighs more on a portfolio that holds more stocks. The benchmark holds about three times as many stocks as the winner or the loser portfolio. The sell-side charge of rule 6 therefore reduces the benchmark's net return by more than it reduces the winner portfolio's, which raises the winner portfolio's net return relative to the benchmark. The same holds for any per-order rupee brokerage.

This follows from the frozen design (the per-portfolio notional and the rule that the benchmark pays costs on its own turnover), not from this addendum. **Its size has not been quantified, because no cost calculation has been performed.** It may favour the survival result, and it must be stated wherever step E or H4 is reported.

## 6. What remains open

- **B2 remains OPEN.** This addendum is a specification only. No evidence has been acquired or archived under it, and the delivery cost schedule is not complete: five class 1 rates are still empty. B2 closes only when every input required by rules 1–6 has an archived source with a hash, or a documented fallback, and the cost schedule file has no empty rate.
- **B3 remains OPEN** (full texts of cited papers). It is separate from this addendum.
- **B4 remains OPEN** (references cited from memory). It is separate from this addendum.
- The procedural sequencing deviation DEV-1 (`docs/research/s2_mom_v1_deviation_log.md`) stands as recorded.

## 7. Stages after this addendum

| Stage | Status |
|---|---|
| Methodological decision | Done: the six rules above, approved 2026-10-05 |
| Protocol amendment | This addendum |
| Evidence acquisition | Not started |
| Implementation | Not started. It must be new code that reads the saved holdings; the registered experiment code is not to be changed |
| Execution of step E | Not authorised |
