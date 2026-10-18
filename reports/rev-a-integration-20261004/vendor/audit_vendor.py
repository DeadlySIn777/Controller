"""Read-only vendor-flow preflight grounded in current and adopted source.

This writes inspection evidence, never a dummy Efinity project/SDC/bitstream.
No license content is read, printed, hashed or transmitted.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import winreg
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def unix(path):
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


def installed_programs():
    matches = []
    for hive, base in [(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"), (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"), (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")]:
        try:
            handle = winreg.OpenKey(hive, base)
        except OSError:
            continue
        with handle:
            for index in range(winreg.QueryInfoKey(handle)[0]):
                try:
                    with winreg.OpenKey(handle, winreg.EnumKey(handle, index)) as item:
                        name = winreg.QueryValueEx(item, "DisplayName")[0]
                        if not any(term in name.lower() for term in ["efinix", "efinity", "yosys"]):
                            continue
                        row = {"display_name": name}
                        for key in ["DisplayVersion", "InstallLocation"]:
                            try:
                                row[key] = winreg.QueryValueEx(item, key)[0]
                            except OSError:
                                row[key] = None
                        matches.append(row)
                except OSError:
                    continue
    return matches


def windows_search():
    roots = [Path("C:/"), Path(os.environ["USERPROFILE"]), Path(os.environ["ProgramFiles"]), Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")), Path(os.environ["LOCALAPPDATA"])]
    matches, errors = [], []
    visited = 0
    for base in roots:
        def on_error(exc):
            errors.append({"path": exc.filename, "type": type(exc).__name__})
        for parent, directories, files in os.walk(base, topdown=True, onerror=on_error, followlinks=False):
            visited += 1
            depth = len(Path(parent).relative_to(base).parts)
            if depth >= 2:
                directories[:] = []
            else:
                directories[:] = [d for d in directories if d not in {".git", "node_modules", "Windows", "$Recycle.Bin", "System Volume Information"}]
            for name in directories + files:
                if any(term in name.lower() for term in ["efinity", "efinix", "efx_run"]):
                    item = Path(parent) / name
                    matches.append({"path": str(item), "is_directory": item.is_dir(), "is_symlink": item.is_symlink()})
    return {"roots": [str(p) for p in roots], "maximum_directory_depth": 2, "visited_directories": visited, "matched_names": matches, "errors": errors, "scope_note": "Bounded discovery, not proof that an unrelated arbitrary directory cannot contain a portable install."}


def project_artifacts():
    command = ["rg", "--files", "gateware", "hardware", "reports", "tools", "-g", "*.sdc", "-g", "*.xdc", "-g", "*.qsf", "-g", "*.peri.xml", "-g", "*.pt.xml", "-g", "*.xml", "-g", "*efinity*", "-g", "*efx_run*"]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    rows, xml_examined = [], 0
    for filename in proc.stdout.splitlines():
        item = ROOT / filename
        include = item.suffix.lower() in {".sdc", ".xdc", ".qsf"} or any(x in item.name.lower() for x in [".peri.xml", ".pt.xml", "efinity", "efx_run"])
        if item.suffix.lower() == ".xml":
            xml_examined += 1
            # Efinity XML has efx:project and the efinity namespace; KiCad netlists do not.
            with item.open("rb") as handle:
                head = handle.read(8192).lower()
            include = include or b"efinity" in head or b"efx:project" in head
        if include:
            rows.append({"path": filename.replace("\\", "/"), "sha256": sha(item), "bytes": item.stat().st_size})
    return {"rg_exit": proc.returncode, "command": command, "xml_headers_examined": xml_examined, "recognized_constraint_or_vendor_project_artifacts": rows}


def native_fpga(path):
    tree = ET.parse(path)
    component = tree.find("./components/comp[@ref='U1001']")
    mpn = None
    if component is not None:
        for field in component.findall("./fields/field"):
            if field.attrib.get("name", "").lower() in {"mpn", "mfr part #", "manufacturer part number"}:
                mpn = field.text
    nets = {}
    for net in tree.findall("./nets/net"):
        for node in net.findall("node"):
            if node.attrib.get("ref") == "U1001":
                nets[node.attrib["pin"]] = net.attrib.get("name")
    return {"reference": "U1001", "native_value": component.findtext("value") if component is not None else None, "native_mpn": mpn, "native_ball_nets": nets}


def inspect_board(design_path, native_path, official):
    design = json.loads(design_path.read_text(encoding="utf8"))
    fpga = design["components"]["U1001"]
    pins = fpga["pins"]
    counts = Counter()
    ball_rows = []
    supplies = {}
    for ball, signal in pins.items():
        row = official.get(ball, {})
        kind = "unconnected" if signal is None else "supply" if signal in {"CORE_1V2", "IO_3V3", "LOGIC_GND"} else "connected_function_or_configuration"
        counts[kind] += 1
        ball_rows.append({"ball": ball, "signal": signal, "manufacturer_name": row.get("name"), "bank": row.get("bank"), "config": row.get("config"), "clock_region": row.get("clock_region"), "lvds": row.get("lvds"), "kind": kind})
        if row.get("name", "").startswith("VCCIO"):
            supplies[ball] = {"manufacturer_name": row["name"], "bank": row.get("bank"), "source_rail": signal}
    connected_gpio = [r for r in ball_rows if r["signal"] and (r["manufacturer_name"] or "").startswith("GPIO")]
    components = design["components"]
    clock_support = {ref: {key: c[key] for key in ["value", "mpn", "pins", "role"] if key in c} for ref, c in components.items() if ref != "U1001" and (any(term in str(c.get("pins", {})) for term in ["FPGA_CLK_50M", "FPGA_CLK_SOURCE"]) or str(c.get("mpn", "")).startswith("ASE-"))}
    native = native_fpga(native_path)
    complete_native_ledger = [{**row, "native_net": native["native_ball_nets"].get(ball), "in_design_pin_dictionary": ball in pins, "source_dictionary_signal": pins.get(ball)} for ball, row in official.items()]
    native_gpio = [row for row in complete_native_ledger if row["name"].startswith("GPIO") and row["native_net"] and "unconnected-" not in row["native_net"]]
    return {"design_revision": design.get("revision"), "source_scope": design.get("scope"), "source_fpga_vendor_fit": design.get("fpga_vendor_fit"), "reference": "U1001", "mpn": fpga["mpn"], "package": fpga.get("package"), "footprint": fpga.get("footprint"), "candidate_status": fpga.get("status"), "ball_counts": dict(counts), "connected_gpio_count_including_reserved_gpio": len(connected_gpio), "connected_gpio_by_bank": dict(Counter(r["bank"] for r in connected_gpio)), "unknown_balls": [r["ball"] for r in ball_rows if not r["manufacturer_name"]], "ball_source_ledger": ball_rows, "complete_256_ball_native_ledger": complete_native_ledger, "native_ball_count": len(native["native_ball_nets"]), "missing_native_balls": [ball for ball in official if ball not in native["native_ball_nets"]], "source_dictionary_omissions": [row for row in complete_native_ledger if not row["in_design_pin_dictionary"]], "native_connected_gpio_count_including_reserved_gpio": len(native_gpio), "native_connected_gpio_by_bank": dict(Counter(row["bank"] for row in native_gpio)), "VCCIO_source_rails": supplies, "clock": {"nominal_design_hz": 50000000, "nominal_period_ns": 20, "physical_ball": "H3", "manufacturer_pin": official.get("H3"), "source_support": clock_support, "applied_SDC": False, "physical_clock_measured": False}, "native": native}


def main(out):
    if out.exists():
        raise RuntimeError("Fresh inspection output required")
    out.mkdir(parents=True)
    inputs = ["hardware/motherboard/design.json", "hardware/motherboard/netlist.xml", "hardware/motherboard/bom.csv", "hardware/motherboard/fpga-allocation-applied.json", "hardware/motherboard/fpga-allocation-proposal.json", "hardware/board_review/revisions/20261002-30/source-inputs/design.json", "hardware/board_review/revisions/20261002-30/source-inputs/netlist.xml", "hardware/board_review/revisions/20261002-30/source-inputs/bom.csv", "research/fpga-core/pins-official.json", "research/fpga-core/t20-pinout.xlsx", "research/fpga-core/trion20-ds-v6.0.pdf", "docs/MOTHERBOARD_IS2.md", "docs/MOTION_EXPANSION_8_TO_12.md", "research/fpga-core/ase.pdf", "research/fpga-core/ase.txt"]
    before = {p: sha(ROOT / p) for p in inputs}
    official = {r["ball"]: r for r in json.loads((ROOT / "research/fpga-core/pins-official.json").read_text(encoding="utf8"))}
    path_tools = {name: shutil.which(name) for name in ["efx_run.bat", "efx_run.py", "efx_run", "efinity", "yosys", "wsl", "rg"]}
    wsl = subprocess.run(["wsl", "-d", "GarciaMechBuilder", "--", "python3", unix(HERE / "audit_wsl.py")], capture_output=True, text=True, encoding="utf8", errors="replace", timeout=60)
    if wsl.returncode:
        raise RuntimeError("WSL inventory did not complete")
    wsl_data = json.loads(wsl.stdout)
    (out / "wsl-inventory.json").write_text(json.dumps(wsl_data, indent=2) + "\n", encoding="utf8")
    windows = {"platform": sys.platform, "path_tools": path_tools, "installed_program_registry_matches": installed_programs(), "vendor_environment_names_only": sorted(k for k in os.environ if any(term in k.upper() for term in ["EFINITY", "EFINIX", "LM_LICENSE", "LICENSE_FILE"])), "bounded_search": windows_search(), "license_contents_read": False}
    (out / "windows-inventory.json").write_text(json.dumps(windows, indent=2) + "\n", encoding="utf8")
    artifacts = project_artifacts()
    (out / "project-artifacts.json").write_text(json.dumps(artifacts, indent=2) + "\n", encoding="utf8")
    current = inspect_board(ROOT / inputs[0], ROOT / inputs[1], official)
    adopted = inspect_board(ROOT / inputs[5], ROOT / inputs[6], official)
    for name, item in [("current-source-board-inspection.json", current), ("adopted-source26-cad30-board-inspection.json", adopted)]:
        (out / name).write_text(json.dumps(item, indent=2) + "\n", encoding="utf8")
    unchanged = all(sha(ROOT / name) == digest for name, digest in before.items())
    receipt = {"status": "BLOCKED", "inspection_completed": True, "utc": datetime.now(timezone.utc).isoformat(), "source_hashes": before, "source_unchanged": unchanged, "vendor_synthesis_executed": False, "vendor_place_route_executed": False, "vendor_static_timing_executed": False, "vendor_FPGA_PASS": False, "bitstream_generated": False, "hardware_programmed": False, "license_state": "UNVERIFIED_NO_DISCOVERABLE_EFINITY_INSTALL", "license_contents_read": False, "blockers": ["No Efinity executable found in PATH, program registry or bounded Windows/WSL installation discovery.", "No recognized Efinity project, Interface Designer pad project or applied SDC file in scoped workspace.", "No adopted complete current IS2 CNC3 top; structural endpoint and report-local motion/IOL1/CAP3 candidates have distinct omissions.", "Exact pad/rail/function ledger exists as source inspection; vendor interface legality, output defaults and CDC/timing constraints are unqualified."], "output_sha256": {p.name: sha(p) for p in out.iterdir() if p.is_file()}}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"status": receipt["status"], "source_unchanged": unchanged, "mpn_current": current["mpn"], "mpn_adopted": adopted["mpn"], "windows_vendor_match_count": len(windows["bounded_search"]["matched_names"]), "wsl_vendor_named_install_directories": [row for row in wsl_data["search"]["matched_names"] if row["is_directory"]], "project_artifact_count": len(artifacts["recognized_constraint_or_vendor_project_artifacts"]), "receipt": str(out / "receipt.json")}))
    return 0 if unchanged else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.out.resolve()))
