"""Deterministic, read-only reproduction of the registered S2-MOM-v1 results (F-05).

    python3 scripts/reproduce_s2_mom_v1.py              # everything; exit 0 = PASS, 1 = FAIL
    python3 scripts/reproduce_s2_mom_v1.py --verify     # steps 1-5 only (hashes, registry, inputs; no recomputation)
    python3 scripts/reproduce_s2_mom_v1.py --report F   # also write the full report as JSON to F (outside the repository)

 1 environment          interpreter and every pinned dependency (release/s2_mom_v1/ENVIRONMENT.json)
 2 protocol             frozen protocol, addendum and supplements: file == registry == pinned SHA-256
 3 registry             validated history, state FINAL, hash chain, one trial per registered mode
 4 manifest             registry anchor -> Stage 3 manifest -> every input (and Stage 2 files, code hashes)
 5 inputs and outputs   every registered result file hash; structural and numerical validation of the inputs
 6 recomputation        an INDEPENDENT implementation of the ladder A-D, delta, the Newey-West test, the step E
                        costs and the C2 arithmetic, written from the frozen protocol text, not from the code
 7 comparison           recomputed numbers vs the registered files, absolute tolerance 1e-9
 8 leaves no trace      the repository is fingerprinted before and after; any change is a FAIL

It registers nothing, writes nothing inside the repository, never downloads, and never calls a
registered runner. Any missing or altered input is a FAIL (fail closed): there is no partial PASS.
What is NOT recomputed, only hash- and consistency-checked: the six sensitivity treatments, the
reverse-order ladder and the bootstrap resampling stream (the bootstrap p-value is recomputed with
the registered routine on the independently recomputed delta series, and is labelled as such).
"""

import hashlib
import json
import math
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True                      # leave no __pycache__ behind
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                  # noqa: E402
import pandas as pd                                 # noqa: E402

from src.registry import experiments, integrity     # noqa: E402

TOL = 1e-9
EXPERIMENT = "S2-MOM-v1"
PINNED = {      # independent pins: this file, the registry and the files on disk must all agree
    "protocol": ("docs/research/phase3a_momentum_protocol.md", "f1abd954f698307f7aafe234c5d5c9f1681ccc5aadb9cb21e9f8e34d47abd838"),
    "univ1": ("data/stage2/universe/univ1_pit_universe.parquet", "2abf457a06abf0e8a0b96c0b0ca0f75ccc07729c0166b1812d7af4646cba9c42"),
    "schedule": ("config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json", "47a9bad407b87b781c3584986b76b23216c2af33eb2b2f9986d23f710098a10f"),
    "c2_spec": ("docs/research/s2_mom_v1_c2_analysis_spec.md", "78864a4f6fddad86a7b3273e8d8c1e7ab818ed318deb0fdb75cc99e2c5a0c0aa"),
}
RESULT_HEADLINE = {"primary_results": "fe7e95ba97482d6d53faba543d860e4f0d1e50cfa0312d669e910346d41ef857",
                   "sensitivity_results": "7d6081d8c4a099f7cd1d7d688791c23180d6977536ae4c7860a08b429ff0c19b",
                   "confirmation_results": "38d1d0a9fbb1d22a19b7912ec4e6285d1dbcb920ffd0e6d99ea19e096c304d92",
                   "step_e_results": "675398488b4a9c11a3f25d70afd32ce3d6f62340e0d9a8a0d3c33df7f7b039e0",
                   "c2_results": "cf977e8a5efce7ba83ce91bf70ae247ed1aea96c7004f8d03162669097689513",
                   "blinded_precision": "1e26341044f3e46052fdcda53a56721124412e26d5b93156bf274a9a4de5c693"}
CODE = {        # the file lists behind each registered code hash (restated; compared with the registry)
    "primary_run": ("src/stage3/protocol.py", "src/stage3/ladder.py", "src/stage3/data.py", "src/stage3/stats.py",
                    "src/stage3/costs.py", "src/stage3/experiment.py", "scripts/run_s2_mom.py"),
    "step_e_run": ("src/stage3/step_e.py", "scripts/run_s2_mom_step_e.py"),
    "c2_run": ("scripts/run_s2_mom_c2.py",),
}
RUN_DIRS = {"primary_run": "results/s2_mom_v1", "confirmation_run": "results/s2_mom_v1", "step_e_run": "results/s2_mom_v1_step_e",
            "c2_run": "results/s2_mom_v1_c2"}
TRIALS = ["primary", "sensitivity", "confirmation", "step_e", "c2"]         # exactly one logged run of each, in this order
DELIST = {"VOLUNTARY": 0.0, "OTHER": -0.30}                                # protocol §22
NW_LAG = {"primary": 4, "oos": 3}                                           # protocol §15
SLIPPAGE = {"S0": (0, 0), "S1": (5, 15), "S2": (10, 30), "S3": (25, 75), "S4": (50, 150)}      # protocol §13, bps (1-200, 201-500)
NOTIONAL = 1e7
MODE = {"primary": "primary", "oos": "confirmation"}
# written by the scheduled intraday collector (launchd), never by this script and never read by S2-MOM-v1
NOT_OURS = ("data/india/", "data/raw/collection_log.jsonl", "data/raw/manifest.jsonl", "data/raw/yahoo/", "logs/", ".pytest_cache/")


