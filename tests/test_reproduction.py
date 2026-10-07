"""F-05: the reproduction entry point (scripts/reproduce_s2_mom_v1.py).

Part 1 checks the INDEPENDENT implementation against hand numbers and against the frozen code on
synthetic data - two implementations written separately must agree. Part 2 runs the real command in
a clean process and checks PASS, exit code, and that nothing in the repository changed.
"""

import ast
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.registry import experiments as reg
from src.stage3 import ladder as L, stats, step_e
from tests import test_s2mom_mutation_kills as G
from tests.test_s2mom_step_e import S as SCHEDULE, holdings
from tests.test_stage3_ladder import DAYS, ME, make_world

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reproduce_s2_mom_v1.py"
spec = importlib.util.spec_from_file_location("reproduce_s2_mom_v1_t", SCRIPT)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
HAVE_DATA = (ROOT / "data/stage2/datasets/ret1_1").exists() and (ROOT / "data/stage3/s2_mom_v1/research/panel.parquet").exists()


def frames_of(panel, days, delist):
    ents = sorted(panel["entity"].unique())
    return {"sessions": pd.DataFrame({"date": days}), "panel": panel,
            "identity": pd.DataFrame({"entity_id": ents, "delist_class": [delist.get(e, "OTHER") for e in ents]})}


def universe_frame(univ):
    return pd.concat([g.assign(key=k, t=t) for (k, t), g in univ.items()], ignore_index=True)[["t", "key", "entity", "rank"]]


# ====================================================================== 1. the independent implementation
def test_independent_ladder_gives_the_hand_computed_golden_numbers():
    """The same golden world as tests/test_s2mom_mutation_kills.py, through the SECOND implementation."""
    M = R.Matrices(frames_of(G.golden_panel(), G.DAYS, {"V1": "VOLUNTARY"}))
    univ = {(k, G.T): pd.DataFrame({"entity": v, "rank": np.arange(1.0, len(v) + 1)}) for k, v in G.UNIVERSE.items()}
    got, members = R.ladder(M, L.calendar(G.DAYS, G.T, G.T, G.T), universe_frame(univ))
    m = got.set_index("step")
    assert m["n_rankable"].to_dict() == {"A": 10, "B": 10, "C": 10, "D": 9} and (m["k"] == 3).all()
    assert members[("D", G.T, "W")] == ["V1", "E0", "E1"] and members[("A", G.T, "L")] == ["E7", "E8", "E9"]
    assert m.at["A", "W"] == pytest.approx((0.10 + G.E1_HOLD) / 3, abs=1e-12)
    assert m.at["B", "L"] == pytest.approx((-0.04 + 0.02 - 0.10) / 3, abs=1e-12)
    assert m.at["C", "L"] == pytest.approx((0.01 - 0.04 + G.D1_HOLD) / 3, abs=1e-12)
    assert m.at["D", "W"] == pytest.approx((0.0 + 0.015 + G.E1_HOLD) / 3, abs=1e-12)
    assert m.at["D", "BM"] == pytest.approx((G.D1_HOLD + 0.03 / 8 + G.E1_HOLD + 0.01 - 0.04 + 0.07) / 9, abs=1e-12)
    assert (m["WML"] - (m["W"] - m["L"])).abs().max() == 0


def test_independent_ladder_agrees_with_the_frozen_ladder_on_a_random_world():
    """16 months, 30 stocks, delistings, gap returns: two separately written implementations, same numbers."""
    wd = make_world()
    univ = L.universes(wd["univ"], wd["seg2ent"], wd["pool"], wd["cal"], wd["top"], ME["2014-06"])
    frozen, hold = L.run_ladder(L.wide(wd["panel"], wd["ents"], DAYS), wd["cal"], univ, L.STEP_SPECS)
    got, members = R.ladder(R.Matrices(frames_of(wd["panel"], DAYS, {})), wd["cal"], universe_frame(univ))
    m = got.merge(frozen, on=["t", "step"], suffixes=("", "_frozen"))
    assert len(m) == len(frozen) == 64 and (frozen["status"] == "OK").all()
    for col in ("W", "L", "BM", "WML"):
        assert np.abs(m[col] - m[col + "_frozen"]).max() < 1e-12, col
    assert (m["n_rankable"] == m["n_rankable_frozen"]).all() and (m["k"] == m["k_frozen"]).all()
    assert all(members[(s, t, p)] == hold[(s, t)][p] for (s, t) in hold for p in ("W", "L", "BM"))
    assert frozen.filter(like="delisting_return_applied").sum().sum() > 0        # the world does exercise §22


