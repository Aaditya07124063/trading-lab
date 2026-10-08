# Manuscript verification report — Phase 10 (2026-10-07)

The forensic audit said that the sensitivity results, the C2 results and the manuscript were not re-verified. This report closes that, using **saved, registered artifacts only**. No experiment was rerun. The manuscript was **not edited**.

Tool: `python3 scripts/verify_manuscript.py` (read-only). Test: `tests/test_manuscript_verification.py`.
Raw output: `docs/audit/remediation/manuscript_verification.txt` and `.json`.
Result: **59 checks pass, 1 flag, 3 information items.**

## 1. Sensitivity and C2 artifacts

| Check | Result |
|---|---|
| `sensitivity_results.json` equals its registered SHA-256 (`7d6081d8…c19b`) | pass |
| `c2_results.json` equals its registered SHA-256 (`cf977e8a…9513`) | pass |
| The C2 file names the registered specification hash, and the specification file still has it | pass |
| The six C2 input hashes in the file = the six in the registry = the files on disk = registered result files | pass |
| The C2 file carries its own statement "not blind and not confirmatory" | pass |
| C2 registry metadata: command, code hash, environment with scipy and platform | pass |
| Holm family m = 4; Benjamini–Hochberg family m = 6; the omission of H5 is stated in the file | pass |
| Sensitivity file: the six frozen treatments and the two reverse-ladder variants, nothing else | pass |
| Sensitivity file: "not reliable" arises through R-span only | pass |
| Sensitivity run registered with the same code hash as the primary run | pass |
| C2 numbers recomputed independently (H2d both samples, status, Holm, BH, five block deltas) | pass — done by the reproduction, largest difference below 1e-13 |
| Sensitivity numbers recomputed independently | **not done.** Each saved p-value was checked against its saved mean and standard error; the treatments themselves were not recomputed. |

## 2. Numerical claims

| Check | Result |
|---|---|
| All 565 numbers of `number_audit.csv` come from files that are registered and unchanged | pass |
| Each audited raw value equals the field of the registered file today | pass (565 of 565) |
| Each number shown is the registered value correctly rounded | pass (565 of 565) |
| Each audited number appears in `manuscript.md` | pass |
| The same numbers appear in `manuscript.html` and `manuscript.docx` | pass |
| The same numbers appear in the text extracted from `manuscript.pdf` | pass (0 of 565 missing; text extraction, layout not compared) |
| Rounded statements ("about 0.58%", "about 1.22%", "0.591%", "157" bps, 114 / 56 months, 10,000 resamples) agree with their artifacts | pass |
| Decimal numbers in the text that are neither audited results nor design constants | none unexplained. Besides the 565 audited results the text holds: section numbers, one arXiv identifier, the t-ratio 3.0 of Harvey, Liu and Zhu (literature), and "brokerage of 0.03%" in the description of the unexecuted analysis R-cost (protocol §16) |

## 3. Result hashes and protocol references

| Check | Result |
|---|---|
| Table A5: all 26 printed hashes equal the files on disk | pass |
| Table A5: every printed hash equals the registry value for that file | pass |
| The six result-file hashes are printed in the manuscript | pass |
| No SHA-256 in the manuscript is unknown to the registry or to Table A5 | pass |
| The gross-run code hash printed = registered primary = confirmation code hash | pass |
| Protocol file, "revision 4", freeze commit `7d4cb6d9…` as registered | pass |
| Addendum 1, Supplements 1–4 and the C2 specification are referenced | pass |
| **Table A5 lists the hash of every registered addendum and supplement** | **FLAG** |

**The flag (classified 2026-10-08 as a documentation-only accepted issue, N-02).** The manuscript says the cost rules are in "Addendum 1 and Supplements 1–4". Table A5 prints the hashes of the protocol, Addendum 1, Supplement 1 and Supplement 4. It does not print the hashes of **Supplement 2** (rulings 8–16, the step E method) and **Supplement 3** (rulings 19–20). Both are registered (`6c373c5f…e888`, `682191de…80ce`) and both files match. Nothing is wrong with the results; the disclosure table is incomplete. Suggested action for the author: add the two rows in the next manuscript revision. Not done here: it is not required by any specification (the builder's hash list is a curated selection, and no protocol, supplement, results guide or C2 specification defines Table A5), the two hashes are registered and verified elsewhere, and the fix would regenerate all manuscript files, which are frozen in the pre-release phase.

Information: three files in Table A5 (`run_s2_mom_c2.py`, `run_s2_mom_step_e.py`, `src/stage3/step_e.py`) have per-file hashes that the registry does not hold individually (it holds the combined code hashes). They were verified against disk.

## 4. Wording

| Topic | What the registered artifacts say | What the manuscript says | Result |
|---|---|---|---|
| H1, primary | mean −0.0587, two-sided p 0.7806, label INCONCLUSIVE; not reliable through R-span | "INCONCLUSIVE; NOT RELIABLE (§25, R-span)"; "Two-sided, α = 0.05" | pass |
| H1, confirmation | mean +0.6750 (opposite sign), p 0.0138 | "NOT CONFIRMED (opposite sign to primary)"; "The primary estimand is not confirmed" | pass |
| H1 overclaim | — | no sentence says H1 is supported, confirmed or significant | pass |
| H1 code label | `confirmation_results.json` holds the code-level label `MATERIAL` (the §27 table applied to the confirmation sample) | the label is not presented as a protocol decision | pass |
| H2d | pre-registered, executed late, one-sided, Holm-rejected, status CONFIRMED by the frozen B3 rule | reported with "not blind and not confirmatory", "executed only after the main results were known", "supplementary and non-confirmatory"; "H2d was a secondary test" | pass |
| Confirmation sample | chronological; H3 not supported there; H4 not run there | "chronological confirmation sample"; "does not provide significant evidence for the same effect"; "H4 are not reported for the confirmation sample" | pass |
| Cost timing | Addendum 1 and supplements were registered after the gross runs | "The cost rules were specified after the gross results of steps A–D were known and before any cost, turnover or net return was computed" | pass |
| L and net WML | hypothetical (ruling 14) | "every net figure for L and for WML is hypothetical" | pass |
| DEV-1, DEV-2 | deviation log | both named; "scope deviation" | pass |
| DEV-2 unexecuted analyses | 19 items in the deviation log | all 19 named in the manuscript | pass |
| DEV-2 late analyses | 7 | all 7 disclosed as late | pass |
| Unexecuted analyses | no result exists | "No result was computed or seen for any analysis marked 'Not executed'" | pass |

## 5. Limits of this verification

1. It checks that statements are **supported by registered artifacts**. It does not judge whether the science is right, whether the literature is cited correctly, or whether the references exist (the manuscript's own `references_verification_checklist.md` covers that and was not re-audited).
2. Wording checks look for required sentences and for forbidden patterns. A subtly misleading sentence that uses neither would pass. A human reading is still needed.
3. The manuscript builder was not rerun (it writes files). Its own log (699 checks) was read, not reproduced.
4. Figures were not compared with the data.

## 6. Status

| Item | Status |
|---|---|
| Sensitivity hashes, C2 hashes, C2 metadata | verified |
| Manuscript numerical claims, result hashes, protocol references | verified |
| DEV-2 disclosure, H1 wording, H2d wording, confirmation wording, cost-timing disclosure | verified |
| Table A5 omits Supplements 2 and 3 | **FIXED 2026-10-08 (N-02)**: both rows added, manuscript rebuilt (presentation only); now 60 PASS, 0 FLAG |
| Sensitivity treatments not independently recomputed | **ACCEPTED RISK** (hash and code-hash evidence only) |