class Fail(Exception):
    pass


def sha(path):
    return integrity.sha256(path)


def fingerprint(root):
    """(path, size, mtime) of every file outside .git - to prove the run changed nothing."""
    out = {}
    for p in root.rglob("*"):
        rel = p.relative_to(root).as_posix()
        if ".git" in p.parts or "__pycache__" in p.parts or not p.is_file() or rel.startswith(NOT_OURS):
            continue
        st = p.stat()
        out[p.relative_to(root).as_posix()] = (st.st_size, st.st_mtime_ns)
    return out


# ====================================================================== steps 1-5: verification
def check_environment(root, rec):
    anchors = (rec or {}).get("anchors") or {}
    spec = anchors.get("environment_files_sha256_v2") or anchors.get("environment_files_sha256")      # v2 supersedes v1 (see the registry)
    if not spec:
        raise Fail("the environment specification is not anchored in the registry")
    for rel, want in spec.items():
        if not (root / rel).is_file() or sha(root / rel) != want:
            raise Fail(f"{rel}: environment specification does not match the registry anchor")
    rep = integrity.environment_report(root)
    if rep["missing"]:
        raise Fail(f"missing dependencies: {rep['missing']}")
    if rep["broken"]:
        raise Fail(f"dependencies installed but not loadable: {rep['broken']}")
    if rep["optimized"]:
        raise Fail("python -O / PYTHONOPTIMIZE is set: assert-based guards of the frozen code would be disabled - refused")
    note = "identical to the tested environment" if rep["identical_to_tested"] else \
        f"DIFFERS from the tested environment {rep['mismatch']} - numbers are compared at tolerance {TOL}, not bytes"
    return note, rep


def check_protocol(root, rec):
    for name, (rel, want) in PINNED.items():
        if sha(root / rel) != want:
            raise Fail(f"{rel} does not have its pinned SHA-256")
    if rec.get("protocol_sha256") != PINNED["protocol"][1] or rec.get("protocol_file") != PINNED["protocol"][0]:
        raise Fail("the registry record does not carry the frozen protocol SHA-256")
    if rec.get("universe_sha256") != PINNED["univ1"][1]:
        raise Fail("the registry record does not carry the frozen UNIV-1 SHA-256")
    addenda = rec.get("addenda") or []
    if len(addenda) != 5:
        raise Fail(f"expected Addendum 1 and Supplements 1-4 in the registry, found {len(addenda)}")
    for a in addenda:
        if sha(root / a["file"]) != a["sha256"]:
            raise Fail(f"{a['file']} does not match the registry")
    anchored = (rec.get("anchors") or {}).get("cost_schedules_sha256") or {}
    if anchored.get(PINNED["schedule"][0]) != PINNED["schedule"][1]:
        raise Fail("the cost schedule is not anchored in the registry with its pinned SHA-256")
    for rel, want in anchored.items():
        if sha(root / rel) != want:
            raise Fail(f"{rel} does not match the registry anchor")
    return f"protocol, UNIV-1, cost schedule, C2 specification and {len(addenda)} addenda/supplements match"


def load_registry(root):
    state = experiments.load(root / "registry" / "experiments.jsonl", (experiments.GENESIS_LINES, experiments.GENESIS_SHA256))
    if EXPERIMENT not in state:
        raise Fail(f"{EXPERIMENT} is not registered")
    return state[EXPERIMENT]


def check_registry(root, rec):
    if rec["status"] != "FINAL":
        raise Fail(f"registry state of {EXPERIMENT} is {rec['status']!r}, not FINAL")
    trials = [json.loads(x) for x in (root / "registry" / "trials.jsonl").read_text().splitlines()]
    mine = [t for t in trials if t["kind"] == "s2_mom_v1"]
    if [t["params"]["mode"] for t in mine] != TRIALS:
        raise Fail(f"trial log: expected exactly one run of each of {TRIALS}, found {[t['params']['mode'] for t in mine]} "
                   f"(an unregistered or repeated run?)")
    prov = rec["provenance"]
    want = {"primary": prov["primary_run"]["results_sha256"], "sensitivity": prov["sensitivity_run"]["results_sha256"],
            "confirmation": prov["confirmation_run"]["results_sha256"], "step_e": prov["step_e_run"]["results_sha256"],
            "c2": prov["c2_run"]["results_sha256"]}
    for t in mine:
        if t["headline"] != {"results_sha256": want[t["params"]["mode"]]}:
            raise Fail(f"trial log entry for {t['params']['mode']} names a different result than the registry")
    headline = {"primary_results": want["primary"], "sensitivity_results": want["sensitivity"], "confirmation_results": want["confirmation"],
                "step_e_results": want["step_e"], "c2_results": want["c2"], "blinded_precision": prov["blinded_precision_artifact_sha256"]}
    if headline != RESULT_HEADLINE:
        raise Fail("a registered result hash in the registry differs from the published one pinned in this script")
    if prov["primary_run"]["code_sha256"] != prov["confirmation_run"]["code_sha256"] or \
            prov["primary_run"]["code_sha256"] != prov["sensitivity_run"]["code_sha256"]:
        raise Fail("primary, sensitivity and confirmation were not registered with one code hash")
    lines = len((root / "registry" / "experiments.jsonl").read_text().splitlines())
    return f"{lines} lines valid (history pinned, chain intact); state FINAL; 5 registered runs, each logged once; same-code confirmation"


