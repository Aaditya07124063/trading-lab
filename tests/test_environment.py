"""F-06 / F-10: the pinned research environment, and the inventory of assert-based guards in frozen code."""

import ast
import json
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import pytest

from src.registry import experiments as reg
from src.registry import integrity as I

ROOT = Path(__file__).resolve().parents[1]
ENV = json.loads((ROOT / I.ENVIRONMENT).read_text())
RESEARCH_PATH = ["src/stage2", "src/stage3", "src/registry", "src/access.py", "src/config.py", "src/intraday/inference.py",
                 "scripts/run_s2_mom.py", "scripts/run_s2_mom_step_e.py", "scripts/run_s2_mom_c2.py", "scripts/build_stage2.py",
                 "scripts/build_stage3.py", "scripts/reproduce_s2_mom_v1.py", "scripts/release_archive.py"]
IMPORT_TO_DIST = {"numpy": "numpy", "pandas": "pandas", "scipy": "scipy", "pyarrow": "pyarrow"}
NETWORK_ONLY = {"requests", "urllib3"}         # used only by the raw-archive downloader, never by a registered calculation


def _files():
    for rel in RESEARCH_PATH:
        p = ROOT / rel
        yield from ([p] if p.is_file() else sorted(p.rglob("*.py")))


def third_party_imports():
    found = set()
    for p in _files():
        for n in ast.walk(ast.parse(p.read_text())):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                [n.module] if isinstance(n, ast.ImportFrom) and n.module and n.level == 0 else []
            found |= {m.split(".")[0] for m in mods}
    return {m for m in found if m not in sys.stdlib_module_names and m != "src"}


def test_every_runtime_import_of_the_research_code_path_is_pinned_exactly():
    used = third_party_imports() - NETWORK_ONLY
    assert used <= set(IMPORT_TO_DIST), f"unpinned import(s) in research code: {sorted(used - set(IMPORT_TO_DIST))}"
    assert {"numpy", "pandas", "scipy"} <= used
    assert "pyarrow" in ENV["packages"]                         # parquet engine: imported by pandas, not by name
    for dist in IMPORT_TO_DIST.values():
        v = ENV["packages"][dist]
        assert v and v[0].isdigit() and not any(c in v for c in "<>=~*, "), f"{dist} is not pinned to one version: {v!r}"
    for dist in ("pandas", "numpy", "scipy", "pyarrow"):        # every runtime requirement of the pinned packages is pinned too
        for req in metadata.requires(dist) or []:
            if "extra ==" in req:
                continue
            name = re.match(r"[A-Za-z0-9_.-]+", req).group(0).lower()
            assert name in {k.lower() for k in ENV["packages"]}, f"{dist} requires {name}, which is not pinned"


def test_lock_file_and_environment_specification_agree_and_are_anchored_in_the_registry():
    lock = dict(line.split("==") for line in (ROOT / "requirements-lock.txt").read_text().splitlines()
                if line and not line.startswith("#"))
    assert lock == {**ENV["packages"], **ENV["test_and_app_packages"]}
    anchors = reg.current()["S2-MOM-v1"]["anchors"]
    files = (I.ENVIRONMENT, "requirements-lock.txt", "release/s2_mom_v1/environment.yml", "release/s2_mom_v1/conda-osx-arm64.lock")
    assert anchors["environment_files_sha256_v2"] == {f: I.sha256(ROOT / f) for f in files}
    assert set(anchors["environment_files_sha256"]) == set(files[:2])            # v1 stays in the registry; it is superseded, not erased
    assert anchors["environment_observed_20261007"]["packages"] == ENV["packages"]
    assert "after the fact" in ENV["label"] and any("Bit-for-bit" in n for n in ENV["notes"])       # no stronger claim than was shown


def test_registry_environment_block_now_records_what_the_old_one_missed():
    env = reg.environment()
    assert {"scipy", "pyarrow", "numpy", "pandas"} <= set(env["packages"]) and env["platform"] and env["machine"]
    old = reg.current()["S2-MOM-v1"]["environment"]["packages"]
    assert "scipy" not in old and "pyarrow" not in old          # the historical gap (F-06) is documented, not rewritten


def test_environment_report_states_python_os_architecture_versions_missing_and_mismatches(monkeypatch):
    rep = I.environment_report()
    for key in ("python", "os", "architecture", "packages", "missing", "broken", "mismatch", "identical_to_tested", "optimized", "executable"):
        assert key in rep
    assert rep["packages"].keys() == ENV["packages"].keys() and rep["optimized"] is False
    real = metadata.version

    def fake(name):
        if name == "scipy":
            raise metadata.PackageNotFoundError(name)
        return "0.0.1" if name == "numpy" else real(name)
    monkeypatch.setattr(metadata, "version", fake)
    monkeypatch.setattr("platform.machine", lambda: "x86_64")
    bad = I.environment_report()
    assert bad["missing"] == ["scipy"] and bad["mismatch"]["numpy"] == {"tested": ENV["packages"]["numpy"], "installed": "0.0.1"}
    assert bad["mismatch"]["architecture"]["installed"] == "x86_64" and bad["identical_to_tested"] is False
    monkeypatch.setattr(metadata, "version", real)
    monkeypatch.setattr(I, "IMPORTS", ("numpy", "no_such_library_xyz"))
    broken = I.environment_report()
    assert list(broken["broken"]) == ["no_such_library_xyz"] and broken["identical_to_tested"] is False      # installed != loadable


def test_this_test_run_states_whether_it_is_the_tested_environment():
    """Report-only: a different environment is allowed, but it must be visible, never assumed equal."""
    rep = I.environment_report()
    assert rep["identical_to_tested"] == (not rep["missing"] and not rep["mismatch"])
    assert not rep["missing"], f"missing research dependencies: {rep['missing']}"


