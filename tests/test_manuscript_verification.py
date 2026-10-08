"""Phase 10: manuscript claims must stay supported by the registered artifacts (read-only; nothing is rebuilt)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Flags found on 2026-10-07 and reported to the researcher (docs/audit/MANUSCRIPT_VERIFICATION_REPORT.md).
# The manuscript was deliberately NOT edited. A new flag, or the disappearance of this list's reason, fails the test.
KNOWN_OPEN_FLAGS = set()          # N-02 fixed 2026-10-08: Table A5 now lists Supplements 2 and 3


def test_manuscript_is_supported_by_registered_artifacts(capsys):
    spec = importlib.util.spec_from_file_location("verify_manuscript", ROOT / "scripts" / "verify_manuscript.py")
    vm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vm)
    rows = vm.main()
    flags = {r["check"] for r in rows if r["status"] == "FLAG"}
    assert flags == KNOWN_OPEN_FLAGS, f"unexpected manuscript flags: {sorted(flags ^ KNOWN_OPEN_FLAGS)}"
    assert sum(r["status"] == "PASS" for r in rows) >= 59
    groups = {r["group"][0] for r in rows}
    assert groups == {"1", "2", "3", "4", "5"}
