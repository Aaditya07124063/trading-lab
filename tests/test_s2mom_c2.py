"""S2-MOM-v1 C2 runner: made-up series only. No registered result file is read for a calculation here."""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from src.stage3.protocol import NotReady
from src.stage3.stats import mean_test

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("run_s2_mom_c2", ROOT / "scripts/run_s2_mom_c2.py")
c2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(c2)


def made_up(seed=1):
    """Monthly and delta frames for both samples, plus the 'registered' JSONs they imply."""
    rng = np.random.default_rng(seed)
    monthly, delta = {}, {}
    for name, start, n in (("primary", "2012-07", 114), ("confirmation", "2022-01", 56)):
        months = pd.period_range(start, periods=n, freq="M").astype(str)
        rows = []
        for s in c2.STEPS:
            w, l, bm = rng.normal(0.015, 0.05, n), rng.normal(0.008, 0.07, n), rng.normal(0.011, 0.06, n)
            rows.append(pd.DataFrame({"holding_month": months, "step": s, "status": "OK", "W": w, "L": l, "BM": bm, "WML": w - l}))
        m = pd.concat(rows, ignore_index=True)
        p = m.pivot(index="holding_month", columns="step", values="WML")
        monthly[name], delta[name] = m, pd.DataFrame({"holding_month": months, "delta": ((p["A"] - p["D"]) * 100).to_numpy()})
    b = c2.block(c2.wide(monthly["primary"], 114), *c2.BLOCKS["primary"])
    registered = {"H1": b["delta"], "step_differences_pct": b["step_differences_pct"], "ladder": b["ladder"]}
    step_e = {"samples": {"primary": {"H3": {"p_one_sided": 0.02}, "H4": {"p_one_sided": 0.003}}}}
    return monthly, delta, registered, step_e


