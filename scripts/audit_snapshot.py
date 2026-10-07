"""Whole-repository hash snapshot and frozen-artifact verifier (remediation tooling, read-only on the repo).

    python3 scripts/audit_snapshot.py snapshot OUT.json     # hash every file, record git + environment
    python3 scripts/audit_snapshot.py verify SNAPSHOT.json  # exit 1 if anything outside the allow-list changed

verify is fail-closed: every file of the snapshot must be byte-identical unless its path matches
ALLOWED (files remediation may modify), APPEND_ONLY (old bytes must remain an exact prefix) or
EXTERNAL (written by the launchd intraday collector, not by remediation). New files are accepted
only under NEW_OK. Anything else is a violation.
"""

import fnmatch
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".claude"}
SKIP_FILES = {".DS_Store", ".coverage"}

# Existing files remediation is allowed to modify. Everything else in the snapshot is frozen.
ALLOWED = ["src/registry/experiments.py", "requirements.txt", "README.md", "REPRODUCIBILITY.md", "CHANGELOG.md",
           "RESEARCH_LOG.md", ".gitignore", "pytest.ini", "EXPERIMENT_REGISTRY.md", "tests/conftest.py",
           "scripts/audit_snapshot.py",
           "tests/test_access_boundary.py",       # only its allow-list gains the two new read-only verification tools
           # regenerated final reports; the originals are preserved byte-identical in docs/audit/forensic_20261007/
           "docs/audit/*.md", "docs/audit/*.csv", "docs/audit/*.json"]
APPEND_ONLY = ["registry/experiments.jsonl", "registry/trials.jsonl"]
EXTERNAL = ["data/india/*", "data/raw/collection_log.jsonl", "data/raw/manifest.jsonl", "logs/*",
            "data/raw/yahoo/*", "data/**/backups/*"]
NEW_OK = ["docs/audit/*", "tests/*", "scripts/*", "src/registry/*", "requirements*.txt", "release/*"] + EXTERNAL


def _match(rel, patterns):
    return any(fnmatch.fnmatch(rel, p) for p in patterns)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files():
    for p in sorted(BASE.rglob("*")):
        if p.is_file() and not p.is_symlink() and not (set(p.relative_to(BASE).parts) & SKIP_DIRS) \
                and p.name not in SKIP_FILES:
            yield p.relative_to(BASE).as_posix(), p


def _run(*cmd):
    return subprocess.run(cmd, cwd=BASE, text=True, capture_output=True).stdout


def snapshot(out):
    out = Path(out)
    if out.exists():
        raise SystemExit(f"{out} exists - a snapshot is never overwritten")
    snap = {
        "taken_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git": {"head": _run("git", "rev-parse", "HEAD").strip(), "branch": _run("git", "branch", "--show-current").strip(),
                "status_porcelain": _run("git", "status", "--porcelain").splitlines()},
        "environment": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
                        "machine": platform.machine(),
                        "pip_freeze": _run(sys.executable, "-m", "pip", "freeze").splitlines()},
        "allowed_to_modify": ALLOWED, "append_only": APPEND_ONLY, "external_writers": EXTERNAL, "new_files_ok": NEW_OK,
        "files": {rel: {"sha256": sha256(p), "bytes": p.stat().st_size} for rel, p in files()},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, indent=1) + "\n")
    print(f"{len(snap['files'])} files hashed -> {out}")


def verify(snap_path):
    snap = json.loads(Path(snap_path).read_text())
    old, now = snap["files"], dict(files())
    self_rel = Path(snap_path).resolve().relative_to(BASE).as_posix() if BASE in Path(snap_path).resolve().parents else None
    violations, allowed, external, appended = [], [], [], []
    for rel, meta in old.items():
        p = now.get(rel)
        same = p is not None and sha256(p) == meta["sha256"]
        if same:
            continue
        if _match(rel, APPEND_ONLY):
            if p is None or sha256_prefix(p, meta["bytes"]) != meta["sha256"]:
                violations.append(f"APPEND-ONLY FILE REWRITTEN OR MISSING: {rel}")
            else:
                appended.append(rel)
        elif _match(rel, EXTERNAL):
            external.append(rel)
        elif _match(rel, ALLOWED) and p is not None:
            allowed.append(rel)
        else:
            violations.append(f"{'MISSING' if p is None else 'CHANGED'}: {rel}")
    new = [r for r in now if r not in old and r != self_rel]
    violations += [f"UNEXPECTED NEW FILE: {r}" for r in new if not _match(r, NEW_OK)]
    frozen = sum(1 for r in old if not _match(r, ALLOWED + APPEND_ONLY + EXTERNAL))
    print(f"frozen files byte-identical: {frozen - sum(v.startswith(('MISSING', 'CHANGED')) for v in violations)}/{frozen}")
    print(f"modified (allow-list): {sorted(allowed)}")
    print(f"appended (append-only, old bytes intact): {appended}")
    print(f"changed by external collector: {len(external)} file(s)")
    print(f"new files: {len(new)}")
    for v in violations:
        print("VIOLATION", v)
    print("FROZEN-HASH VERIFICATION:", "FAIL" if violations else "PASS")
    return 1 if violations else 0


def sha256_prefix(path, n):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read(n)).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("snapshot", "verify"):
        raise SystemExit(__doc__)
    sys.exit(snapshot(sys.argv[2]) if sys.argv[1] == "snapshot" else verify(sys.argv[2]))