def test_independent_newey_west_holm_and_bh():
    x = np.random.default_rng(4).normal(0.2, 1.0, 80)
    for lag in (0, 3, 4):
        a, b = R.nw_test(x, lag), stats.mean_test(x, lag)
        assert a["mean"] == pytest.approx(b["mean"], abs=1e-14) and a["se"] == pytest.approx(b["se_nw"], abs=1e-14)
        assert a["p_two"] == pytest.approx(b["p_two_sided"], abs=1e-14) and a["p_one"] == pytest.approx(a["p_two"] / 2, abs=1e-14)
    assert R.nw_test(-x, 3)["p_one"] == pytest.approx(1 - R.nw_test(x, 3)["p_one"], abs=1e-14)      # the tail has a direction
    assert R.holm({"a": 0.01, "b": 0.04, "c": 0.03}) == pytest.approx({"a": 0.03, "c": 0.06, "b": 0.06})
    assert R.benjamini_hochberg({"a": 0.01, "b": 0.04, "c": 0.03}) == pytest.approx({"b": 0.04, "c": 0.04, "a": 0.03})
    assert R.holm({"a": 0.5, "b": 0.9}) == {"a": 1.0, "b": 1.0}


def test_independent_step_e_costs_agree_with_the_frozen_cost_ledger():
    months = [("2015-09-30", "2015-10-01", "2015-11-02", {"A": (0.5, 0.6), "B": (0.5, 0.4)}),
              ("2015-10-30", "2015-11-02", "2015-12-01", {"A": (0.5, 0.45), "C": (0.5, 0.55)}),        # last month of paid brokerage
              ("2015-11-30", "2015-12-01", "2016-01-01", {"A": (0.4, 0.4), "C": (0.3, 0.3), "D": (0.3, 0.3)})]
    rank = {"A": 10.0, "B": 250.0, "C": 700.0, "D": 200.0}          # both slippage bands, the boundary, and the >500 fallback
    h = pd.concat([holdings(months, p) for p in ("W", "L", "BM")])
    h = h.assign(liquidity_rank=h["entity"].map(rank))
    ranks = {(pd.Timestamp(t), e): r for t in ("2015-09-30", "2015-10-30", "2015-11-30") for e, r in rank.items()}
    mine = R.step_e_costs(h, SCHEDULE, ranks)
    for p in ("W", "L", "BM"):
        frozen = step_e.monthly_costs(step_e.cost_ledger(h, SCHEDULE, portfolio=p, ranks=step_e.rank_index(
            pd.DataFrame([{"selection_date": t, "entity_id": e, "rank": r} for (t, e), r in ranks.items()]))))
        for row in frozen.itertuples():
            for s in R.SLIPPAGE:
                assert mine[p][pd.Timestamp(row.t)][s] == pytest.approx(getattr(row, f"cost_fraction_{s}"), abs=1e-15)
    with pytest.raises(R.Fail, match="no UNIV-1 row"):
        R.step_e_costs(h, SCHEDULE, {})