def check_outputs(root, rec):
    prov, n = rec["provenance"], 0
    for run, folder in RUN_DIRS.items():
        for name, want in prov[run]["files_sha256"].items():
            if sha(root / folder / name) != want:
                raise Fail(f"{folder}/{name} does not match its registered SHA-256")
            n += 1
    for name, want in (("sensitivity_results.json", prov["sensitivity_run"]["results_sha256"]),
                       ("blinded_precision.json", prov["blinded_precision_artifact_sha256"])):
        if sha(root / "results/s2_mom_v1" / name) != want:
            raise Fail(f"results/s2_mom_v1/{name} does not match its registered SHA-256")
        n += 1
    for folder in sorted(set(RUN_DIRS.values())):
        known = {f for run, d in RUN_DIRS.items() if d == folder for f in prov[run]["files_sha256"]}
        known |= {"sensitivity_results.json", "blinded_precision.json"} if folder == "results/s2_mom_v1" else set()
        extra = sorted(p.name for p in (root / folder).iterdir() if p.name not in known and p.name != ".DS_Store")
        if extra:
            raise Fail(f"unregistered file(s) in {folder}: {extra}")
    for run, files in CODE.items():
        got = hashlib.sha256(b"".join((root / f).read_bytes() for f in files)).hexdigest()
        if got != prov[run]["code_sha256"]:
            raise Fail(f"the code behind {run} differs from its registered code hash")
    for s in ("primary", "oos"):
        c = json.loads((root / integrity.STAGE3 / f"checks/pre_run_checks_{s}.json").read_text())
        if c.get("all_passed") is not True or c.get("code_sha256") != prov["primary_run"]["code_sha256"]:
            raise Fail(f"pre-run checks ({s}) did not pass with the registered code")
    log = (root / integrity.STAGE3 / "checks/stage2_rebuild_20261005.log").read_text().splitlines()
    rebuilt = prov["stage2_rebuild"]            # F-12: the "150 of 150" gate value must follow from the anchored log
    if sum(x.startswith("  OK ") for x in log) != 150 or log[-1] != "RESULT: ALL CHECKS PASSED" or any("FAIL" in x for x in log) \
            or (rebuilt["checks_passed"], rebuilt["checks_failed"]) != (150, 0):
        raise Fail("the Stage 2 rebuild log does not show 150 of 150 checks passed")
    arch = (rec.get("anchors") or {}).get("external_archive") or {}
    if not arch or sha(root / arch["manifest"]) != arch["manifest_sha256"]:
        raise Fail("the external archive manifest is missing or does not match the registry anchor")
    return f"{n} registered result files, 3 registered code hashes, pre-run checks and the archive manifest match the registry"


def check_inputs(root):
    integrity.validate_cutoffs()
    frames = integrity.load_stage3(root)
    integrity.validate_stage3(frames)
    kinds = integrity.validate_delisting_types(root)
    for s, (_, months) in integrity.SAMPLES.items():
        integrity.validate_monthly(pd.read_csv(root / f"results/s2_mom_v1/{MODE[s]}_monthly.csv"), months, f"{MODE[s]}_monthly.csv")
        integrity.validate_step_e(pd.read_csv(root / f"results/s2_mom_v1_step_e/{MODE[s]}_step_e_monthly.csv"), months,
                                  f"{MODE[s]}_step_e_monthly.csv")
    return frames, (f"panel {len(frames['panel']):,} rows, {len(frames['sessions'])} sessions, 170 months, 510 universes of 200; "
                    f"no NaN/inf/duplicate; delisting wording {sorted(kinds)}")


# ====================================================================== step 6: independent recomputation
def nw_test(x, lag):
    """Mean, Newey-West (Bartlett, /n) standard error, t and two-sided normal p of H0: mean = 0."""
    x = np.asarray(x, float)
    n, d = len(x), np.asarray(x, float) - np.mean(x)
    lrv = d @ d / n + sum(2 * (1 - k / (lag + 1)) * (d[k:] @ d[:-k]) / n for k in range(1, lag + 1))
    se = math.sqrt(lrv / n)
    t = x.mean() / se
    return {"n": n, "mean": float(x.mean()), "se": se, "t": t, "p_two": math.erfc(abs(t) / math.sqrt(2)),
            "p_one": 0.5 * math.erfc(t / math.sqrt(2))}


