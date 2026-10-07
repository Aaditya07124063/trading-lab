"""F-01 guard: no research-critical file may exist only as an untracked or silently ignored working-tree copy."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_PATHS = ["src", "scripts", "tests", "config", "registry", "release", "results/s2_mom_v1", "results/s2_mom_v1_step_e",
                  "results/s2_mom_v1_c2", "data/stage2", "data/stage3", "docs/research", "docs/manuscript", "docs/evidence",
                  "docs/audit", "requirements.txt", "requirements-lock.txt", "pytest.ini", "evaluate_orb_v1.py"]
NOISE = ("__pycache__/", ".DS_Store", ".pytest_cache/", ".ipynb_checkpoints/")


def _git(*args):
    return subprocess.run(["git", *args, "--", *RESEARCH_PATHS], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()


@pytest.fixture(scope="module", autouse=True)
def _needs_git():
    if not (ROOT / ".git").exists() or not shutil.which("git"):
        pytest.skip("not a git checkout (reproduction package or scratch copy)")


def test_no_research_critical_file_is_untracked():
    untracked = _git("ls-files", "--others", "--exclude-standard")
    assert untracked == [], f"research-critical files outside version control: {untracked[:20]}"


def test_every_ignored_research_file_is_in_the_external_archive_manifest():
    archived = set(json.loads((ROOT / "release/s2_mom_v1/ARCHIVE_MANIFEST.json").read_text())["files"])
    ignored = [f for f in _git("ls-files", "--others", "--ignored", "--exclude-standard")
               if not any(n in f for n in NOISE) and not f.endswith(".pyc")]
    orphan = [f for f in ignored if f not in archived]
    assert orphan == [], f"ignored research files with no hash anywhere: {orphan[:20]}"


def test_registered_result_files_and_the_registry_are_tracked():
    tracked = set(_git("ls-files"))
    rec = [json.loads(line) for line in (ROOT / "registry/experiments.jsonl").read_text().splitlines()]
    files = {f for r in rec if isinstance(r.get("results"), dict) for f in r["results"].get("files", [])}
    assert files and files <= tracked
    for must in ("registry/experiments.jsonl", "registry/trials.jsonl", "data/stage3/s2_mom_v1/manifest.json",
                 "release/s2_mom_v1/ARCHIVE_MANIFEST.json", "scripts/run_s2_mom.py", "src/stage3/ladder.py",
                 "docs/research/phase3a_momentum_protocol.md", "config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json"):
        assert must in tracked, must
