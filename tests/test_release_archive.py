"""External data archive (F-01): deterministic, content-addressed, fail-closed. Synthetic files only."""

import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_archive", ROOT / "scripts" / "release_archive.py")
RA = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RA)


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "repo"
    for rel, body in {"data/raw/nse_archive/a/x.zip": b"raw-x", "data/raw/nse_archive/y.json": b"raw-y",
                      "data/stage2/datasets/ret1_1/r.parquet": b"ret", "data/stage3/s2_mom_v1/research/panel.parquet": b"panel"}.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(body)
    RA.cmd_manifest(root)
    return root


def test_manifest_lists_every_file_with_its_hash_and_is_deterministic(tree):
    man = RA.load_manifest(tree)
    assert man["n_files"] == 4 and set(man["files"]) == set(RA.listing(tree))
    assert all(len(m["sha256"]) == 64 for m in man["files"].values())
    assert RA.build_manifest(tree) == man                      # same files -> same archive id and tar hash
    assert man["archive_id"].startswith("s2-mom-v1-data-") and set(man["provenance"]) == set(RA.EXTERNAL)
    assert RA.verify(tree)["tar_sha256"] == man["tar_sha256"]


def test_pack_is_reproducible_and_materialize_restores_a_lost_file(tree, tmp_path):
    a, b = tmp_path / "a.tar", tmp_path / "b.tar"
    assert RA.pack(a, tree) == RA.pack(b, tree) == RA.sha256(a) == RA.sha256(b)
    lost = tree / "data/stage2/datasets/ret1_1/r.parquet"
    lost.unlink()
    with pytest.raises(RA.ArchiveError, match="MISSING"):
        RA.verify(tree)
    assert RA.materialize(a, tree) == 1 and lost.read_bytes() == b"ret"
    with pytest.raises(RA.ArchiveError, match="never overwritten"):
        RA.pack(a, tree)


@pytest.mark.parametrize("attack, message", [
    (lambda r: (r / "data/raw/nse_archive/y.json").write_bytes(b"raw-Y"), "CHANGED"),
    (lambda r: (r / "data/raw/nse_archive/y.json").unlink(), "MISSING"),
    (lambda r: (r / "data/raw/nse_archive/extra.zip").write_bytes(b"new"), "UNEXPECTED"),
    (lambda r: (r / "data/stage3/s2_mom_v1/research/panel.parquet").write_bytes(b"panel "), "CHANGED"),
])
def test_verify_fails_closed_on_any_change(tree, attack, message):
    attack(tree)
    with pytest.raises(RA.ArchiveError, match=message):
        RA.verify(tree)
    with pytest.raises(RA.ArchiveError):                       # and the committed manifest is never silently rewritten
        RA.cmd_manifest(tree)


def test_a_rewritten_manifest_listing_is_detected(tree):
    f = tree / RA.MANIFEST
    man = json.loads(f.read_text())
    (tree / "data/raw/nse_archive/y.json").write_bytes(b"evil")
    man["files"]["data/raw/nse_archive/y.json"]["sha256"] = RA.sha256(tree / "data/raw/nse_archive/y.json")
    f.write_text(json.dumps(man))
    with pytest.raises(RA.ArchiveError, match="own SHA-256"):
        RA.verify(tree)


def test_materialize_refuses_a_wrong_archive_and_never_overwrites(tree, tmp_path):
    good = tmp_path / "good.tar"
    RA.pack(good, tree)
    bad = tmp_path / "bad.tar"
    bad.write_bytes(good.read_bytes()[:-1] + b"\x01")
    with pytest.raises(RA.ArchiveError, match="does not match the manifest"):
        RA.materialize(bad, tree)
    (tree / "data/raw/nse_archive/y.json").write_bytes(b"local edit")
    with pytest.raises(RA.ArchiveError, match="not overwritten"):
        RA.materialize(good, tree)
    assert (tree / "data/raw/nse_archive/y.json").read_bytes() == b"local edit"


def test_materialize_refuses_path_traversal_and_unknown_members(tree, tmp_path):
    evil = tmp_path / "evil.tar"
    with tarfile.open(evil, "w") as tar:
        info = tarfile.TarInfo("../outside.txt")
        info.size = 4
        tar.addfile(info, io.BytesIO(b"evil"))
    man = json.loads((tree / RA.MANIFEST).read_text())
    man["tar_sha256"] = RA.sha256(evil)                         # even with a manifest that names this archive
    (tree / RA.MANIFEST).write_text(json.dumps(man))
    with pytest.raises(RA.ArchiveError, match="unexpected archive member"):
        RA.materialize(evil, tree)
    assert not (tmp_path / "outside.txt").exists()


def test_symlinks_are_refused(tree, tmp_path):
    (tree / "data/raw/nse_archive/link.zip").symlink_to(tmp_path)
    with pytest.raises(RA.ArchiveError, match="symlink"):
        RA.listing(tree)


def test_real_archive_manifest_matches_the_working_tree_when_data_is_present():
    """Hash-only check of the committed manifest; skipped in a clone without the external data."""
    if not (ROOT / RA.MANIFEST).exists() or not (ROOT / "data/stage2/datasets").exists():
        pytest.skip("external data or manifest not present")
    man = RA.load_manifest(ROOT)
    assert sorted(man["files"]) == RA.listing(ROOT)
    panel = "data/stage3/s2_mom_v1/research/panel.parquet"
    stage3 = json.loads((ROOT / "data/stage3/s2_mom_v1/manifest.json").read_text())["content"]["outputs_sha256"]
    assert man["files"][panel]["sha256"] == stage3["research/panel.parquet"]
    ret = json.loads((ROOT / "data/stage2/returns/ret1_1_manifest.json").read_text())["datasets"]
    assert all(man["files"][rel]["sha256"] == h for rel, h in ret.items())      # two independent records agree