# ------------------------------------------------------------------ assert-based guards (F-10)
ASSERTS = {     # every `assert` in research-critical frozen code -> the explicit check that restates it outside `assert`
    "src/stage3/data.py": 7, "src/stage3/protocol.py": 1, "src/access.py": 1, "evaluate_orb_v1.py": 4, "src/stage3/ladder.py": 0, "src/stage3/experiment.py": 0,
    "src/stage3/stats.py": 0, "src/stage3/step_e.py": 0, "src/stage3/costs.py": 0, "scripts/run_s2_mom.py": 0,
    "scripts/run_s2_mom_step_e.py": 0, "scripts/run_s2_mom_c2.py": 0, "src/stage2/universe.py": 0, "src/stage2/returns.py": 0,
}


def test_inventory_of_assert_statements_in_frozen_research_code_is_complete():
    found = {f: sum(isinstance(n, ast.Assert) for n in ast.walk(ast.parse((ROOT / f).read_text()))) for f in ASSERTS}
    assert found == ASSERTS, "an assert-based guard appeared or disappeared in frozen code - restate it in src/registry/integrity.py"
    for f in ("src/registry/experiments.py", "src/registry/integrity.py", "scripts/reproduce_s2_mom_v1.py", "scripts/release_archive.py"):
        n = sum(isinstance(x, ast.Assert) for x in ast.walk(ast.parse((ROOT / f).read_text())))
        assert n == 0, f"{f}: the release tooling must not guard anything with assert"


def test_python_O_really_disables_the_frozen_asserts_and_the_explicit_checks_still_fire():
    """Demonstration, in a subprocess: under -O an assert is gone; ValidationError is not."""
    code = ("import sys; sys.path.insert(0, %r)\n"
            "assert False, 'asserts are active'\n"
            "from tests.test_failure_injection import synthetic_frames\n"
            "from src.registry import integrity as I\n"
            "f = synthetic_frames(); f['sessions'] = f['sessions'].iloc[:-1]\n"
            "try:\n    I.validate_stage3(f)\nexcept I.ValidationError as e:\n    print('EXPLICIT CHECK FIRED:', e)\n" % str(ROOT))
    r = subprocess.run([sys.executable, "-O", "-B", "-c", code], capture_output=True, text=True, cwd=ROOT,
                       env={"PATH": "/usr/bin:/bin", "TRADING_LAB_NO_TRIAL_LOG": "1"})
    assert r.returncode == 0, r.stderr[-1500:]
    assert "EXPLICIT CHECK FIRED" in r.stdout and "is not T*" in r.stdout
    r = subprocess.run([sys.executable, "-B", "-c", "assert False, 'asserts are active'"], capture_output=True, text=True)
    assert r.returncode != 0 and "asserts are active" in r.stderr


def test_cutoff_asserts_are_restated_as_explicit_checks(monkeypatch):
    """Each of the three checks is broken alone, so each must fire on its own."""
    import src.access
    import src.config
    assert I.validate_cutoffs() is True
    with monkeypatch.context() as m:
        m.setattr(src.config, "HOLDOUT_START", "2026-10-02")           # a gap between research cutoff and holdout
        with pytest.raises(I.ValidationError, match="not consecutive days"):
            I.validate_cutoffs()
    with monkeypatch.context() as m:
        m.setattr(src.access, "RESEARCH_CUTOFF", "2026-09-29")          # T* after the cutoff
        m.setattr(src.config, "HOLDOUT_START", "2026-09-30")
        with pytest.raises(I.ValidationError, match="T\\* lies after the research cutoff"):
            I.validate_cutoffs()
    with monkeypatch.context() as m:
        m.setattr(src.access, "RESEARCH_CUTOFF", "2026-10-15")          # a later cutoff than the registered T*
        m.setattr(src.config, "HOLDOUT_START", "2026-10-16")
        with pytest.raises(I.ValidationError, match="is not the registered T\\*"):
            I.validate_cutoffs()


def test_the_reproducibility_contract_is_conda_and_does_not_imply_pip():
    """The official environment is stated once, precisely, and the pip pins say they are not an installation contract."""
    c = ENV["contract"]
    assert c["official_environment"].startswith("Conda") and "NOT a supported" in c["pip"] and "1e-9" in c["numerical_acceptance"]
    lock = (ROOT / "requirements-lock.txt").read_text()
    assert "NOT THE INSTALLATION CONTRACT" in lock and "pip install -r" not in lock
    assert "NOT the research environment" in (ROOT / "requirements.txt").read_text()
    yml = (ROOT / "release/s2_mom_v1/environment.yml").read_text()
    explicit = (ROOT / "release/s2_mom_v1/conda-osx-arm64.lock").read_text()
    builds = {"python": "3.13.5-h2eb94d5_100_cp313", "numpy": "2.1.3-py313h7c57ca2_0", "pandas": "2.2.3-py313hcf29cfe_0",
              "scipy": "1.15.3-py313hd7edaaf_0", "pyarrow": "19.0.0-py313h313beb8_1", "libopenblas": "0.3.29-hea593b9_0"}
    for name, build in builds.items():
        assert f"- {name}={build.replace('-', '=', 1)}" in yml, name                 # exact build in the specification
        assert f"/{name}-{build}." in explicit, name                                  # and the same build in the explicit lock
        if name in ENV["packages"]:
            assert ENV["packages"][name] == build.split("-")[0]
    assert "@EXPLICIT" in explicit and "osx-arm64" in explicit
