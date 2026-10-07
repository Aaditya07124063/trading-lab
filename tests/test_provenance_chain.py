"""F-02: registry -> Stage 3 manifest SHA-256 -> manifest contents -> individual input hashes.

Adversarial tests on a small synthetic tree (no real data is read or written), plus one read-only
check that the real chain verifies. The registry record is the root of trust: several attacks
below also re-point the registry anchor on purpose, to prove that the later links hold on their own.
"""

import hashlib
import json
from pathlib import Path

import pytest

from src.registry import integrity as I
from src.registry.integrity import ProvenanceError

ROOT = Path(__file__).resolve().parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest()


def write(root, rel, body):
    f = root / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(body)
    return sha(body)


@pytest.fixture
def chain(tmp_path):
    root = tmp_path / "repo"
    outs = {rel: write(root, f"{I.STAGE3}/{rel}", f"stage3:{rel}".encode()) for rel in I.OUTPUTS}
    ins = {k: write(root, rel, f"stage2:{k}".encode()) for k, rel in I.STAGE2_INPUTS.items()}
    ins["ret1_1_datasets"] = {f"{I.RET_PREFIX}ret1_1_{y}.parquet": write(root, f"{I.RET_PREFIX}ret1_1_{y}.parquet", f"ret{y}".encode())
                              for y in (2011, 2012)}
    code = {f: write(root, f, f.encode()) for f in ("src/stage3/ladder.py", "src/stage3/data.py", "src/stage3/protocol.py")}
    checks = {f"{I.STAGE3}/{c}": write(root, f"{I.STAGE3}/{c}", c.encode()) for c in I.CHECK_FILES}
    content = {"protocol_sha256": "p" * 64, "inputs_sha256": ins, "outputs_sha256": outs, "code_sha256": code}
    man = root / I.STAGE3 / "manifest.json"
    man.write_text(json.dumps({"content": content, "build": {"built_at": "x"}}, indent=1) + "\n")
    rec = {"protocol_sha256": "p" * 64, "universe_sha256": ins["univ1"],
           "anchors": {"stage3_manifest_sha256": sha(man.read_bytes()), "stage3_check_files_sha256": checks}}
    return root, rec, man


def rewrite(man, edit, rec=None, raw=None):
    """Rewrite the manifest; with `rec`, ALSO re-point the registry anchor (an attacker who controls both)."""
    if raw is None:
        doc = json.loads(man.read_text())
        edit(doc["content"])
        raw = json.dumps(doc, indent=1) + "\n"
    man.write_text(raw)
    if rec is not None:
        rec["anchors"]["stage3_manifest_sha256"] = sha(man.read_bytes())


def test_intact_chain_verifies(chain):
    root, rec, _ = chain
    content = I.verify_stage3(rec, root)
    assert set(content["outputs_sha256"]) == set(I.OUTPUTS)


def test_modified_input_with_unchanged_manifest_fails(chain):
    root, rec, _ = chain
    (root / I.STAGE3 / "primary/calendar.csv").write_bytes(b"stage3:primary/calendar.csv ")
    with pytest.raises(ProvenanceError, match="primary/calendar.csv does not match"):
        I.verify_stage3(rec, root)


def test_rewritten_manifest_with_modified_input_fails(chain):
    """The F-02 attack: change an input AND make the manifest agree with it. Self-consistent, but not registered."""
    root, rec, man = chain
    new = write(root, f"{I.STAGE3}/primary/universes.csv", b"edited universe")
    rewrite(man, lambda c: c["outputs_sha256"].update({"primary/universes.csv": new}))
    with pytest.raises(ProvenanceError, match="does not match the SHA-256 anchored in the registry"):
        I.verify_stage3(rec, root)


@pytest.mark.parametrize("edit", [lambda t: t + "\n", lambda t: t.replace('"built_at": "x"', '"built_at": "y"'),
                                  lambda t: t.replace("p" * 64, "q" * 64)])
def test_modified_manifest_with_unchanged_registry_hash_fails(chain, edit):
    root, rec, man = chain
    man.write_text(edit(man.read_text()))
    with pytest.raises(ProvenanceError, match="anchored in the registry"):
        I.verify_stage3(rec, root)


def test_missing_manifest_and_missing_anchor_fail(chain):
    root, rec, man = chain
    for bad in ({}, {"anchors": {}}, {"anchors": {"stage3_manifest_sha256": None}}, {"anchors": {"stage3_manifest_sha256": "abc"}}):
        with pytest.raises(ProvenanceError, match="unanchored"):
            I.verify_stage3({**rec, **bad} if bad else {"protocol_sha256": "p" * 64}, root)
    man.unlink()
    with pytest.raises(ProvenanceError, match="manifest is missing"):
        I.verify_stage3(rec, root)
    man.symlink_to(root / I.STAGE3 / "primary/calendar.csv")
    with pytest.raises(ProvenanceError, match="manifest is missing"):
        I.verify_stage3(rec, root)


def test_duplicate_manifest_entry_fails_even_when_the_registry_names_that_manifest(chain):
    root, rec, man = chain
    text = man.read_text()
    key = '"primary/calendar.csv": '
    dup = text.replace(f'   {key}', f'   {key}"{"0" * 64}",\n   {key}', 1)
    assert dup != text and dup.count(key) == 2 and json.loads(dup)                    # a plain json.loads keeps the last one
    rewrite(man, None, rec, raw=dup)
    with pytest.raises(ProvenanceError, match="duplicate manifest entry"):
        I.verify_stage3(rec, root)