class Matrices:
    """Date x entity arrays of the Stage 3 panel (NaN / '' where the stock has no row)."""

    def __init__(self, f):
        self.days = pd.DatetimeIndex(pd.to_datetime(f["sessions"]["date"]))
        self.ents = pd.Index(sorted(f["identity"]["entity_id"]))
        p = f["panel"]
        i, j = self.days.get_indexer(p["date"]), self.ents.get_indexer(p["entity"])
        if (i < 0).any() or (j < 0).any():
            raise Fail("panel row outside the session list or the identity table")
        shape = (len(self.days), len(self.ents))

        def mat(col, fill, dtype=float):
            m = np.full(shape, fill, dtype)
            m[i, j] = p[col].to_numpy()
            return m
        self.rn, self.rg, self.rr = mat("r_naive", np.nan), mat("r_rg", np.nan), mat("r_raw", np.nan)
        code = mat("cls", "", object)
        self.present, self.first = code != "", code == "FIRST"
        self.ok, self.bad = code == "OK", (code == "BAD") | (code == "FIRST")
        self.pos = {d: n for n, d in enumerate(self.days)}
        self.delist = f["identity"].set_index("entity_id")["delist_class"].map(DELIST).reindex(self.ents).to_numpy()
        if np.isnan(self.delist).any():
            raise Fail("entity without a delisting class")


STEPS = {"A": ("A", "N"), "B": ("B", "N"), "C": ("C", "N"), "D": ("C", "R")}      # universe, return rule (protocol B1)


def ladder(M, cal, universes):
    """Protocol B1, §7-§10, §20-§22, written from the text: one row per (month, step) with W, L, BM."""
    cal = cal.assign(**{k: pd.to_datetime(cal[k]) for k in ("t", "m12", "m1", "s_plus", "s_pp")})
    U = {(k, pd.Timestamp(t)): list(g["entity"]) for (k, t), g in universes.groupby(["key", "t"])}
    booked = {(s, p): set() for s in STEPS for p in ("W", "L", "BM")}
    rows, members = [], {}
    for c in cal.itertuples():
        a12, a1, sp, spp = (M.pos[x] for x in (c.m12, c.m1, c.s_plus, c.s_pp))
        form = slice(a12 + 1, a1 + 1)                              # (m12, m1]: twelve months, the last one skipped
        for step, (ukey, rule) in STEPS.items():
            names = np.array(U[(ukey, c.t)], dtype=object)
            j = M.ents.get_indexer(names)
            if (j < 0).any():
                raise Fail("universe entity without panel data")
            rankable = M.present[a12, j] & M.present[a1, j]
            if rule == "R":
                rankable &= ~M.bad[form][:, j].any(0)               # §21: any flagged row in the window excludes the stock
                gross = np.where(M.ok[form][:, j], M.rg[form][:, j], 0.0)
            else:
                gross = np.where(M.present[form][:, j] & ~M.first[form][:, j], M.rn[form][:, j], 0.0)
            score = np.prod(1 + gross, axis=0) - 1
            order = sorted(zip(-score[rankable], names[rankable]))  # best first; ties by entity ascending (§10)
            ranked = [e for _, e in order]
            k = int(math.floor(0.30 * len(ranked) + 0.5))
            ports = {"W": ranked[:k], "L": ranked[len(ranked) - k:], "BM": sorted(ranked)}
            row = {"t": c.t, "step": step, "n_rankable": len(ranked), "k": k}
            for pname, held in ports.items():
                q = M.ents.get_indexer(held)
                v, done = np.ones(len(q)), booked[(step, pname)]
                for i in range(sp + 1, spp + 1):                    # (s_plus, s_pp]: bought and sold at the close
                    skip = np.array([(e, i) in done for e in q]) if done else np.zeros(len(q), bool)
                    if rule == "N":
                        v *= 1 + np.where(M.present[i, q] & ~M.first[i, q] & ~skip, M.rn[i, q], 0.0)
                    else:
                        ok, bad = M.ok[i, q] & ~skip, M.bad[i, q] & ~skip
                        r = np.where(ok, M.rg[i, q], 0.0)
                        if bad.any():                               # §20(b): mean of the other stocks' research returns
                            v[bad] *= 1 + (r[ok].mean() if ok.any() else 0.0)
                        v[ok] *= 1 + r[ok]
                if ukey == "C":                                     # §22, from step C on
                    for n, e in enumerate(q):
                        if M.present[spp, e]:
                            continue
                        later = np.flatnonzero(M.present[spp + 1:, e])
                        if len(later):                              # trades again: book the realised gap return once
                            i = spp + 1 + int(later[0])
                            v[n] *= 1 + (M.rn[i, e] if rule == "N" else M.rr[i, e])
                            done.add((e, i))
                        else:                                       # never trades again: the delisting return
                            v[n] *= 1 + M.delist[e]
                row[pname] = float(v.mean() - 1)                    # equal weights
                members[(step, c.t, pname)] = held
            row["WML"] = row["W"] - row["L"]
            rows.append(row)
    return pd.DataFrame(rows), members


