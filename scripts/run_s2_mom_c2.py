"""S2-MOM-v1 C2 runner: seven pre-registered analyses executed late, from the SAVED registered result files.

    python3 scripts/run_s2_mom_c2.py execute      # needs the reviewer's explicit authorisation; runs once

Specification: docs/research/s2_mom_v1_c2_analysis_spec.md (hash-checked here). H2d, Holm, Benjamini-Hochberg,
the two halves of the primary sample, the pooled 170 months (gross A-D and delta only), skewness, worst month.
Fail-closed:
  - reads exactly the six registered inputs below, read-only, after checking the SHA-256 of all six;
  - never calls the backtest, ladder, data or step E code; the only registered code reused is stats.mean_test;
  - refuses if its output directory already exists; writes one file into its own new directory;
  - registers the run only after the output file is complete and hashed.
Results go to the file only - nothing is printed.
"""

import hashlib
import json
import platform
import sys
from importlib import metadata
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, skew

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import BASE_DIR                                              # noqa: E402
from src.registry import experiments                                         # noqa: E402
from src.stage3.protocol import ALPHA, PROTOCOL_ID, NotReady, verify_protocol   # noqa: E402
from src.stage3.stats import mean_test                                       # noqa: E402

SPEC = ("docs/research/s2_mom_v1_c2_analysis_spec.md", "78864a4f6fddad86a7b3273e8d8c1e7ab818ed318deb0fdb75cc99e2c5a0c0aa")
INPUTS = {   # specification section 3: exactly these six
    "primary_monthly": ("results/s2_mom_v1/primary_monthly.csv", "f7c8d3ab5a0ef7a08b6a0ca8a12bf26a1f901006c21637cf7886e297b97bb372"),
    "confirmation_monthly": ("results/s2_mom_v1/confirmation_monthly.csv", "4d88f385375ad681f85be739b292097e2e898acb6acb71013230c67415a43ce3"),
    "primary_delta": ("results/s2_mom_v1/primary_delta.csv", "2efa04351a6bca10fbf1e6a96d6c5240fb0f2570420185250750b77d5c4fecc9"),
    "confirmation_delta": ("results/s2_mom_v1/confirmation_delta.csv", "a462455acb343910a02206ab6af50582eaedef20b0ed6cec81a88f73cbc58b75"),
    "primary_results": ("results/s2_mom_v1/primary_results.json", "fe7e95ba97482d6d53faba543d860e4f0d1e50cfa0312d669e910346d41ef857"),
    "step_e_results": ("results/s2_mom_v1_step_e/step_e_results.json", "675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0"),
}
MONTHS = {"primary": 114, "confirmation": 56}
BLOCKS = {   # specification section 5: (first holding month, last holding month, Newey-West lag)
    "primary": ("2012-07", "2021-12", 4), "confirmation": ("2022-01", "2026-08", 3),
    "primary_half_1": ("2012-07", "2017-03", 3), "primary_half_2": ("2017-04", "2021-12", 3),
    "pooled": ("2012-07", "2026-08", 4),
}
STEPS, PORTFOLIOS, DIFFS = ("A", "B", "C", "D"), ("W", "L", "BM", "WML"), (("A", "B"), ("B", "C"), ("C", "D"))
OUT = BASE_DIR / "results" / "s2_mom_v1_c2"
CODE = ("scripts/run_s2_mom_c2.py",)
TOL = 1e-9
STATEMENT = ("These analyses were pre-registered in the frozen protocol S2-MOM-v1 but executed late, after the primary, "
             "sensitivity, confirmation and step E results were already known. They are not blind and not confirmatory. "
             "No backtest was rerun: every figure is computed from the saved registered result files. The pooled block "
             "is descriptive only (gross A-D and delta; no step E figure). Steps A-C are biased by construction. "
             "The Benjamini-Hochberg family omits H5, which was pre-registered and not executed.")
BH_NOTE = "six executed secondary tests, primary sample; H5 was pre-registered and not executed (m would have been 7)"


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_sha():
    return hashlib.sha256(b"".join((BASE_DIR / f).read_bytes() for f in CODE)).hexdigest()