@pytest.mark.parametrize("name", ["../../../outside.csv", "/etc/passwd", "primary/../../secret.csv", "research/extra.csv",
                                  "primary\\calendar.csv", ""])
def test_path_traversal_or_unexpected_path_fails(chain, tmp_path, name):
    root, rec, man = chain
    (tmp_path / "outside.csv").write_bytes(b"x")
    rewrite(man, lambda c: c["outputs_sha256"].update({name: sha(b"x")}), rec)
    with pytest.raises(ProvenanceError, match="not exactly the eight"):
        I.verify_stage3(rec, root)


def test_missing_manifest_entry_deleted_input_and_extra_file_fail(chain):
    root, rec, man = chain
    keep = man.read_text(), dict(rec["anchors"])
    rewrite(man, lambda c: c["outputs_sha256"].pop("oos/calendar.csv"), rec)
    with pytest.raises(ProvenanceError, match="not exactly the eight"):
        I.verify_stage3(rec, root)
    man.write_text(keep[0])
    rec["anchors"] = keep[1]
    (root / I.STAGE3 / "research/extra.csv").write_bytes(b"new")
    with pytest.raises(ProvenanceError, match="unexpected file"):
        I.verify_stage3(rec, root)
    (root / I.STAGE3 / "research/extra.csv").unlink()
    (root / I.STAGE3 / "research/panel.parquet.bak").symlink_to(root / I.STAGE3 / "research/panel.parquet")
    with pytest.raises(ProvenanceError, match="unexpected file"):
        I.verify_stage3(rec, root)
    (root / I.STAGE3 / "research/panel.parquet.bak").unlink()
    (root / I.STAGE3 / "research/panel.parquet").unlink()
    with pytest.raises(ProvenanceError, match="missing input"):
        I.verify_stage3(rec, root)


def test_an_input_replaced_by_a_symlink_to_identical_bytes_fails(chain, tmp_path):
    root, rec, _ = chain
    f = root / I.STAGE3 / "research/sessions.csv"
    (tmp_path / "elsewhere.csv").write_bytes(f.read_bytes())
    f.unlink()
    f.symlink_to(tmp_path / "elsewhere.csv")
    with pytest.raises(ProvenanceError, match="symlink"):
        I.verify_stage3(rec, root)


@pytest.mark.parametrize("attack, match", [
    (lambda r: (r / I.STAGE2_INPUTS["univ1"]).write_bytes(b"x"), "univ1_pit_universe.parquet does not match"),
    (lambda r: (r / I.STAGE2_INPUTS["id1_entities"]).unlink(), "missing input"),
    (lambda r: (r / I.RET_PREFIX / "ret1_1_2012.parquet").write_bytes(b"x"), "ret1_1_2012.parquet does not match"),
    (lambda r: (r / I.RET_PREFIX / "ret1_1_2013.parquet").write_bytes(b"x"), "dataset folder differs"),
    (lambda r: (r / "src/stage3/ladder.py").write_bytes(b"x"), "ladder.py does not match"),
    (lambda r: (r / I.STAGE3 / I.CHECK_FILES[0]).write_bytes(b'{"all_passed": true}'), "pre_run_checks_primary.json does not match"),
])
def test_stage2_inputs_code_and_check_files_are_part_of_the_chain(chain, attack, match):
    root, rec, _ = chain
    attack(root)
    with pytest.raises(ProvenanceError, match=match):
        I.verify_stage3(rec, root)


def test_registry_record_and_manifest_must_name_the_same_protocol_and_universe(chain):
    root, rec, man = chain
    with pytest.raises(ProvenanceError, match="protocol SHA-256 differs"):
        I.verify_stage3({**rec, "protocol_sha256": "z" * 64}, root)
    with pytest.raises(ProvenanceError, match="UNIV-1 SHA-256 differs"):
        I.verify_stage3({**rec, "universe_sha256": "z" * 64}, root)
    rewrite(man, lambda c: c["inputs_sha256"]["ret1_1_datasets"].update({"data/stage2/identity/id1_links.csv": "0" * 64}), rec)
    with pytest.raises(ProvenanceError, match="unexpected path"):
        I.verify_stage3(rec, root)


def test_the_real_chain_is_anchored_in_the_registry_and_verifies():
    """Read-only on the real repository. Stage 2 parquet files are checked when present (not in a bare clone)."""
    from src.registry import experiments
    rec = experiments.current()["S2-MOM-v1"]
    anchors = rec["anchors"]
    assert anchors["stage3_manifest_sha256"] == I.sha256(ROOT / I.STAGE3 / "manifest.json")
    assert set(anchors["stage3_check_files_sha256"]) == {f"{I.STAGE3}/{c}" for c in I.CHECK_FILES}
    full = (ROOT / I.RET_PREFIX).exists() and (ROOT / I.STAGE3 / "research/panel.parquet").exists()
    if not full:
        pytest.skip("external data not materialised (see scripts/release_archive.py)")
    content = I.verify_stage3()
    assert content["protocol_sha256"] == rec["protocol_sha256"]