def step_e_costs(holdings, schedule, ranks):
    """Addendum 1 rules 1-6 and Supplement 2, from the saved holdings: {portfolio: {t: {scenario: cost fraction}}}."""
    comp = {c: [(pd.Timestamp(p["from"]), pd.Timestamp(p["to"]), p) for p in ps] for c, ps in schedule["components"].items()}

    def on(name, day):
        hit = [p for lo, hi, p in comp[name] if lo <= day <= hi]
        if len(hit) != 1:
            raise Fail(f"cost schedule: {len(hit)} periods of {name} on {day.date()}")
        return hit[0]
    out = {}
    h = holdings[holdings["step"] == "D"]
    for pname in ("W", "L", "BM"):
        drift, out[pname] = {}, {}
        for t, g in h[h["portfolio"] == pname].groupby("t", sort=True):
            day = pd.Timestamp(g["s_plus"].iloc[0])                 # rates in force on the entry session
            r = {c: on(c, day) for c in comp}
            target, total = dict(zip(g["entity"], g["begin_weight"])), dict.fromkeys(SLIPPAGE, 0.0)
            for e in set(target) | set(drift):
                d = target.get(e, 0.0) - drift.get(e, 0.0)
                if d == 0:
                    continue
                value, buy = abs(d) * NOTIONAL, d > 0
                brokerage = min(value * r["brokerage"]["rate"], r["brokerage"]["cap_rs_per_order"])
                taxed = brokerage + value * (r["exchange_txn"]["rate"] + r["ipft"]["rate"] + r["sebi_fee"]["rate"])
                cost = taxed * (1 + r["indirect_tax"]["rate"]) + value * r["stt_buy" if buy else "stt_sell"]["rate"]
                cost += value * r["stamp_duty_buy"]["rate"] if buy else r["dp_charge"]["billed_rs"]
                rank = ranks.get((pd.Timestamp(t), e))
                if rank is None:
                    raise Fail(f"no UNIV-1 row for {e} at {pd.Timestamp(t).date()}")
                low = not (rank == rank and rank <= 200)            # 201-500, and the fallback above 500 / unranked
                for s, (top, rest) in SLIPPAGE.items():
                    total[s] += cost + value * (rest if low else top) / 1e4
            out[pname][pd.Timestamp(t)] = {s: x / NOTIONAL for s, x in total.items()}
            drift = dict(zip(g["entity"], g["end_weight"]))
    return out


def holm(p):
    out, running = {}, 0.0
    for n, (k, v) in enumerate(sorted(p.items(), key=lambda kv: kv[1])):
        running = max(running, min(1.0, (len(p) - n) * v))
        out[k] = running
    return out


def benjamini_hochberg(p):
    ranked, out, running = sorted(p.items(), key=lambda kv: kv[1]), {}, 1.0
    for n in range(len(ranked), 0, -1):
        running = min(running, len(p) * ranked[n - 1][1] / n)
        out[ranked[n - 1][0]] = running
    return out


class Compare:
    def __init__(self):
        self.rows, self.worst = [], 0.0

    def close(self, name, got, want, tol=TOL):
        got, want = np.asarray(got, float), np.asarray(want, float)
        if got.shape != want.shape:
            raise Fail(f"{name}: {got.shape} values recomputed, {want.shape} registered")
        if not (np.isfinite(got).all() and np.isfinite(want).all()):
            raise Fail(f"{name}: NaN or infinite value")
        diff = float(np.abs(got - want).max()) if got.size else 0.0
        self.rows.append({"quantity": name, "values": int(got.size), "max_abs_diff": diff, "tolerance": tol, "within_tolerance": diff <= tol})
        self.worst = max(self.worst, diff)
        if diff > tol:
            raise Fail(f"{name}: recomputed value differs from the registered one by {diff:.3e} (tolerance {tol})")

    def same(self, name, got, want):
        self.rows.append({"quantity": name, "values": 1, "max_abs_diff": 0.0, "tolerance": "exact equality", "within_tolerance": got == want})
        if got != want:
            raise Fail(f"{name}: recomputed {got!r} != registered {want!r}")


