"""Release-side integrity checks for S2-MOM-v1 (read-only; the frozen experiment code is not touched).

    registry record (root of trust)
      -> anchors.stage3_manifest_sha256
      -> data/stage3/s2_mom_v1/manifest.json
      -> outputs_sha256 / inputs_sha256 / code_sha256
      -> the files

verify_stage3() walks that chain and raises ProvenanceError at the first broken link. A manifest is
never trusted because it agrees with the files beside it: it must first equal the hash the registry
holds. validate_inputs() repeats, as explicit raises, the structural checks that the frozen builder
states as `assert` (switched off by python -O) and the value checks the frozen matrix builder omits.
"""

import hashlib
import json
from pathlib import Path

from src.config import BASE_DIR
from src.registry import experiments

EXPERIMENT_ID = "S2-MOM-v1"
STAGE3 = "data/stage3/s2_mom_v1"
OUTPUTS = ("research/panel.parquet", "research/sessions.csv", "research/identity.csv", "research/gap_rows.csv",
           "primary/calendar.csv", "primary/universes.csv", "oos/calendar.csv", "oos/universes.csv")
CHECK_FILES = ("checks/pre_run_checks_primary.json", "checks/pre_run_checks_oos.json", "checks/stage2_rebuild_20261005.log")
STAGE2_INPUTS = {"univ1": "data/stage2/universe/univ1_pit_universe.parquet",
                 "ret1_1_manifest": "data/stage2/returns/ret1_1_manifest.json",
                 "id1_segments": "data/stage2/identity/id1_segments.csv",
                 "id1_entities": "data/stage2/identity/id1_entities.csv"}
RET_PREFIX = "data/stage2/datasets/ret1_1/"


