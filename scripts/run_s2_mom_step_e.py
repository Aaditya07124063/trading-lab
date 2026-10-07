"""S2-MOM-v1 step E runner: costs, net returns under S0-S4, H4 and break-even from the SAVED step D holdings.

    python3 scripts/run_s2_mom_step_e.py execute      # needs the reviewer's explicit authorisation

Frozen §13, Addendum 1, Supplements 1-3. Fail-closed:
  - reads exactly the five registered inputs below, read-only, and nothing else (Supplement 3, ruling 19);
  - checks the SHA-256 of all five BEFORE reading any of them, and refuses if one differs;
  - never rebuilds UNIV-1, never reads raw market data, RET-1.1 or ID-1;
  - refuses if its output directory (or a partial one left by a failed run) already exists: step E
    runs once and nothing is overwritten or deleted;
  - writes only into its own directory; the registered A-D files are not touched;
  - registers the run (registry and trials log) only after every output file is complete and hashed.
    A refused, failed or interrupted run registers nothing.
Results go to files only - nothing is printed. S1-S4 are pre-specified cost scenarios, not estimates.
"""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import BASE_DIR                                              # noqa: E402
from src.registry import experiments                                         # noqa: E402
from src.stage3 import step_e                                                # noqa: E402
from src.stage3.protocol import PROTOCOL_ID, NotReady, verify_protocol       # noqa: E402

INPUTS = {   # Supplement 3, ruling 19: exactly these five
    "primary_holdings": ("results/s2_mom_v1/primary_holdings.csv", "3887995763861a2ed17e280f1f975c6fd716dab4923c954d3ca70b91c2d93748"),
    "primary_monthly": ("results/s2_mom_v1/primary_monthly.csv", "f7c8d3ab5a0ef7a08b6a0ca8a12bf26a1f901006c21637cf7886e297b97bb372"),
    "confirmation_holdings": ("results/s2_mom_v1/confirmation_holdings.csv", "96bb174ed2942e7b93630ae445d11817551a44e15b90e5454272ddb79aa825b0"),
    "confirmation_monthly": ("results/s2_mom_v1/confirmation_monthly.csv", "4d88f385375ad681f85be739b292097e2e898acb6acb71013230c67415a43ce3"),
    "univ1": ("data/stage2/universe/univ1_pit_universe.parquet", "2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42"),
}
SAMPLES = {"primary": "PRIMARY", "confirmation": "OOS"}
OUT = BASE_DIR / "results" / "s2_mom_v1_step_e"       # its own directory, outside the registered results/s2_mom_v1
CODE = ("src/stage3/step_e.py", "scripts/run_s2_mom_step_e.py")
STATEMENT = ("Costs were specified (Addendum 1, Supplements 1-3) after the gross A-D, sensitivity and confirmation "
             "results were known and before any cost, turnover or net return was computed. Step E changes no A-D "
             "result. S1-S4 are pre-specified cost scenarios, not estimates. Every figure for L and every net WML is "
             "HYPOTHETICAL: L is costed as a long Rs 1 crore portfolio; hypothetical net WML = gross WML - cost of W - "
             "cost of L; it is not tested and is not an implementable long-short return. Each sample starts from cash "
             "(a full purchase, also at the confirmation boundary) and has no terminal liquidation. Orders above "
             "UNIV-1 rank 500 or unranked take the 201-500 slippage rate as an assumption. No break-even and no H4 "
             "for the confirmation sample (narrows the frozen §13 'always reported' line). A flat per-stock sell-side "
             "charge weighs more on the benchmark than on W (Addendum 1 §5). Schedule fallbacks and assumptions are "
             "listed per order in the ledger.")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_sha():
    return hashlib.sha256(b"".join((BASE_DIR / f).read_bytes() for f in CODE)).hexdigest()


def run(root=BASE_DIR, inputs=INPUTS, out=OUT):
    """Compute step E for both samples and write the output files. Returns {file name: SHA-256}."""
    root, out = Path(root), Path(out)
    partial = out.with_name(out.name + ".partial")
    if out.exists() or partial.exists():
        raise NotReady(f"{out} (or its .partial) already exists - step E runs once and nothing is overwritten")
    for rel, sha in inputs.values():                                         # all five, before any read
        if _sha(root / rel) != sha:
            raise NotReady(f"{rel} does not match its registered SHA-256 - step E refused")
    schedule = step_e.load_schedule()
    ranks = step_e.rank_index(pd.read_parquet(root / inputs["univ1"][0], columns=["selection_date", "entity_id", "rank"]))
    frames, results = {}, {"statement": STATEMENT, "inputs_sha256": {rel: sha for rel, sha in inputs.values()},
                           "schedule_sha256": step_e.SCHEDULE_SHA256, "samples": {}}
    for name, sample in SAMPLES.items():
        h = pd.read_csv(root / inputs[f"{name}_holdings"][0])
        m = pd.read_csv(root / inputs[f"{name}_monthly"][0])
        h, m = h[h["step"] == "D"], m[m["step"] == "D"]
        if set(h["sample"]) != {sample} or set(m["sample"]) != {sample}:
            raise NotReady(f"{name} files do not hold the {sample} sample")
        ledger = pd.concat([step_e.cost_ledger(h, schedule, "D", p, ranks=ranks) for p in step_e.PORTFOLIOS], ignore_index=True)
        net = step_e.net_returns(m, step_e.monthly_costs(ledger), h)
        orders = ledger.assign(value=ledger["order_value_rs"]).groupby(["portfolio", "slippage_band", "band_fallback"])["value"]
        results["samples"][name] = {**step_e.summarise(sample, net),
                                    "orders_by_band": [{"portfolio": p, "band": b, "fallback_above_500_or_unranked": bool(f),
                                                        "orders": int(n), "traded_value_rs": float(v)}
                                                       for (p, b, f), n, v in zip(orders.size().index, orders.size(), orders.sum())]}
        frames[f"{name}_step_e_ledger.csv"], frames[f"{name}_step_e_monthly.csv"] = ledger, net
    partial.mkdir(parents=True)                                              # everything computed; only now write
    for f, df in frames.items():
        df.to_csv(partial / f, index=False)
    (partial / "step_e_results.json").write_text(json.dumps(results, indent=1, default=str) + "\n")
    partial.rename(out)                                                      # the final directory appears only when complete
    return {p.name: _sha(p) for p in sorted(out.iterdir())}


def main():
    rec = verify_protocol()
    files = run()                                                            # raises on any refusal or failure: nothing below runs
    experiments.amend(PROTOCOL_ID, "step E run registered",
                      provenance={**rec["provenance"], "step_e_run": {"results_sha256": files["step_e_results.json"],
                                                                      "code_sha256": code_sha(), "files_sha256": files}})
    experiments.log_trial("s2_mom_v1", {"mode": "step_e"}, "PRIMARY+OOS",
                          {"results_sha256": files["step_e_results.json"]}, "scripts/run_s2_mom_step_e.py")
    experiments.write_md()


if __name__ == "__main__":
    if sys.argv[1:] != ["execute"]:
        sys.exit(__doc__)
    main()
