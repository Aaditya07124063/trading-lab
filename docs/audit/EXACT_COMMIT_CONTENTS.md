# Exact commit contents (2026-10-08, generated from the Git index — nothing committed)

Source: `git diff --cached` of `~/Projects/trading-lab` on `main` at HEAD `7d4cb6d977ee1fbe40351fc6b6049c49af7638b2`. SHA-256 = hash of the staged blob. "Snapshot" = `docs/audit/remediation/pre_remediation_snapshot.json`. This file is listed but its own lines and hash are not counted (self-reference).

## Summary

| | Files | Lines added | Lines deleted | Binary files |
|---|---|---|---|---|
| Everything staged now | 258 | 484,446 (+ this file) | 70 | 46 |
| **Commit 1** — experiment + remediation (`F01_CLOSURE_PLAN.md` step 1) | **256** | 484,294 (+ this file) | 70 | 46 |
| Moved to **commit 2** with the UI work (`server.py`, `web/`, `README.md` + these two) | 2 | 152 | 0 | 0 |

No file is deleted or renamed. All 70 deleted lines are in `src/registry/experiments.py` (69) and `EXPERIMENT_REGISTRY.md` (1).

| Commit | Class | Files |
|---|---|---|
| 1 | EXPERIMENT: unchanged since snapshot | 160 |
| 1 | REMEDIATION: modified existing file | 8 |
| 1 | REMEDIATION: new file | 60 |
| 1 | REMEDIATION: preserved forensic copy | 18 |
| 1 | REMEDIATION: regenerated (remediation-owned file) | 8 |
| 1 | RESEARCHER: earlier change, unchanged since snapshot | 2 |
| 2 | EXPERIMENT: unchanged since snapshot | 2 |

Class meanings: **EXPERIMENT** — never committed before, byte-identical to the pre-remediation snapshot (research evidence; must not change). **RESEARCHER** — the researcher's earlier uncommitted change, byte-identical to the snapshot. **REMEDIATION** — written or changed by the remediation; none of these files is frozen research evidence. The two commit-2 files are EXPERIMENT-class only in the sense that they existed unchanged before remediation; they belong to the UI work.

Not in either commit: the collector's files (`data/india/*`, `data/raw/collection_log.jsonl`, `data/raw/manifest.jsonl`) and the external data (`data/raw/nse_archive/`, `data/stage2/datasets/`, the Stage 3 panel), which are git-ignored and listed in `release/s2_mom_v1/ARCHIVE_MANIFEST.json`.

## Files