def test_the_script_restates_the_protocol_constants_independently_and_they_agree():
    import src.stage3.protocol as P
    assert R.DELIST == P.DELIST_RETURN and R.NW_LAG == {"primary": P.NW_LAG["PRIMARY"], "oos": P.NW_LAG["OOS"]}
    assert {k: tuple(v.values()) for k, v in P.SLIPPAGE_BPS.items()} == R.SLIPPAGE and R.NOTIONAL == P.NOTIONAL_RS
    assert R.PINNED["protocol"][1] == P.PROTOCOL_SHA256 and R.PINNED["univ1"][1] == P.UNIV1_SHA256
    assert R.PINNED["schedule"][1] == step_e.SCHEDULE_SHA256 and R.TOL == 1e-9
    src = SCRIPT.read_text()
    assert "from src.stage3 import ladder" not in src and "experiment" not in [n.names[0].name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import)]


def test_the_script_cannot_register_or_overwrite_anything():
    """It calls no registry writer and no file writer except the optional report, which must be outside the repository."""
    tree = ast.parse(SCRIPT.read_text())
    calls = [getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(tree) if isinstance(n, ast.Call)]
    assert not {"amend", "record", "anchor", "log_trial", "write_md", "to_csv", "to_parquet", "write_bytes", "unlink", "mkdir",
                "rename", "urlopen", "request"} & set(calls)
    assert calls.count("write_text") == 1 and calls.count("replace") == 1 and "open" not in calls
    imports = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
              {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert imports <= {"hashlib", "json", "math", "os", "sys", "pathlib", "numpy", "pandas", "src"}      # no network module
    with pytest.raises(SystemExit, match="outside the repository"):
        R.main(ROOT / "no-such-root", verify_only=True, report=ROOT / "no-such-root" / "report.json")


def test_python_O_is_refused(monkeypatch):
    rec = reg.current()["S2-MOM-v1"]
    monkeypatch.setattr(R.integrity, "environment_report", lambda root: {"missing": [], "broken": {}, "optimized": True, "identical_to_tested": True, "mismatch": {}})
    with pytest.raises(R.Fail, match="python -O"):
        R.check_environment(ROOT, rec)
    monkeypatch.setattr(R.integrity, "environment_report", lambda root: {"missing": ["scipy"], "broken": {}, "optimized": False, "identical_to_tested": False, "mismatch": {}})
    with pytest.raises(R.Fail, match="missing dependencies"):
        R.check_environment(ROOT, rec)
    monkeypatch.setattr(R.integrity, "environment_report", lambda root: {"missing": [], "broken": {"scipy.stats": "ImportError: dlopen"}, "optimized": False,
                                                                         "identical_to_tested": False, "mismatch": {}})
    with pytest.raises(R.Fail, match="not loadable"):
        R.check_environment(ROOT, rec)
    with pytest.raises(R.Fail, match="not anchored"):
        R.check_environment(ROOT, {"anchors": {}})


# ====================================================================== 2. the real command, clean process
def _listing():
    keep = ("registry", "results/s2_mom_v1", "results/s2_mom_v1_step_e", "results/s2_mom_v1_c2", "data/stage3", "EXPERIMENT_REGISTRY.md")
    out = {}
    for k in keep:
        p = ROOT / k
        for f in ([p] if p.is_file() else sorted(p.rglob("*"))):
            if f.is_file() and "__pycache__" not in f.parts:
                out[f.relative_to(ROOT).as_posix()] = (f.stat().st_size, R.sha(f) if f.stat().st_size < 5_000_000 else f.stat().st_mtime_ns)
    return out


def test_reproduction_command_in_a_clean_process(tmp_path):
    """`python3 scripts/reproduce_s2_mom_v1.py` with an empty environment, from another directory, ignoring
    PYTHON* variables and the user site. With the external data: PASS and exit 0. Without it (bare clone):
    FAIL and exit 1 - never a partial pass. Either way the repository is left exactly as it was."""
    before = _listing()
    r = subprocess.run([sys.executable, "-E", "-s", "-B", str(SCRIPT), "--report", str(tmp_path / "report.json")], cwd=tmp_path,
                       env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "TRADING_LAB_NO_TRIAL_LOG": ""}, capture_output=True, text=True)
    assert _listing() == before, "the reproduction changed a registered artifact or the registry"
    assert not list(ROOT.glob("*.partial")) and (tmp_path / "report.json").exists()
    if HAVE_DATA:
        assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
        assert "REPRODUCTION OF S2-MOM-v1: PASS  [full reproduction]" in r.stdout and "FAIL" not in r.stdout
        assert all(f"PASS  {n} " in r.stdout for n in range(1, 9))
    else:
        assert r.returncode == 1 and "REPRODUCTION OF S2-MOM-v1: FAIL" in r.stdout and "NOT RUN 6" in r.stdout


