"""N-06: the only change to the frozen manuscript after the release commit is one presentation sentence.

Undoing that sentence must give back exactly the registered pre-remediation bytes (md, template, html) or,
for the .docx, exactly the registered document text with every other part of the file identical. So no
number, table, figure or conclusion of the manuscript can have changed. manuscript.pdf was not rebuilt
and still carries the old sentence (documented in docs/audit/FINAL_RELEASE_GATE.md, N-06).
"""

import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS = "docs/manuscript/s2_mom_v1/"
SNAP = json.loads((ROOT / "docs/audit/remediation/pre_remediation_snapshot.json").read_text())["files"]
OLD = ("At the time of writing, the experiment code, the addenda, the cost schedule, the result files and this manuscript exist in the "
       "working tree and are not yet committed; the registry records the tree as dirty at every run. The current working tree is therefore "
       "not the final reproducibility snapshot. A tagged commit containing all of these files, with the hashes in Table A5 unchanged, should "
       "be created and cited before the paper is circulated.")
NEW = ("The experiment code, the addenda, the cost schedule and the result files were committed, unchanged from the registered runs, in "
       "commit {c} (tag {t}); the registry records the tree as dirty at every run because the runs were made before that commit. The hashes "
       "in Table A5 are unchanged.")
STYLE = {"manuscript.md": ("`f5bfed8`", "`s2-mom-v1-release-1`"), "manuscript.template.md": ("`f5bfed8`", "`s2-mom-v1-release-1`"),
         "manuscript.html": ("<code>f5bfed8</code>", "<code>s2-mom-v1-release-1</code>"), "manuscript.docx": ("f5bfed8", "s2-mom-v1-release-1")}


def new_text(name):
    c, t = STYLE[name]
    return NEW.format(c=c, t=t)


def apply(raw, name, old, new):
    if name.endswith(".docx"):
        zin, buf = zipfile.ZipFile(io.BytesIO(raw)), io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename == "word/document.xml":
                    assert data.count(old.encode()) == 1
                    data = data.replace(old.encode(), new.encode())
                zout.writestr(info, data)
        return buf.getvalue()
    text = raw.decode()
    assert text.count(old) == 1, name
    return text.replace(old, new).encode()


def test_undoing_the_n06_sentence_gives_back_the_registered_manuscript():
    for name in STYLE:
        now = (ROOT / MS / name).read_bytes()
        reverted = apply(now, name, new_text(name), OLD)
        if name.endswith(".docx"):
            registered = ROOT / "docs/audit/remediation/manuscript_docx_registered.bin"      # byte copy of the registered .docx
            assert hashlib.sha256(registered.read_bytes()).hexdigest() == SNAP[MS + name]["sha256"]
            a, b = zipfile.ZipFile(io.BytesIO(reverted)), zipfile.ZipFile(registered)
            assert [i.filename for i in a.infolist()] == [i.filename for i in b.infolist()]
            assert all(a.read(n) == b.read(n) for n in a.namelist()), "a part of the .docx other than the N-06 sentence changed"
        else:
            assert hashlib.sha256(reverted).hexdigest() == SNAP[MS + name]["sha256"], name
        assert b"not yet committed" not in (zipfile.ZipFile(ROOT / MS / name).read("word/document.xml") if name.endswith(".docx") else now)


def test_pdf_was_not_rebuilt():
    assert hashlib.sha256((ROOT / MS / "manuscript.pdf").read_bytes()).hexdigest() == SNAP[MS + "manuscript.pdf"]["sha256"]