| # | Commit | Status | + | − | Class | Path | SHA-256 |
|---|---|---|---|---|---|---|---|
| 1 | 1 | M | 8 | 0 | REMEDIATION | `.gitignore` | `0a650495c0334cb3206fd26732446680d71569efd1d54388b268ece1daaaa372` |
| 2 | 1 | M | 2 | 0 | REMEDIATION | `CHANGELOG.md` | `d223a12f0058af3905ef2d1d1bb11a70baa9685093a08d3cba0b83084999c38d` |
| 3 | 1 | M | 75 | 1 | REMEDIATION | `EXPERIMENT_REGISTRY.md` | `67b9ab6ed584913a92c015fe2f5f30ee760a29a85c91c2c9b0fadcc73a42be52` |
| 4 | 1 | M | 57 | 0 | REMEDIATION | `REPRODUCIBILITY.md` | `e9e1b01c761007a9c17fc804def5e1d6d2b16da2efe7ff754dbfb28be8ed7002` |
| 5 | 1 | M | 210 | 0 | RESEARCHER | `RESEARCH_LOG.md` | `f7676ead2801abfb8ce9df46313861331d685cf5029f954cb9d043c3112634bc` |
| 6 | 1 | A | 70 | 0 | EXPERIMENT | `config/cost_schedules/delivery_nse_eq_s2mom.json` | `c0270a3678714836eb635adfccfa03433197bfa189fad6a22a2e1b5ecc386f4e` |
| 7 | 1 | A | 1091 | 0 | EXPERIMENT | `config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json` | `47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f` |
| 8 | 1 | A | 58 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/checks/pre_run_checks_oos.json` | `2cd0e9ba0045c157c83b282cbd01c16da681ff9ffd206034b2a030014b443157` |
| 9 | 1 | A | 58 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/checks/pre_run_checks_primary.json` | `781b62778f48e9374cf7d482eac8ac0e7f463cfc2f0811fc1ecd9e35a68f2c50` |
| 10 | 1 | A | 167 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/checks/stage2_rebuild_20261005.log` | `22c06516f5c120ffe1875464395a31171c76908be5bf86699a0fde97b1cd3c33` |
| 11 | 1 | A | 96 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/manifest.json` | `6f08fd0fb389d36027e02bb06b9e8ff06ee1d7cb45c30c15c6c41dd79c711fe5` |
| 12 | 1 | A | 57 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/oos/calendar.csv` | `55d159200cfec3c71eee9d3f6808a990adbdd3520fef1c9d661ba5d25f2ad74d` |
| 13 | 1 | A | 33601 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/oos/universes.csv` | `632827b41cb9a6c431c8528da01c9f73247c4c1c45b9cd2213f617f57c299712` |
| 14 | 1 | A | 115 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/primary/calendar.csv` | `91cccb5468e7b070779e9ab28c66a98b5eac60ce1b7b146187f0967900f39789` |
| 15 | 1 | A | 68401 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/primary/universes.csv` | `d42d9aea09a38b90a517feb0270791ece48744c27fb84a09d226621c296650aa` |
| 16 | 1 | A | 1193 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/research/gap_rows.csv` | `748343967a76ff69df2ff21a6f9928ca9a94a83232ff458df6d52390873247ae` |
| 17 | 1 | A | 736 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/research/identity.csv` | `c7356c4efab339338fc3aa3563299221d007cb3c740ba98fa901806736f56f5a` |
| 18 | 1 | A | 3769 | 0 | EXPERIMENT | `data/stage3/s2_mom_v1/research/sessions.csv` | `a0181d024c85073060ce382213bc26ad7cb44de621390b65eb72e1cd949938fe` |
| 19 | 1 | A | 492 | 0 | EXPERIMENT | `docs/audit/BUG_FINDINGS.md` | `bfef77d8bac9a7d2059914230ba1c86ca5fd2a12d4155b2eeb9927e33415238b` |
| 20 | 1 | A | 109 | 0 | REMEDIATION | `docs/audit/DATA_FLOW.md` | `c9bec777304808b68a78b38f619b47389ceba8b62e905f8b4a0db0d9f1ce17bb` |
| 21 | 1 | A | 42 | 0 | EXPERIMENT | `docs/audit/DEPENDENCY_AUDIT.md` | `11e322a0a98f251c1a8a73dedc1f2f3cfbc0b0e04199c1d4de0a3386e4aeca5d` |
| 22 | 1 | A | 81 | 0 | REMEDIATION | `docs/audit/DEPENDENCY_FINAL_REPORT.md` | `b19ba9380751436422ccacc98a31690dfc725efd13bb406cd65ba731f7133bb7` |
| 23 | 1 | A | 40 | 0 | EXPERIMENT | `docs/audit/DOCUMENTATION_CODE_AUDIT.md` | `fb2f301daa76e963bec0eaa9e96d78802ea6f499a6ca21497f36bc1bb74ce1f9` |
| 24 | 1 | A | — | — | REMEDIATION | `docs/audit/EXACT_COMMIT_CONTENTS.md` | (this file) |
| 25 | 1 | A | 111 | 0 | REMEDIATION | `docs/audit/F01_CLOSURE_PLAN.md` | `847463b6beb1abf40df3f0453f1ce8138206e6cd10eb1db3267c07585cb2c2b4` |
| 26 | 1 | A | 179 | 0 | REMEDIATION | `docs/audit/FAILURE_INJECTION_REPORT.md` | `d81c038a295fc770015f8926a8efb15a126268eb67471fdbbc1a3d7123f99f21` |
| 27 | 1 | A | 151 | 0 | REMEDIATION | `docs/audit/FINAL_RELEASE_GATE.md` | `c85eb3487d0bb1b48f6986784d7ee3e0d79418cf55d8ea6830595029c18f9cee` |
| 28 | 1 | A | 57 | 0 | EXPERIMENT | `docs/audit/LOOPHOLE_AUDIT.md` | `b55b5d817d768329f801ae0aa9ed6b3c2ff342909f68383dbef2f1e76aa41abc` |
| 29 | 1 | A | 88 | 0 | REMEDIATION | `docs/audit/MANUSCRIPT_VERIFICATION_REPORT.md` | `2e3f1d4b9a745643db6daadd3abe01d71c963e33096c315e767db62e6fe938cf` |
| 30 | 1 | A | 372 | 0 | REMEDIATION | `docs/audit/MUTATION_FINAL_REPORT.md` | `060726e0a057c9043c06d437580dea53b4c76f04742ef9b1007d95ef69e21c33` |
| 31 | 1 | A | 145 | 0 | EXPERIMENT | `docs/audit/MUTATION_TEST_REPORT.md` | `3bfb668b42ae937aa300fdd65c8d781d0e8d12bac14a1956263ca45e9aca3fd4` |
| 32 | 1 | A | 123 | 0 | REMEDIATION | `docs/audit/PRE_RELEASE_CHECKLIST.md` | `4fcf1cf7a33ecd3491ae970717783686cae1518149a3bf62a671dd18634a19fa` |
| 33 | 1 | A | 77 | 0 | REMEDIATION | `docs/audit/PROVENANCE_VERIFICATION_REPORT.md` | `882c5379e3f04ccaa5f4a49abd6d46479a0040962304b7f3af524b964f2544d2` |
| 34 | 1 | A | 86 | 0 | REMEDIATION | `docs/audit/REGISTRY_SECURITY_REPORT.md` | `421b96a5270d810da21b21913f3d2dcb18c4693f5f96ee9e987fa09bfee546e3` |
| 35 | 1 | A | 77 | 0 | EXPERIMENT | `docs/audit/REMEDIATION_PLAN.md` | `4a54cb935180cd77263996326b5a595dbb5f18a9766d6046fd8123ced8c79ba3` |
| 36 | 1 | A | 160 | 0 | REMEDIATION | `docs/audit/REMEDIATION_REPORT.md` | `4f46809f749811aad780337331980b112f1233bd54125dee424e2e037460d90f` |
| 37 | 1 | A | 59 | 0 | EXPERIMENT | `docs/audit/REPRODUCIBILITY_AUDIT.md` | `0a392b39c93fa8524d9ed27b24121adc8a5c2a0d3bb9bae3f6612f86c2b43a24` |
| 38 | 1 | A | 111 | 0 | REMEDIATION | `docs/audit/REPRODUCTION_REPORT.md` | `3f5a26c21d00b1b166d55c04ee4e6b340ad2c3dd117abddbb7f51098090d6e89` |
| 39 | 1 | A | 53 | 0 | EXPERIMENT | `docs/audit/REQUIREMENTS_TRACEABILITY.md` | `8e81cf9142dbdd94871a3f8839d560eaa08d5c859b702ec70896cf8f56f1e051` |
| 40 | 1 | A | 93 | 0 | EXPERIMENT | `docs/audit/RESEARCH_INTEGRITY_AUDIT.md` | `9f360f5d0b2685cef69e2a5d53d86cc0fd1818d9f4c460d3450ed5f9b6ad028a` |
| 41 | 1 | A | 265 | 0 | REMEDIATION | `docs/audit/SYSTEM_ARCHITECTURE.md` | `78314dc61d3b494a7139e3d6ea8a1338d1bc9215c4665308e7120ef68ab16ad6` |
| 42 | 1 | A | 109 | 0 | EXPERIMENT | `docs/audit/TEST_COVERAGE_AUDIT.md` | `6187c86fa97a7f36b217c6bb13e3a85bf19f3ead52484a877413712b6c213414` |
| 43 | 1 | A | 48 | 0 | EXPERIMENT | `docs/audit/TEST_GAP_MATRIX.md` | `df199a7c20a10fb7430734743e93004b3d79c8cbd27f6d38717d7ade3e2468fd` |
| 44 | 1 | A | 53 | 0 | REMEDIATION | `docs/audit/THREAT_MODEL.md` | `da9d8b78d108d98f7734639a81de4dab3a1afed58d7d86d768c1ce113eb1ef59` |
| 45 | 1 | A | 814 | 0 | REMEDIATION | `docs/audit/findings.json` | `f36ddaa623780ee29233efb5f9ee5c8ea94456ad2bd30b6e16c8362254fc09c1` |
| 46 | 1 | A | 492 | 0 | REMEDIATION | `docs/audit/forensic_20261007/BUG_FINDINGS.md` | `bfef77d8bac9a7d2059914230ba1c86ca5fd2a12d4155b2eeb9927e33415238b` |
| 47 | 1 | A | 131 | 0 | REMEDIATION | `docs/audit/forensic_20261007/DATA_FLOW.md` | `9f6413551265806c2b5716627d8f4cf48e3f9859b2eacde2d6b87de7470e74b6` |
| 48 | 1 | A | 42 | 0 | REMEDIATION | `docs/audit/forensic_20261007/DEPENDENCY_AUDIT.md` | `11e322a0a98f251c1a8a73dedc1f2f3cfbc0b0e04199c1d4de0a3386e4aeca5d` |
| 49 | 1 | A | 40 | 0 | REMEDIATION | `docs/audit/forensic_20261007/DOCUMENTATION_CODE_AUDIT.md` | `fb2f301daa76e963bec0eaa9e96d78802ea6f499a6ca21497f36bc1bb74ce1f9` |
| 50 | 1 | A | 73 | 0 | REMEDIATION | `docs/audit/forensic_20261007/FINAL_RELEASE_GATE.md` | `606ae9e232bc83fe8bb072847587ad44ffe2d328577bf527ad3df634ced1df19` |
| 51 | 1 | A | 57 | 0 | REMEDIATION | `docs/audit/forensic_20261007/LOOPHOLE_AUDIT.md` | `b55b5d817d768329f801ae0aa9ed6b3c2ff342909f68383dbef2f1e76aa41abc` |
| 52 | 1 | A | 145 | 0 | REMEDIATION | `docs/audit/forensic_20261007/MUTATION_TEST_REPORT.md` | `3bfb668b42ae937aa300fdd65c8d781d0e8d12bac14a1956263ca45e9aca3fd4` |
| 53 | 1 | A | 77 | 0 | REMEDIATION | `docs/audit/forensic_20261007/REMEDIATION_PLAN.md` | `4a54cb935180cd77263996326b5a595dbb5f18a9766d6046fd8123ced8c79ba3` |
| 54 | 1 | A | 59 | 0 | REMEDIATION | `docs/audit/forensic_20261007/REPRODUCIBILITY_AUDIT.md` | `0a392b39c93fa8524d9ed27b24121adc8a5c2a0d3bb9bae3f6612f86c2b43a24` |
| 55 | 1 | A | 53 | 0 | REMEDIATION | `docs/audit/forensic_20261007/REQUIREMENTS_TRACEABILITY.md` | `8e81cf9142dbdd94871a3f8839d560eaa08d5c859b702ec70896cf8f56f1e051` |
| 56 | 1 | A | 93 | 0 | REMEDIATION | `docs/audit/forensic_20261007/RESEARCH_INTEGRITY_AUDIT.md` | `9f360f5d0b2685cef69e2a5d53d86cc0fd1818d9f4c460d3450ed5f9b6ad028a` |
| 57 | 1 | A | 127 | 0 | REMEDIATION | `docs/audit/forensic_20261007/SYSTEM_ARCHITECTURE.md` | `1563174e0cbe934e9ac94eeeafc2c323c8071ec61cd5c4810efe676c63fc2c9a` |
| 58 | 1 | A | 109 | 0 | REMEDIATION | `docs/audit/forensic_20261007/TEST_COVERAGE_AUDIT.md` | `6187c86fa97a7f36b217c6bb13e3a85bf19f3ead52484a877413712b6c213414` |
| 59 | 1 | A | 48 | 0 | REMEDIATION | `docs/audit/forensic_20261007/TEST_GAP_MATRIX.md` | `df199a7c20a10fb7430734743e93004b3d79c8cbd27f6d38717d7ade3e2468fd` |
| 60 | 1 | A | 74 | 0 | REMEDIATION | `docs/audit/forensic_20261007/THREAT_MODEL.md` | `276cff68c8f2071947d9ec005cd3a50227cd18d1106e605435f9a1aeced0efac` |
| 61 | 1 | A | 551 | 0 | REMEDIATION | `docs/audit/forensic_20261007/findings.json` | `b29f5df0a6de3f2c2f34e7a2112aeea364ca96d607bd889b3320f8a0364d3674` |
| 62 | 1 | A | 44 | 0 | REMEDIATION | `docs/audit/forensic_20261007/requirements_traceability.csv` | `209c30c1b302a5c4d8ca17fa2549f777bfc07b0748cb23f10caf4ecdbe1cfe83` |
| 63 | 1 | A | 22 | 0 | REMEDIATION | `docs/audit/forensic_20261007/test_matrix.csv` | `e58dafae64f37594c83c8dcfc2165dced05b007d64fcea042393548a0b28407c` |
| 64 | 1 | A | 553 | 0 | REMEDIATION | `docs/audit/remediation/build_tables.py` | `b34c36b27a13494b8f3b0275f46f43109301a8d04ca010bbaebd7b9a479d8c46` |
| 65 | 1 | A | 980 | 0 | REMEDIATION | `docs/audit/remediation/coverage_summary.json` | `205c60b60695a12d3e374654d85ee334af1f6da9a39e10d5f87c70a1f95bfea0` |
| 66 | 1 | A | 714 | 0 | REMEDIATION | `docs/audit/remediation/failure_injection_results.json` | `031f9df52b9c4c3c0b6a7bdfd551484b802d2a9e7a6d823dd67681ccb61bf109` |
| 67 | 1 | A | 18 | 0 | REMEDIATION | `docs/audit/remediation/forensic_20261007.SHA256SUMS` | `3af71e7e51157386c445817edcf842e282eb73b3cf68c90269d7d00b1ecbc0bc` |
| 68 | 1 | A | 380 | 0 | REMEDIATION | `docs/audit/remediation/manuscript_verification.json` | `7385ad097651c697facc92c254778ce10fa8dbc9a78556c584c49ea17c2fac45` |
| 69 | 1 | A | 65 | 0 | REMEDIATION | `docs/audit/remediation/manuscript_verification.txt` | `35be6ffefed34e673483a2f2f2be713c8975a0a69dd6bbf991fe6007a96224f4` |
| 70 | 1 | A | 8 | 0 | REMEDIATION | `docs/audit/remediation/mutation_aborted_runs/batch_0.run0_disk_full.jsonl` | `c6da59bdbb60df712d60df736f15e04b6f5cdcb69479597e3f7b6d8715233e0e` |
| 71 | 1 | A | 7 | 0 | REMEDIATION | `docs/audit/remediation/mutation_aborted_runs/batch_0.run1_stopped_method_change.jsonl` | `d20a2ae797e6711f79ec52d742692fc779b1f2efff16f2926fdff80d6b3ce38a` |
| 72 | 1 | A | 8 | 0 | REMEDIATION | `docs/audit/remediation/mutation_aborted_runs/batch_1.run0_disk_full.jsonl` | `fd9e24bdcb34e7b49821af930bcb8880bb8b7b1e06131389d6f05eeee3c23d3a` |
| 73 | 1 | A | 7 | 0 | REMEDIATION | `docs/audit/remediation/mutation_aborted_runs/batch_1.run1_stopped_method_change.jsonl` | `8c42b9f31c6089fbc5af78fc34d21cba7e1480f613a7dcd175184f0e26c4e2e6` |
| 74 | 1 | A | 13 | 0 | REMEDIATION | `docs/audit/remediation/mutation_aborted_runs/batch_2.run0_disk_full.jsonl` | `f745b0d9a93adb57d99e4630a4d2ce598f288449d388272164e5639ec8e67871` |
| 75 | 1 | A | 7 | 0 | REMEDIATION | `docs/audit/remediation/mutation_aborted_runs/batch_2.run1_stopped_method_change.jsonl` | `9ce4b47d332e2733cea961c434047cc4595ae3c8ec16b17cb4921b3b4400321a` |
| 76 | 1 | A | 8 | 0 | REMEDIATION | `docs/audit/remediation/mutation_aborted_runs/batch_3.run0_disk_full.jsonl` | `b5c6eabb0f9117c08ccfbdd287e253d7d8cf2529c3d60c98e3be120732354fcc` |
| 77 | 1 | A | 66 | 0 | REMEDIATION | `docs/audit/remediation/mutation_final/batch_0.jsonl` | `0de82c4772825ae42f0a982acd86b75c1a37bc839a9484e495ff048cb1b36e86` |
| 78 | 1 | A | 66 | 0 | REMEDIATION | `docs/audit/remediation/mutation_final/batch_1.jsonl` | `ec99425517b10515c56c51625819faba74fe67833a74ac0578a71367d7459c50` |
| 79 | 1 | A | 66 | 0 | REMEDIATION | `docs/audit/remediation/mutation_final/batch_2.jsonl` | `0b156b962071ac32ad050ecabf6ba0606a94d34e96d0a639727d4ae8467f586b` |
| 80 | 1 | A | 22 | 0 | REMEDIATION | `docs/audit/remediation/mutation_final/code_state.json` | `01c6407b47629a3268b494ca891f7e93fb9e537bee49eb9c70fca17ec5ab2fc7` |
| 81 | 1 | A | 1388 | 0 | REMEDIATION | `docs/audit/remediation/mutation_final/mutation_results.json` | `1348a403430020349400f36487a0c111edf5671b91f252c145207100b9bee2c2` |
| 82 | 1 | A | 1066 | 0 | REMEDIATION | `docs/audit/remediation/mutation_forensic_20261007.json` | `12bf85b56c29220da327b7c885dc423c4c15279c46dfbddc26198ffca5d53eaf` |
| 83 | 1 | A | 65 | 0 | REMEDIATION | `docs/audit/remediation/mutation_run2_superseded/batch_0.jsonl` | `9ffd1fc29a0e851ca756ec9fa71710c87d1da2d5cb90c2bcba8bd175f0630a80` |
| 84 | 1 | A | 65 | 0 | REMEDIATION | `docs/audit/remediation/mutation_run2_superseded/batch_1.jsonl` | `e1c27c46f666776708968aa4ba70cdcb0a0babf3dc14f0ef87bc070f39f026cf` |
| 85 | 1 | A | 64 | 0 | REMEDIATION | `docs/audit/remediation/mutation_run2_superseded/batch_2.jsonl` | `ee42f8b63b46b5a1efd230d1ab83257a236532e8bb8dc34b421c6e3ef3be94b6` |
| 86 | 1 | A | 22 | 0 | REMEDIATION | `docs/audit/remediation/mutation_run2_superseded/code_state.json` | `d45b67e5d10e10707125eb0ec269980aaa71515b6b652efe01225f23b3df00bc` |
| 87 | 1 | A | 1360 | 0 | REMEDIATION | `docs/audit/remediation/mutation_run2_superseded/mutation_results.json` | `7e0d4855d38a9079afba4835736ab40d57b6b481ef861fb3e5982712bbde59d1` |
| 88 | 1 | A | 28543 | 0 | REMEDIATION | `docs/audit/remediation/pre_remediation_snapshot.json` | `0294702f45204c9cde11bf7ab21268dbefbbc2751adc8206b15e259912aa9190` |
| 89 | 1 | A | 25 | 0 | REMEDIATION | `docs/audit/remediation/provenance_attacks_pytest.txt` | `9ff142ed76b63f1b9e141c2fbdc67809b2a09c02c8520bdcb4828b4b1c9e2e2e` |
| 90 | 1 | A | 236 | 0 | REMEDIATION | `docs/audit/remediation/registry_attacks_pytest.txt` | `5c6be4b9df981051b39d1d89fe2178edc44dcbce75e461fa68f9739c316ef896` |
| 91 | 1 | A | 934 | 0 | REMEDIATION | `docs/audit/remediation/reproduction_report.json` | `f55ab96c6532e2c0621f0b327b32b2c6461ab8e2c702ae3d393c4adba7fae843` |
| 92 | 1 | A | 691 | 0 | REMEDIATION | `docs/audit/remediation/reproduction_report_clean_conda_env.json` | `bd38aa5ddc0967ef60364cc393c4a487e6ae64bea83aadeffdddd83ef0afecdc` |
| 93 | 1 | A | 49 | 0 | REMEDIATION | `docs/audit/requirements_traceability.csv` | `d603db545f159b94f366f44b88a608dee6e0121b8e76a90bb7031106fef7317e` |
| 94 | 1 | A | 29 | 0 | REMEDIATION | `docs/audit/test_matrix.csv` | `d9dc309d80520677406880fd0196bb20f6ec3edf8688f3faecaf0949625389b6` |
| 95 | 1 | A | 157 | 0 | EXPERIMENT | `docs/evidence/s2mom_cost_evidence_audit_20261005.md` | `25785f97d086d1623787aea2d1e54f2f00069151b409c33de5adecc6b8bc51fd` |
| 96 | 1 | A | 217 | 0 | EXPERIMENT | `docs/evidence/s2mom_cost_evidence_audit_stage2_20261005.md` | `18b7377ea079ef6b589a6492112cd8e579903c1ca3033fefb12176522f3c7837` |
| 97 | 1 | A | 94 | 0 | EXPERIMENT | `docs/evidence/s2mom_cost_evidence_closure_report_20261006.md` | `783547b450c3cf8327f68acc81e2621c74fa6a72e203a8bfbabd1af983fb084d` |
| 98 | 1 | A | 149 | 0 | EXPERIMENT | `docs/evidence/s2mom_cost_evidence_closure_report_20261006_pass2.md` | `e1913a0622dea2163e264056899f3f577e9213a295846b633416510b89faecd8` |
| 99 | 1 | A | 185 | 0 | EXPERIMENT | `docs/evidence/s2mom_cost_schedule_audit_20261006.md` | `13fef303e8e3b0d1c7d4e841c21d2ed7985ff709548ae137d8aeb1d7248d2c0a` |
| 100 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/CBIC_GST_notfn11_2017_central_tax_rate.pdf` | `a8051c8882b8a7e3e2d8b2ad10e3c18b9c85c755fbbfe324dce43b4c6b44d934` |
| 101 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/CBIC_GST_notfn8_2017_integrated_tax_rate.pdf` | `1f2d7ff6b92290164420906f86325052b4a710fd7b545f2f9896ded7e7713f5d` |
| 102 | 1 | A | 2319 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/CSE_notice_SEBI_turnover_fees_2019.htm` | `99ebdca9a5ce4ceeccfece0e68bf80b341862a2dbacec5b509a5fcdc5838cccc` |
| 103 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/GOI_FinanceBill2012_memorandum_direct_taxes.pdf` | `1899459535ce9a2c44b92651dd6cfc3ebf209a1c32c8354ac9e1f540c22fd862` |
| 104 | 1 | A | 66 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/MANIFEST.csv` | `f813054b0f2a935bf15fb48915f1d6abf0fcd9bb9793794d81dc80b973632dc2` |
| 105 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_FA46225.pdf` | `2918e89609d1aceb3f632fc1832cfdba9699128c95091ef239df45ba079a9eb6` |
| 106 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_FA46730.pdf` | `a9ff85ab4deec82e02bb1e3fc213a2bbc02a72e9edb7b36cdf1568aeb792febf` |
| 107 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_FA56129.pdf` | `ec260386adbcf3a0c3326d7d8b3b45b15ba693c55081fdc78fb05b83a5ee93e0` |
| 108 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_FA61137.pdf` | `e01c5b6c76d29d559bc7f559758c99cb289ec44a88e3f89d5e46b8c2c360e0ac` |
| 109 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_FA64232.pdf` | `85b816208f33bdd1c6c0d827b1ba996aba1fe08fe883a6d31c6a2c0ad55304a4` |
| 110 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_FAAC13028_20090907.pdf` | `5c018e6a880fccbb9d9c818a7829357a3e2e4d7a4ddbb8928de96cec92b001e4` |
| 111 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_FATAX63809.pdf` | `e72218a4aaffccfc5ea485c714bf83d019c2bb0a5ebb4724029552b0cd7fc31f` |
| 112 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_FATAX73524.pdf` | `f4cbd1f917f88dcb9d59b95e0e9ef8bbb98017edbbdd16669a3d40776416a9f6` |
| 113 | 1 | A | 5170 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_static_sebi_fees_stt_page.html` | `a9c261eed75c44f8f0bccc129bcc5f2da091c9b71f7d6f2114ae2474a4b6ad82` |
| 114 | 1 | A | 5165 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/NSE_static_stamp_duty_page.html` | `670216ea1d4fa74d6b4c5391a99900cb3451451a8f48582a0f73bf7267600ef4` |
| 115 | 1 | A | 1142 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/PIB_stamp_duty_PRID1635399_20200630.html` | `a94e6043b555ae2a101de0dbdb93d28025f8910e308b52f41794ba5f3272e936` |
| 116 | 1 | A | 47 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/SEARCH_LOG_20261006.txt` | `e2bc86c0e11296745b5ac9a9149e682ee769e252e3b6cba58d58c298b49e8772` |
| 117 | 1 | A | 107 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/SEARCH_LOG_20261006b.txt` | `1647f7fb4e8bd50e459d5922e84799f3b906df58ab5e0e3e4540331858afb85d` |
| 118 | 1 | A | 150 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/SEBI_PR_payment_of_fees_amendment_2014.html` | `7608634ec8a6b17c6c2840d460d9079c9b988951191bfe68d92a38bcda6156b2` |
| 119 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/SEBI_board_memo_fee_relaxation_jul2020.pdf` | `fcc397d8893b1ff0f7abf3e221703c00bb1b4013c815807947fe2e2672eff58f` |
| 120 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/SEBI_board_memo_fees_mar2019.pdf` | `ed3f87f2f37fb73a7267c506a8b92938e19c90d505b9a1573c35d2a4a3c90625` |
| 121 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/SEBI_gazette_fees_amendment_2017.pdf` | `4b826aaa618929490f196d385f0b5d8d7c291b266d3ac0ac8d8de585e4302459` |
| 122 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/SEBI_payment_of_fees_amendment_regs_2014.pdf` | `4a78abbe563f18f40fc719858b37c757decf525954d5b14b396e6efb2c759a3c` |
| 123 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/SEBI_stock_brokers_amendment_regs_commondocs.pdf` | `6b48fde69507635593650fe63749e2e7d9d700f7f36b0afd301257c44459e27a` |
| 124 | 1 | A | 65 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/SHA256SUMS` | `d2044ddac315c42168cfc2c0416b658ce1f32a2243134c0f569f673cd3df18f8` |
| 125 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/THC_SEBI_stock_brokers_regulations_1992_consolidated.pdf` | `f18f452b08c71cbac3f0e7249ca64e5b475ccbefa7967d9aa6d7a1697a656236` |
| 126 | 1 | A | 2379 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_blog_poa_demat_20150620.html` | `1f0e7d7c7de01afea2e8d84145e83057774b709ccfd663bf0f6e0fc5509cafc5` |
| 127 | 1 | A | 1 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charge-list_20140504002448.html` | `166b556a2c73ddd1f47bec0455c16a4574448484eb5f401a8bd8799c147f3da2` |
| 128 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_chargelist_20120504125926.xls` | `b4bccc8b057432b866734d5fa5b5f6235126420601cfe6bff3c9ffdeeec2fe6f` |
| 129 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_chargelist_20121225060108.xls` | `ae240f3dd100d116f97cb98e1a3205dbf312fc3d2c88121e448204219b4225e1` |
| 130 | 1 | A | 654 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20161009084026.html` | `cd66fee700c77ab9520c0e0854b19b03a54dfba440117c2f4a6e8e78611981ab` |
| 131 | 1 | A | 656 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20170317010757.html` | `7da660e591254536f8e012b10826a6796cd64286d60afa6ebd9ead3d97f911ed` |
| 132 | 1 | A | 713 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20180822091806.html` | `9bdbe5edb345d217bc48b0623ca5f8a8f6e01f65e07c9be5f9e8261025800577` |
| 133 | 1 | A | 768 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20190506071501.html` | `0331ea42e3741704d5ead9278775c1fa61fa656df1872fffe89cad296f7a0908` |
| 134 | 1 | A | 622 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20200217130322.html` | `c2ff785fb4aeb646472f6354e4bd72f2b1aed5853732e412fd4cf75149e7a7ca` |
| 135 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20210102232152.html` | `b5b8a26da359ade4a0bdb8f7de788d696343f100c123834b78db9fa521d487b4` |
| 136 | 1 | A | 780 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20220117095119.html` | `964292b4e465a56a2099fafc9d17bb31b41ee78cb2407ce09de428adea351020` |
| 137 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20230103104753.html` | `c69ac74a4efd80a5e4406550cfa409a91f367c523206180d302065211dca01ce` |
| 138 | 1 | A | 856 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20240301020050.html` | `cd4467daab8220ffdd2c109f03d55885197d79f5183ca7a77d8595b2ef1f0021` |
| 139 | 1 | A | 860 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20240917083204.html` | `256680064b7365b27b7e2d42534ce34a3e925624c7f8effabd630025f5fb36ae` |
| 140 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20241008053010.html` | `2095c01bc98490bfd2f5ec57173e9f30239decf7240e5f11fb8da1bd13443f60` |
| 141 | 1 | A | 860 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20241102213954.html` | `0aea1fc026404c1d4d6a5908cccbe139addab176b6e1f5520ca6b25e7d2f0a74` |
| 142 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20250107144419.html` | `d25f368df51affb419347360dbd3b931712512b41480f2f2fb8861aeda47cb55` |
| 143 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_charges_20260107113438.html` | `86aaa8d0993b36e08fc286a1df19bd3df7be7f7d8e0306e81780aacbf4692d2a` |
| 144 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_demat_form_20120504125220.pdf` | `f7bbf2eb4cc71210c5d352be4888056dee8724eaf246bfad75ee38d1d19534b9` |
| 145 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_ilfs_demat_form_20121225052153.pdf` | `6f03dee81cb2acfbdb34266ca0e4e3a7f46de2b6c54c2b56a5cec2708d9524c4` |
| 146 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_ilfsdemat_20140703122832.pdf` | `1969f54936ab5f39ab252782e2342cd3a158ab06bfcec5e1afb17d13d844d836` |
| 147 | 1 | A | 180 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_pricing_20120927020225.html` | `62f6e36dfe94e7d36e4dcacedc4e3fe9778dd178cafcdb25738d49ad4ab445fe` |
| 148 | 1 | A | 183 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_pricing_20130104171836.html` | `8d63ea94b1f07ccb3f8482af12afbb49e4f04823da256c70c768d468a99395d5` |
| 149 | 1 | A | 1 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_pricing_20140109010453.html` | `1cf820285461e8e1f142f9108305ea91f59e22896cd7e758b6a0d21193f2be3c` |
| 150 | 1 | A | 1 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WAYBACK_zerodha_pricing_20150206043100.html` | `5b723a9c86c77930bb5b76332a370d180ea3574d2cd5a1548489fba3326a4f87` |
| 151 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_faq-sbc_20161022.pdf` | `09c94bafb6037d48d9a5808fab15ced0f7733380ae3eb6f09744a91337d055ae` |
| 152 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_finact2015_20150528.pdf` | `33e73c90d8c3502d1793b03594814fae385ccc0627321714b0d4c64085f7ca99` |
| 153 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_st-act-ason-01apr2017_20170611.pdf` | `f170777f5ede1237bb8b3f3d96370ee99beed4a451687b775092c087377fb0a2` |
| 154 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_st-act-ason24oct2013_20150829.pdf` | `ef4f4b35418cd6d442071b66ce4cb9a95f22b0ff857994cb8f2b74d83c131f0b` |
| 155 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_st-finact-062016_20161023.pdf` | `66ce1c85a2c6b7c08e9f18476f3e44bf6b69150ebea7ac89f9589aae0d2e6411` |
| 156 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_st14-2015.pdf` | `6c9ab52e02bf08e69b9be6fef3179773adf7fc2773cb76db61bd9c1b667d9a30` |
| 157 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_st21h-2015_20151123.pdf` | `41fcf099114c43ecd611a872bcbfd72a115986cd2c9d36428b6f4ca1fbd36d18` |
| 158 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_st22h-2015_20151123.pdf` | `d14727f3754134cddcb784380a26353098e0241a5d425b21ee2e493bad6880e4` |
| 159 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_st27-2016.pdf` | `278b5d3a0b91a03b9a0a5172a5e472ee015b5ff0c058ef1ffc23075b7236f30e` |
| 160 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_CBEC_st28-2016.pdf` | `caaf64be41ce1a347dc7f9d6cb6b210c8e736c3a13aadfc9da7d235611c3495f` |
| 161 | 1 | A | 537 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/WB_NSDL_fee_payable_by_participants_20130818.html` | `6825fa90f405ea11e7e4d0bd770b566f1bf66538d7c9720440fccc36b01180a6` |
| 162 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_NSDL_fees_and_charges_to_DPs_20170708.pdf` | `bc45eddb4e0d62af0a0d2b3fa4297975d21e3b1c67764aed2434765641a07255` |
| 163 | 1 | A | - | - | EXPERIMENT | `docs/evidence/s2mom_costs/WB_NSDL_policy_2010-0029_settlement_fee_20131028.pdf` | `932a1f380984c5311ad03e0e2a7385ae4d4f41f54aec3bbb5421dc8b1e53dc43` |
| 164 | 1 | A | 552 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/ZERODHA_bulletin_uniform_stamp_duty_20200701.html` | `871057fc1efcfb721f10ca6a17b99c33d130a77075f86e4df4cc49adf26465bf` |
| 165 | 1 | A | 979 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/ZERODHA_charges_page.html` | `aae15a3dd992339b1efafa608817ae0378c25e939d4300acce1375e56ca80e98` |
| 166 | 1 | A | 7227 | 0 | EXPERIMENT | `docs/evidence/s2mom_costs/ZERODHA_zconnect_zero_brokerage_20151130.html` | `0a72bc0fe7a1f76fb754835c25af7cd3ac8d635868b7119212d1496640cdd5b7` |
| 167 | 1 | A | 656 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/build_manuscript.py` | `00b20043a226246e3a54a916b658a759e03f6f49623373e894a922a6962e6da3` |
| 168 | 1 | A | 47 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/claim_audit.md` | `07b25d8ac9ac6467fda56ab43622721e8d92e1c632844615a082e186a0816d9e` |
| 169 | 1 | A | 701 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/consistency_check_log.txt` | `9b727b881f3b82de6e46afc03b2f7b45673eb5d0b1a9944b59cb2f5e6227d53e` |
| 170 | 1 | A | - | - | EXPERIMENT | `docs/manuscript/s2_mom_v1/figures/fig1_ladder_gross.png` | `05489d8342231d147cdb06dc051ca0520f8a263a0e670c0228d8c94a3b9fc475` |
| 171 | 1 | A | - | - | EXPERIMENT | `docs/manuscript/s2_mom_v1/figures/fig2_cost_sensitivity.png` | `b80db7d8e11faded184b374a76643ac13ee679d5483f59e1a4e158d1c3456d1b` |
| 172 | 1 | A | - | - | EXPERIMENT | `docs/manuscript/s2_mom_v1/figures/fig3_delta_primary_vs_confirmation.png` | `b2ec0a3c8c951629140a637c24b550f16d68d79c260e62ef36735059a0282aab` |
| 173 | 1 | A | - | - | EXPERIMENT | `docs/manuscript/s2_mom_v1/figures/fig4_primary_halves.png` | `5890ad956958d302401ce927610123ca96549600110f1ca0c08f41972f32465d` |
| 174 | 1 | A | - | - | EXPERIMENT | `docs/manuscript/s2_mom_v1/figures/fig5_cumulative_differences.png` | `43ade1dbdc29366c027ced796da5d2e5aa3c6be174d050df7b5c490aa161dfdd` |
| 175 | 1 | A | - | - | EXPERIMENT | `docs/manuscript/s2_mom_v1/manuscript.docx` | `6372efc4c6b7b627d8d9857fed5751d460036350de1253b8c975e87119f73b83` |
| 176 | 1 | A | 1558 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/manuscript.html` | `1d4462297f89e751307a2b61a480908ecd477bb17230579ebb19486dcdeabbf8` |
| 177 | 1 | A | 606 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/manuscript.md` | `10ee21376ba9872e9fedbe743e2506130f4fd14c1355e17cd3c1adb0c79d7f1b` |
| 178 | 1 | A | - | - | EXPERIMENT | `docs/manuscript/s2_mom_v1/manuscript.pdf` | `440f1c68a5c7ba75a1e7327780a2f7a763b8eafe9310f13eeb99fe26b0f90b4d` |
| 179 | 1 | A | 487 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/manuscript.template.md` | `4329f88120c589e69307bdff94207d33ef43f1f4e09c37fc40e66a4dd47fdbf1` |
| 180 | 1 | A | 566 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/number_audit.csv` | `c313642f323602612b0ba43c8d66d799b76f6c6777f8d17c080fc6eab802a668` |
| 181 | 1 | A | 74 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/number_audit.md` | `47a547bf3071a724549e37c788e16e17c22ead8d80b0da33c9f1c3880ac497b5` |
| 182 | 1 | A | 89 | 0 | EXPERIMENT | `docs/manuscript/s2_mom_v1/references_verification_checklist.md` | `b26cec1f5d66188cb8855b6a0c91da130a821d62169f50f1554b4c90560fed30` |
| 183 | 1 | A | 88 | 0 | EXPERIMENT | `docs/research/phase3a_momentum_protocol_addendum1_costs.md` | `d12ccaa6fa23143f808b429d75c757a57a853afa42e961a94157d3b772dffefe` |
| 184 | 1 | A | 33 | 0 | EXPERIMENT | `docs/research/phase3a_momentum_protocol_addendum1_supplement1.md` | `ab28fd1750db3e222819013ef70ff69c4b48d5d5757d51ec5c77e9b6232253b3` |
| 185 | 1 | A | 222 | 0 | EXPERIMENT | `docs/research/phase3a_momentum_protocol_addendum1_supplement2.md` | `6c373c5ff0db321cb753fff7a08db078ff29ca2c3f2f0cfbe8c0fb1431e6a888` |
| 186 | 1 | A | 99 | 0 | EXPERIMENT | `docs/research/phase3a_momentum_protocol_addendum1_supplement3.md` | `682191de462bac3b5d2901995be8d20d355bb4d6146fd87a3f02ed8c6c2580ce` |
| 187 | 1 | A | 63 | 0 | EXPERIMENT | `docs/research/phase3a_momentum_protocol_addendum1_supplement4.md` | `e4617ccb6fa8713ea5a1f82843e5ee1d5fceda84432675c3ce081047b7508b87` |
| 188 | 1 | A | 267 | 0 | EXPERIMENT | `docs/research/phase3b_final_prerun_audit.md` | `307bd200995811f6807068356254b99b73cca8b40b03283b0acda0de0a0c1c11` |
| 189 | 1 | A | 143 | 0 | EXPERIMENT | `docs/research/phase3b_implementation_checklist.md` | `d54fdc4f535fe669411196e634f9258af3bbb2927ac771d8ab3682a024476f43` |
| 190 | 1 | A | 166 | 0 | EXPERIMENT | `docs/research/s2_mom_v1_c2_analysis_spec.md` | `78864a4f6fddad86a7b3273e8d8c1e7ab818ed318deb0fdb75cc99e2c5a0c0aa` |
| 191 | 1 | A | 68 | 0 | EXPERIMENT | `docs/research/s2_mom_v1_deviation_log.md` | `8b1187384ebf1f54f41fcec2cb2d92bfa4f0200b24ffc2319ee1c5216da9a315` |
| 192 | 1 | A | 59 | 0 | EXPERIMENT | `docs/research/s2_mom_v1_results_guide.md` | `96d6004e5b03b9a4ca0b9e265b02c598617291dec4cd32368920238a3e500b56` |
| 193 | 1 | A | 142 | 0 | EXPERIMENT | `docs/research/s2_mom_v1_step_e_full_implementation_report_20261006.md` | `43a29e041f8156c31550b5bd46fcb008e18381702abcd97be13bd848e117b5b2` |
| 194 | 1 | A | 111 | 0 | EXPERIMENT | `docs/research/s2_mom_v1_step_e_implementation_report_20261006.md` | `2f88ab3bdca4831ba9a72c7efd3008845ff70793584ce9a6a63eaf6023222738` |
| 195 | 1 | M | 24 | 0 | REMEDIATION | `registry/experiments.jsonl` | `f017411051b92d36ca2c712cf1906d05c070be78d12e65527e574ce566bd56fd` |
| 196 | 1 | M | 6 | 0 | RESEARCHER | `registry/trials.jsonl` | `540d6d9a5dcd4023e4f87d5ba6568e3bae154988f5b4ef63fba99ea034651eb5` |
| 197 | 1 | A | 22564 | 0 | REMEDIATION | `release/s2_mom_v1/ARCHIVE_MANIFEST.json` | `394df99cd6f0fde7ebb8198e996e355498e6977f19bc5125ef89c4144af7790e` |
| 198 | 1 | A | 56 | 0 | REMEDIATION | `release/s2_mom_v1/ENVIRONMENT.json` | `ae13bad77bb000715e0973b192f938c884f7b3799f9461fdd32e1d7efdb1ce27` |
| 199 | 1 | A | 94 | 0 | REMEDIATION | `release/s2_mom_v1/conda-osx-arm64.lock` | `eef4e14bc0c5d86e51b0c8b032bf9160b0b5c3e0dac02e462300fe5ad413d665` |
| 200 | 1 | A | 22 | 0 | REMEDIATION | `release/s2_mom_v1/environment.yml` | `2262cdcdb5486e3abbe43b839f55c154b5b98f5de75ba16b086645e751ad790b` |
| 201 | 1 | A | 27 | 0 | REMEDIATION | `requirements-lock.txt` | `81f7dfb8de2a3ca4d7104fea8f6ab32aa1756333ea434a09dd114127cedd6af0` |
| 202 | 1 | M | 2 | 0 | REMEDIATION | `requirements.txt` | `942cfa5792a16f9a587416209a9614fe8e1ab1b3ecab54fee5cb3717a45ae930` |
| 203 | 1 | A | 46 | 0 | EXPERIMENT | `results/s2_mom_v1/blinded_precision.json` | `1e26341044f3e46052fdcda53a56721124412e26d5b93156bf274a9a4de5c693` |
| 204 | 1 | A | 57 | 0 | EXPERIMENT | `results/s2_mom_v1/confirmation_delta.csv` | `a462455acb343910a02206ab6af50582eaedef20b0ed6cec81a88f73cbc58b75` |
| 205 | 1 | A | 84 | 0 | EXPERIMENT | `results/s2_mom_v1/confirmation_events.csv` | `4ee6861fd1cb33f70f8c519e1a84801a816cbb96d900a901a0aea029f0562834` |
| 206 | 1 | A | 67328 | 0 | EXPERIMENT | `results/s2_mom_v1/confirmation_holdings.csv` | `96bb174ed2942e7b93630ae445d11817551a44e15b90e5454272ddb79aa825b0` |
| 207 | 1 | A | 225 | 0 | EXPERIMENT | `results/s2_mom_v1/confirmation_monthly.csv` | `4d88f385375ad681f85be739b292097e2e898acb6acb71013230c67415a43ce3` |
| 208 | 1 | A | 277 | 0 | EXPERIMENT | `results/s2_mom_v1/confirmation_results.json` | `38d1d0a9fbb1d22a19b7912ec4e6285d1dbcb920ffd0e6d99ea19e096c304d92` |
| 209 | 1 | A | 115 | 0 | EXPERIMENT | `results/s2_mom_v1/primary_delta.csv` | `2efa04351a6bca10fbf1e6a96d6c5240fb0f2570420185250750b77d5c4fecc9` |
| 210 | 1 | A | 316 | 0 | EXPERIMENT | `results/s2_mom_v1/primary_events.csv` | `2f1e1f56806fb7b7c11b14d24c94835502eba4d9d8eefe4ca2001f83c0e87850` |
| 211 | 1 | A | 131135 | 0 | EXPERIMENT | `results/s2_mom_v1/primary_holdings.csv` | `3887995763861a2ed17e280f1f975c6fd716dab4923c954d3ca70b91c2d93748` |
| 212 | 1 | A | 457 | 0 | EXPERIMENT | `results/s2_mom_v1/primary_monthly.csv` | `f7c8d3ab5a0ef7a08b6a0ca8a12bf26a1f901006c21637cf7886e297b97bb372` |
| 213 | 1 | A | 277 | 0 | EXPERIMENT | `results/s2_mom_v1/primary_results.json` | `fe7e95ba97482d6d53faba543d860e4f0d1e50cfa0312d669e910346d41ef857` |
| 214 | 1 | A | 204 | 0 | EXPERIMENT | `results/s2_mom_v1/sensitivity_results.json` | `7d6081d8c4a099f7cd1d7d688791c23180d6977536ae4c7860a08b429ff0c19b` |
| 215 | 1 | A | 1267 | 0 | EXPERIMENT | `results/s2_mom_v1_c2/c2_results.json` | `cf977e8a5efce7ba83ce91bf70ae247ed1aea96c7004f8d03162669097689513` |
| 216 | 1 | A | 18842 | 0 | EXPERIMENT | `results/s2_mom_v1_step_e/confirmation_step_e_ledger.csv` | `547c7be5adfc82d6fc62b7517b698c14199032d8041a34b84de61ea9a5ac1037` |
| 217 | 1 | A | 57 | 0 | EXPERIMENT | `results/s2_mom_v1_step_e/confirmation_step_e_monthly.csv` | `f43b4a4d9d9898a45ff2d46fa3e0381b1386ec35f4a8e3d92de898d5a2f10638` |
| 218 | 1 | A | 38051 | 0 | EXPERIMENT | `results/s2_mom_v1_step_e/primary_step_e_ledger.csv` | `75d0fbb0ae2eedda5970836d66c6961f6203e0c3d4bf63134421371dc3397352` |
| 219 | 1 | A | 115 | 0 | EXPERIMENT | `results/s2_mom_v1_step_e/primary_step_e_monthly.csv` | `3ec30ebdd256234c61bd82292dc01b3acbf582e94eec7f558f06f715b8b3dfd7` |
| 220 | 1 | A | 359 | 0 | EXPERIMENT | `results/s2_mom_v1_step_e/step_e_results.json` | `675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0` |
| 221 | 1 | A | 123 | 0 | REMEDIATION | `scripts/audit_snapshot.py` | `22f2c7973fb632465fafcee3c22e270e2b343145079816c55cd663eebf471ed7` |
| 222 | 1 | A | 20 | 0 | EXPERIMENT | `scripts/build_stage3.py` | `98f5d15dbd0322dc47a1f81f91cb8fbd5d8d084d5468c761ab94c8d7eafb3cf1` |
| 223 | 1 | A | 340 | 0 | REMEDIATION | `scripts/mutation_campaign.py` | `5fb96e69fe07813b3ee36bbdc875fc7a79eab425399d4e9c891c4cd2188d2e2c` |
| 224 | 1 | A | 195 | 0 | REMEDIATION | `scripts/release_archive.py` | `e060d5de8e8001a149bda6e898adc586572d83bdae8f2d4b5d0290c80ebe0335` |
| 225 | 1 | A | 615 | 0 | REMEDIATION | `scripts/reproduce_s2_mom_v1.py` | `5a6ef13b57548f30bc246b089660a009b051cbffc3c605ee608bbfa4cc77f24a` |
| 226 | 1 | A | 132 | 0 | EXPERIMENT | `scripts/run_s2_mom.py` | `de806c3b8bbbeadca5ae55c9eca6cf3e788165020f0d9b171d4f1210ef6edcfa` |
| 227 | 1 | A | 205 | 0 | EXPERIMENT | `scripts/run_s2_mom_c2.py` | `505b2e4ed9d4e1f34dc2e441f2ff73e8399998e4744a6f0b4b7d62e59668b3fa` |
| 228 | 1 | A | 110 | 0 | EXPERIMENT | `scripts/run_s2_mom_step_e.py` | `997d25ba88111eea113b0f52a8cc16f2948bc59cad689c085dd3e07d0508ae6d` |
| 229 | 1 | A | 235 | 0 | REMEDIATION | `scripts/verify_manuscript.py` | `cf4e16ec39252af5c57375ecdf6a0777b5a2b52e92fe63a3ce1f344af2d43651` |
| 230 | 1 | M | 323 | 69 | REMEDIATION | `src/registry/experiments.py` | `17a9f2e3777bec67a092c3975063a1f3cb577b037cd0b296a6ec2604c984426e` |
| 231 | 1 | A | 348 | 0 | REMEDIATION | `src/registry/integrity.py` | `6fd9f98766576b523f19e6b58714e02cabab30d7515821f3fc587f29ea333fda` |
| 232 | 2 | A | 100 | 0 | EXPERIMENT | `src/research_view.py` | `9981fd6c192b98728813e2236a37f00a91830ce77d746e4f016a14eeabe914c2` |
| 233 | 1 | A | 0 | 0 | EXPERIMENT | `src/stage3/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 234 | 1 | A | 96 | 0 | EXPERIMENT | `src/stage3/costs.py` | `851ec208dbdd1e2ceaf8ad7d811ce244aa50af457021e8bbae36ba1eeabceb6f` |
| 235 | 1 | A | 233 | 0 | EXPERIMENT | `src/stage3/data.py` | `a88b754a59521d8f634ee8a4c2df2dc431d42ade485ced0623e9e0e1a38c5f5d` |
| 236 | 1 | A | 308 | 0 | EXPERIMENT | `src/stage3/experiment.py` | `947c9de12d8257696439f62a15971ccc4011df578097a38c381843e3daa0b7a9` |
| 237 | 1 | A | 329 | 0 | EXPERIMENT | `src/stage3/ladder.py` | `4f3f447a1378b1367a6e0cb05fd19220778da3384c0539f5b6e656c68767705b` |
| 238 | 1 | A | 173 | 0 | EXPERIMENT | `src/stage3/protocol.py` | `fc42ce58e28d0df5d122019f5ce727ee9bc194b409d5056313377ef6c581ceb5` |
| 239 | 1 | A | 66 | 0 | EXPERIMENT | `src/stage3/stats.py` | `846b128d67dac4c07744703a29bd054416f0cef5332c1353f76c9dcd3100b558` |
| 240 | 1 | A | 337 | 0 | EXPERIMENT | `src/stage3/step_e.py` | `17e1908270bf544878164ed6b0704af5ba74a7a440055684f78b0cc56c397554` |
| 241 | 1 | M | 5 | 0 | REMEDIATION | `tests/test_access_boundary.py` | `8aab6b4ffec2646743d36633e639c738949baaa102c0427249bf49191ac6c04b` |
| 242 | 1 | A | 174 | 0 | REMEDIATION | `tests/test_environment.py` | `029000780338c86278c2c8f328870123e599d902193201bcf147e7d99ed9199e` |
| 243 | 1 | A | 409 | 0 | REMEDIATION | `tests/test_failure_injection.py` | `36b67a11205cdd405eff7219fae7e42c55b6faa97ec8fe0082d4484fb57fc3b0` |
| 244 | 1 | A | 69 | 0 | REMEDIATION | `tests/test_frozen_code.py` | `f57abded07678c5734f0a88c4bcf22fd8cd355ee8ca02463c8b1afb9e70ae75e` |
| 245 | 1 | A | 21 | 0 | REMEDIATION | `tests/test_manuscript_verification.py` | `0aa75eb43a6d59d6d3ee212a9b5a7236e9771379898f749eade7d70ea02ded76` |
| 246 | 1 | A | 189 | 0 | REMEDIATION | `tests/test_provenance_chain.py` | `40e232704245674a58ae72a9043d0100e165200abc7f3407fd41d890cb8962b1` |
| 247 | 1 | A | 382 | 0 | REMEDIATION | `tests/test_registry_state_machine.py` | `c32292b7fce53215b42b8abdae7c76637736b74913be3002d45aa6b99bbc273a` |
| 248 | 1 | A | 116 | 0 | REMEDIATION | `tests/test_release_archive.py` | `e66c3f7a55be6bc3e97bf3cfc2b1bcd01cc90f2f343a17b2c335ac6abf34a788` |
| 249 | 1 | A | 230 | 0 | REMEDIATION | `tests/test_reproduction.py` | `e10eed11e0bdb53d3d09d9ab5278af83570911a66b2042c8af6caceb0361f29a` |
| 250 | 1 | A | 140 | 0 | EXPERIMENT | `tests/test_s2mom_c2.py` | `3b2f12eccfd3826f5e69049d4239e682d50c21226a6a7af6c465ec2f7bfe55d3` |
| 251 | 1 | A | 209 | 0 | EXPERIMENT | `tests/test_s2mom_cost_schedule.py` | `5dde2863982e23bda782dea2d05b22f4f2a283f23c737a0feecce1cd92b5acc6` |
| 252 | 1 | A | 566 | 0 | REMEDIATION | `tests/test_s2mom_mutation_kills.py` | `a48ef04604599cdc5b4dff3da29736df136fd859f3274122ead46d98c696985c` |
| 253 | 1 | A | 331 | 0 | EXPERIMENT | `tests/test_s2mom_step_e.py` | `7db365f7116f56f4809264c05ba10b5fe90eedae33a2caed3d0b0fd961d44e10` |
| 254 | 1 | A | 546 | 0 | EXPERIMENT | `tests/test_s2mom_step_e_scenarios.py` | `7e4f2905d85286dd9862ac35508637cd63638b8c47b9ec96a3b7848a071a4a81` |
| 255 | 1 | A | 543 | 0 | EXPERIMENT | `tests/test_stage3_infra.py` | `f4bf4db9b8d300121cad3596e88f03fb5c73eccd9662867acd408e98137499e1` |
| 256 | 1 | A | 513 | 0 | EXPERIMENT | `tests/test_stage3_ladder.py` | `6d43795990004ecff047211e05a1925aba8c02218e7a388e1ca0b6f935492044` |
| 257 | 2 | A | 52 | 0 | EXPERIMENT | `tests/test_ui_api.py` | `5ebc504f5cf52d9390e2a368672bab141f0b262cce85a52b8a84ad61d2882561` |
| 258 | 1 | A | 48 | 0 | REMEDIATION | `tests/test_version_control.py` | `1fac91052ae9677b57c8717a0b96e3d31e9ce7a6968fe22e8d6d90123c772d5e` |
