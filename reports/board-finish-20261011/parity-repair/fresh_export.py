"""Scheduled native schematic export and semantic provenance check; no ERC/DRC."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from host_parity import load_parser
from prepare_parity import HERE, EXTERNAL, sha, write
from run_native_parity import verify_frozen


def canonical(netlist):
    if netlist["duplicate_refs"] or netlist["node_conflicts"] or netlist["name_collisions"]:
        raise ValueError("Export has duplicate references, contradictory nodes or name collisions")
    components = {}
    for ref, c in netlist["components"].items():
        components[ref] = {key: c[key] for key in ["value", "footprint", "sheet_names", "sheet_tstamps", "properties",
                                                 "dnp", "exclude_from_board", "exclude_from_bom"]}
        components[ref].update(tstamps=sorted(c["tstamps"]), pins=sorted(c["pins"]))
    nets = {name: sorted((n["ref"], n["pin"], n["pinfunction"], n["pintype"]) for n in net["nodes"])
            for name, net in netlist["nets"].items()}
    return {"components": components, "nets": nets,
            "node_assignments": sorted((ref, pin, name) for (ref, pin), name in netlist["node_net"].items())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prepared-out", required=True, type=Path)
    args = ap.parse_args()
    prepared = args.prepared_out.resolve()
    if not prepared.is_relative_to(HERE) or prepared == HERE:
        raise ValueError("Prepared output is not isolated")
    inputs = verify_frozen(prepared, prepared / "board.kicad_pcb")
    out = prepared / "source-export"
    out.mkdir(exist_ok=False)
    wrapper = EXTERNAL / "tools/heavy.sh"
    wrapper_sha = sha(wrapper)
    command = ["C:/Program Files/Git/usr/bin/sh.exe", wrapper.as_posix(), "kicad",
               "C:/Program Files/KiCad/10.0/bin/kicad-cli.exe", "sch", "export", "netlist", "--format", "kicadsexpr",
               "--output", (out / "fresh.net").as_posix(), (prepared / "source/motherboard.kicad_sch").as_posix()]
    started = time.time()
    write(out / "invocation.json", {"command": command, "started_unix": started, "slot": "shared KiCad",
          "slot_wrapper_sha256": wrapper_sha, "source_root": "motherboard.kicad_sch",
          "script_sha256": sha(__file__), "erc_run": False, "refill_run": False, "drc_run": False})
    env = os.environ.copy()
    env["PATH"] = "C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;" + env["PATH"]
    env.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
    with (out / "export.log").open("w", encoding="utf-8") as log:
        run = subprocess.run(command, env=env, cwd=prepared / "source", stdout=log, stderr=subprocess.STDOUT)
    try:
        if run.returncode != 0:
            raise ValueError("Fresh export exited " + str(run.returncode))
        verify_frozen(prepared, prepared / "board.kicad_pcb")
        if sha(wrapper) != wrapper_sha:
            raise ValueError("Slot wrapper changed during source export")
        parser = load_parser(prepared / "tools/netlist_parity.py")
        previous = parser["read_netlist"](prepared / "source/sch.net")
        fresh = parser["read_netlist"](out / "fresh.net")
        before, after = canonical(previous), canonical(fresh)
        differences = {key: before[key] != after[key] for key in before}
        if any(differences.values()):
            write(out / "semantic-differences.json", {"changed_sections": differences, "before": before, "after": after})
        result = {"verdict": "PASS" if not any(differences.values()) else "FAIL", "semantic_difference_sections": differences,
                  "evidence_class": "native KiCad schematic netlist export + semantic component/net/node comparison",
                  "saved_export_sha256": inputs["netlist_sha256"], "fresh_export_sha256": sha(out / "fresh.net"),
                  "saved_export_metadata": previous["info"], "fresh_export_metadata": fresh["info"],
                  "components": len(fresh["components"]), "nets": len(fresh["nets"]), "nodes": len(fresh["node_net"]),
                  "native_exit_code": run.returncode, "elapsed_seconds": round(time.time() - started, 3),
                  "frozen_source_inputs_unchanged": True, "cli_schematic_drc_parity": "NOT RUN by netlist export",
                  "erc_run": False, "existing_erc_warnings": "3171 prior warnings retained; no ERC rerun or reclassification",
                  "drc_run": False, "refill_run": False, "adopted": False}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {"verdict": "INVALID_OR_FAIL", "reason": str(exc), "native_exit_code": run.returncode,
                  "elapsed_seconds": round(time.time() - started, 3), "adopted": False}
    write(out / "receipt.json", result)
    print(json.dumps(result))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