def holm(p):
    """Holm step-down adjusted p-values of {name: p}."""
    out, running = {}, 0.0
    for j, (k, v) in enumerate(sorted(p.items(), key=lambda kv: kv[1])):
        running = max(running, min(1.0, (len(p) - j) * v))
        out[k] = running
    return out


def bh(p):
    """Benjamini-Hochberg q-values of {name: p}."""
    out, running = {}, 1.0
    ranked = sorted(p.items(), key=lambda kv: kv[1])
    for j in range(len(ranked), 0, -1):
        running = min(running, len(p) * ranked[j - 1][1] / j)
        out[ranked[j - 1][0]] = running
    return out


def one_sided(x, lag):
    """H: mean > 0, Newey-West, standard normal reference (as the registered H3/H4 test)."""
    r = mean_test(x, lag)
    return {**r, "p_one_sided": float(norm.sf(r["t"]))}


def confirmation_status(primary_mean, conf):
    """Frozen B3 rule."""
    if primary_mean * conf["mean"] <= 0:
        return "NOT CONFIRMED"
    return "CONFIRMED" if conf["p_one_sided"] < ALPHA else "CONSISTENT, NOT CONFIRMED"


def wide(monthly, n_months):
    """Monthly file -> one row per holding month, columns (portfolio, step), in percent. Fail closed (section 9)."""
    m = monthly
    if sorted(m["step"].unique()) != list(STEPS) or m.duplicated(["holding_month", "step"]).any() \
            or (m["status"] != "OK").any() or m[list(PORTFOLIOS)].isna().any().any():
        raise NotReady("monthly file: unexpected steps, duplicate rows, a status other than OK or a missing return")
    w = m.pivot(index="holding_month", columns="step", values=list(PORTFOLIOS)).sort_index() * 100
    if len(w) != n_months or w.isna().any().any():
        raise NotReady(f"monthly file: expected {n_months} complete months, found {len(w)}")
    return w


def block(w, first, last, lag):
    """Sections 6 and 8 for the months first..last of a wide frame."""
    w = w.loc[first:last]
    ladder = {}
    for s in STEPS:
        ladder[s] = {}
        for p in PORTFOLIOS:
            x, t = w[(p, s)], mean_test(w[(p, s)], lag)
            ladder[s][p] = {"n": len(x), "mean_pct": float(x.mean()), "sd_pct": float(x.std(ddof=1)), "t_nw": t["t"],
                            "p_two_sided": t["p_two_sided"], "skewness": float(skew(x, bias=False)),
                            "worst_month_pct": float(x.min()), "worst_month": str(x.idxmin())}
    return {"months": [w.index[0], w.index[-1]], "n": len(w), "lag": lag,
            "delta": mean_test(w[("WML", "A")] - w[("WML", "D")], lag),
            "step_differences_pct": {f"{a}-{b}": mean_test(w[("WML", a)] - w[("WML", b)], lag) for a, b in DIFFS},
            "ladder": ladder}


def _guard(w, delta_file, name):
    d = delta_file.sort_values("holding_month")
    if list(d["holding_month"]) != list(w.index) or \
            np.abs((w[("WML", "A")] - w[("WML", "D")]).to_numpy() - d["delta"].to_numpy()).max() > TOL:
        raise NotReady(f"{name}: recomputed delta differs from the registered delta file")


def _guard_primary(b, reg):
    pairs = [(b["delta"][k], reg["H1"][k]) for k in ("mean", "t")]
    pairs += [(b["step_differences_pct"][d][k], reg["step_differences_pct"][d][k]) for d in b["step_differences_pct"] for k in ("mean", "t")]
    pairs += [(b["ladder"][s][p]["mean_pct"], reg["ladder"][s][p]["mean_pct"]) for s in STEPS for p in PORTFOLIOS]
    if any(abs(x - y) > TOL for x, y in pairs):
        raise NotReady("primary block does not reproduce the registered primary results")


