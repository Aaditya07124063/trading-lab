"""Final manuscript (2026-10-08): the rebuild for submission changed presentation only.

Compared with the manuscript in the research release (tag s2-mom-v1-release-1):
  - every number filled from a registered file is the same, plus exactly one new filled number
    (the minimum detectable effect, now also quoted in the abstract, from blinded_precision.json);
  - every figure is byte-identical;
  - the stale "not yet committed" statement is gone from every format, the PDF included (N-06);
  - Table A5 lists every addendum and supplement registered in the registry (N-02).
"""

import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from src.registry import experiments

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "docs/manuscript/s2_mom_v1"
TAG = "s2-mom-v1-release-1"
SNAP = json.loads((ROOT / "docs/audit/remediation/pre_remediation_snapshot.json").read_text())["files"]


def at_release(rel):
    if not shutil.which("git") or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    r = subprocess.run(["git", "show", f"{TAG}:{rel}"], cwd=ROOT, capture_output=True)
    if r.returncode:
        pytest.skip(f"tag {TAG} not available")
    return r.stdout


def rows(text):
    keep = ("location", "reported", "kind", "source_file", "json_path", "raw_value", "scale")
    return sorted(tuple(r[k] for k in keep) for r in csv.DictReader(io.StringIO(text)))


def test_numbers_are_those_of_the_release_plus_the_abstract_detectable_effect():
    old = rows(at_release("docs/manuscript/s2_mom_v1/number_audit.csv").decode())
    new = rows((MS / "number_audit.csv").read_text())
    added = list(new)
    for r in old:
        added.remove(r)                                         # raises if a released number disappeared or changed
    assert added == [("text", "0.59", "REGISTERED", "results/s2_mom_v1/blinded_precision.json",
                      "detectable_effect_80pct_two_sided_5pct", "0.5906507070303696", "1.0")]
    assert all(r[2] == "REGISTERED" for r in new)              # no derived number


def test_figures_are_byte_identical_to_the_registered_state():
    figs = sorted((MS / "figures").glob("*.png"))
    assert len(figs) == 5
    for f in figs:
        assert hashlib.sha256(f.read_bytes()).hexdigest() == SNAP[f"docs/manuscript/s2_mom_v1/figures/{f.name}"]["sha256"], f.name


def test_no_format_says_the_release_is_not_yet_committed():
    texts = {n: (MS / n).read_text() for n in ("manuscript.md", "manuscript.template.md", "manuscript.html")}
    texts["manuscript.docx"] = zipfile.ZipFile(MS / "manuscript.docx").read("word/document.xml").decode()
    if shutil.which("pdftotext"):
        texts["manuscript.pdf"] = subprocess.run(["pdftotext", str(MS / "manuscript.pdf"), "-"], capture_output=True, text=True).stdout
    for name, t in texts.items():
        flat = re.sub(r"\s+", " ", t)
        assert "not yet committed" not in flat, name
        assert "s2-mom-v1-release-1" in flat and "f5bfed8" in flat, name
        assert "has not been tested" in flat, name             # no claim of reproduction on other hardware


def test_table_a5_lists_every_registered_addendum_and_supplement():
    md = (MS / "manuscript.md").read_text()
    table = dict(re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", md))
    for a in experiments.current()["S2-MOM-v1"]["addenda"]:
        assert table.get(a["file"]) == a["sha256"], a["file"]