def test_holm_and_bh_known_values():
    p = {"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005}
    assert c2.holm(p) == pytest.approx({"d": 0.02, "a": 0.03, "c": 0.06, "b": 0.06})
    assert c2.bh(p) == pytest.approx({"d": 0.02, "a": 0.02, "c": 0.04, "b": 0.04})
    assert c2.holm({"x": 0.9, "y": 0.8}) == {"y": 1.0, "x": 1.0}                         # capped at 1, monotone


def test_analysis_matches_hand_calculation():
    monthly, delta, registered, step_e = made_up()
    res = c2.analyse(monthly, delta, registered, step_e)
    m = monthly["primary"].pivot(index="holding_month", columns="step", values=["W", "WML"]) * 100
    h = (m[("W", "A")] - m[("W", "D")]).to_numpy()
    ref = mean_test(h, 4)
    assert res["H2d"]["primary"]["t"] == pytest.approx(ref["t"]) and res["H2d"]["primary"]["p_one_sided"] == pytest.approx(norm.sf(ref["t"]))
    assert res["H2d"]["confirmation"]["lag"] == 3 and res["H2d"]["confirmation"]["n"] == 56
    assert {k: v["n"] for k, v in res["blocks"].items()} == {"primary": 114, "confirmation": 56, "primary_half_1": 57,
                                                             "primary_half_2": 57, "pooled": 170}
    assert res["blocks"]["primary_half_1"]["months"] == ["2012-07", "2017-03"] and res["blocks"]["primary_half_2"]["months"] == ["2017-04", "2021-12"]
    assert {k: v["lag"] for k, v in res["blocks"].items()} == {"primary": 4, "confirmation": 3, "primary_half_1": 3, "primary_half_2": 3, "pooled": 4}
    half = (m[("WML", "A")] - m[("WML", "D")]).to_numpy()[57:]
    assert res["blocks"]["primary_half_2"]["delta"]["mean"] == pytest.approx(half.mean())
    assert res["blocks"]["primary_half_2"]["delta"]["se_nw"] == pytest.approx(mean_test(half, 3)["se_nw"])   # own months only
    x = m[("WML", "D")]
    d = res["blocks"]["primary"]["ladder"]["D"]["WML"]
    n, c = len(x), x - x.mean()
    g1 = np.sqrt(n * (n - 1)) / (n - 2) * (c ** 3).mean() / (c ** 2).mean() ** 1.5
    assert d["skewness"] == pytest.approx(g1) and d["worst_month_pct"] == x.min() and d["worst_month"] == x.idxmin()
    assert res["holm"]["m"] == 4 and res["benjamini_hochberg"]["m"] == 6 and "H5" in res["benjamini_hochberg"]["note"]
    assert res["holm"]["H2d"]["sided"] == "one" and res["holm"]["H2a"]["sided"] == "two"
    assert res["holm"]["H2a"]["p"] == registered["step_differences_pct"]["A-B"]["p_two_sided"]            # registered p, not recomputed
    assert json.dumps(res, default=str) == json.dumps(c2.analyse(*made_up()), default=str)               # deterministic


def test_confirmation_status_rule():
    assert c2.confirmation_status(0.5, {"mean": -0.1, "p_one_sided": 0.9}) == "NOT CONFIRMED"
    assert c2.confirmation_status(0.5, {"mean": 0.1, "p_one_sided": 0.2}) == "CONSISTENT, NOT CONFIRMED"
    assert c2.confirmation_status(0.5, {"mean": 0.1, "p_one_sided": 0.01}) == "CONFIRMED"


def test_fails_closed_on_bad_series():
    monthly, delta, registered, step_e = made_up()
    bad = {**delta, "primary": delta["primary"].assign(delta=delta["primary"]["delta"] + 1e-6)}
    with pytest.raises(NotReady, match="registered delta"):
        c2.analyse(monthly, bad, registered, step_e)
    for change in (lambda m: m.assign(W=m["W"].where(m.index != 3)), lambda m: m.assign(status="X"), lambda m: m.iloc[:-1],
                   lambda m: m[m["step"] != "C"]):
        with pytest.raises(NotReady):
            c2.analyse({**monthly, "primary": change(monthly["primary"])}, delta, registered, step_e)
    wrong = json.loads(json.dumps(registered, default=str))
    wrong["ladder"]["D"]["WML"]["mean_pct"] += 1e-6
    with pytest.raises(NotReady, match="reproduce"):
        c2.analyse(monthly, delta, wrong, step_e)


def test_run_checks_hashes_first_and_runs_once(tmp_path):
    monthly, delta, registered, step_e = made_up()
    files = {"primary_monthly": monthly["primary"], "confirmation_monthly": monthly["confirmation"],
             "primary_delta": delta["primary"], "confirmation_delta": delta["confirmation"]}
    inputs = {}
    for k, obj in {**files, "primary_results": registered, "step_e_results": step_e}.items():
        f = tmp_path / (k + (".csv" if k in files else ".json"))
        obj.to_csv(f, index=False) if k in files else f.write_text(json.dumps(obj, default=str))
        inputs[k] = (f.name, hashlib.sha256(f.read_bytes()).hexdigest())
    (tmp_path / "spec.md").write_text("spec")
    spec = ("spec.md", hashlib.sha256(b"spec").hexdigest())
    out = tmp_path / "c2"
    for broken in ({**inputs, "step_e_results": (inputs["step_e_results"][0], "0" * 64)},):
        with pytest.raises(NotReady, match="SHA-256"):
            c2.run(tmp_path, broken, out, spec)
    with pytest.raises(NotReady, match="SHA-256"):
        c2.run(tmp_path, inputs, out, ("spec.md", "0" * 64))
    assert not out.exists()
    sha = c2.run(tmp_path, inputs, out, spec)
    assert [p.name for p in out.iterdir()] == ["c2_results.json"] and sha == hashlib.sha256((out / "c2_results.json").read_bytes()).hexdigest()
    saved = json.loads((out / "c2_results.json").read_text())
    assert saved["spec_sha256"] == spec[1] and "executed late" in saved["statement"] and "not confirmatory" in saved["statement"]
    with pytest.raises(NotReady, match="already exists"):
        c2.run(tmp_path, inputs, out, spec)


def test_runner_is_isolated_from_the_backtest_and_pins_the_frozen_inputs():
    tree = ast.parse((ROOT / "scripts/run_s2_mom_c2.py").read_text())
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module.startswith("src")}
    assert imported == {"src.config", "src.registry", "src.stage3.protocol", "src.stage3.stats"}     # no backtest, ladder, data or step E code
    assert not any("holdings" in rel or "univ1" in rel or "ret1" in rel for rel, _ in c2.INPUTS.values())
    assert hashlib.sha256((ROOT / c2.SPEC[0]).read_bytes()).hexdigest() == c2.SPEC[1]
    assert c2.OUT == ROOT / "results" / "s2_mom_v1_c2" and len(c2.INPUTS) == 6


def test_registered_c2_output_is_intact():
    """Post-execution integrity. The file is hashed only; nothing is recomputed."""
    sha = hashlib.sha256((c2.OUT / "c2_results.json").read_bytes()).hexdigest()
    assert [p.name for p in c2.OUT.iterdir()] == ["c2_results.json"]
    records = [json.loads(line) for line in (ROOT / "registry" / "experiments.jsonl").read_text().splitlines()]
    runs = [r["provenance"]["c2_run"] for r in records if "c2_run" in (r.get("provenance") or {})]
    assert runs and all(r == runs[0] for r in runs)                                  # one execution
    assert runs[0]["results_sha256"] == sha and runs[0]["spec_sha256"] == c2.SPEC[1] and runs[0]["code_sha256"] == c2.code_sha()
    trials = [json.loads(line) for line in (ROOT / "registry" / "trials.jsonl").read_text().splitlines()]
    assert [t["headline"] for t in trials if t["source"] == "scripts/run_s2_mom_c2.py"] == [{"results_sha256": sha}]
