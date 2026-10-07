# S2-MOM-v1 — deviation log

Deviations from the frozen protocol (`docs/research/phase3a_momentum_protocol.md`, SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`). The protocol text is not changed. Registered results are not changed.

## DEV-1 — procedural sequencing: open items not closed before returns were computed (recorded 2026-10-05)

**What the frozen text says.** The heading of §32 reads: "Open items at the freeze (to be closed in Phase 3B before any return is computed)".

**What happened.** Three items under that heading were still open when the A–D returns were computed (primary run 21:10, sensitivity 21:17, confirmation 21:28, all on 2026-10-05):
- **B2** — no archived source for the delivery cost inputs;
- **B3** — full texts not obtained for several cited papers;
- **B4** — a reference Sharpe ratio and standard references cited from memory.

**Why the runs went ahead.** The gross primary run was authorised on the reading that cost evidence does not affect the primary estimand; §32 itself says B2 affects "Step E; H4; anchor 1 of §27. Not the primary estimand (A → D is gross)". The literal instruction in the heading was not flagged at that time. It should have been.

**Effect on the calculation.** None of B2, B3 or B4 enters the A–D calculation:
- B2 concerns costs; steps A–D are gross and no cost was computed;
- B3 concerns the literature table and the wording of the contribution;
- B4 concerns a power statement for a secondary test and the reference list.

**Classification.** Procedural sequencing deviation.

**Consequence.** The registered primary, sensitivity and confirmation results are preserved unchanged. The deviation is disclosed with them. It is not a reason to alter any result.

**Still open.** B2, B3 and B4 remain open. Step E and H4 have not been run.

---

## Status update to DEV-1 (appended 2026-10-07; the text above is preserved as written on 2026-10-05)

The line "Still open. B2, B3 and B4 remain open. Step E and H4 have not been run." described 2026-10-05. Since then:
- **B2 was closed** on 2026-10-06 (`docs/evidence/s2mom_cost_evidence_closure_report_20261006_pass2.md`; dated schedule `config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json`, SHA-256 `47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f`).
- **Step E was executed once** on 2026-10-06, and **H4 was run** for the primary sample (`results/s2_mom_v1_step_e/step_e_results.json`, SHA-256 `675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0`). H4 and the break-even were not run for the confirmation sample, because H3 is not supported there (Supplement 2, rulings 13 and 15).
- **B3 and B4 remain open.**

DEV-1 itself stands as recorded.

## DEV-2 — pre-registered analyses not executed, and seven executed late (recorded 2026-10-07)

**What the frozen text says.** §16 lists fixed robustness analyses and §19 states that all are reported. §3, §13, §14, §17 and §28 list further tests, statistics, tables and figures.

**Not executed.** No result for any of these was computed or seen:
- H5 (liquidity bands, rank 1–200 against 201–500) and its robustness (rank 1–100 against 101–200);
- R-JK (the 16 formation and holding cells), with the Romano–Wolf and White reality-check adjusted p-values;
- R-skip; R-bp; R-wt; R-entry; R-cost; R-mono; R-ext;
- holding periods longer than one month;
- the deflated Sharpe ratio;
- H4 under the sensitivity treatments;
- the stationary bootstrap for any test other than H1;
- capacity (§13);
- the middle portfolio;
- the monotonicity figure;
- turnover at steps A–C.

**Executed late.** H2d, the Holm and Benjamini–Hochberg adjustments, the two halves of the primary sample, the pooled sample (gross A–D and δ only), skewness and worst month were computed on 2026-10-07 from the saved registered files, under `docs/research/s2_mom_v1_c2_analysis_spec.md` (SHA-256 `78864a4f6fddad86a7b3273e8d8c1e7ab818ed318deb0fdb75cc99e2c5a0c0aa`), output `results/s2_mom_v1_c2/c2_results.json` (SHA-256 `cf977e8a5efce7ba83ce91bf70ae247ed1aea96c7004f8d03162669097689513`). **They were pre-registered, but executed after the main results were known. They are not blind and not confirmatory.** No backtest was rerun.

**Why.** Following review of the frozen protocol and registered results on 2026-10-07, the study was limited to the primary specification and the seven C2 analyses described above. This was decided after the results were known. It is not a reason arising from the data.

**Effect.**
- No registered result changes.
- The unexecuted analyses support nothing. No claim may rest on them.
- The study makes no claim about liquidity conditioning, other formation or holding periods, breakpoints, weighting, entry timing, alternative costs or capacity.
- The sensitivity of H3 and H4 to these design choices is unknown.
- Frozen §25 criterion 3 was evaluated for H1 and H3 only. The label "not reliable" stands for H1 through R-span. The sensitivity of H4 is unknown.
- The Benjamini–Hochberg family omits H5.
- The specifications run were: one primary, six sensitivity treatments and two reverse-ladder variants.

**Classification.** Scope deviation: incomplete execution of the pre-registered robustness set.
