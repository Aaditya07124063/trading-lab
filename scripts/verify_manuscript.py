"""Read-only verification of the S2-MOM-v1 manuscript against the REGISTERED artifacts (Phase 10).

    python3 scripts/verify_manuscript.py [OUT.json]      # exit 0 = no flag, 1 = at least one FLAG

Nothing is recomputed from data and no experiment is run: every check compares the manuscript text with
saved, hash-registered files. Nothing is edited. A statement that a registered artifact does not support
is reported as FLAG for the researcher; this script never changes a claim.
"""

import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from src.registry import experiments  # noqa: E402

MS = ROOT / "docs/manuscript/s2_mom_v1"
MINUS = "−"
ROWS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(group, name, ok, detail=""):
    ROWS.append({"group": group, "check": name, "status": "PASS" if ok else "FLAG", "detail": detail})
    return ok


def at(obj, path):
    for k in path.split("/"):
        obj = obj[int(k)] if isinstance(obj, list) else obj[k]
    return obj


def number(text):
    return float(text.replace(MINUS, "-").replace(",", "").replace("+", ""))


def registered_hashes(rec):
    """{repository path: registered SHA-256} from the registry record (root of trust)."""
    prov, out = rec["provenance"], {}
    for run, folder in (("primary_run", "results/s2_mom_v1"), ("confirmation_run", "results/s2_mom_v1"),
                        ("step_e_run", "results/s2_mom_v1_step_e"), ("c2_run", "results/s2_mom_v1_c2")):
        out.update({f"{folder}/{k}": v for k, v in prov[run]["files_sha256"].items()})
    out["results/s2_mom_v1/sensitivity_results.json"] = prov["sensitivity_run"]["results_sha256"]
    out["results/s2_mom_v1/blinded_precision.json"] = prov["blinded_precision_artifact_sha256"]
    out[rec["protocol_file"]] = rec["protocol_sha256"]
    out["data/stage2/universe/univ1_pit_universe.parquet"] = rec["universe_sha256"]
    out.update({a["file"]: a["sha256"] for a in rec["addenda"]})
    out["docs/research/s2_mom_v1_c2_analysis_spec.md"] = prov["c2_run"]["spec_sha256"]
    out.update(rec["anchors"]["cost_schedules_sha256"])
    out.update(rec["anchors"]["stage3_check_files_sha256"])
    return out


