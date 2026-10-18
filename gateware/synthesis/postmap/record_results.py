"""Record or check the isolated mapped-netlist functional harness evidence.

Recording and --check both re-derive the summary (assertion count, absence of
FAIL lines, exit status, Verilator warning counts, primitive-input and LUT-mask
audits) from the hashed logs and netlist. --check is read-only: it verifies file
hashes and that the re-derived summary equals the recorded one.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[2]
SUMMARY_KEYS = ("assertions_passed", "verilator_warning_counts", "lutmask_width_histogram",
                "all_LUT_inputs_above_shortened_mask_tied_zero", "missing_or_undriven_primitive_inputs",
                "unconnected_primitive_outputs", "source_RTL_used_as_DUT", "physical_timing_or_gate_delay_simulated")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_summary():
    result = (BASE / "results/exit-status.txt").read_text().strip()
    tests = (BASE / "results/tests.log").read_text()
    assert result == "0", "post-map harness exit status is not 0"
    assert "FAIL " not in tests, "post-map harness log contains FAIL lines"
    count = int(re.search(r"CNC1_COMPILED_RTL_CHECKS=(\d+)", tests).group(1))
    assert count == sum(line.startswith("PASS ") for line in tests.splitlines())
    diagnostics = (BASE / "results/verilator.log").read_text()
    assert "%Error" not in diagnostics
    warnings = Counter(re.findall(r"%Warning-([A-Z0-9_]+):", diagnostics))
    netlist = json.loads((BASE.parent / "results/cnc_endpoint_efinix.json").read_text())
    cells = netlist["modules"]["cnc_endpoint"]["cells"]
    top = netlist["modules"]["cnc_endpoint"]
    driven = {"0", "1"}
    for port in top["ports"].values():
        if port["direction"] == "input":
            driven.update(port["bits"])
    for cell in cells.values():
        for name, direction in cell["port_directions"].items():
            if direction == "output":
                driven.update(cell["connections"].get(name, []))
    unused_outputs = 0
    for cell in cells.values():
        for name, port in netlist["modules"][cell["type"]]["ports"].items():
            if port["direction"] == "input":
                assert name in cell["connections"], f"Missing primitive input: {cell['type']}.{name}"
                assert set(cell["connections"][name]) <= driven, f"Undriven primitive input: {cell['type']}.{name}"
            elif name not in cell["connections"]:
                unused_outputs += 1
    mask_widths = Counter()
    for cell in cells.values():
        if cell["type"] != "EFX_LUT4":
            continue
        mask = cell["parameters"]["LUTMASK"]
        assert not set(mask) - set("01")
        mask_widths[len(mask)] += 1
        for pin in range(4):
            if 2 ** pin >= len(mask):
                assert cell["connections"][f"I{pin}"] == ["0"], "Upper LUT input can select outside the shortened mask"
    # String keys throughout, so the summary compares equal after a JSON round trip.
    return {"assertions_passed": count,
            "verilator_warning_counts": dict(sorted(warnings.items())),
            "lutmask_width_histogram": {str(width): number for width, number in sorted(mask_widths.items())},
            "all_LUT_inputs_above_shortened_mask_tied_zero": True,
            "missing_or_undriven_primitive_inputs": 0,
            "unconnected_primitive_outputs": unused_outputs,
            "source_RTL_used_as_DUT": False, "physical_timing_or_gate_delay_simulated": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = BASE / "manifest.json"
    if args.check:
        data = json.loads(target.read_text())
        for name, expected in data["files_sha256"].items():
            assert sha(PROJECT / name) == expected, name
        summary = checked_summary()
        recorded = {key: data[key] for key in SUMMARY_KEYS}
        assert summary == recorded, f"re-derived summary {summary} differs from manifest {recorded}"
        print(f"Post-map functional evidence verified: {summary['assertions_passed']} assertions re-derived from tests.log; "
              f"exit status, warning counts and netlist audits match; {len(data['files_sha256'])} files")
        return
    summary = checked_summary()
    files = [*sorted((BASE / "input").glob("*")), *sorted((BASE / "results").glob("*")), BASE / "run.sh", Path(__file__), BASE.parent / "results/cnc_endpoint_efinix.json", BASE.parent / "manifest.json"]
    data = {"schema_version": 1, "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Mapped Efinix primitive netlist in Verilator, compiled CNC1 C driver and bit-level SPI simulation",
            "input_driver_origin": "cnc1/evidence/before-persistent-runtime/cnc1; four files snapshotted in postmap/input",
            **summary,
            "files_sha256": {str(path.relative_to(PROJECT)).replace('\\', '/'): sha(path) for path in files}}
    # LF on every host so the recorded bytes do not depend on the recording platform.
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=2) + "\n")
    print(f"Post-map tests: {summary['assertions_passed']} assertions; warnings={summary['verilator_warning_counts']}")


if __name__ == "__main__":
    main()