def recompute(root, frames, cmp):
    M = Matrices(frames)
    res = root / "results"
    mine = {}
    for s, mode in MODE.items():
        months = integrity.SAMPLES[s][1]
        got, members = ladder(M, frames[f"{s}/calendar"], frames[f"{s}/universes"])
        reg = pd.read_csv(res / f"s2_mom_v1/{mode}_monthly.csv", parse_dates=["t"])
        m = got.merge(reg, on=["t", "step"], suffixes=("", "_reg"), validate="one_to_one")
        if not len(m) == len(reg) == len(got) == 4 * months:
            raise Fail(f"{mode}: step-months recomputed and registered do not match one to one")
        for col in ("W", "L", "BM", "WML"):
            cmp.close(f"{mode} ladder A-D monthly {col}", m[col], m[col + "_reg"])
        cmp.same(f"{mode} n_rankable and k, every step-month", (m["n_rankable"].tolist(), m["k"].tolist()),
                 (m["n_rankable_reg"].tolist(), m["k_reg"].tolist()))
        hold = pd.read_csv(res / f"s2_mom_v1/{mode}_holdings.csv", parse_dates=["t"])
        saved = {key: sorted(g) for key, g in hold.groupby(["step", "t", "portfolio"])["entity"]}
        cmp.same(f"{mode} portfolio membership (W, L, BM of every step-month)",
                 {k: sorted(v) for k, v in members.items()}, saved)
        wml = got.pivot(index="t", columns="step", values="WML")
        delta = (wml["A"] - wml["D"]) * 100                          # protocol §2, percent per month
        regd = pd.read_csv(res / f"s2_mom_v1/{mode}_delta.csv", parse_dates=["t"]).set_index("t")
        if not regd["paired"].all() or list(regd.index) != list(delta.index):
            raise Fail(f"{mode}: registered delta file is not fully paired or has other months")
        cmp.close(f"{mode} delta = (WML_A - WML_D) x 100", delta, regd["delta"])
        r = json.loads((res / f"s2_mom_v1/{mode}_results.json").read_text())
        lag = NW_LAG[s]
        cmp.same(f"{mode} Newey-West lag = floor(4 (n/100)^(2/9))", (r["H1"]["lag"], math.floor(4 * (months / 100) ** (2 / 9))), (lag, lag))
        h1 = nw_test(delta, lag)
        cmp.close(f"{mode} H1 mean, NW se, t, two-sided p", [h1["mean"], h1["se"], h1["t"], h1["p_two"]],
                  [r["H1"]["mean"], r["H1"]["se_nw"], r["H1"]["t"], r["H1"]["p_two_sided"]])
        cmp.close(f"{mode} H1 90% interval", [h1["mean"] - 1.6448536269514722 * h1["se"], h1["mean"] + 1.6448536269514722 * h1["se"]], r["H1"]["ci90"])
        lo, hi = r["H1"]["ci90"]
        label = ("MATERIAL" if (lo > 0.10 or hi < -0.10) else "DETECTED_SIZE_UNCERTAIN") if h1["p_two"] < 0.05 else \
            ("IMMATERIAL" if (-0.10 < lo and hi < 0.10) else "INCONCLUSIVE")
        cmp.same(f"{mode} H1 label (protocol §27 table)", label, r["H1"]["decision"])
        for a, b in (("A", "B"), ("B", "C"), ("C", "D")):
            d = nw_test((wml[a] - wml[b]) * 100, lag)
            reg_d = r["step_differences_pct"][f"{a}-{b}"]
            cmp.close(f"{mode} step difference {a}-{b} mean, t, p", [d["mean"], d["t"], d["p_two"]], [reg_d["mean"], reg_d["t"], reg_d["p_two_sided"]])
        for step, g in got.groupby("step"):
            for col in ("W", "L", "WML", "BM"):
                d, reg_t = nw_test(g[col], lag), r["ladder"][step][col]
                cmp.close(f"{mode} ladder table {step}/{col} mean%, sd%, t, p", [d["mean"] * 100, g[col].std(ddof=1) * 100, d["t"], d["p_two"]],
                          [reg_t["mean_pct"], reg_t["sd_pct"], reg_t["t_nw"], reg_t["p_two_sided"]])
        from src.stage3 import stats as registered_stats          # the registered resampler, on the independent series
        boot = registered_stats.bootstrap_test(delta.to_numpy(), r["H1_bootstrap"]["seed"], r["H1_bootstrap"]["B"])
        cmp.same(f"{mode} bootstrap configuration (seed 20261005, B 10000)", (r["H1_bootstrap"]["seed"], r["H1_bootstrap"]["B"]), (20261005, 10000))
        cmp.close(f"{mode} bootstrap p-value and block length (registered routine, independent delta)",
                  [boot["p_two_sided"], boot["block_length"]], [r["H1_bootstrap"]["p_two_sided"], r["H1_bootstrap"]["block_length"]])
        mine[s] = {"monthly": got, "wml": wml, "delta": delta, "results": r}

    # ---- step E from the saved holdings and the approved schedule
    schedule = json.loads((root / PINNED["schedule"][0]).read_text())
    u1 = pd.read_parquet(root / PINNED["univ1"][0], columns=["selection_date", "entity_id", "rank"])
    ranks = {(pd.Timestamp(t), e): r for t, e, r in zip(u1["selection_date"], u1["entity_id"], u1["rank"])}
    se = json.loads((res / "s2_mom_v1_step_e/step_e_results.json").read_text())
    names = {"W": "cost_W_{}", "L": "hypothetical_cost_L_{}", "BM": "cost_BM_{}"}
    for s, mode in MODE.items():
        hold = pd.read_csv(res / f"s2_mom_v1/{mode}_holdings.csv", parse_dates=["t"])
        costs = step_e_costs(hold, schedule, ranks)
        reg = pd.read_csv(res / f"s2_mom_v1_step_e/{mode}_step_e_monthly.csv", parse_dates=["t"]).set_index("t")
        d = mine[s]["monthly"]
        d = d[d["step"] == "D"].set_index("t")
        for p, pattern in names.items():
            got = pd.DataFrame(costs[p]).T.reindex(reg.index)
            cmp.close(f"{mode} step E monthly cost of {p}, S0-S4", got[list(SLIPPAGE)].to_numpy(),
                      reg[[pattern.format(x) for x in SLIPPAGE]].to_numpy(), 1e-12)
        cw, cb, cl = (pd.DataFrame(costs[p]).T.reindex(reg.index) for p in ("W", "BM", "L"))
        for x in SLIPPAGE:
            cmp.close(f"{mode} step E net W, net BM, hypothetical net WML under {x}",
                      np.c_[d["W"] - cw[x], d["BM"] - cb[x], d["WML"] - cw[x] - cl[x]],
                      reg[[f"net_W_{x}", f"net_BM_{x}", f"hypothetical_net_WML_{x}"]].to_numpy())
        block = se["samples"][mode]
        h3 = nw_test(d["WML"] * 100, 4 if s == "primary" else 3)
        cmp.close(f"{mode} H3 mean%, t, one-sided p", [h3["mean"], h3["t"], h3["p_one"]],
                  [block["H3"]["mean_pct"], block["H3"]["t"], block["H3"]["p_one_sided"]])
        cmp.same(f"{mode} H3 supported (mean > 0 and one-sided p < 0.05)", bool(h3["mean"] > 0 and h3["p_one"] < 0.05), block["H3"]["supported"])
        for x in SLIPPAGE:
            sc = block["scenarios"][x]
            cmp.close(f"{mode} step E scenario {x} means", [cw[x].mean(), cb[x].mean(), cl[x].mean(), (d["W"] - cw[x] - d["BM"] + cb[x]).mean()],
                      [sc["cost_W"], sc["cost_BM"], sc["hypothetical_cost_L"], sc["net_excess_W_over_BM"]])
        if isinstance(block.get("H4"), dict) and "mean_pct" in block["H4"]:
            h4 = nw_test((d["W"] - cw["S0"] - d["BM"] + cb["S0"]) * 100, 4)
            cmp.close(f"{mode} H4 mean%, t, one-sided p", [h4["mean"], h4["t"], h4["p_one"]],
                      [block["H4"]["mean_pct"], block["H4"]["t"], block["H4"]["p_one_sided"]])
        elif s == "primary":
            raise Fail("registered step E results carry no H4 test for the primary sample")
        mine[s]["H3_p"] = h3["p_one"]
        mine[s]["H4_p"] = block["H4"]["p_one_sided"] if isinstance(block.get("H4"), dict) and "p_one_sided" in block["H4"] else None

    # ---- C2 arithmetic (from the independently recomputed monthly series)
    c2 = json.loads((res / "s2_mom_v1_c2/c2_results.json").read_text())
    wide = {s: mine[s]["monthly"].pivot(index="t", columns="step", values=["W", "WML"]) * 100 for s in MODE}
    h2d = {s: nw_test(wide[s][("W", "A")] - wide[s][("W", "D")], NW_LAG[s]) for s in MODE}
    for s, mode in MODE.items():
        reg = c2["H2d"][mode]
        cmp.close(f"C2 H2d ({mode}) mean, t, one-sided p", [h2d[s]["mean"], h2d[s]["t"], h2d[s]["p_one"]], [reg["mean"], reg["t"], reg["p_one_sided"]])
    status = "NOT CONFIRMED" if h2d["primary"]["mean"] * h2d["oos"]["mean"] <= 0 else \
        ("CONFIRMED" if h2d["oos"]["p_one"] < 0.05 else "CONSISTENT, NOT CONFIRMED")
    cmp.same("C2 H2d confirmation status (frozen B3 rule)", status, c2["H2d"]["confirmation_status"])
    pr = mine["primary"]
    step_p = {f"{a}-{b}": nw_test((pr["wml"][a] - pr["wml"][b]) * 100, 4)["p_two"] for a, b in (("A", "B"), ("B", "C"), ("C", "D"))}
    p4 = {"H2a": step_p["A-B"], "H2b": step_p["B-C"], "H2c": step_p["C-D"], "H2d": h2d["primary"]["p_one"]}
    hm = holm(p4)
    cmp.close("C2 Holm-adjusted p (H2a-H2d)", [hm[k] for k in sorted(hm)], [c2["holm"][k]["p_holm"] for k in sorted(hm)])
    cmp.same("C2 Holm rejections at 5%", {k: bool(v < 0.05) for k, v in hm.items()}, {k: c2["holm"][k]["rejected"] for k in hm})
    p6 = {**p4, "H3": mine["primary"]["H3_p"], "H4": mine["primary"]["H4_p"]}
    bq = benjamini_hochberg(p6)
    cmp.close("C2 Benjamini-Hochberg q (six tests)", [bq[k] for k in sorted(bq)], [c2["benjamini_hochberg"][k]["q"] for k in sorted(bq)])
    pooled = pd.concat([mine["primary"]["delta"], mine["oos"]["delta"]])
    half = len(mine["primary"]["delta"]) // 2
    for name, series, lag in (("primary", mine["primary"]["delta"], 4), ("confirmation", mine["oos"]["delta"], 3),
                              ("primary_half_1", mine["primary"]["delta"].iloc[:half], 3), ("primary_half_2", mine["primary"]["delta"].iloc[half:], 3),
                              ("pooled", pooled, 4)):
        d, reg = nw_test(series, lag), c2["blocks"][name]["delta"]
        cmp.same(f"C2 block {name}: months and lag", (len(series), lag), (c2["blocks"][name]["n"], c2["blocks"][name]["lag"]))
        cmp.close(f"C2 block {name}: delta mean, t, p", [d["mean"], d["t"], d["p_two"]], [reg["mean"], reg["t"], reg["p_two_sided"]])

    # ---- sensitivity file: not recomputed; internal consistency of the saved artifact only
    sens = json.loads((res / "s2_mom_v1/sensitivity_results.json").read_text())
    for name, v in sens["sensitivity"].items():
        t = v["H1"]
        cmp.close(f"sensitivity {name}: saved p-value follows from its saved mean and se (not recomputed)",
                  [math.erfc(abs(t["mean"] / t["se_nw"]) / math.sqrt(2))], [t["p_two_sided"]])
    return {"H1": {MODE[s]: {k: v for k, v in nw_test(mine[s]["delta"], NW_LAG[s]).items()} for s in MODE}}


