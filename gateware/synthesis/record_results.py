"""Validate completed synthesis output and record exact source/tool/evidence hashes.

No hardware access or synthesis is performed by this recorder. run.sh invokes the
tools first. --check only checks the saved manifest and current source identities.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


BASE = Path(__file__).resolve().parent
PROJECT = BASE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_summary():
    results = BASE / "results"
    assert (results / "exit-status.txt").read_text().strip() == "0"
    log = (results / "synthesis.log").read_text()
    assert "ERROR:" not in log
    assert "Found and reported 0 problems." in log
    lint = (results / "verilator.log").read_text()
    assert "%Warning" not in lint and "%Error" not in lint
    data = json.loads((results / "cnc_endpoint_efinix.json").read_text())
    module = data["modules"]["cnc_endpoint"]
    assert int(module["attributes"]["top"], 2) == 1
    assert int(module["parameter_default_values"]["ENABLE_DISCOVERY"], 2) == 1
    cells = Counter(cell["type"] for cell in module["cells"].values())
    allowed = {"EFX_LUT4", "EFX_ADD", "EFX_FF", "EFX_GBUFCE", "EFX_RAM_5K"}
    assert set(cells) <= allowed, cells
    assert cells["EFX_FF"] and cells["EFX_LUT4"] and cells["EFX_GBUFCE"] == 1
    for name, count in (("step_out", 6), ("dir_out", 6), ("enc_a", 2), ("enc_b", 2), ("enc_z", 2), ("progress_wdi", 1)):
        assert len(module["ports"][name]["bits"]) == count
    cdc = (results / "cdc-check.log").read_text(encoding="utf-8")
    assert "ERROR" not in cdc and "CDC_STRUCTURAL_CHECK_PASSED" in cdc
    stat = json.loads((results / "mapped-stat.json").read_text())
    assert stat["design"]["num_cells_by_type"] == dict(cells)
    parameters = {name: int(value, 2) for name, value in module["parameter_default_values"].items()}
    return {
        "top": "cnc_endpoint", "configuration": "six-step/two-ABZ CNC1 ABI2",
        "parameters": parameters,
        "mapped_cells": dict(sorted(cells.items())), "mapped_cell_total": sum(cells.values()),
        "top_ports": {name: {"direction": port["direction"], "bits": len(port["bits"])} for name, port in module["ports"].items()},
        "top_port_bits": sum(len(port["bits"]) for port in module["ports"].values()),
        "latches": 0, "structural_check_problems": 0,
        "reference_device": "T20 / T20F256C4 candidate; package not fitted",
        "reference_equivalent_logic_elements": 19728,
        "primitive_counts_are_occupied_LE_or_fit_percentage": False,
        "scope_metadata_removed": int(re.search(r"\$scopeinfo\s+(\d+)", log).group(1)),
        "inhibit_cdc_structural_check": "passed: Verilog-2005 parse; only inhibit capture and first-stage synchronizer flip-flops see inhibit_n/inhibit_sync/inhibit_authorized at D/EN",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest_path = BASE / "manifest.json"
    if args.check:
        manifest = json.loads(manifest_path.read_text())
        for name, expected in manifest["files_sha256"].items():
            assert sha(PROJECT / name) == expected, name
        assert checked_summary() == manifest["summary"]
        print(f"Synthesis evidence verified: {len(manifest['files_sha256'])} files; unchanged ABI2 input; mapped checks pass.")
        return
    summary = checked_summary()
    sources = [BASE / "run.sh", BASE / "synth.ys", BASE / "cdc_check.ys", Path(__file__), *sorted((BASE / "input").glob("*.v"))]
    for snapshot in (BASE / "input").glob("*.v"):
        current = BASE.parent / "rtl" / snapshot.name
        assert sha(current) == sha(snapshot), f"RTL changed during synthesis: {snapshot.name}"
        sources.append(current)
    evidence = sorted(path for path in (BASE / "results").iterdir() if path.is_file())
    manifest = {
        "schema_version": 1, "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Actual Yosys Efinix-family mapping; no vendor place/route, package fit, static timing or bitstream",
        "environment": "WSL GarciaMechBuilder; isolated Debian 13 rootfs; Yosys/yosys-abc 0.52-2",
        "tool_version": (BASE / "results/yosys-version.txt").read_text().strip(),
        "summary": summary,
        "files_sha256": {str(path.relative_to(PROJECT)).replace('\\', '/'): sha(path) for path in sources + evidence},
        "not_proven": ["T20F256C4 package pin/bank fit", "vendor mapper interoperability", "routed utilization", "50 MHz timing closure", "CDC metastability/MTBF or minimum asynchronous pulse capture (only a structural inhibit CDC check is run)", "bitstream/configuration boot", "complete field I/O", "eight-step/four-encoder scope", "physical electrical or motion behavior"],
    }
    # LF on every host so the byte hash chained into the post-map manifest is checkout-stable.
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
