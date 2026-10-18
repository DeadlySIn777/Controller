"""Finalize completed FAG native outputs, preserving the failed runner receipt.

Read-only on all native inputs. Only fag-r06/final-proof.json and
fag-final-status.json are written. No native job, board adoption or parity claim.
"""
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXT = Path("Z:/pcb-runs/claude-finish")
OUT = HERE / "fag-r06"
BASE = EXT / "integrate/revs/r06-stitch-plane-pads-2.kicad_pcb"
BASE_SHA = "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53"
AFTER_SHA = "a10803bbfa3aa5b7e1a859ca4c5a7b6481969c97dc038a66cef21f92e5f61789"
DONOR_SHA = "6abe14a856b2d5f13846a4911f13d1b986d07c0ddeab7b4d1fdd0d28052c196e"
BMEASURE = EXT / "integrate/measure/r06-stitch-plane-pads-2"
NET = "/motherboard_motors{slash}FIELD_GND"
sys.path.insert(0, str(HERE.parents[1] / "routing-resume-20261011"))
from partition_guard import compare
from finish_bridge_proof import ReadSet, check_summary, digest, footprint_fingerprint, library_inventory, require


def decode_filename(value):
    """GNU sha256sum escapes only backslash, newline and carriage return."""
    result, index = [], 0
    while index < len(value):
        if value[index] != "\\":
            result.append(value[index])
            index += 1
            continue
        require(index + 1 < len(value) and value[index + 1] in "\\nr", "invalid manifest filename escape")
        result.append({"\\": "\\", "n": "\n", "r": "\r"}[value[index + 1]])
        index += 2
    return "".join(result)


def native_manifest(data):
    """Keep complete paths; reject duplicate roles and malformed Windows escaping."""
    result = {}
    for line in data.decode("utf-8").splitlines():
        match = re.fullmatch(r"(\\?)([0-9a-f]{64}) [ *](.+)", line)
        require(match is not None, "invalid sha256 manifest line")
        escaped, value, path = match.groups()
        path = decode_filename(path) if escaped else path
        require("\n" not in path and "\r" not in path and "\x00" not in path, "unsafe manifest filename")
        path = path.replace("\\", "/")
        name = path.rsplit("/", 1)[-1]
        role = "board.kicad_pcb" if name.endswith(".kicad_pcb") else name
        require(role not in result, f"duplicate manifest role: {role}")
        result[role] = {"sha256": value, "path": path}
    require(set(result) == {"board.kicad_pcb", "board.kicad_pro", "board.kicad_dru", "sch.net", "fp-lib-table"},
            "manifest roles differ from exact native measurement inventory")
    return result


def canon(path):
    value = str(path).replace("\\", "/")
    # Git's /z/ mount and Windows Z:/ refer to the same workspace.
    value = re.sub(r"^/([a-zA-Z])/", lambda match: match[1] + ":/", value)
    return value.casefold()