# ====================================================================== driver
def main(root=ROOT, verify_only=False, report=None, stage2=True):
    root = Path(root)
    before = fingerprint(root)
    out, ok = {"experiment": EXPERIMENT, "root": str(root), "steps": []}, True
    frames, rec = None, None

    def step(n, name, fn):
        nonlocal ok
        try:
            detail = fn()
            out["steps"].append({"step": n, "name": name, "result": "PASS", "detail": detail})
            print(f"PASS  {n} {name}: {detail}")
        except Exception as e:                                      # any failure, expected or not, is a FAIL
            ok = False
            out["steps"].append({"step": n, "name": name, "result": "FAIL", "detail": f"{type(e).__name__}: {e}"})
            print(f"FAIL  {n} {name}: {type(e).__name__}: {e}")

    def registry():
        nonlocal rec
        rec = load_registry(root)
        return check_registry(root, rec)
    step(3, "registry", registry)

    def env():
        note, rep = check_environment(root, rec)
        out["environment"] = rep
        return note
    step(1, "environment", env)
    if rec is not None:
        step(2, "protocol", lambda: check_protocol(root, rec))
        step(4, "manifest", lambda: (integrity.verify_stage3(rec, root, stage2), "registry anchor -> manifest -> 8 Stage 3 inputs, "
                                     + ("4 Stage 2 inputs, 16 RET-1.1 files, 3 code files, " if stage2 else "") + "3 check files")[1])
        step(5, "registered outputs", lambda: check_outputs(root, rec))
    if ok:
        def inputs():
            nonlocal frames
            frames, detail = check_inputs(root)
            return detail
        step(5, "input validation", inputs)
    if ok and not verify_only:
        cmp = Compare()

        def calc():
            out["H1_recomputed"] = recompute(root, frames, cmp)["H1"]
            return f"{len(cmp.rows)} quantities, {sum(r['values'] for r in cmp.rows):,} numbers recomputed independently"
        step(6, "independent recomputation", calc)
        out["comparison"] = cmp.rows
        def verdict():
            if not ok:
                raise Fail("recomputation failed")
            if not all(r["within_tolerance"] for r in cmp.rows):
                raise Fail("a compared quantity is outside its tolerance")
            worst = max(cmp.rows, key=lambda r: r["max_abs_diff"])
            out["acceptance"] = {"criterion": f"absolute difference <= {TOL} for returns, statistics and p-values; <= 1e-12 for step E costs; "
                                              "counts, labels and membership exactly equal",
                                 "quantities": len(cmp.rows), "numbers": sum(r["values"] for r in cmp.rows),
                                 "within_tolerance": sum(r["within_tolerance"] for r in cmp.rows),
                                 "exactly_equal": sum(r["max_abs_diff"] == 0 for r in cmp.rows),
                                 "largest_abs_diff": worst["max_abs_diff"], "largest_in": worst["quantity"]}
            return (f"all {len(cmp.rows)} quantities ({out['acceptance']['numbers']:,} numbers) within tolerance; largest absolute difference "
                    f"{worst['max_abs_diff']:.2e} in '{worst['quantity']}' (tolerance {TOL}; step E costs 1e-12); "
                    f"{out['acceptance']['exactly_equal']} quantities exactly equal")
        step(7, "numerical comparison", verdict)
    elif not ok:
        out["steps"].append({"step": 6, "name": "independent recomputation", "result": "NOT RUN", "detail": "verification failed"})
        print("NOT RUN 6 independent recomputation: verification failed (fail closed)")

    def untouched():
        after = fingerprint(root)
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        if changed:
            raise Fail(f"the run changed the repository: {changed[:10]}")
        return f"{len(after):,} files identical before and after; nothing registered, nothing written"
    step(8, "repository unchanged", untouched)
    out["verdict"] = "PASS" if ok else "FAIL"
    out["scope"] = ("verification only (steps 1-5, 8)" if verify_only else "full reproduction") + \
        ("" if stage2 else " - PARTIAL: Stage 2 files and Stage 3 code hashes NOT checked (test mode, not a release result)")
    print(f"\nREPRODUCTION OF {EXPERIMENT}: {out['verdict']}  [{out['scope']}]")
    if report:
        report = Path(report).resolve()
        if root.resolve() == report.parent or root.resolve() in report.parents:
            raise SystemExit("--report must point outside the repository (the run leaves the repository unchanged)")
        tmp = report.with_name(report.name + ".partial")
        tmp.write_text(json.dumps(out, indent=1, default=str) + "\n")
        os.replace(tmp, report)                                     # atomic: a report is complete or absent
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    unknown = [x for n, x in enumerate(a) if x not in ("--verify", "--report") and (n == 0 or a[n - 1] != "--report")]
    if unknown:
        raise SystemExit(__doc__)
    result = main(verify_only="--verify" in a, report=a[a.index("--report") + 1] if "--report" in a else None)
    sys.exit(0 if result["verdict"] == "PASS" else 1)