class ProvenanceError(Exception):
    """A link of the registry -> manifest -> file chain is broken. Fail closed."""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _no_duplicate_keys(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ProvenanceError(f"duplicate manifest entry: {sorted(k for k in keys if keys.count(k) > 1)}")
    return dict(pairs)


def _file(root, rel, inside):
    """root/rel as a real file strictly inside root/inside - no absolute path, no '..', no symlink."""
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts or "\\" in rel:
        raise ProvenanceError(f"unsafe path in manifest: {rel!r}")
    f, base = root / rel, (root / inside).resolve()
    if f.is_symlink() or not f.is_file():
        raise ProvenanceError(f"missing input (or a symlink): {rel}")
    if base not in f.resolve().parents:
        raise ProvenanceError(f"path escapes {inside}: {rel!r}")
    return f


def _match(root, rel, want, inside):
    if not isinstance(want, str) or sha256(_file(root, rel, inside)) != want:
        raise ProvenanceError(f"{rel} does not match its recorded SHA-256")


def verify_stage3(record=None, root=BASE_DIR, stage2=True):
    """Registry anchor -> manifest -> every Stage 3 input (and, with stage2=True, the Stage 2 files and
    the code the manifest names). Returns the manifest content. Raises ProvenanceError."""
    root = Path(root)
    rec = experiments.current()[EXPERIMENT_ID] if record is None else record
    anchors = rec.get("anchors") or {}
    want = anchors.get("stage3_manifest_sha256")
    if not isinstance(want, str) or len(want) != 64:
        raise ProvenanceError("the registry record carries no Stage 3 manifest SHA-256 - the manifest is unanchored")
    man = root / STAGE3 / "manifest.json"
    if man.is_symlink() or not man.is_file():
        raise ProvenanceError("Stage 3 manifest is missing")
    raw = man.read_bytes()
    if hashlib.sha256(raw).hexdigest() != want:
        raise ProvenanceError("Stage 3 manifest does not match the SHA-256 anchored in the registry")
    try:
        content = json.loads(raw, object_pairs_hook=_no_duplicate_keys)["content"]
    except (ValueError, KeyError, TypeError) as e:
        raise ProvenanceError(f"Stage 3 manifest is unreadable: {e}") from None
    outs = content.get("outputs_sha256")
    if not isinstance(outs, dict) or set(outs) != set(OUTPUTS):
        odd = sorted(set(outs or ()) ^ set(OUTPUTS))
        raise ProvenanceError(f"manifest outputs are not exactly the eight Stage 3 inputs: {odd}")
    for rel, h in outs.items():
        _match(root, f"{STAGE3}/{rel}", h, STAGE3)
    known = {"manifest.json", *OUTPUTS, *CHECK_FILES}
    extra = sorted(p.relative_to(root / STAGE3).as_posix() for p in (root / STAGE3).rglob("*")
                   if (p.is_file() or p.is_symlink()) and p.name != ".DS_Store"
                   and p.relative_to(root / STAGE3).as_posix() not in known)
    if extra:
        raise ProvenanceError(f"unexpected file(s) in the Stage 3 input folder: {extra}")
    for rel, h in (anchors.get("stage3_check_files_sha256") or {}).items():
        _match(root, rel, h, STAGE3)
    if content.get("protocol_sha256") != rec.get("protocol_sha256"):
        raise ProvenanceError("manifest protocol SHA-256 differs from the registry record")
    ins = content.get("inputs_sha256") or {}
    if ins.get("univ1") != rec.get("universe_sha256"):
        raise ProvenanceError("manifest UNIV-1 SHA-256 differs from the registry record")
    if stage2:
        for key, rel in STAGE2_INPUTS.items():
            _match(root, rel, ins.get(key), "data/stage2")
        datasets = ins.get("ret1_1_datasets")
        if not isinstance(datasets, dict) or not datasets or any(not r.startswith(RET_PREFIX) for r in datasets):
            raise ProvenanceError("manifest RET-1.1 dataset list is missing or names an unexpected path")
        for rel, h in datasets.items():
            _match(root, rel, h, RET_PREFIX)
        on_disk = sorted(p.relative_to(root).as_posix() for p in (root / RET_PREFIX).iterdir() if p.name != ".DS_Store")
        if on_disk != sorted(datasets):
            raise ProvenanceError(f"RET-1.1 dataset folder differs from the manifest list: {sorted(set(on_disk) ^ set(datasets))}")
        for rel, h in (content.get("code_sha256") or {}).items():
            _match(root, rel, h, "src")
    return content


# ---------------------------------------------------------------------------------------------
# Explicit input validation. The frozen builder (src/stage3/data.py) states its structural checks as
# `assert`, which python -O removes, and the frozen matrix builder (ladder.wide) does not check the
# values it is given (F-07, F-10). These checks restate both as plain raises, outside frozen code.
# Constants are restated from the frozen protocol on purpose (an independent pin, not an import).
T_STAR, FIRST_T, LAST_T = "2026-09-30", "2012-06-29", "2026-07-31"          # B1.1, §9
SAMPLES = {"primary": ("PRIMARY", 114), "oos": ("OOS", 56)}                 # B3
TOP_N = 200                                                                 # B1.1
CLASSES = {"OK", "SPAN", "BAD", "FIRST"}
COLUMNS = {"panel": ["date", "entity", "r_naive", "r_rg", "r_raw", "cls", "raw_ok"], "sessions": ["date"],
           "identity": ["entity_id", "in_pool", "delist_class", "end_status"], "gap_rows": ["date", "entity", "no_event"],
           "calendar": ["t", "m12", "m1", "s_plus", "s_pp", "holding_month", "sample"],
           "universes": ["t", "key", "entity", "rank"]}
DELISTING_TYPES = {"Voluntary Delisting", "Compulsory Delisting", "Delisting - Liquidation"}        # F-25


class ValidationError(Exception):
    """A research input or a registered output violates a structural or numerical invariant. Fail closed."""


def _need(ok, message):
    if not bool(ok):
        raise ValidationError(message)


def _columns(df, name, kind=None):
    want = COLUMNS[kind or name]
    _need(list(df.columns) == want, f"{name}: columns {list(df.columns)} != {want}")


def _finite(s, name):
    import numpy as np
    import pandas as pd
    _need(pd.api.types.is_float_dtype(s) or pd.api.types.is_integer_dtype(s), f"{name}: not a numeric column ({s.dtype})")
    _need(np.isfinite(s.to_numpy(dtype=float)).all(), f"{name}: NaN or infinite value")


def load_stage3(root=BASE_DIR):
    """The eight Stage 3 inputs as frames (call verify_stage3 first: this function does not check hashes)."""
    import pandas as pd
    d = Path(root) / STAGE3
    f = {"panel": pd.read_parquet(d / "research/panel.parquet"), "sessions": pd.read_csv(d / "research/sessions.csv"),
         "identity": pd.read_csv(d / "research/identity.csv"), "gap_rows": pd.read_csv(d / "research/gap_rows.csv")}
    for s in SAMPLES:
        f[f"{s}/calendar"], f[f"{s}/universes"] = pd.read_csv(d / s / "calendar.csv"), pd.read_csv(d / s / "universes.csv")
    return f


def validate_stage3(f):
    """Structural and numerical invariants of the Stage 3 inputs. Raises ValidationError at the first breach."""
    import numpy as np
    import pandas as pd

    def dates(s, name):
        _need(not s.isna().any(), f"{name}: missing date")
        try:
            return pd.to_datetime(s, format="%Y-%m-%d") if s.dtype == object else pd.to_datetime(s)
        except (ValueError, TypeError) as e:
            raise ValidationError(f"{name}: not a date column ({e})") from None

    _columns(f["sessions"], "sessions")
    sessions = dates(f["sessions"]["date"], "sessions.date")
    _need(sessions.is_unique and sessions.is_monotonic_increasing, "sessions: duplicate or unsorted dates")
    _need(sessions.iloc[-1] == pd.Timestamp(T_STAR), f"sessions: last session {sessions.iloc[-1].date()} is not T* {T_STAR}")
    days = set(sessions)

    ident = f["identity"]
    _columns(ident, "identity")
    _need(ident["entity_id"].notna().all() and ident["entity_id"].is_unique, "identity: missing or duplicate entity_id")
    _need(set(ident["delist_class"]) <= {"VOLUNTARY", "OTHER"}, "identity: unknown delisting class")
    _need(ident["in_pool"].dtype == bool, "identity: in_pool is not boolean")
    _need(ident["end_status"].notna().all(), "identity: missing end_status")
    _need((ident.loc[ident["in_pool"], "end_status"] == "ACTIVE_AT_CUTOFF").all()
          and (ident.loc[~ident["in_pool"], "end_status"] != "ACTIVE_AT_CUTOFF").all(), "identity: survivor pool != ACTIVE_AT_CUTOFF")
    ents = set(ident["entity_id"])

    p = f["panel"]
    _columns(p, "panel")
    _need(pd.api.types.is_datetime64_any_dtype(p["date"]), f"panel.date: not a date column ({p['date'].dtype})")
    _need(p["raw_ok"].dtype == bool, "panel.raw_ok: not boolean")
    _need(not p[["date", "entity", "cls"]].isna().any().any(), "panel: missing date, entity or class")
    _need(not p.duplicated(["date", "entity"]).any(), "panel: duplicate (date, entity) row")
    _need(p["date"].isin(days).all(), "panel: row on a date that is not a market session")
    _need(p["date"].max() <= pd.Timestamp(T_STAR), "panel: row after the research cutoff")
    _need(set(p["cls"].unique()) <= CLASSES, f"panel: unknown class {sorted(set(p['cls'].unique()) - CLASSES)}")
    _need(set(p["entity"].unique()) <= ents, "panel: entity that is not in the identity table")
    for c in ("r_naive", "r_rg", "r_raw"):
        _need(pd.api.types.is_float_dtype(p[c]), f"panel.{c}: not a float column ({p[c].dtype})")
        _need(not np.isinf(p[c].to_numpy()).any(), f"panel.{c}: infinite value")
        _need((p[c].dropna() > -1).all(), f"panel.{c}: return of -100% or less")
    first = p["cls"] == "FIRST"
    _need(not p.loc[~first, "r_naive"].isna().any(), "panel: missing naive return on a row that is not a first observation")
    _need(not p.loc[p["cls"] == "OK", "r_rg"].isna().any(), "panel: research-grade row without a research return")
    _need(p.loc[p["cls"] != "OK", "r_rg"].isna().all(), "panel: research return on a row that is not research-grade")
    _need(p.loc[first].groupby("entity").size().max() == 1 and
          (p.loc[first, "date"].to_numpy() == p.groupby("entity")["date"].min().reindex(p.loc[first, "entity"]).to_numpy()).all(),
          "panel: a FIRST row is not the entity's first row")

    g = f["gap_rows"]
    _columns(g, "gap_rows")
    gd = dates(g["date"], "gap_rows.date")
    _need(not g.assign(date=gd).duplicated(["date", "entity"]).any(), "gap_rows: duplicate row")
    bad = p.loc[p["cls"] == "BAD", ["date", "entity"]]
    _need(len(g.assign(date=gd).merge(bad, on=["date", "entity"])) == len(g), "gap_rows: a gap row is not a flagged panel row")

    fixed = None
    for s, (label, months) in SAMPLES.items():
        cal, u = f[f"{s}/calendar"], f[f"{s}/universes"]
        _columns(cal, f"{s}/calendar", "calendar")
        _columns(u, f"{s}/universes", "universes")
        c = {k: dates(cal[k], f"{s}/calendar.{k}") for k in ("t", "m12", "m1", "s_plus", "s_pp")}
        _need(len(cal) == months, f"{s}/calendar: {len(cal)} months, protocol B3 says {months}")
        _need((cal["sample"] == label).all(), f"{s}/calendar: wrong sample label")
        _need(c["t"].is_unique and c["t"].is_monotonic_increasing and cal["holding_month"].is_unique, f"{s}/calendar: duplicate or unsorted month")
        _need(((c["m12"] < c["m1"]) & (c["m1"] < c["t"]) & (c["t"] < c["s_plus"]) & (c["s_plus"] < c["s_pp"])).all(),
              f"{s}/calendar: m12 < m1 < t < s_plus < s_pp violated")
        _need(all(set(v) <= days for v in c.values()), f"{s}/calendar: a date that is not a market session")
        _need(c["s_pp"].max() <= pd.Timestamp(T_STAR), f"{s}/calendar: exit session after the research cutoff")
        _need((c["t"] + pd.offsets.MonthBegin(1)).dt.strftime("%Y-%m").tolist() == cal["holding_month"].astype(str).tolist(),
              f"{s}/calendar: holding month is not the month after t")
        ut = dates(u["t"], f"{s}/universes.t")
        _finite(u["rank"], f"{s}/universes.rank")
        _need((u["rank"] >= 1).all(), f"{s}/universes: rank below 1")
        _need(not u.duplicated(["t", "key", "entity"]).any(), f"{s}/universes: duplicate (t, key, entity)")
        _need(set(u["key"].unique()) == {"A", "B", "C"}, f"{s}/universes: keys are not exactly A, B, C")
        _need(set(u["entity"].unique()) <= ents, f"{s}/universes: entity that is not in the identity table")
        _need(set(ut) == set(c["t"]), f"{s}/universes: selection dates differ from the calendar")
        sizes = u.groupby(["t", "key"]).size()
        _need(len(sizes) == 3 * months and (sizes == TOP_N).all(), f"{s}/universes: a universe does not have exactly {TOP_N} stocks")
        pool = set(ident.loc[ident["in_pool"], "entity_id"])
        _need(set(u.loc[u["key"].isin(["A", "B"]), "entity"]) <= pool, f"{s}/universes: step A/B stock outside the survivor pool")
        for t, grp in u[u["key"] == "A"].groupby("t"):
            fixed = fixed or frozenset(grp["entity"])
            _need(frozenset(grp["entity"]) == fixed, f"{s}/universes: step A universe is not the same list at {t}")
    first_t = pd.to_datetime(f["primary/calendar"]["t"]).min()
    last_t = pd.to_datetime(f["oos/calendar"]["t"]).max()
    _need(first_t == pd.Timestamp(FIRST_T) and last_t == pd.Timestamp(LAST_T), "calendar: first/last selection date != protocol §9")
    _need(pd.to_datetime(f["primary/calendar"]["t"]).max() < pd.to_datetime(f["oos/calendar"]["t"]).min(), "calendar: samples overlap")
    return True


def validate_delisting_types(root=BASE_DIR):
    """F-25: the delisting class is decided by the word 'Voluntary' in NSE free text; unknown wording must stop."""
    import pandas as pd
    ev = pd.read_csv(Path(root) / STAGE2_INPUTS["id1_entities"], usecols=["end_status", "end_evidence"])["end_evidence"].dropna()
    kinds = {x for x in DELISTING_TYPES if ev.str.contains(x, regex=False).any()}
    unknown = ev[ev.str.contains("elist", case=False) & ~ev.apply(lambda s: any(k in s for k in DELISTING_TYPES))]
    _need(unknown.empty, f"ID-1: unrecognised delisting wording: {sorted(set(unknown))[:3]}")
    return kinds


def validate_cutoffs():
    """The two module-level asserts of src/access.py and src/stage3/protocol.py, as explicit checks."""
    import pandas as pd
    from src.access import RESEARCH_CUTOFF
    from src.config import HOLDOUT_START
    _need(pd.Timestamp(RESEARCH_CUTOFF) + pd.Timedelta(days=1) == pd.Timestamp(HOLDOUT_START),
          "research cutoff and holdout start are not consecutive days")
    _need(pd.Timestamp(T_STAR) <= pd.Timestamp(RESEARCH_CUTOFF), "T* lies after the research cutoff")
    _need(str(RESEARCH_CUTOFF) == T_STAR, f"research cutoff {RESEARCH_CUTOFF} is not the registered T* {T_STAR}")
    return True


MONTHLY_NUMERIC = ("W", "L", "BM", "WML")


def validate_monthly(m, months, name="monthly"):
    """One saved *_monthly.csv frame: 4 steps x `months`, every month OK, every return finite and above -100%."""
    need = {"t", "holding_month", "sample", "step", "status", "n_universe", "n_rankable", "k", *MONTHLY_NUMERIC}
    _need(need <= set(m.columns), f"{name}: missing column(s) {sorted(need - set(m.columns))}")
    _need(not m.duplicated(["t", "step"]).any(), f"{name}: duplicate (month, step) row")
    _need(sorted(m["step"].unique()) == ["A", "B", "C", "D"] and len(m) == 4 * months, f"{name}: not 4 steps x {months} months")
    _need((m["status"] == "OK").all(), f"{name}: a month is not OK")
    for c in MONTHLY_NUMERIC:
        _finite(m[c], f"{name}.{c}")
        _need(c == "WML" or (m[c] > -1).all(), f"{name}.{c}: return of -100% or less")
    return True


def validate_step_e(e, months, name="step E monthly"):
    _need(e["t"].is_unique and len(e) == months, f"{name}: not one row for each of {months} months")
    cost = [c for c in e.columns if c.startswith(("cost_", "hypothetical_cost_"))]
    _need(len(cost) == 15, f"{name}: expected 15 cost columns, found {len(cost)}")
    for c in [c for c in e.columns if c != "t"]:
        _finite(e[c], f"{name}.{c}")
    _need((e[cost] > 0).all().all(), f"{name}: a month with zero or negative cost (no cost is ever zero)")
    return True


# ---------------------------------------------------------------------------------------------
# Environment (F-06)
ENVIRONMENT = "release/s2_mom_v1/ENVIRONMENT.json"
IMPORTS = ("numpy", "pandas", "scipy.stats", "pyarrow.parquet")


def environment_report(root=BASE_DIR):
    """Compare the running interpreter with the tested environment. Returns a report; raises nothing."""
    import platform
    import sys
    from importlib import metadata
    want = json.loads((Path(root) / ENVIRONMENT).read_text())
    have, missing, mismatch = {}, [], {}
    for name, version in want["packages"].items():
        try:
            have[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            have[name] = None
            missing.append(name)
            continue
        if have[name] != version:
            mismatch[name] = {"tested": version, "installed": have[name]}
    broken = {}
    for module in IMPORTS:                                  # a version string is not enough: the library must load
        try:
            __import__(module)
        except Exception as e:                              # e.g. a wheel that the operating system refuses to load
            broken[module] = f"{type(e).__name__}: {str(e)[:160]}"
    now = {"python": platform.python_version(), "implementation": platform.python_implementation(),
           "os": platform.system(), "os_release": platform.release(), "architecture": platform.machine(), "optimized": not __debug__}
    for k in ("python", "os", "architecture"):
        if now[k] != want[k]:
            mismatch[k] = {"tested": want[k], "installed": now[k]}
    return {**now, "executable": sys.executable, "packages": have, "missing": missing, "broken": broken, "mismatch": mismatch,
            "tested_environment": want["label"], "identical_to_tested": not missing and not mismatch and not broken}
