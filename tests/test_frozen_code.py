"""F-09 / frozen-artifact guard: every frozen research file is byte-identical to the pre-remediation snapshot.

The registered code hashes cover 10 files. The experiment also executes code outside those lists
(statistics used by step E and C2, the bootstrap resampler, Stage 2 rules, the access boundary).
This test pins ALL of it, plus the protocol documents, inputs and registered results, to the hashes
recorded in docs/audit/remediation/pre_remediation_snapshot.json before remediation started.
Changing one of these files is not a bug fix; it is a new protocol version. Open one deliberately.
"""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = json.loads((ROOT / "docs/audit/remediation/pre_remediation_snapshot.json").read_text())["files"]
FROZEN_CODE = [f for f in SNAPSHOT if f.endswith(".py") and (
    f.startswith(("src/stage2/", "src/stage3/", "src/intraday/")) or f in (
        "src/access.py", "src/config.py", "scripts/run_s2_mom.py", "scripts/run_s2_mom_step_e.py", "scripts/run_s2_mom_c2.py",
        "scripts/build_stage2.py", "scripts/build_stage3.py", "evaluate_orb_v1.py", "docs/manuscript/s2_mom_v1/build_manuscript.py"))]
FROZEN_ARTIFACTS = [f for f in SNAPSHOT if f.startswith(("docs/research/", "results/s2_mom_v1", "config/cost_schedules/", "data/stage3/",
                                                         "docs/manuscript/s2_mom_v1/"))
                    or (f.startswith("data/stage2/") and "/datasets/" not in f)]


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def test_the_lists_are_not_empty_and_cover_the_registered_code_hash_files():
    assert len(FROZEN_CODE) >= 30 and len(FROZEN_ARTIFACTS) >= 80
    for must in ("src/stage3/ladder.py", "src/stage3/stats.py", "src/stage3/step_e.py", "src/intraday/inference.py", "src/stage2/returns.py",
                 "src/stage2/universe.py", "scripts/run_s2_mom.py", "scripts/run_s2_mom_c2.py"):
        assert must in FROZEN_CODE
    assert "src/registry/experiments.py" not in FROZEN_CODE          # remediated on purpose; not part of any registered code hash


@pytest.mark.parametrize("rel", FROZEN_CODE)
def test_frozen_code_is_byte_identical_to_the_pre_remediation_snapshot(rel):
    assert _sha(ROOT / rel) == SNAPSHOT[rel]["sha256"], f"{rel} changed - frozen research code may only change under a new protocol version"


def test_frozen_artifacts_are_byte_identical_to_the_pre_remediation_snapshot():
    """Protocol documents, cost schedules, Stage 2 tables, Stage 3 inputs, registered results, manuscript, original audit files."""
    missing = [f for f in FROZEN_ARTIFACTS if not (ROOT / f).exists() and not f.endswith("panel.parquet")]
    changed = [f for f in FROZEN_ARTIFACTS if (ROOT / f).exists() and _sha(ROOT / f) != SNAPSHOT[f]["sha256"]]
    assert not missing and not changed, f"missing {missing[:5]} changed {changed[:5]}"


def test_registry_and_trial_log_only_grew():
    for rel in ("registry/experiments.jsonl", "registry/trials.jsonl"):
        old = SNAPSHOT[rel]
        with open(ROOT / rel, "rb") as fh:
            assert hashlib.sha256(fh.read(old["bytes"])).hexdigest() == old["sha256"], f"{rel}: bytes that existed before remediation changed"
    trials = (ROOT / "registry/trials.jsonl").read_bytes()
    assert len(trials) == SNAPSHOT["registry/trials.jsonl"]["bytes"], "a new trial was logged during remediation - was an experiment run?"


def test_original_forensic_audit_files_are_preserved_unchanged():
    """The 18 files of the 2026-10-07 forensic audit were copied to docs/audit/forensic_20261007/ before any report was regenerated."""
    originals = {f: v["sha256"] for f, v in SNAPSHOT.items() if f.startswith("docs/audit/") and f.count("/") == 2}
    assert len(originals) == 18
    for rel, want in originals.items():
        assert _sha(ROOT / "docs/audit/forensic_20261007" / Path(rel).name) == want, rel