def main(out_path=None):
    rec = experiments.current()["S2-MOM-v1"]
    prov, reg = rec["provenance"], registered_hashes(rec)
    md = (MS / "manuscript.md").read_text()

    # ---- 1. sensitivity and C2 artifacts: hashes and metadata
    g = "1 sensitivity / C2 artifacts"
    for rel in ("results/s2_mom_v1/sensitivity_results.json", "results/s2_mom_v1_c2/c2_results.json"):
        check(g, f"{rel} equals its registered SHA-256", sha(ROOT / rel) == reg[rel], reg[rel][:16])
    c2 = json.loads((ROOT / "results/s2_mom_v1_c2/c2_results.json").read_text())
    c2run = prov["c2_run"]
    check(g, "C2 file names the registered specification hash", c2["spec_sha256"] == c2run["spec_sha256"] == sha(ROOT / "docs/research/s2_mom_v1_c2_analysis_spec.md"))
    check(g, "C2 inputs recorded in the file == inputs recorded in the registry", c2["inputs_sha256"] == c2run["inputs_sha256"])
    check(g, "every C2 input still has that hash and is a registered result file",
          all(sha(ROOT / f) == h == reg.get(f) for f, h in c2["inputs_sha256"].items()), f"{len(c2['inputs_sha256'])} inputs")
    check(g, "C2 file carries the 'not blind and not confirmatory' statement", "not blind and not confirmatory" in c2["statement"])
    check(g, "C2 registry metadata: command, code hash, environment with scipy and platform",
          c2run["command"].endswith("run_s2_mom_c2.py execute") and len(c2run["code_sha256"]) == 64
          and "scipy" in c2run["environment"] and "platform" in c2run["environment"])
    check(g, "C2 Holm family m = 4 and Benjamini-Hochberg family m = 6, H5 omission stated",
          c2["holm"]["m"] == 4 and c2["benjamini_hochberg"]["m"] == 6 and "H5" in c2["benjamini_hochberg"]["note"])
    sens = json.loads((ROOT / "results/s2_mom_v1/sensitivity_results.json").read_text())
    check(g, "sensitivity file has the six frozen treatments and the two reverse-ladder variants",
          sorted(sens["sensitivity"]) == ["R_DELIST_MINUS100", "R_DELIST_ZERO", "R_GAP", "R_MISS_RAW", "R_MISS_ZERO", "R_SPAN"]
          and sorted(sens["reverse_ladder"]) == ["R_POOL", "R_RETURNS"])
    flips = sens["reliability"]["sensitivity_treatments_that_change_H1_or_H3"]
    check(g, "sensitivity file: NOT RELIABLE arises through R_SPAN only", flips == ["R_SPAN"] and sens["reliability"]["not_reliable"] is True, str(flips))
    check(g, "sensitivity run registered with the same code hash as the primary run",
          prov["sensitivity_run"]["code_sha256"] == prov["primary_run"]["code_sha256"])

    # ---- 2. every number filled from an artifact
    g = "2 numerical claims"
    audit = list(csv.DictReader(open(MS / "number_audit.csv")))
    cache, bad_src, bad_val, bad_fmt, absent = {}, [], [], [], []
    for r in audit:
        f = r["source_file"]
        if f not in cache:
            cache[f] = json.loads((ROOT / f).read_text()) if (ROOT / f).exists() and sha(ROOT / f) == reg.get(f) else None
        if cache[f] is None:
            bad_src.append(f)
            continue
        try:
            v = at(cache[f], r["json_path"])
        except (KeyError, IndexError, ValueError):
            bad_val.append(f"#{r['n']} {r['json_path']}: no such field")
            continue
        if repr(v) != r["raw_value"] and str(v) != r["raw_value"]:
            bad_val.append(f"#{r['n']} {r['json_path']}: audit {r['raw_value']} != artifact {v!r}")
        if r["scale"]:
            shown = r["reported"]
            decimals = len(shown.split(".")[1]) if "." in shown else 0
            if abs(number(shown) - float(v) * float(r["scale"])) > 0.5000001 * 10 ** -decimals:
                bad_fmt.append(f"#{r['n']} shows {shown}, artifact {float(v) * float(r['scale'])!r}")
        elif str(v) != r["reported"]:
            bad_fmt.append(f"#{r['n']} shows {r['reported']!r}, artifact {v!r}")
        if r["reported"] not in md:
            absent.append(f"#{r['n']} {r['reported']}")
    check(g, f"all {len(audit)} audited numbers come from files that are registered and unchanged", not bad_src, str(sorted(set(bad_src))))
    check(g, "each audited raw value equals the field of the registered file today", not bad_val, "; ".join(bad_val[:5]))
    check(g, "each number shown is the registered value correctly rounded", not bad_fmt, "; ".join(bad_fmt[:5]))
    check(g, "each audited number appears in manuscript.md", not absent, "; ".join(absent[:5]))
    shown = {r["reported"] for r in audit}
    design = {"0.05", "0.10", "0.30", "1.4", "0.1", "0.015", "0.5", "1.25", "4.94", "0.8", "3.3", "0.0", "2.0", "1.0", "3.1", "0.01", "3.25", "0.03", "3.0"}
    prose = re.sub(r"`[^`]*`", " ", md)                                          # hashes and paths are checked separately
    found = set(re.findall(rf"(?<![\w.])[+{MINUS}-]?\d+\.\d+(?![\w.]*\d)", prose))
    loose = sorted(x for x in found if x not in shown and x.lstrip("+" + MINUS + "-") not in design
                   and x.lstrip("+" + MINUS + "-") not in {s.lstrip("+" + MINUS + "-") for s in shown})
    ROWS.append({"group": g, "check": "decimal numbers in the text that are neither audited results nor listed design constants",
                 "status": "INFO", "detail": f"{len(loose)}: {', '.join(loose[:40])}"})
    pr = json.loads((ROOT / "results/s2_mom_v1/primary_results.json").read_text())
    se = json.loads((ROOT / "results/s2_mom_v1_step_e/step_e_results.json").read_text())
    bl = json.loads((ROOT / "results/s2_mom_v1/blinded_precision.json").read_text())
    rounded = [("about 0.58% per month", round(c2["H2d"]["primary"]["mean"], 2) == 0.58),
               ("about 1.22% per month", round(c2["H2d"]["confirmation"]["mean"], 2) == 1.22),
               ("0.591% per month", round(bl["detectable_effect_80pct_two_sided_5pct"], 3) == 0.591),
               ("114 months", pr["H1"]["n"] == 114), ("10,000 resamples", pr["H1_bootstrap"]["B"] == 10000),
               ("56 months", json.loads((ROOT / "results/s2_mom_v1/confirmation_results.json").read_text())["H1"]["n"] == 56)]
    be = se["samples"]["primary"]["break_even"]["break_even_one_way_cost_bps"]
    rounded.append((f"{be:.0f}", f"{be:.0f}" in md))
    for text, ok in rounded:
        check(g, f"rounded statement '{text}' present and supported by its artifact", ok and text in md)

    # ---- 3. hashes and protocol references printed in the manuscript
    g = "3 hashes and protocol references"
    table = re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", md)
    wrong = [f for f, h in table if not (ROOT / f).exists() or sha(ROOT / f) != h]
    check(g, f"Table A5: all {len(table)} printed hashes equal the files on disk", len(table) >= 26 and not wrong, str(wrong))
    unreg = [f for f, h in table if f in reg and reg[f] != h]
    check(g, "Table A5: every printed hash equals the registry value for that file", not unreg, str(unreg))
    not_in_registry = sorted(f for f, _ in table if f not in reg)
    ROWS.append({"group": g, "check": "Table A5 files whose hash is not held by the registry itself (verified against disk only)",
                 "status": "INFO", "detail": ", ".join(not_in_registry)})
    for name in ("primary_results.json", "sensitivity_results.json", "confirmation_results.json", "step_e_results.json", "c2_results.json", "blinded_precision.json"):
        rel = next(f for f in reg if f.endswith("/" + name))
        check(g, f"result hash of {name} is printed in the manuscript", reg[rel] in md)
    every = set(re.findall(r"\b[0-9a-f]{64}\b", md))
    known = set(reg.values()) | {h for _, h in table} | {prov["primary_run"]["code_sha256"], prov["step_e_run"]["code_sha256"], c2run["code_sha256"]}
    check(g, "no SHA-256 in the manuscript is unknown to the registry or to Table A5", every <= known, str(sorted(every - known)))
    check(g, "gross-run code hash printed == registered primary/confirmation code hash", prov["primary_run"]["code_sha256"] in md
          and prov["primary_run"]["code_sha256"] == prov["confirmation_run"]["code_sha256"])
    check(g, "protocol file, revision and freeze commit as registered",
          rec["protocol_file"] in md and "revision 4" in md and rec["freeze_commit"] in md and rec["protocol_version"] == "revision 4")
    check(g, "Addendum 1, Supplements 1-4 and the C2 specification are referenced", "Addendum 1 and Supplements 1–4" in md and "s2_mom_v1_c2_analysis_spec.md" in md)
    listed = {f for f, _ in table}
    missing = [a["file"] for a in rec["addenda"] if a["file"] not in listed]
    check(g, "Table A5 lists the hash of every registered addendum and supplement", not missing, "not listed: " + ", ".join(Path(m).name for m in missing))

    # ---- 4. wording that the registered results must support
    g = "4 wording"
    h1p, h1c = pr["H1"], json.loads((ROOT / "results/s2_mom_v1/confirmation_results.json").read_text())["H1"]
    check(g, "H1 primary is reported as INCONCLUSIVE and NOT RELIABLE, as registered",
          h1p["decision"] == "INCONCLUSIVE" and "INCONCLUSIVE; NOT RELIABLE" in md and "primary sample INCONCLUSIVE and NOT RELIABLE" in md)
    check(g, "H1 is stated as two-sided at 5%", "Two-sided, α = 0.05" in md and "(two-sided)" in md)
    check(g, "H1 confirmation is reported as NOT CONFIRMED with the opposite sign (registered means have opposite signs)",
          h1p["mean"] * h1c["mean"] < 0 and "NOT CONFIRMED (opposite sign to primary)" in md and "The primary estimand is not confirmed" in md)
    claims = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", md)
              if re.search(r"\bH1\b", s) and re.search(r"\b(is|was|are) (supported|confirmed|significant)\b", s) and not re.search(r"\bnot\b", s, re.I)]
    check(g, "no sentence says H1 is supported, confirmed or significant", not claims, " / ".join(c[:120] for c in claims[:3]))
    check(g, "the code-level label MATERIAL of the confirmation file is not presented as a protocol decision",
          not re.search(r"H1[^.\n]*\bMATERIAL\b", md), "confirmation_results.json H1.decision = " + h1c["decision"])
    h2 = c2["H2d"]
    check(g, "H2d: status CONFIRMED is the registered C2 value and is reported with the late-execution caveat",
          h2["confirmation_status"] == "CONFIRMED" and "not blind and not confirmatory" in md.lower().replace("they are ", "")
          and "executed only after the main results were known" in md)
    check(g, "H2d is described as secondary; H1 remains the headline test", "H2d was a secondary test" in md and "H1 was the test designed to carry the headline" in md)
    check(g, "H2d: one-sided test, Holm-rejected, stated as supplementary and non-confirmatory",
          c2["holm"]["H2d"]["rejected"] is True and c2["holm"]["H2d"]["sided"] == "one" and "supplementary and non-confirmatory" in md)
    check(g, "confirmation sample is described as chronological; H3 not supported there; H4 not run there",
          "chronological confirmation sample" in md and se["samples"]["confirmation"]["H3"]["supported"] is False
          and "the confirmation sample does not provide significant evidence for the same effect" in md
          and "H4 are not reported for the confirmation sample" in md)
    check(g, "cost timing: cost rules specified after the gross results and before any cost was computed",
          "The cost rules were specified after the gross results of steps A–D were known and before any cost, turnover or net return was computed" in md)
    check(g, "cost results for L and net WML are labelled hypothetical", "every net figure for L and for WML is hypothetical" in md)
    check(g, "DEV-1 and DEV-2 are disclosed by name", "DEV-1" in md and "DEV-2" in md and "scope deviation" in md)
    dev = (ROOT / "docs/research/s2_mom_v1_deviation_log.md").read_text()
    section = dev[dev.index("**Not executed.**"):dev.index("**Executed late.**")]
    items = {"H5": r"\bH5\b", "R-JK": r"R-JK", "Romano–Wolf": r"Romano", "reality check": r"reality.check", "R-skip": r"R-skip", "R-bp": r"R-bp",
             "R-wt": r"R-wt", "R-entry": r"R-entry", "R-cost": r"R-cost", "R-mono": r"R-mono", "R-ext": r"R-ext",
             "holding periods longer than one month": r"[Hh]olding periods? longer", "deflated Sharpe ratio": r"[Dd]eflated Sharpe",
             "H4 under the sensitivity treatments": r"H4 under the sensitivity", "bootstrap for tests other than H1": r"bootstrap for (any )?tests? other than H1",
             "capacity": r"[Cc]apacity", "middle portfolio": r"[Mm]iddle portfolio", "monotonicity figure": r"[Mm]onotonicity", "turnover at steps A–C": r"[Tt]urnover at steps A"}
    lost = [k for k, pat in items.items() if re.search(pat, section) and not re.search(pat, md)]
    in_log = [k for k, pat in items.items() if re.search(pat, section)]
    check(g, f"every unexecuted analysis of DEV-2 ({len(in_log)} items) is named in the manuscript", len(in_log) >= 17 and not lost, "missing: " + ", ".join(lost))
    for late in ("H2d", "Holm", "Benjamini–Hochberg", "halves", "pooled", "skewness", "worst month"):
        check(g, f"late-executed analysis '{late}' is disclosed as late", late in md[md.index("Late execution"):md.index("Late execution") + 400])
    check(g, "statement that no result was computed or seen for unexecuted analyses", 'No result was computed or seen for any analysis marked "Not executed"' in md)

    # ---- 5. the other manuscript formats carry the same numbers
    g = "5 other formats"
    html = re.sub(r"<[^>]+>", "", (MS / "manuscript.html").read_text())
    docx = re.sub(r"<[^>]+>", "", zipfile.ZipFile(MS / "manuscript.docx").read("word/document.xml").decode())
    for name, text in (("manuscript.html", html), ("manuscript.docx", docx)):
        gone = sorted({r["reported"] for r in audit if r["reported"] not in text})
        check(g, f"{name}: every audited number is present", not gone, f"{len(gone)} missing: {', '.join(gone[:8])}")
        check(g, f"{name}: the six result hashes are present", all(reg[f] in text for f in reg if f.endswith("_results.json") or f.endswith("blinded_precision.json")))
    ROWS.append({"group": g, "check": "manuscript.pdf", "status": "INFO", "detail": "binary layout; not compared number by number in this check"})

    flags = [r for r in ROWS if r["status"] == "FLAG"]
    for r in ROWS:
        print(f"{r['status']:5s} [{r['group']}] {r['check']}" + (f"  -> {r['detail']}" if r["detail"] and r["status"] != "PASS" else ""))
    print(f"\n{sum(r['status'] == 'PASS' for r in ROWS)} PASS, {len(flags)} FLAG, {sum(r['status'] == 'INFO' for r in ROWS)} INFO")
    if out_path:
        Path(out_path).write_text(json.dumps(ROWS, indent=1) + "\n")
    return ROWS


if __name__ == "__main__":
    rows = main(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(1 if any(r["status"] == "FLAG" for r in rows) else 0)