def evaluate():
    reads = ReadSet()
    original_status = reads.json(HERE / "fag-status.json")
    require(original_status.get("phase") == "FAILED" and original_status.get("reason") == "invalid sha256 manifest line",
            "only the known completed-native manifest parsing failure may be recovered")
    inputs = reads.json(OUT / "inputs.json")
    require(inputs["base_sha256"] == BASE_SHA and inputs["donor_sha256"] == DONOR_SHA
            and canon(inputs["base"]) == canon(BASE) and inputs["selected_net"] == NET
            and inputs["modeled_current_a"] == 0.096 and inputs["adopted"] is False
            and inputs["new_gpu_jobs"] == 0, "frozen selection identity changed")
    for index, (source, expected) in enumerate(inputs["frozen_sources"].items()):
        path = Path(source)
        require(digest(reads.read(path)) == expected, f"source changed since native run: {path}")
        require(digest(reads.read(OUT / "source" / f"{index}-{path.name}")) == expected,
                f"saved source snapshot differs: {path}")
    donor = Path(inputs["donor"]) / "applied.kicad_pcb"
    require(digest(reads.read(donor)) == DONOR_SHA, "donor board changed")
    candidate = OUT / "candidate/board.kicad_pcb"
    boards = {"before": reads.read(BASE), "after": reads.read(candidate)}
    require(digest(boards["before"]) == BASE_SHA and digest(boards["after"]) == AFTER_SHA, "pinned board changed")
    footprints = {key: footprint_fingerprint(value) for key, value in boards.items()}
    require(footprints["before"] == footprints["after"], "native footprint identity/geometry/net changed")
    require(reads.read(OUT / "input/board.kicad_pcb") == boards["before"], "input baseline differs")
    additive = reads.json(OUT / "additive-guard.json")
    require(additive == {"ok": True, "problems": [], "added_tracks": 253, "added_vias": 8,
                        "removed": 0, "changed": 0, "nets": [NET], "zones": 620, "footprints": 2717},
            "native additive copper guard differs from reviewed subset")
    manifests = {"before": native_manifest(reads.read(OUT / "baseline-sha256.txt")),
                 "after": native_manifest(reads.read(OUT / "measure/sha256.txt"))}
    for name in ("partitions.json", "summary.json", "drc.json", "sha256.txt"):
        require(reads.read(OUT / ("baseline-" + name)) == reads.read(BMEASURE / name),
                f"baseline snapshot differs from authoritative r06 receipt: {name}")
    # The authoritative plain r06 receipt was renamed after targeted repair. Its
    # manifest retains the exact original repaired-directory/source paths.
    baseline_board_path = EXT / "integrate/work/r06-stitch-plane-pads-2/out.kicad_pcb"
    baseline_copy_path = EXT / "integrate/measure/r06-stitch-plane-pads-2-repaired/copy"
    for side, copy, pin in (("before", BMEASURE / "copy", BASE_SHA),
                            ("after", OUT / "measure/copy", AFTER_SHA)):
        require(manifests[side]["board.kicad_pcb"]["sha256"] == pin, "manifest board hash mismatch")
        for name, record in manifests[side].items():
            expected_path = ((baseline_board_path if name == "board.kicad_pcb" else baseline_copy_path / name)
                             if side == "before" else (candidate if name == "board.kicad_pcb" else copy / name))
            require(canon(record["path"]) == canon(expected_path), f"unexpected native manifest path: {side}/{name}")
            require(digest(reads.read(copy / name)) == record["sha256"], f"measured copy hash differs: {side}/{name}")
        for name in ("board.kicad_pro", "board.kicad_dru", "sch.net", "fp-lib-table"):
            require(manifests["before"][name]["sha256"] == manifests["after"][name]["sha256"],
                    f"native project/rules/netlist differ: {name}")
            require(reads.read(OUT / "input" / name) == reads.read(copy / name), f"copied project changed: {name}")
    inventories = {"before": library_inventory(BMEASURE / "copy", reads),
                   "after": library_inventory(OUT / "measure/copy", reads)}
    require(inventories["before"] == inventories["after"], "effective footprint libraries differ")
    before = reads.json(OUT / "baseline-partitions.json")
    after = reads.json(OUT / "measure/partitions.json")
    require(before["sha256"] == BASE_SHA and after["sha256"] == AFTER_SHA, "stale partition evidence")
    guard = compare(before, after)
    require(set(guard["per_net"]) <= {NET}, "non-selected net connectivity changed")
    drc = {side: check_summary(reads.json(path / "drc.json"), part, reads.json(path / "summary.json"), part["sha256"])
           for side, path, part in (("before", BMEASURE, before), ("after", OUT / "measure", after))}
    require(drc["before"]["kicad"] == drc["after"]["kicad"] == "10.0.4", "native version changed")
    logs = {side: reads.read(path / "drc.log").decode("utf-8") for side, path in
            (("before", BMEASURE), ("after", OUT / "measure"))}
    require(all("Failed to fetch schematic netlist for parity tests." in log
                and "Schematic parity tests require a fully annotated schematic." in log for log in logs.values()),
            "native parity log changed; review exact execution status")
    start = (OUT / "inputs.json").stat().st_mtime_ns
    for name in ("sha256.txt", "partitions.json", "drc.json", "summary.json"):
        require((OUT / "measure" / name).stat().st_mtime_ns >= start, f"native receipt predates candidate: {name}")
    require((OUT / "measure/summary.json").stat().st_mtime_ns >= (OUT / "measure/drc.json").stat().st_mtime_ns,
            "summary predates raw DRC")
    reads.read(__file__)
    reads.read(HERE.parents[1] / "routing-resume-20261011/partition_guard.py")
    reads.read(HERE.parents[1] / "routing-resume-20261011/finish_bridge_proof.py")
    reads.verify()
    passed = guard["verdict"] == "PASS" and not drc["after"]["errors"]
    return {"native_drc_connectivity_verdict": "PASS" if passed else "FAIL", "candidate": str(candidate),
            "candidate_sha256": AFTER_SHA, "base_sha256": BASE_SHA, "connectivity": guard, "drc": drc,
            "project_manifests": manifests, "footprints": footprints, "evidence_sha256": reads.hashes,
            "native_runner_recovery": "Completed raw native outputs; failed runner's manifest parser recovered independently; no KiCad rerun",
            "original_runner_status_preserved": original_status, "schematic_parity_verdict": "OPEN_NATIVE_CHECK_SKIPPED",
            "electrical_full_rail_verdict": "OPEN", "adopted": False,
            "evidence_class": "native KiCad DRC/connectivity, source and host checks; no physical or full electrical qualification",
            "limits": ["Raw DRC lists no parity items, but both logs say parity could not run because schematic annotation was incomplete",
                       "0.096 A terminal allocation, 35 um copper, 60 C resistance and 0.5 A/via remain design assumptions",
                       "Two relay islands carry zero/unspecified assigned current; fault/transient return qualification remains open",
                       "82 FIELD_A return islands remain unreachable; this addition is a partial return branch",
                       "Full field model caps require reconciliation: FA/FAG maxima 5.036/5.268 A vs design 4.58 A; FB/FBG 6.55/6.61 A vs design 4.82 A",
                       "Cluster maximum sums are assumptions, not measured simultaneous source current; no channel or current limits were reduced",
                       "Candidate extracted-copper current sharing, IR, thermal, fault, transient, isolation and return gates remain open",
                       "No manufacturing release or external/source board adoption"]}


def main():
    try:
        result = evaluate()
        phase, code = "COMPLETE", 0 if result["native_drc_connectivity_verdict"] == "PASS" else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result, phase, code = {"native_drc_connectivity_verdict": "INVALID", "reason": str(exc), "adopted": False}, "FAILED", 2
    (OUT / "final-proof.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    status = {"phase": phase, "native_drc_connectivity_verdict": result["native_drc_connectivity_verdict"],
              "completed": result.get("connectivity", {}).get("completed"), "lost": result.get("connectivity", {}).get("lost"),
              "parity": result.get("schematic_parity_verdict", "OPEN"), "adopted": False,
              "proof": str(OUT / "final-proof.json"), "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    if "reason" in result:
        status["reason"] = result["reason"]
    (HERE / "fag-final-status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
