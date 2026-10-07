# S2-MOM-v1 — Supplement 2 to Addendum 1: rulings on the step E method

**Status:** APPROVED by the reviewer on 2026-10-06. Registered. Its SHA-256 is recorded in `registry/experiments.jsonl` (record `S2-MOM-v1`) and in `RESEARCH_LOG.md`.

**Parents:**
- Frozen protocol `docs/research/phase3a_momentum_protocol.md`, SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`.
- Addendum 1 `docs/research/phase3a_momentum_protocol_addendum1_costs.md`, SHA-256 `d12ccaa6fa23143f808b429d75c757a57a853afa42e961a94157d3b772dffefe`.
- Supplement 1 `docs/research/phase3a_momentum_protocol_addendum1_supplement1.md`, SHA-256 `ab28fd1750db3e222819013ef70ff69c4b48d5d5757d51ec5c77e9b6232253b3`.

This supplement is a separate file. No parent is edited, and all three hashes are unchanged.

**Timing.** Specified after the gross primary, sensitivity and confirmation results of steps A–D were computed, registered and known (so the H3 outcomes were known), after the dated cost schedule was approved, and after the class 1 cost code was written and tested on made-up holdings only. Specified **before** any real cost, turnover, net return, break-even cost or H4 result was computed. Every result that uses this supplement must carry this statement.

**It changes no A–D calculation.** Universes, identity, return rules, formation, holding, ranking, weights, the primary estimand, the samples, the statistical tests and every registered gross, sensitivity and confirmation result are exactly as frozen and registered. Costs are a deduction applied afterwards to the holdings saved by the registered runs.

## 1. Scope

- Rulings 8–16 close the points that frozen §13, §23 and Addendum 1 leave open for step E: the first month, the sample boundary, the two samples, slippage, the break-even cost, the H3 → H4 sequence, which portfolios are costed, the required outputs, and how the scenarios are described.
- They apply to step E only, at ladder step D holdings (frozen B1.4: "Step D net, under each scenario").
- They add no scenario and no parameter. The slippage values are the frozen ones.
- Rulings 1–7 (Supplement 1) and rules 1–6 (Addendum 1) stand unchanged.
- Rulings 11 and 14 were amended by the reviewer on 2026-10-06, before this supplement was hashed and before any result existed. Section 3 states what was replaced.

## 2. The rulings

### Ruling 8 — First month
The first holding month is established from cash.

- The drifted weight of every stock is zero.
- The entire target portfolio is purchased at the first entry session.
- Each stock therefore generates one buy order with order value = target weight × ₹1 crore.
- All applicable buy-side class 1 costs and the selected S0–S4 slippage are charged.
- This applies to W, the hypothetical L portfolio, and the benchmark where those portfolios are costed.
- It applies independently to the primary and confirmation samples.
- This changes no A–D gross result.

### Ruling 9 — Final sample boundary
- No artificial terminal liquidation is created.
- The final holding month ends at the defined `s⁺⁺` observation boundary.
- No additional sell order, depository charge, statutory cost or slippage is created at the sample boundary.
- Costs occur at entry and rebalance sessions within the sample.

### Ruling 10 — Primary and confirmation samples
- The primary and confirmation samples are costed independently.
- The confirmation sample starts from cash. It does not inherit the primary sample's final portfolio.
- **Disclosure:** this creates a full initial purchase at the confirmation boundary, where a continuously invested portfolio would instead rebalance.

### Ruling 11 — Slippage (as amended, see section 3)
For every S1–S4 order:

- slippage is a one-way rate applied to traded order value;
- it applies to buys and sells;
- the rate is determined from the stock's UNIV-1 liquidity rank at the selection date `t` of the rebalance at which the order is traded. This holds for every order, including the sale of a stock that has left the portfolio;
- an order for a stock ranked above 500, or with no UNIV-1 rank, at that date takes the frozen 201–500 rate of the same scenario. This is an **assumption**; step E must report how many orders, and how much traded value, use it;
- the same scenario applies to W, hypothetical L and the benchmark;
- slippage is **not** included in the statutory indirect-tax base;
- S0 = 0 bps slippage.

Frozen scenario values (one-way, rank 1–200 / rank 201–500), used exactly:

| Scenario | Rank 1–200 | Rank 201–500 |
|---|---|---|
| S0 | 0 bps | 0 bps |
| S1 | 5 bps | 15 bps |
| S2 | 10 bps | 30 bps |
| S3 | 25 bps | 75 bps |
| S4 | 50 bps | 150 bps |

The frozen rank bands are used exactly. The frozen scenario values are not altered.

**To be reported:** every stock *held* at step D is inside the UNIV-1 top-200 liquidity universe at its selection date, so every purchase and every increase is in the 1–200 band. The 201–500 rate can arise only on the sale of a stock that left the top 200 by the rebalance at which it is sold. Step E must report the number and traded value of orders in each band.

### Ruling 12 — Break-even
Define:

- `x` = mean monthly net excess return of W over the benchmark under S0.
- `d` = mean monthly traded value of W minus the benchmark, where traded value includes buys + sells and is expressed as a fraction of the ₹1 crore portfolio.
- `break_even_one_way_cost = x / d`.

Undefined cases:

- If `d <= 0`: report "no break-even: W does not trade more than benchmark."
- If `x <= 0`: report "does not pass S0."
- No break-even value is manufactured for an undefined case.

The break-even calculation is descriptive economic analysis. It is not a replacement for H4.

### Ruling 13 — H3 and H4
**Primary sample: H3 IS SUPPORTED.** The registered step D WML satisfies the frozen H3 criterion: mean `WML_D` > 0 and one-sided p < 0.05. Therefore H4 is eligible in the **primary** sample.

H4 uses the frozen inference convention: one-sided Newey–West inference with lag 4. Frozen §15 fixes lag 4 for T = 114, which is the length of the primary sample, and the registered code uses the same lag for that sample (`NW_LAG["PRIMARY"] = 4` in `src/stage3/protocol.py`). No other lag is established for this test.

**Confirmation (chronological out-of-sample): H3 is NOT supported.** Therefore H4 is **not run** for the confirmation sample. The confirmation result is not modified.

### Ruling 14 — Which portfolios are costed (as amended, see section 3)
For hypothesis testing and the primary economic comparison:

- W: costed.
- Benchmark: costed.
- L: not used in H4.

Because the frozen reporting tables require an A–E presentation with W, L, WML and the benchmark, a hypothetical cost treatment is also calculated for L. L is treated as a hypothetical long ₹1 crore portfolio under exactly the same cost rules as W.

Then:

`hypothetical_net_WML_E = gross WML_D − cost of W − cost of L`

The costs of both legs are deducted.

This hypothetical net WML:

- is descriptive only;
- must be explicitly labelled "hypothetical";
- must **not** be used in H4;
- must **not** be used as a separately tested hypothesis;
- must **not** be presented as the performance of an implementable long-short portfolio.

L turnover remains reported separately under the existing §23 convention.

### Ruling 15 — Required step E outputs
Step E must support:

- For W, hypothetical L and the benchmark: S0, S1, S2, S3, S4.
- For W and the benchmark: monthly net returns; mean net return; turnover; cost; the H4 comparison where eligible.
- For L: descriptive hypothetical net return only.
- Break-even: the primary sample, where H3 is supported. No confirmation break-even and no confirmation H4, because H3 is not supported there.

No additional scenario or parameter is introduced.

### Ruling 16 — Interpretation of results
- S1–S4 are not called "post-hoc robustness tests". They are pre-specified cost scenarios required by the frozen step E specification.
- No result is used to alter these rulings.

## 3. Amendments made by the reviewer before registration

Three points were put to the reviewer on 2026-10-06 while this supplement was being drafted. No cost, turnover or net return existed. The reviewer's answers are part of the rulings above.

| Ruling | First wording | Problem | Reviewer's answer |
|---|---|---|---|
| 11 | Rank "at the relevant rebalance/entry time"; and "the 201–500 band does not actually occur in these portfolios" | A stock sold because it left the top 200 is ranked above 200 at that rebalance, so the two sentences disagree for exit sales. Frozen §13 has no band above rank 500 | The rank at the rebalance where the order trades is used. The sentence that the 201–500 band does not occur is withdrawn. Above rank 500 or unranked: the frozen 201–500 rate, labelled an assumption |
| 14 | `hypothetical_net_WML_E = net_W_E − net_L_E` | With L costed as a long portfolio, this formula adds L's costs to WML, so more cost on the loser leg would raise the hypothetical net WML | Both legs' costs are deducted: gross `WML_D` − cost of W − cost of L |
| 15 | "no confirmation break-even/H4 if H3 is not supported there" | Frozen §13 lists the break-even under "Always reported, for W and for the benchmark" | Ruling 15 is kept as written, and the difference is disclosed (section 7) |

The two readings chosen for ruling 11, and the one chosen for ruling 14, are the higher-cost readings.

## 4. Formulas

All symbols are per sample, per portfolio `P` ∈ {W, L, BM}, per holding month `t`, at ladder step D.

**Orders (Addendum 1 rule 4; rulings 8 and 9).**
- `target_i(t)` = saved begin weight of stock `i`. `drift_i(t)` = saved end weight of stock `i` in the previous holding month of the same sample, and zero in the first month of the sample.
- One order per stock with `target_i(t) ≠ drift_i(t)`. `order_value_i(t) = |target_i(t) − drift_i(t)| × ₹1 crore`. It is a buy if the target is above the drifted weight, and a sale otherwise.
- Orders trade at the entry session `s⁺` of month `t`. No order exists after the last holding month.

**Costs.**
- `class1_i(t)` = the class 1 cost of the order in rupees, from the dated schedule, under Addendum 1 and Supplement 1.
- `slippage_i(t, S) = order_value_i(t) × rate(S, band_i(t)) / 10,000`, with the rate in bps. `band_i(t)` is 1–200 if the stock's UNIV-1 rank at `t` is 200 or better, and 201–500 otherwise (ruling 11).
- Slippage is not part of the indirect-tax base and is not taxed.
- `C_P(t, S) = [Σ_i class1_i(t) + Σ_i slippage_i(t, S)] ÷ ₹1 crore`. Under S0 this is the class 1 cost alone.

**Net returns.**
- `net_P(t, S) = gross_P,D(t) − C_P(t, S)`, in the unit of the saved gross return. The gross return is copied from the registered result file and never recomputed.
- For L this is the hypothetical net return of a long portfolio (ruling 14).
- `hypothetical_net_WML(t, S) = gross_WML,D(t) − C_W(t, S) − C_L(t, S)`.

**Turnover.**
- Traded value: `TV_P(t) = Σ_i |target_i(t) − drift_i(t)|`, buys plus sells, as a fraction of ₹1 crore.
- One-way turnover (frozen §23): `½ × TV_P(t)`.
- In the first month of a sample `TV_P = 1` for every portfolio (ruling 8), so that month adds nothing to `d` below.

**H4 (primary sample only).**
- `e(t) = net_W(t, S0) − net_BM(t, S0)`, T = 114.
- Test: mean of `e` > 0, one-sided, Newey–West standard error with lag 4, standard normal reference distribution (registered decision `p_value_distribution = NORMAL`), α = 0.05.

**Break-even (primary sample only).**
- `x = mean_t e(t)`; `d = mean_t [TV_W(t) − TV_BM(t)]`; `break_even_one_way_cost = x / d`, stated in bps.
- It is the uniform one-way cost per unit of traded value, on top of class 1 costs, at which the mean net excess return of W over the benchmark is zero. It is one number and does not use the two rank bands.

## 5. Primary and confirmation treatment

| Item | Primary (Jul 2012 – Dec 2021, 114 months) | Confirmation (Jan 2022 – Aug 2026, 56 months) |
|---|---|---|
| Start | from cash, full purchase (rulings 8, 10) | from cash, full purchase; does not inherit the primary portfolio (ruling 10) |
| End | no terminal liquidation (ruling 9) | no terminal liquidation (ruling 9) |
| W, benchmark: cost, turnover, net return S0–S4 | yes | yes |
| Hypothetical L and hypothetical net WML, S0–S4 | yes, descriptive | yes, descriptive |
| H3 | **supported** | **not supported** |
| H4 | run, under S0 | **not run** |
| Break-even | reported, or its undefined-case text | **not reported** |

## 6. H3 → H4 conditionality

Frozen §3 and §17: H3 → H4 is a fixed sequence, each at α = 0.05, and H4 is tested only if H3 is rejected.

Registered step D WML, read from the registered result files and not recomputed:

| Sample | n | Mean, % per month | Newey–West t | Two-sided p (registered) | One-sided p | H3 |
|---|---|---|---|---|---|---|
| Primary (`primary_results.json`, SHA-256 `fe7e95ba…f857`) | 114 | 0.925 | 1.998 | 0.0458 | 0.0229 | supported |
| Confirmation (`confirmation_results.json`, SHA-256 `38d1d0a9…4d92`) | 56 | 0.337 | 0.665 | 0.5063 | 0.2532 | not supported |

The one-sided p is half the registered two-sided p, because the mean is positive and the reference distribution is the standard normal. It is not a new calculation on data.

- H4 is tested once, in the primary sample, under S0.
- H4 is not tested in the confirmation sample. No H4 statistic, p-value or decision is produced there.
- A break-even value is not a test and cannot stand in for H4.

## 7. Disclosures that go with these rulings

- **Hypothetical L (ruling 14).** L is costed as if it were bought and held as a long ₹1 crore portfolio. The loser portfolio cannot be sold short and held overnight in the cash market, and no point-in-time list of futures-eligible stocks is archived (frozen §13). The net L return and the net WML are therefore hypothetical. They carry no borrowing cost, no margin and no futures cost. They are not the performance of a strategy that could have been run, are not tested, and do not enter H4.
- **Ruling 10** creates a second full purchase at January 2022 that a continuously invested portfolio would not make. It lowers the confirmation net returns of W, L and the benchmark in that month.
- **Ruling 9** charges nothing for selling the last portfolio of each sample. Every portfolio is treated the same way.
- **Ruling 11.** The 201–500 rate for stocks above rank 500 or unranked is an assumption. Frozen §13 gives no rate for them.
- **Ruling 15 and frozen §13.** Frozen §13 lists the break-even under "Always reported". Under ruling 15 it is not reported for the confirmation sample. This is a narrowing of the frozen reporting line, decided by the reviewer before any cost result existed, and it must be stated wherever the cost table is shown.
- **Ruling 13.** The H3 outcomes were known when this supplement was written. The H3 → H4 sequence itself is frozen and is applied as written.
- The disclosure of Addendum 1 §5 (a flat per-stock sell-side charge weighs more on the benchmark) and the disclosures of Supplement 1 stand, and travel with every step E result.

## 8. What remains open

- **B3 and B4 remain OPEN** and are separate from this supplement.
- Step E is not implemented for rulings 8–16 and has not been run. No runner exists. No real cost, turnover, net return, break-even or H4 result has been calculated.
- Execution of step E needs separate, explicit authorisation.