def test_unknown_arguments_do_nothing():
    r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--register"], capture_output=True, text=True, env={**os.environ})
    assert r.returncode != 0 and "PASS" not in r.stdout and "Deterministic, read-only reproduction" in r.stderr


def test_frozen_loader_and_independent_loader_build_the_same_matrices_from_the_registered_inputs():
    """Read-only on the real Stage 3 inputs (no return of a portfolio is computed): the frozen loader's
    matrices and the reproduction's own matrices must describe the same panel, cell for cell."""
    if not HAVE_DATA:
        pytest.skip("external data not materialised")
    from src.registry import integrity
    from src.stage3 import data
    assert data.verify_provenance() == []
    inp = data.load_inputs("OOS")
    M = R.Matrices(integrity.load_stage3(ROOT))
    assert list(inp.w.ents) == list(M.ents) and list(inp.w.days) == list(M.days)
    assert np.array_equal(inp.w.present, M.present) and np.array_equal(inp.w.ok, M.ok) and np.array_equal(inp.w.bad, M.bad)
    seen = M.present & ~M.first
    assert np.allclose(np.expm1(inp.w.ln[seen]), M.rn[seen], atol=1e-12, rtol=0)
    assert np.allclose(np.expm1(inp.w.lr[M.ok]), M.rg[M.ok], atol=1e-12, rtol=0) and (inp.w.lr[~M.ok] == 0).all()
    assert np.array_equal(inp.delist_ret, M.delist) and inp.data_end <= inp.cutoff == pd.Timestamp("2026-09-30")
    assert len(inp.cal) == 56 and len(inp.univ) == 3 * 56


@pytest.mark.parametrize("state", ["PLANNED", "REGISTERED", "SUPERSEDED", "INVALID", "REQUIRES REVALIDATION"])
def test_reproduction_requires_the_registry_state_final(state):
    rec = reg.current()["S2-MOM-v1"]
    assert "state FINAL" in R.check_registry(ROOT, rec)
    with pytest.raises(R.Fail, match="not FINAL"):
        R.check_registry(ROOT, {**rec, "status": state})


def test_a_run_that_changes_the_repository_fails(monkeypatch, tmp_path, capsys):
    """Step 8: any file created, changed or removed between start and end is a FAIL."""
    (tmp_path / "a.txt").write_text("x")
    calls = []

    def fake(root):
        calls.append(1)
        return {"a.txt": (1, 1)} if len(calls) == 1 else {"a.txt": (1, 2), "new.txt": (1, 1)}
    monkeypatch.setattr(R, "fingerprint", fake)
    out = R.main(tmp_path, verify_only=True)
    step8 = [s for s in out["steps"] if s["step"] == 8][0]
    assert out["verdict"] == "FAIL" and step8["result"] == "FAIL" and "changed the repository" in step8["detail"] and "new.txt" in step8["detail"]


def test_fingerprint_sees_a_new_changed_or_removed_file(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    before = R.fingerprint(tmp_path)
    (tmp_path / "b.txt").write_text("y")
    assert set(R.fingerprint(tmp_path)) - set(before) == {"b.txt"}
    (tmp_path / "a.txt").write_text("xx")
    assert R.fingerprint(tmp_path)["a.txt"] != before["a.txt"]
    (tmp_path / "data/india").mkdir(parents=True)
    (tmp_path / "data/india/c.csv").write_text("collector")
    assert "data/india/c.csv" not in R.fingerprint(tmp_path)        # the scheduled collector's files are not ours
