# S2-MOM-v1 — results guide: which registered artifact holds which result

**Written:** 2026-10-07. Presentation-layer documentation only. It changes no result, no protocol text and no registered file. Every file named here is unchanged and keeps its registered SHA-256.

**Why it exists.** The result files are immutable: each was written once and hash-registered. Some fields in the earlier files say `PENDING` because the later runs had not happened yet. Those fields were never filled in afterwards, and must not be. This guide says where the later, registered value is.

## 1. Registered artifacts, in execution order

| Run | Date | File | SHA-256 |
|---|---|---|---|
| Blinded precision | 2026-10-05 | `results/s2_mom_v1/blinded_precision.json` | `1e26341044f3e46052fdcda53a56721124412e26d5b93156bf274a9a4de5c693` |
| Primary (A–D, gross) | 2026-10-05 | `results/s2_mom_v1/primary_results.json` | `fe7e95ba97482d6d53faba543d860e4f0d1e50cfa0312d669e910346d41ef857` |
| Sensitivity and reverse ladder | 2026-10-05 | `results/s2_mom_v1/sensitivity_results.json` | `7d6081d8c4a099f7cd1d7d688791c23180d6977536ae4c7860a08b429ff0c19b` |
| Confirmation (A–D, gross) | 2026-10-05 | `results/s2_mom_v1/confirmation_results.json` | `38d1d0a9fbb1d22a19b7912ec4e6285d1dbcb920ffd0e6d99ea19e096c304d92` |
| Step E (costs, H3, H4, break-even) | 2026-10-06 | `results/s2_mom_v1_step_e/step_e_results.json` | `675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0` |
| C2 (seven analyses executed late) | 2026-10-07 | `results/s2_mom_v1_c2/c2_results.json` | `cf977e8a5efce7ba83ce91bf70ae247ed1aea96c7004f8d03162669097689513` |

## 2. Stale fields and what supersedes them

| File | Field | Value in the file | Superseded by |
|---|---|---|---|
| `primary_results.json` | `step_E` | `COST-EVIDENCE-PENDING`, five rates listed as missing | `step_e_results.json` → `samples.primary` |
| `primary_results.json` | `sensitivity` | `SENSITIVITY-PENDING` | `sensitivity_results.json` → `sensitivity` |
| `primary_results.json` | `reverse_ladder` | `SENSITIVITY-PENDING` | `sensitivity_results.json` → `reverse_ladder` |
| `primary_results.json` | `reliability` (`changes_under_sensitivity` pending, `not_reliable: null`, status `PARTIAL`) | pending | `sensitivity_results.json` → `reliability` (`not_reliable: true`), read with section 3 below |
| `confirmation_results.json` | `step_E` | `COST-EVIDENCE-PENDING` | `step_e_results.json` → `samples.confirmation` |
| `confirmation_results.json` | `sensitivity`, `reverse_ladder`, `reliability` | `SENSITIVITY-PENDING` / `PARTIAL` | **Nothing.** The sensitivity treatments and the reverse ladder were run on the primary sample only. No confirmation-sample value exists |
| `sensitivity_results.json` | `H4` under each treatment; `reliability.H4_under_sensitivity` | `COST-EVIDENCE-PENDING` | **Nothing.** H4 was never computed under the sensitivity treatments (deviation DEV-2). See section 3 |
| `primary_results.json`, `confirmation_results.json` | H2d; Holm and Benjamini–Hochberg adjustments; skewness; worst month; halves; pooled | absent | `c2_results.json` (executed late; not blind, not confirmatory) |

The gross figures of steps A–D, the primary estimand, the step differences and the bootstrap in `primary_results.json` and `confirmation_results.json` are current. Nothing supersedes them.

## 3. Reliability label (frozen §25)

- §25 criterion 3 reads: "H1, H3 or H4 changes sign or significance under R-span, R-gap, R-miss or R-delist".
- It was evaluated for **H1 and H3 only**.
- The label **NOT RELIABLE stands for H1**: under R-span the sign of the primary estimand changes (`sensitivity_results.json`, `R_SPAN.H1_sign_changed: true`).
- H3 did not change sign or significance under any of the six treatments.
- **The sensitivity of H4 is UNKNOWN.** The sensitivity treatments were not executed for step E. No statement about the robustness of H4 to these treatments is supported.

## 4. Scope note on the confirmation `decision` field

`confirmation_results.json` carries `H1.decision: "MATERIAL"`. This is the code applying the decision rule of frozen §27 to the confirmation sample. Frozen §27 states that rule for the **primary sample only** ("Decision rules for H1 (primary sample)"). The label is therefore a code-level application outside the rule's stated scope and is **not a registered conclusion**.

The registered status of H1 is:
- primary sample: **INCONCLUSIVE**, and NOT RELIABLE under §25;
- confirmation sample, by the confirmation rule of frozen B3: **NOT CONFIRMED** (opposite sign to the primary).

## 5. Protocol header

The frozen protocol's status line says "Not yet registered in `registry/`". That was true when the file was frozen (commit `7d4cb6d`, 2026-10-05 18:56). The registry record `S2-MOM-v1` was created afterwards and carries the frozen SHA-256 `f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838`. The header is not edited, because any edit would change that hash.

## 6. Cost schedule

Step E used `config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json`, SHA-256 `47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f` (recorded in `step_e_results.json` as `schedule_sha256`). The file `delivery_nse_eq_s2mom.json`, named in the original registry record, is the earlier incomplete template of 2026-10-05. No cost was ever calculated from it.

## 7. Deviations

`docs/research/s2_mom_v1_deviation_log.md`: DEV-1 (procedural sequencing) and DEV-2 (pre-registered analyses not executed, and seven executed late).