def analyse(monthly, delta, registered, step_e):
    """Everything of the specification, from in-memory frames. `monthly`/`delta`: {"primary": df, "confirmation": df}."""
    w = {s: wide(monthly[s], MONTHS[s]) for s in MONTHS}
    for s in MONTHS:
        _guard(w[s], delta[s], s)
    frames = {"primary": w["primary"], "confirmation": w["confirmation"], "primary_half_1": w["primary"],
              "primary_half_2": w["primary"], "pooled": pd.concat([w["primary"], w["confirmation"]])}
    blocks = {name: block(frames[name], *BLOCKS[name]) for name in BLOCKS}
    if any(blocks[n]["n"] != t for n, t in (("primary_half_1", 57), ("primary_half_2", 57), ("pooled", 170))):
        raise NotReady("a block does not have its specified number of months")
    _guard_primary(blocks["primary"], registered)
    h = {s: one_sided(w[s][("W", "A")] - w[s][("W", "D")], BLOCKS[s][2]) for s in MONTHS}
    p2 = {"H2a": registered["step_differences_pct"]["A-B"]["p_two_sided"], "H2b": registered["step_differences_pct"]["B-C"]["p_two_sided"],
          "H2c": registered["step_differences_pct"]["C-D"]["p_two_sided"], "H2d": h["primary"]["p_one_sided"]}
    p6 = {**p2, "H3": step_e["samples"]["primary"]["H3"]["p_one_sided"], "H4": step_e["samples"]["primary"]["H4"]["p_one_sided"]}
    sided = lambda k: "two" if k in ("H2a", "H2b", "H2c") else "one"                     # noqa: E731
    return {"blocks": blocks,
            "H2d": {**h, "confirmation_status": confirmation_status(h["primary"]["mean"], h["confirmation"])},
            "holm": {"family_alpha": ALPHA, "m": len(p2),
                     **{k: {"p": p2[k], "sided": sided(k), "p_holm": v, "rejected": bool(v < ALPHA)} for k, v in holm(p2).items()}},
            "benjamini_hochberg": {"m": len(p6), "note": BH_NOTE,
                                   **{k: {"p": p6[k], "sided": sided(k), "q": v} for k, v in bh(p6).items()}}}


def run(root=BASE_DIR, inputs=INPUTS, out=OUT, spec=SPEC):
    """Check every hash, compute, write the one output file. Returns its SHA-256."""
    root, out = Path(root), Path(out)
    partial = out.with_name(out.name + ".partial")
    if out.exists() or partial.exists():
        raise NotReady(f"{out} (or its .partial) already exists - C2 runs once and nothing is overwritten")
    for rel, sha in (spec, *inputs.values()):                                # all of them, before any read
        if _sha(root / rel) != sha:
            raise NotReady(f"{rel} does not match its registered SHA-256 - C2 refused")
    read = lambda k: pd.read_csv(root / inputs[k][0], dtype={"holding_month": str})      # noqa: E731
    load = lambda k: json.loads((root / inputs[k][0]).read_text())                       # noqa: E731
    res = analyse({s: read(f"{s}_monthly") for s in MONTHS}, {s: read(f"{s}_delta") for s in MONTHS},
                  load("primary_results"), load("step_e_results"))
    res = {"statement": STATEMENT, "spec_sha256": spec[1], "inputs_sha256": {rel: sha for rel, sha in inputs.values()}, **res}
    partial.mkdir(parents=True)                                              # everything computed; only now write
    (partial / "c2_results.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    partial.rename(out)
    return _sha(out / "c2_results.json")


def main():
    rec = verify_protocol()
    sha = run()                                                              # raises on any refusal or failure: nothing below runs
    env = {**experiments.environment(), "platform": platform.platform(), "scipy": metadata.version("scipy")}
    experiments.amend(PROTOCOL_ID, "C2 run registered: pre-registered analyses executed late, after the primary, "
                                   "sensitivity, confirmation and step E results were known (not blind, not confirmatory)",
                      provenance={**rec["provenance"], "c2_run": {
                          "command": "python3 scripts/run_s2_mom_c2.py execute", "results_sha256": sha,
                          "files_sha256": {"c2_results.json": sha}, "code_sha256": code_sha(), "spec_sha256": SPEC[1],
                          "inputs_sha256": {rel: h for rel, h in INPUTS.values()}, "environment": env}})
    experiments.log_trial("s2_mom_v1", {"mode": "c2"}, "PRIMARY+OOS", {"results_sha256": sha}, "scripts/run_s2_mom_c2.py")
    experiments.write_md()


if __name__ == "__main__":
    if sys.argv[1:] != ["execute"]:
        sys.exit(__doc__)
    main()
