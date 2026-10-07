"""Failure injection (Phase 7): deliberate corruption of inputs, manifest, registry, results, code and
environment. Every attack must be REJECTED, or be shown to be an operation that cannot change a result.

Two layers are attacked separately, so that neither hides behind the other:
  files   a scratch copy of the registered artifacts, checked by scripts/reproduce_s2_mom_v1.py (hash layer);
  values  in-memory frames that an attacker has made hash-valid, checked by src/registry/integrity.py.
Nothing here touches the real repository: file attacks run on a temporary copy, value attacks on synthetic frames.

    python3 tests/test_failure_injection.py OUT.json     # write the attack table used by FAILURE_INJECTION_REPORT.md
"""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.registry import experiments as reg  # noqa: E402
from src.registry import integrity as I  # noqa: E402
from src.registry.integrity import ValidationError  # noqa: E402

spec = importlib.util.spec_from_file_location("reproduce_s2_mom_v1", ROOT / "scripts" / "reproduce_s2_mom_v1.py")
REPRO = importlib.util.module_from_spec(spec)
spec.loader.exec_module(REPRO)

S3 = I.STAGE3
COPY = ["src", "scripts", "registry", "release", "config", "docs/research", "results/s2_mom_v1", "results/s2_mom_v1_step_e",
        "results/s2_mom_v1_c2", "data/stage3", "data/stage2/universe", "data/stage2/identity", "data/stage2/returns", "requirements-lock.txt"]
HAVE_DATA = (ROOT / S3 / "research/panel.parquet").exists()


def make_copy(dest):
    """Scratch copy of the registered artifacts (copy-on-write where the file system supports it)."""
    for rel in COPY:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        if subprocess.run(["cp", "-cR", str(ROOT / rel), str(dest / rel)], capture_output=True).returncode:
            (shutil.copytree if (ROOT / rel).is_dir() else shutil.copy)(ROOT / rel, dest / rel)
    for junk in dest.rglob("__pycache__"):
        shutil.rmtree(junk)
    return dest


def edit(path, fn):
    path.write_bytes(fn(path.read_bytes()))


def forge_amendment(root, **fields):
    """Hand-append an amendment with a correct hash chain and self-consistent hashes."""
    f = root / "registry/experiments.jsonl"
    raw = f.read_bytes()
    exp = reg.load(f, (reg.GENESIS_LINES, reg.GENESIS_SHA256))["S2-MOM-v1"]
    rec = {"amends": "S2-MOM-v1", "amended_at": "2026-10-08T00:00:00+05:30", "reason": "forged", "actor": "attacker",
           "previous_state": exp["status"], "new_state": fields.get("status", exp["status"]), "changed_fields": sorted(fields),
           "previous_hashes": {k: (reg._sha(exp[k]) if k in exp else None) for k in sorted(fields)},
           "new_hashes": {k: reg._sha(v) for k, v in sorted(fields.items())}, "revalidation_required": False,
           "chain_prev_sha256": hashlib.sha256(raw).hexdigest(), **fields}
    f.write_bytes(raw + json.dumps(rec).encode() + b"\n")


def rewrite_manifest(root, fn):
    f = root / S3 / "manifest.json"
    doc = json.loads(f.read_text())
    fn(doc["content"])
    f.write_text(json.dumps(doc, indent=1) + "\n")


def sha_of(root, rel):
    return I.sha256(root / rel)


def line(n, fn):
    def go(b):
        rows = b.split(b"\n")
        rows[n] = fn(rows[n])
        return b"\n".join(rows)
    return go


