"""Build and measure only the additive FIELD_A return subset of the completed r06 donor.

The 0.096 A terminal allocation and 60 C/35 um copper model are assumptions.
This never adopts copper or claims complete FIELD_A supply/return qualification.
Every native step uses the shared KiCad slot limiter; no GPU job is started.
"""
import collections
import datetime
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path("Z:/pcb-runs/claude-finish")
HERE = Path(__file__).resolve().parent
BASE = ROOT / "integrate/revs/r06-stitch-plane-pads-2.kicad_pcb"
BASE_SHA = "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53"
DONOR = ROOT / "agent-work/field-pdn/testA3"
DONOR_SHA = "6abe14a856b2d5f13846a4911f13d1b986d07c0ddeab7b4d1fdd0d28052c196e"
NET = "/motherboard_motors{slash}FIELD_GND"
T = ROOT / "tools"
KPY = "C:/Program Files/KiCad/10.0/bin/python.exe"
SH = "C:/Program Files/Git/usr/bin/sh.exe"
OUT = HERE / "fag-r06"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def status(phase, **extra):
    write(HERE / "fag-status.json", {"phase": phase, "pid": os.getpid(), "adopted": False,
          "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), **extra})
    print(phase, flush=True)


def run(command, name, env):
    with (OUT / (name + ".log")).open("w", encoding="utf-8") as log:
        code = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    if code:
        raise RuntimeError(f"{name} exited {code}; inspect {OUT / (name + '.log')}")


def validate_selection(analysis, design, routes):
    if analysis["input"]["board_sha256"] != BASE_SHA or analysis["input"].get("refilled") is not True:
        raise ValueError("designer did not use the pinned refilled r06 board")
    fag = design["nets"]["FAG"]
    if fag["net"] != NET or fag["domain"] != "DOM_FIELD_A":
        raise ValueError("unexpected return net/domain")
    if fag["summary"]["segments_over_10C"] or fag["summary"]["via_groups_below_n_req"]:
        raise ValueError("selected branch violates the retained current/width/via assumptions")
    if fag["current_reaching_source_a"] != 0.096 or fag["worst_drop_v"] > fag["budget_v"]:
        raise ValueError("unexpected current assignment or modeled drop")
    for group in fag["via_groups"]:
        if not group["ok"] or group["n"] < max(1, math.ceil(group["amps"] / 0.5 - 1e-9)):
            raise ValueError("insufficient selected via array")
    selected = [record for record in routes["tracks"] if record["net"] == NET]
    if not selected:
        raise ValueError("empty selected branch")
    for record in selected:
        if record.get("kind") == "via":
            if record["d"] != 0.6 or record["drill"] != 0.3:
                raise ValueError("selected donor changed via/drill dimensions")
        elif record["layer"] != "In3.Cu" or record["width"] not in (0.3, 0.8):
            raise ValueError("selected donor changed branch layer/width")
    if sum(r.get("kind") == "via" for r in selected) != 8:
        raise ValueError("unexpected selected via count")
    return {"tracks": selected, "failures": []}


def main():
    if OUT.exists() or (HERE / "fag-status.json").exists():
        raise RuntimeError("candidate/proof already exists; do not duplicate native work")
    if sha(BASE) != BASE_SHA or sha(DONOR / "applied.kicad_pcb") != DONOR_SHA:
        raise ValueError("base or completed donor changed")
    OUT.mkdir()
    (OUT / "source").mkdir()
    source_files = [DONOR / "w/design" / n for n in ("analysis.json", "design.json", "routes.json")]
    source_files += [DONOR / "w/guard.json", DONOR / "m/report.json", DONOR / "m/summary.json",
                     T / "corridor_apply.py", T / "field_pdn_guard.py", T / "step_measure.sh",
                     T / "net_partitions.py", T / "step_summary.py", T / "heavy.sh", T / "field_pdn_spec.json"]
    frozen = {str(p): sha(p) for p in source_files}
    for index, path in enumerate(source_files):
        shutil.copyfile(path, OUT / "source" / (str(index) + "-" + path.name))
    analysis = json.loads((DONOR / "w/design/analysis.json").read_text())
    design = json.loads((DONOR / "w/design/design.json").read_text())
    routes = validate_selection(analysis, design, json.loads((DONOR / "w/design/routes.json").read_text()))
    write(OUT / "routes-fag.json", routes)
    bdir = ROOT / "integrate/measure/r06-stitch-plane-pads-2"
    for name in ("partitions.json", "summary.json", "drc.json", "sha256.txt"):
        shutil.copyfile(bdir / name, OUT / ("baseline-" + name))
    for side in ("input", "candidate"):
        target = OUT / side
        shutil.copytree(bdir / "copy", target, ignore=shutil.ignore_patterns("*.kicad_prl", "*.lck"))
        shutil.copyfile(BASE, target / "board.kicad_pcb")
        shutil.copyfile(target / "board.kicad_pro", target / "board.kicad_pro.good")
    write(OUT / "inputs.json", {"base": str(BASE), "base_sha256": BASE_SHA, "donor": str(DONOR),
          "donor_sha256": DONOR_SHA, "frozen_sources": frozen, "selected_net": NET,
          "modeled_current_a": 0.096, "via_arrays": design["nets"]["FAG"]["via_groups"],
          "unreached_field_a_return_islands": design["nets"]["FAG"]["summary"]["unreached_islands"],
          "omitted_unsafe_fb_groups": [{k: g.get(k) for k in ("name", "amps", "n", "n_req", "ok")}
                                       for g in design["nets"]["FB"]["via_groups"]],
          "scope": "Partial FIELD_A return branch; full rail current, unassigned relay currents and fault returns remain open",
          "adopted": False, "new_gpu_jobs": 0})
    env = os.environ.copy()
    env["PATH"] = "C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;" + env["PATH"]
    env.update(HEAVY="heavy.sh", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
    src, dst = OUT / "input/board.kicad_pcb", OUT / "candidate/board.kicad_pcb"
    status("APPLYING_ADDITIVE_FAG_SUBSET", output=str(OUT))
    run([SH, str(T / "heavy.sh"), "kicad", KPY, str(T / "corridor_apply.py"), str(src),
         str(OUT / "routes-fag.json"), str(dst), "--lock"], "apply", env)
    status("CHECKING_COPPER_PRESERVATION")
    run([SH, str(T / "heavy.sh"), "kicad", KPY, str(T / "field_pdn_guard.py"), str(src), str(dst),
         str(OUT / "routes-fag.json"), str(OUT / "additive-guard.json")], "additive-guard", env)
    status("NATIVE_MEASUREMENT_RUNNING", candidate_sha256=sha(dst))
    run([SH, str(T / "step_measure.sh"), str(dst), str(OUT / "measure"), str(OUT / "input")], "measure", env)
    status("EVALUATING_NATIVE_RECEIPTS")
    sys.path.insert(0, str(HERE.parents[1] / "routing-resume-20261011"))
    from partition_guard import compare, check_board
    from finish_bridge_proof import check_summary, manifest, library_inventory, ReadSet, footprint_fingerprint
    before = json.loads((OUT / "baseline-partitions.json").read_text())
    after = json.loads((OUT / "measure/partitions.json").read_text())
    check_board(before, BASE)
    check_board(after, dst)
    guard = compare(before, after)
    summaries = {side: json.loads(path.read_text()) for side, path in
                 (("before", OUT / "baseline-summary.json"), ("after", OUT / "measure/summary.json"))}
    raw = {side: json.loads(path.read_text()) for side, path in
           (("before", OUT / "baseline-drc.json"), ("after", OUT / "measure/drc.json"))}
    drc = {side: check_summary(raw[side], part, summaries[side], part["sha256"])
           for side, part in (("before", before), ("after", after))}
    bm, am = manifest((OUT / "baseline-sha256.txt").read_bytes()), manifest((OUT / "measure/sha256.txt").read_bytes())
    for name in ("board.kicad_pro", "board.kicad_dru", "sch.net", "fp-lib-table"):
        if bm[name] != am[name] or sha(OUT / "measure/copy" / name) != am[name]:
            raise ValueError(f"native project/rules mismatch: {name}")
    reads = ReadSet()
    if library_inventory(bdir / "copy", reads) != library_inventory(OUT / "measure/copy", reads):
        raise ValueError("footprint resources differ")
    reads.verify()
    if footprint_fingerprint(BASE.read_bytes()) != footprint_fingerprint(dst.read_bytes()):
        raise ValueError("native footprints or pad identities changed")
    changed = [str(p) for p in source_files if sha(p) != frozen[str(p)]]
    if sha(BASE) != BASE_SHA or changed:
        raise ValueError(f"source changed while proving: {changed}")
    native_ok = guard["verdict"] == "PASS" and not drc["after"]["errors"]
    write(OUT / "proof.json", {"native_verdict": "PASS" if native_ok else "FAIL", "connectivity": guard,
          "drc": drc, "candidate": str(dst), "candidate_sha256": sha(dst), "adopted": False,
          "electrical_full_rail_verdict": "OPEN", "evidence_class": "native KiCad DRC/connectivity plus source inspection",
          "limitations": ["0.096 A JD01 allocation, 35 um copper, 60 C resistance and 0.5 A/via are design assumptions",
                          "Two relay islands have zero/unspecified assigned current; that does not qualify fault or transient return currents",
                          "82 FIELD_A return islands remain unreachable in the donor; full4.58 A supply/return remains unqualified",
                          "Current candidate-specific extracted-copper IR, transient, thermal and isolation/return reviews remain open",
                          "This subset excludes both under-counted FIELD_B arrays (5 fitted vs7 required at3.05 A)",
                          "No copper adoption or manufacturing release"]})
    status("COMPLETE", native_verdict="PASS" if native_ok else "FAIL", completed=guard["completed"],
           lost=guard["lost"], drc_errors=drc["after"]["errors"], proof=str(OUT / "proof.json"))
    return 0 if native_ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        status("FAILED", reason=str(exc))
        raise
