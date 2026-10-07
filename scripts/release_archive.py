"""Immutable external archive for the S2-MOM-v1 data that is too large for Git (F-01).

The files below stay git-ignored, but they are no longer "one copy on one laptop": a committed
manifest lists every file with its SHA-256, and a deterministic tar (sorted names, fixed
metadata) has one reproducible SHA-256, so any copy of the archive can be checked anywhere.

    python3 scripts/release_archive.py manifest          # hash the files, write the manifest (refuses to change one)
    python3 scripts/release_archive.py verify            # working-tree files == manifest (fail closed)
    python3 scripts/release_archive.py pack DEST.tar     # write the archive (tmp + fsync + rename), verify its hash
    python3 scripts/release_archive.py materialize A.tar # verify the archive, then restore missing files

materialize never overwrites: a file that exists with other bytes stops the run.
"""

import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MANIFEST = "release/s2_mom_v1/ARCHIVE_MANIFEST.json"
EXTERNAL = {     # path -> provenance
    "data/raw/nse_archive": "raw NSE files (bhavcopies, corporate actions, lists) fetched by src/stage2/archive.py; "
                            "per-file hashes also in data/stage2/raw_manifest.jsonl (git-tracked)",
    "data/stage2/datasets": "PANEL-1.1 / RET-1 / RET-1.1 parquet datasets built by scripts/build_stage2.py from the raw "
                            "archive; hashes also in data/stage2/*/…_manifest.json (git-tracked)",
    "data/stage3/s2_mom_v1/research/panel.parquet": "Stage 3 daily study panel built by scripts/build_stage3.py; hash also "
                                                    "in data/stage3/s2_mom_v1/manifest.json (anchored in the registry)",
}
SKIP = {".DS_Store"}


class ArchiveError(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def listing(root):
    """Sorted relative paths of every external file. A symlink is refused (it could point anywhere)."""
    out = []
    for top in EXTERNAL:
        p = root / top
        if not p.exists():
            raise ArchiveError(f"missing: {top}")
        for f in ([p] if p.is_file() else sorted(p.rglob("*"))):
            if f.is_symlink():
                raise ArchiveError(f"symlink refused: {f.relative_to(root)}")
            if f.is_file() and f.name not in SKIP:
                out.append(f.relative_to(root).as_posix())
    return sorted(out)


class _Hasher:
    def __init__(self):
        self.h, self.n = hashlib.sha256(), 0

    def write(self, b):
        self.h.update(b)
        self.n += len(b)
        return len(b)


def write_tar(root, names, sink):
    """Deterministic tar: sorted names, mtime 0, no owner, mode 0644 - the bytes depend on the files only."""
    with tarfile.open(fileobj=sink, mode="w|", format=tarfile.PAX_FORMAT) as tar:
        for rel in sorted(names):
            info = tarfile.TarInfo(rel)
            info.size, info.mtime, info.mode = (root / rel).stat().st_size, 0, 0o644
            with open(root / rel, "rb") as fh:
                tar.addfile(info, fh)


def build_manifest(root=BASE):
    names = listing(root)
    files = {rel: {"sha256": sha256(root / rel), "bytes": (root / rel).stat().st_size} for rel in names}
    sink = _Hasher()
    write_tar(root, names, sink)
    content = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {"archive_id": f"s2-mom-v1-data-{content[:16]}", "files_listing_sha256": content,
            "tar_sha256": sink.h.hexdigest(), "tar_bytes": sink.n, "tar_format": "deterministic PAX tar, see scripts/release_archive.py",
            "provenance": EXTERNAL, "n_files": len(files), "files": files,
            "retrieval": "copy <archive_id>.tar from the archive location recorded in docs/audit/REPRODUCTION_REPORT.md, then "
                         "python3 scripts/release_archive.py materialize <archive_id>.tar"}


def load_manifest(root=BASE):
    f = root / MANIFEST
    if not f.exists():
        raise ArchiveError(f"{MANIFEST} is missing")
    return json.loads(f.read_text())


def cmd_manifest(root=BASE):
    man, f = build_manifest(root), root / MANIFEST
    if f.exists():
        if json.loads(f.read_text()) != man:
            raise ArchiveError("the external files differ from the committed archive manifest - not rewritten")
        return man
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(man, indent=1) + "\n")
    os.replace(tmp, f)
    return man


def verify(root=BASE):
    """Every file of the manifest is present and identical, and nothing else sits in the archived folders."""
    man = load_manifest(root)
    bad = [f"UNEXPECTED {r}" for r in listing(root) if r not in man["files"]]
    for rel, meta in man["files"].items():
        p = root / rel
        if not p.is_file():
            bad.append(f"MISSING {rel}")
        elif sha256(p) != meta["sha256"]:
            bad.append(f"CHANGED {rel}")
    if hashlib.sha256(json.dumps(man["files"], sort_keys=True).encode()).hexdigest() != man["files_listing_sha256"]:
        bad.append("manifest file listing does not match its own SHA-256")
    if bad:
        raise ArchiveError(f"{len(bad)} problem(s): " + "; ".join(bad[:10]))
    return man


def pack(dest, root=BASE):
    man, dest = verify(root), Path(dest)
    if dest.exists():
        raise ArchiveError(f"{dest} exists - an archive is never overwritten")
    tmp = dest.with_name(dest.name + ".partial")
    with open(tmp, "wb") as fh:
        write_tar(root, man["files"], fh)
        fh.flush()
        os.fsync(fh.fileno())
    if sha256(tmp) != man["tar_sha256"]:
        tmp.unlink()
        raise ArchiveError("the packed archive does not have the manifest SHA-256")
    os.replace(tmp, dest)
    return man["tar_sha256"]


def materialize(archive, root=BASE):
    man = load_manifest(root)
    if sha256(archive) != man["tar_sha256"]:
        raise ArchiveError("archive SHA-256 does not match the manifest - refused")
    restored = 0
    with tarfile.open(archive, mode="r|") as tar:
        for info in tar:
            rel = info.name
            if rel not in man["files"] or not info.isfile():        # also refuses absolute paths and '..'
                raise ArchiveError(f"unexpected archive member: {rel!r}")
            target = root / rel
            if target.exists():
                if sha256(target) != man["files"][rel]["sha256"]:
                    raise ArchiveError(f"{rel} exists with different bytes - not overwritten")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp, h = target.with_name(target.name + ".partial"), hashlib.sha256()
            with open(tmp, "wb") as out:
                src = tar.extractfile(info)
                for block in iter(lambda: src.read(1 << 20), b""):
                    h.update(block)
                    out.write(block)
            if h.hexdigest() != man["files"][rel]["sha256"]:
                tmp.unlink()
                raise ArchiveError(f"{rel}: bytes in the archive do not match the manifest")
            os.replace(tmp, target)
            restored += 1
    verify(root)
    return restored


if __name__ == "__main__":
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    try:
        if cmd == "manifest":
            m = cmd_manifest()
            print(f"{m['archive_id']}  files {m['n_files']}  tar sha256 {m['tar_sha256']}  bytes {m['tar_bytes']}")
        elif cmd == "verify":
            m = verify()
            print(f"PASS {m['archive_id']}: {m['n_files']} files identical")
        elif cmd == "pack" and len(args) == 1:
            print("packed, sha256", pack(args[0]))
        elif cmd == "materialize" and len(args) == 1:
            print("restored", materialize(args[0]), "file(s); verified")
        else:
            raise SystemExit(__doc__)
    except ArchiveError as e:
        raise SystemExit(f"FAIL: {e}")