# (id, what the attacker does, attack on the scratch copy, text the rejection must contain)
FILE_ATTACKS = [
    ("corrupt one input", "flip one character of primary/calendar.csv", lambda r: edit(r / S3 / "primary/calendar.csv", lambda b: b.replace(b"2012-06-29", b"2012-06-28", 1)), "primary/calendar.csv does not match"),
    ("corrupt one input (append a byte)", "append a newline to research/identity.csv", lambda r: edit(r / S3 / "research/identity.csv", lambda b: b + b"\n"), "identity.csv does not match"),
    ("corrupt one manifest entry", "change one hash inside the manifest", lambda r: rewrite_manifest(r, lambda c: c["outputs_sha256"].update({"oos/calendar.csv": "0" * 64})), "anchored in the registry"),
    ("rewrite the manifest", "edit an input and make the manifest agree with it", lambda r: (edit(r / S3 / "oos/universes.csv", lambda b: b.replace(b",1.0\n", b",2.0\n", 1)), rewrite_manifest(r, lambda c: c["outputs_sha256"].update({"oos/universes.csv": sha_of(r, f"{S3}/oos/universes.csv")}))), "anchored in the registry"),
    ("delete one input", "delete research/gap_rows.csv", lambda r: (r / S3 / "research/gap_rows.csv").unlink(), "missing input"),
    ("delete the manifest", "delete manifest.json", lambda r: (r / S3 / "manifest.json").unlink(), "manifest is missing"),
    ("duplicate one input", "copy oos/calendar.csv to a second file", lambda r: shutil.copy(r / S3 / "oos/calendar.csv", r / S3 / "oos/calendar (1).csv"), "unexpected file"),
    ("add an unexpected file (inputs)", "drop a new csv into the input folder", lambda r: (r / S3 / "research/extra.csv").write_text("x\n"), "unexpected file"),
    ("add an unexpected file (results)", "drop a second results file beside the registered ones", lambda r: (r / "results/s2_mom_v1/primary_results_v2.json").write_text("{}"), "unregistered file"),
    ("modify one result", "change one digit of primary_monthly.csv", lambda r: edit(r / "results/s2_mom_v1/primary_monthly.csv", line(5, lambda x: x.replace(b"1", b"2", 1) if b"1" in x else x + b"1")), "primary_monthly.csv does not match its registered"),
    ("modify the protocol", "edit one character of the frozen protocol", lambda r: edit(r / "docs/research/phase3a_momentum_protocol.md", lambda b: b + b" "), "does not have its pinned SHA-256"),
    ("modify a supplement", "edit Supplement 2", lambda r: edit(r / "docs/research/phase3a_momentum_protocol_addendum1_supplement2.md", lambda b: b + b" "), "does not match the registry"),
    ("modify protocol hash (registry)", "append an amendment that replaces protocol_sha256", lambda r: forge_amendment(r, protocol_sha256="0" * 64), "immutable"),
    ("modify code hash (ladder)", "add a comment to src/stage3/ladder.py", lambda r: edit(r / "src/stage3/ladder.py", lambda b: b + b"# x\n"), "differs from its registered code hash"),
    ("modify code hash (C2 runner)", "add a comment to scripts/run_s2_mom_c2.py", lambda r: edit(r / "scripts/run_s2_mom_c2.py", lambda b: b + b"# x\n"), "code behind c2_run"),
    ("modify code hash (registry)", "append an amendment that replaces the registered code hash", lambda r: forge_amendment(r, provenance={"primary_run": {"code_sha256": "0" * 64}}), "immutable"),
    ("modify registry state", "append FINAL -> PLANNED with a valid hash chain", lambda r: forge_amendment(r, status="PLANNED"), "illegal transition FINAL -> PLANNED"),
    ("modify registry state (in place)", "rewrite the historical PLANNED -> FINAL line", lambda r: edit(r / "registry/experiments.jsonl", line(52, lambda x: x.replace(b'"status": "FINAL"', b'"status": "PLANNED"'))), "registered history"),
    ("duplicate registry record", "append a copy of the S2-MOM-v1 record", lambda r: edit(r / "registry/experiments.jsonl", lambda b: b + b.split(b"\n")[37] + b"\n"), "duplicates an earlier record"),
    ("duplicate registry amendment", "append a copy of the last amendment", lambda r: edit(r / "registry/experiments.jsonl", lambda b: b + b.split(b"\n")[-2] + b"\n"), "duplicates an earlier record"),
    ("delete a registry amendment", "remove the last line (the newest anchor)", lambda r: edit(r / "registry/experiments.jsonl", lambda b: b"\n".join(b.split(b"\n")[:-2]) + b"\n"), "does not match the registry anchor"),
    ("delete all remediation amendments", "remove every line after the pinned history (all anchors)", lambda r: edit(r / "registry/experiments.jsonl", lambda b: b"\n".join(b.split(b"\n")[:58]) + b"\n"), "unanchored|not anchored"),
    ("alter confirmation status (result file)", "change the saved confirmation label", lambda r: edit(r / "results/s2_mom_v1/confirmation_results.json", lambda b: b.replace(b'"MATERIAL"', b'"IMMATERIAL"', 1)), "confirmation_results.json does not match"),
    ("alter confirmation status (C2 file)", "change H2d NOT CONFIRMED/CONFIRMED text", lambda r: edit(r / "results/s2_mom_v1_c2/c2_results.json", lambda b: b.replace(b'"confirmation_status": "', b'"confirmation_status": "NOT ', 1)), "c2_results.json does not match"),
    ("alter confirmation status (registry)", "append an amendment that rewrites the results headline", lambda r: forge_amendment(r, results={"headline": "H1 confirmed"}), "immutable"),
    ("alter environment metadata (specification)", "change a pinned version in ENVIRONMENT.json", lambda r: edit(r / I.ENVIRONMENT, lambda b: b.replace(b'"numpy": "', b'"numpy": "9', 1)), "environment specification does not match the registry"),
    ("alter environment metadata (registry)", "append an amendment that replaces the recorded environment", lambda r: forge_amendment(r, environment={"python": "9"}), "immutable"),
    ("alter environment metadata (manifest build block)", "edit the environment recorded in the Stage 3 manifest", lambda r: edit(r / S3 / "manifest.json", lambda b: b.replace(b'"python": "', b'"python": "9', 1)), "anchored in the registry"),
    ("insert NaN (result file)", "write NaN into a monthly return", lambda r: edit(r / "results/s2_mom_v1/confirmation_monthly.csv", line(3, lambda x: x + b",nan")), "confirmation_monthly.csv does not match"),
    ("insert +inf (step E file)", "write inf into a cost", lambda r: edit(r / "results/s2_mom_v1_step_e/primary_step_e_monthly.csv", line(2, lambda x: b"inf" + x[3:])), "primary_step_e_monthly.csv does not match"),
    ("insert -inf (input)", "write -inf into a universe rank", lambda r: edit(r / S3 / "primary/universes.csv", lambda b: b.replace(b",1.0\n", b",-inf\n", 1)), "primary/universes.csv does not match"),
    ("duplicate monthly row", "repeat one row of primary_delta.csv", lambda r: edit(r / "results/s2_mom_v1/primary_delta.csv", lambda b: b + b.split(b"\n")[1] + b"\n"), "primary_delta.csv does not match"),
    ("reorder rows", "swap two rows of oos/calendar.csv", lambda r: edit(r / S3 / "oos/calendar.csv", lambda b: b"\n".join((lambda x: [x[0], x[2], x[1]] + x[3:])(b.split(b"\n")))), "oos/calendar.csv does not match"),
    ("alter a date", "move one exit session by a day", lambda r: edit(r / S3 / "primary/calendar.csv", lambda b: b.replace(b"2012-08-01", b"2012-08-02", 1)), "primary/calendar.csv does not match"),
    ("alter entity id", "rename one stock in a universe", lambda r: edit(r / S3 / "oos/universes.csv", line(1, lambda x: x.replace(b"|", b"X|", 1))), "oos/universes.csv does not match"),
    ("alter return value", "change one digit of a registered monthly delta", lambda r: edit(r / "results/s2_mom_v1/confirmation_delta.csv", line(1, lambda x: x.replace(b".", b".9", 1))), "confirmation_delta.csv does not match"),
    ("alter cost (schedule)", "change one STT rate in the approved schedule", lambda r: edit(r / "config/cost_schedules/delivery_nse_eq_s2mom_v1_dated.json", lambda b: b.replace(b'"rate": 0.001', b'"rate": 0.0005', 1)), "does not have its pinned SHA-256"),
    ("alter cost (step E output)", "change one registered cost", lambda r: edit(r / "results/s2_mom_v1_step_e/confirmation_step_e_monthly.csv", line(1, lambda x: x.replace(b"0.0", b"0.1", 1))), "confirmation_step_e_monthly.csv does not match"),
    ("remove a required column", "drop the last column of research/identity.csv", lambda r: edit(r / S3 / "research/identity.csv", lambda b: b"\n".join(x.rsplit(b",", 1)[0] for x in b.split(b"\n"))), "identity.csv does not match"),
    ("change column type", "quote every rank as text", lambda r: edit(r / S3 / "oos/universes.csv", lambda b: b.replace(b".0\n", b".0x\n")), "oos/universes.csv does not match"),
    ("truncate an output", "cut primary_results.json in half", lambda r: edit(r / "results/s2_mom_v1/primary_results.json", lambda b: b[:len(b) // 2]), "primary_results.json does not match"),
    ("truncate an output (holdings)", "drop the last 1000 bytes of the holdings file", lambda r: edit(r / "results/s2_mom_v1/confirmation_holdings.csv", lambda b: b[:-1000]), "confirmation_holdings.csv does not match"),
    ("interrupted registry write", "leave a half-written last line", lambda r: edit(r / "registry/experiments.jsonl", lambda b: b + b'{"amends": "S2-MOM-v1", "amended_at": "2026'), "truncated line"),
    ("unregistered rerun", "log a second primary run in the trial log", lambda r: edit(r / "registry/trials.jsonl", lambda b: b + [x for x in b.split(b"\n") if b'"mode": "primary"' in x][0] + b"\n"), "exactly one run of each"),
    ("delete a registered output", "delete sensitivity_results.json", lambda r: (r / "results/s2_mom_v1/sensitivity_results.json").unlink(), "sensitivity_results.json"),
    ("symlink an input", "replace sessions.csv by a link to identical bytes elsewhere", lambda r: (shutil.copy(r / S3 / "research/sessions.csv", r / "elsewhere.csv"), (r / S3 / "research/sessions.csv").unlink(), (r / S3 / "research/sessions.csv").symlink_to(r / "elsewhere.csv")), "symlink"),
]


def run_file_attack(root, attack):
    attack(root)
    out = REPRO.main(root, verify_only=True, stage2=False)
    return out["verdict"], " | ".join(s["detail"] for s in out["steps"] if s["result"] == "FAIL")


@pytest.fixture(scope="module")
def pristine(tmp_path_factory):
    if not HAVE_DATA:
        pytest.skip("external data not materialised (scripts/release_archive.py materialize)")
    base = make_copy(tmp_path_factory.mktemp("pristine"))
    yield base
    shutil.rmtree(base, ignore_errors=True)


@pytest.fixture
def scratch(pristine, tmp_path):
    root = tmp_path / "repo"
    if subprocess.run(["cp", "-cR", str(pristine), str(root)], capture_output=True).returncode:
        shutil.copytree(pristine, root)
    yield root
    shutil.rmtree(root, ignore_errors=True)


def test_the_untouched_scratch_copy_verifies(scratch, capsys):
    out = REPRO.main(scratch, verify_only=True, stage2=False)
    assert out["verdict"] == "PASS", [s for s in out["steps"] if s["result"] != "PASS"]
    assert "PARTIAL" in out["scope"]                            # a run without Stage 2 can never be mistaken for a release result


@pytest.mark.parametrize("name, what, attack, expect", FILE_ATTACKS, ids=[a[0] for a in FILE_ATTACKS])
def test_file_attack_is_rejected(scratch, capsys, name, what, attack, expect):
    import re
    verdict, why = run_file_attack(scratch, attack)
    assert verdict == "FAIL", f"SILENTLY ACCEPTED: {name} ({what})"
    assert re.search(expect, why), f"{name}: rejected, but not for the expected reason: {why}"


# ====================================================================== value layer (hash-valid but wrong)
def synthetic_frames():
    """A minimal set of Stage 3 frames that satisfies every structural invariant (170 months, 200-stock universes)."""
    sessions = pd.bdate_range("2011-06-22", I.T_STAR)
    me = pd.Series(sessions, index=sessions.to_period("M")).groupby(level=0).max()
    rows = []
    for per, t in me.items():
        if pd.Timestamp(I.FIRST_T) <= t <= pd.Timestamp(I.LAST_T):
            rows.append({"t": t, "m12": me[per - 12], "m1": me[per - 1], "s_plus": sessions[sessions > t][0],
                         "s_pp": sessions[sessions > me[per + 1]][0], "holding_month": str(per + 1),
                         "sample": "PRIMARY" if t <= pd.Timestamp("2021-11-30") else "OOS"})
    cal = pd.DataFrame(rows)
    ents = [f"E{n:03d}|INE{n:03d}|1" for n in range(210)]
    ident = pd.DataFrame({"entity_id": ents, "in_pool": [n < 205 for n in range(210)],
                          "delist_class": ["VOLUNTARY" if n == 209 else "OTHER" for n in range(210)],
                          "end_status": ["ACTIVE_AT_CUTOFF" if n < 205 else "DELISTED" for n in range(210)]})
    f = {"sessions": pd.DataFrame({"date": sessions.strftime("%Y-%m-%d")}), "identity": ident}
    first = pd.DataFrame({"date": sessions[0], "entity": ents, "r_naive": np.nan, "r_rg": np.nan, "r_raw": np.nan, "cls": "FIRST", "raw_ok": False})
    ok = pd.DataFrame({"date": sessions[1], "entity": ents, "r_naive": 0.01, "r_rg": 0.01, "r_raw": 0.01, "cls": "OK", "raw_ok": True})
    bad = pd.DataFrame({"date": [sessions[2]], "entity": [ents[0]], "r_naive": [0.0], "r_rg": [np.nan], "r_raw": [0.0], "cls": ["BAD"], "raw_ok": [False]})
    f["panel"] = pd.concat([first, ok, bad], ignore_index=True).astype({"date": "datetime64[ms]"})
    f["gap_rows"] = pd.DataFrame({"date": [sessions[2].strftime("%Y-%m-%d")], "entity": [ents[0]], "no_event": [True]})
    for s, (label, _) in I.SAMPLES.items():
        c = cal[cal["sample"] == label].reset_index(drop=True)
        u = pd.concat([pd.DataFrame({"t": t, "key": k, "entity": ents[a:a + 200], "rank": np.arange(1.0, 201.0)})
                       for t in c["t"] for k, a in (("A", 0), ("B", 0), ("C", 10))], ignore_index=True)
        for col in ("t", "m12", "m1", "s_plus", "s_pp"):
            c[col] = c[col].dt.strftime("%Y-%m-%d")
        f[f"{s}/calendar"], f[f"{s}/universes"] = c, u.assign(t=u["t"].dt.strftime("%Y-%m-%d"))
    return f


@pytest.fixture(scope="module")
def frames():
    return synthetic_frames()


def setv(frame, col, value, row=1):
    def go(f):
        f[frame] = f[frame].copy()
        f[frame][col] = f[frame][col].astype(object if isinstance(value, str) and f[frame][col].dtype != object else f[frame][col].dtype)
        f[frame].loc[f[frame].index[row], col] = value
    return go


def panel_ok_row(f):
    return f["panel"].index[f["panel"]["cls"] == "OK"][0]


def on_ok_row(col, value):
    def go(f):
        f["panel"] = f["panel"].copy()
        f["panel"].loc[panel_ok_row(f), col] = value
    return go


def replace(frame, fn):
    def go(f):
        f[frame] = fn(f[frame].copy())
    return go


VALUE_ATTACKS = [
    ("insert NaN (naive return)", on_ok_row("r_naive", np.nan), "missing naive return"),
    ("insert NaN (research return of an OK row)", on_ok_row("r_rg", np.nan), "research-grade row without a research return"),
    ("insert +inf", on_ok_row("r_naive", np.inf), "infinite value"),
    ("insert -inf", on_ok_row("r_raw", -np.inf), "infinite value"),
    ("return of -100%", on_ok_row("r_naive", -1.0), "-100% or less"),
    ("return below -100%", on_ok_row("r_rg", -1.5), "-100% or less"),
    ("unknown row class", on_ok_row("cls", "WEIRD"), "unknown class"),
    ("research return on a flagged row", replace("panel", lambda p: p.assign(r_rg=p["r_rg"].where(p["cls"] != "BAD", 0.5))), "not research-grade"),
    ("duplicate panel row", replace("panel", lambda p: pd.concat([p, p.iloc[[250]]], ignore_index=True)), "duplicate \\(date, entity\\)"),
    ("panel row on a non-session date", on_ok_row("date", pd.Timestamp("2015-08-15")), "not a market session"),
    ("panel row after the cutoff", on_ok_row("date", pd.Timestamp("2026-10-01")), "not a market session|after the research cutoff"),
    ("alter entity id (panel)", on_ok_row("entity", "GHOST|X|1"), "not in the identity table"),
    ("second FIRST row", replace("panel", lambda p: p.assign(cls=p["cls"].where(p.index != 300, "FIRST"), r_rg=p["r_rg"].where(p.index != 300, np.nan))), "FIRST row"),
    ("change column type (returns as text)", replace("panel", lambda p: p.assign(r_naive=p["r_naive"].astype(str))), "not a float column"),
    ("change column type (date as text)", replace("panel", lambda p: p.assign(date=p["date"].astype(str))), "not a date column"),
    ("remove a required column (panel)", replace("panel", lambda p: p.drop(columns="r_raw")), "columns"),
    ("extra column (panel)", replace("panel", lambda p: p.assign(note="x")), "columns"),
    ("remove a required column (calendar)", replace("primary/calendar", lambda c: c.drop(columns="s_pp")), "columns"),
    ("duplicate session", replace("sessions", lambda s: pd.concat([s, s.iloc[[5]]], ignore_index=True)), "duplicate or unsorted"),
    ("last session is not T*", replace("sessions", lambda s: s.iloc[:-1]), "is not T\\*"),
    ("reorder calendar rows", replace("oos/calendar", lambda c: c.iloc[[1, 0] + list(range(2, len(c)))].reset_index(drop=True)), "duplicate or unsorted month"),
    ("duplicate monthly calendar row", replace("primary/calendar", lambda c: pd.concat([c, c.iloc[[3]]], ignore_index=True)), "months, protocol B3"),
    ("113 primary months", replace("primary/calendar", lambda c: c.iloc[:-1]), "113 months, protocol B3 says 114"),
    ("alter a date (exit before entry)", setv("primary/calendar", "s_pp", "2012-06-29", 0), "violated"),
    ("alter a date (holiday)", setv("primary/calendar", "s_plus", "2012-07-01", 0), "not a market session"),
    ("alter a date (unparseable)", setv("oos/calendar", "t", "31/12/2021", 0), "not a date column"),
    ("missing date", setv("oos/calendar", "s_pp", None, 0), "missing date"),
    ("wrong sample label", setv("oos/calendar", "sample", "PRIMARY", 0), "wrong sample label"),
    ("wrong holding month", setv("primary/calendar", "holding_month", "2099-01", 0), "holding month"),
    ("alter entity id (universe)", setv("primary/universes", "entity", "GHOST|X|1", 7), "not in the identity table"),
    ("duplicate universe member", replace("primary/universes", lambda u: pd.concat([u, u.iloc[[0]]], ignore_index=True)), "duplicate \\(t, key, entity\\)"),
    ("199-stock universe", replace("oos/universes", lambda u: u.iloc[1:]), "exactly 200"),
    ("change column type (rank as text)", replace("oos/universes", lambda u: u.assign(rank=u["rank"].astype(str))), "not a numeric column"),
    ("insert NaN (rank)", setv("oos/universes", "rank", np.nan, 4), "NaN or infinite"),
    ("insert inf (rank)", setv("oos/universes", "rank", np.inf, 4), "NaN or infinite"),
    ("rank below 1", setv("oos/universes", "rank", 0.0, 4), "rank below 1"),
    ("step A stock outside the survivor pool", replace("primary/universes", lambda u: u.assign(entity=u["entity"].where(~((u["key"] == "A") & (u["rank"] == 1)), "E207|INE207|1"))), "outside the survivor pool"),
    ("step A list changes over time", replace("oos/universes", lambda u: u.assign(entity=u["entity"].where(~((u["key"] == "A") & (u["rank"] == 1) & (u["t"] == u["t"].max())), "E203|INE203|1"))), "not the same list"),
    ("unknown universe key", setv("primary/universes", "key", "Z", 0), "exactly 200|keys are not exactly"),
    ("unknown delisting class", setv("identity", "delist_class", "MAYBE", 3), "unknown delisting class"),
    ("duplicate identity row", replace("identity", lambda i: pd.concat([i, i.iloc[[0]]], ignore_index=True)), "duplicate entity_id"),
    ("survivor pool flag inconsistent", setv("identity", "in_pool", True, 207), "survivor pool"),
    ("gap row that is not a flagged row", setv("gap_rows", "entity", "E005|INE005|1", 0), "not a flagged panel row"),
]


@pytest.mark.parametrize("name, attack, expect", VALUE_ATTACKS, ids=[a[0] for a in VALUE_ATTACKS])
def test_value_attack_is_rejected_even_when_every_hash_would_be_valid(frames, name, attack, expect):
    f = dict(frames)
    assert I.validate_stage3(f) is True                         # the unmodified synthetic inputs are valid
    attack(f)
    with pytest.raises(ValidationError, match=expect):
        I.validate_stage3(f)


def test_reordering_panel_rows_is_an_allowed_operation_that_cannot_change_a_result(frames):
    """Class B: row order of the panel carries no information. Shown, not assumed."""
    f = dict(frames)
    f["panel"] = f["panel"].sample(frac=1.0, random_state=1).reset_index(drop=True)
    assert I.validate_stage3(f) is True
    a, b = REPRO.Matrices(frames), REPRO.Matrices(f)
    for name in ("rn", "rg", "rr"):
        assert np.array_equal(getattr(a, name), getattr(b, name), equal_nan=True)
    assert np.array_equal(a.ok, b.ok) and np.array_equal(a.bad, b.bad) and np.array_equal(a.present, b.present)


def monthly(months=114):
    t = pd.period_range("2012-07", periods=months, freq="M").astype(str)
    m = pd.DataFrame([{"t": x, "holding_month": x, "sample": "PRIMARY", "step": s, "status": "OK", "n_universe": 200, "n_rankable": 190,
                       "k": 57, "W": 0.01, "L": 0.005, "BM": 0.008, "WML": 0.005} for x in t for s in "ABCD"])
    return m


@pytest.mark.parametrize("name, fn, expect", [
    ("insert NaN", lambda m: m.assign(W=m["W"].where(m.index != 9)), "NaN or infinite"),
    ("insert +inf", lambda m: m.assign(L=m["L"].where(m.index != 9, np.inf)), "NaN or infinite"),
    ("insert -inf", lambda m: m.assign(WML=m["WML"].where(m.index != 9, -np.inf)), "NaN or infinite"),
    ("duplicate monthly row", lambda m: pd.concat([m, m.iloc[[9]]], ignore_index=True), "duplicate"),
    ("missing month", lambda m: m.iloc[4:], "not 4 steps x 114"),
    ("missing step", lambda m: m[m["step"] != "D"], "not 4 steps"),
    ("a month that is not OK", lambda m: m.assign(status=m["status"].where(m.index != 9, "NO_HOLDING_DATA")), "not OK"),
    ("remove a required column", lambda m: m.drop(columns="BM"), "missing column"),
    ("change column type", lambda m: m.assign(W=m["W"].astype(str)), "not a numeric column"),
    ("return of -100%", lambda m: m.assign(BM=m["BM"].where(m.index != 9, -1.0)), "-100%"),
])
def test_registered_monthly_file_validation(name, fn, expect):
    assert I.validate_monthly(monthly(), 114)
    with pytest.raises(ValidationError, match=expect):
        I.validate_monthly(fn(monthly()), 114, "primary_monthly.csv")


def test_step_e_validation_refuses_zero_missing_or_non_finite_costs():
    cols = [f"{p}_{s}" for p in ("cost_W", "cost_BM", "hypothetical_cost_L") for s in ("S0", "S1", "S2", "S3", "S4")]
    e = pd.DataFrame({"t": pd.period_range("2012-07", periods=114, freq="M").astype(str), "gross_W": 0.01, **{c: 0.001 for c in cols}})
    assert I.validate_step_e(e, 114)
    for bad, expect in ((e.assign(cost_W_S0=e["cost_W_S0"].where(e.index != 3, 0.0)), "zero or negative cost"),
                        (e.assign(cost_BM_S2=e["cost_BM_S2"].where(e.index != 3)), "NaN or infinite"),
                        (e.assign(gross_W=e["gross_W"].where(e.index != 3, np.inf)), "NaN or infinite"),
                        (e.drop(columns="cost_W_S4"), "15 cost columns"), (e.iloc[1:], "one row for each"),
                        (pd.concat([e, e.iloc[[0]]]), "one row for each")):
        with pytest.raises(ValidationError, match=expect):
            I.validate_step_e(bad, 114)


def test_the_numerical_comparison_refuses_nan_inf_shape_and_out_of_tolerance_values():
    c = REPRO.Compare()
    c.close("ok", [1.0, 2.0], [1.0, 2.0 + 1e-12])
    for got, want, expect in (([1.0, np.nan], [1.0, 2.0], "NaN or infinite"), ([np.inf], [np.inf], "NaN or infinite"),
                              ([1.0], [1.0, 2.0], "values recomputed"), ([1.0 + 1e-8], [1.0], "differs from the registered")):
        with pytest.raises(REPRO.Fail, match=expect):
            c.close("x", got, want)
    with pytest.raises(REPRO.Fail, match="recomputed"):
        c.same("label", "MATERIAL", "INCONCLUSIVE")


# ====================================================================== interrupted writes
def test_an_interrupted_write_never_leaves_a_complete_looking_file(tmp_path, monkeypatch):
    """New tooling writes to a temporary name and renames; a crash before the rename leaves no final file."""
    import os
    spec = importlib.util.spec_from_file_location("release_archive_fi", ROOT / "scripts" / "release_archive.py")
    ra = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ra)
    root = tmp_path / "repo"
    for rel in ("data/raw/nse_archive/a.zip", "data/stage2/datasets/r.parquet", "data/stage3/s2_mom_v1/research/panel.parquet"):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(rel.encode())
    ra.cmd_manifest(root)

    def crash(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(os, "replace", crash)
    with pytest.raises(KeyboardInterrupt):
        ra.pack(tmp_path / "archive.tar", root)
    assert not (tmp_path / "archive.tar").exists()
    monkeypatch.setattr(reg, "REGISTRY_MD", tmp_path / "REGISTRY.md")
    (tmp_path / "REGISTRY.md").write_text("old")
    with pytest.raises(KeyboardInterrupt):
        reg.write_md()
    assert (tmp_path / "REGISTRY.md").read_text() == "old"


if __name__ == "__main__":
    import contextlib
    import io
    import re
    import tempfile
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        base = make_copy(Path(tmp) / "pristine")
        for n, (name, what, attack, expect) in enumerate(FILE_ATTACKS):
            root = Path(tmp) / f"a{n}"
            subprocess.run(["cp", "-cR", str(base), str(root)], check=True)
            with contextlib.redirect_stdout(io.StringIO()):
                verdict, why = run_file_attack(root, attack)
            shutil.rmtree(root)
            rows.append({"layer": "files", "attack": name, "action": what, "outcome": "REJECTED" if verdict == "FAIL" else "SILENTLY ACCEPTED",
                         "expected_reason_seen": bool(re.search(expect, why)), "message": why[:300]})
    base = synthetic_frames()
    for name, attack, expect in VALUE_ATTACKS:
        f = dict(base)
        attack(f)
        try:
            I.validate_stage3(f)
            rows.append({"layer": "values", "attack": name, "action": "hash-valid frame with this defect", "outcome": "SILENTLY ACCEPTED", "message": ""})
        except ValidationError as e:
            rows.append({"layer": "values", "attack": name, "action": "hash-valid frame with this defect", "outcome": "REJECTED",
                         "expected_reason_seen": bool(re.search(expect, str(e))), "message": str(e)[:300]})
    Path(sys.argv[1]).write_text(json.dumps(rows, indent=1) + "\n")
    bad = [r for r in rows if r["outcome"] != "REJECTED"]
    print(f"{len(rows)} attacks, {len(rows) - len(bad)} rejected, {len(bad)} silently accepted")
    sys.exit(1 if bad else 0)
