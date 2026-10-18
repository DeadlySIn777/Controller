"""Create the canonical BLOCKED vendor receipt from actual retained evidence."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


preflight = read(HERE / "preflight-r03/receipt.json")
windows = read(HERE / "preflight-r03/windows-inventory.json")
wsl = read(HERE / "preflight-r03/wsl-inventory.json")
projects = read(HERE / "preflight-r03/project-artifacts.json")
board = read(HERE / "preflight-r03/current-source-board-inspection.json")
adopted = read(HERE / "preflight-r03/adopted-source26-cad30-board-inspection.json")
mapping = read(HERE / "structural-family-r01/receipt.json")
stats = read(HERE / "structural-family-r01/mapped-stat.json")
iol1_path = HERE.parent / "rtl/current-iol1-r01/receipt.json"
iol1 = read(iol1_path)
mapped = read(HERE / "structural-family-r01/cnc3_frame_endpoint_efinix.json")
ports = mapped["modules"]["cnc3_frame_endpoint"]["ports"]
source_ledger = dict(preflight["source_hashes"])
source_ledger.update({"gateware/v3/" + key: value for key, value in mapping["source_hashes"].items()})
unchanged = all(sha(ROOT / key) == value for key, value in source_ledger.items())
if not unchanged or not preflight["source_unchanged"] or not mapping["source_unchanged"]:
    raise RuntimeError("Inspection sources changed; a new run is required")
assert board["mpn"] == adopted["mpn"] == "T20F256I4"
assert board["native_ball_count"] == adopted["native_ball_count"] == 256
assert not board["missing_native_balls"] and not adopted["missing_native_balls"]
assert not projects["recognized_constraint_or_vendor_project_artifacts"]
assert mapping["status"] == "PASS" and mapping["family_synthesis_only"]
assert not mapping["Efinity_fit_timing"] and not mapping["clock_frequency_qualified"]
receipt = {
    "status": "BLOCKED",
    "evidence_class": "VENDOR_QUALIFICATION_BLOCKED_NOT_FPGA_PASS",
    "actual_device": "T20F256I4",
    "device_scope": "Current and adopted Source26/CAD30 candidate U1001; industrial temperature designator I, speed grade4, FBGA256 13x13mm0.8mm. No device substitution.",
    "utc": datetime.now(timezone.utc).isoformat(),
    "executed_vendor_flow": False,
    "executed_vendor_synthesis": False,
    "executed_vendor_place_route": False,
    "executed_vendor_static_timing": False,
    "FPGA_PASS": False,
    "manufacturing_ready": False,
    "physical_qualification": False,
    "bitstream_generated": False,
    "hardware_programmed": False,
    "license_state": "NOT_DEMONSTRATED",
    "license_contents_read_printed_hashed_or_transmitted": False,
    "tool_search_scope": {
        "windows": {"PATH_commands": list(windows["path_tools"]), "uninstall_registry": "HKLM64/HKLM32/HKCU", "directory_roots": windows["bounded_search"]["roots"], "maximum_depth": 2, "visited_directories": windows["bounded_search"]["visited_directories"], "permission_errors_count": len(windows["bounded_search"]["errors"]), "vendor_named_matches": windows["bounded_search"]["matched_names"]},
        "WSL": {"inspected_distro": "GarciaMechBuilder", "PATH_commands": list(wsl["path_tools"]), "directory_roots": wsl["search"]["roots"], "maximum_depth": 5, "visited_directories": wsl["search"]["visited_directories"], "vendor_named_installation_directories": [r for r in wsl["search"]["matched_names"] if r["is_directory"]], "other_listed_distro_not_inspected": "docker-desktop"},
        "limitations": "Bounded installation discovery. No exhaustive global absence claim, no license-secret read or activation attempt.",
    },
    "tool_finding": "No Efinity executable, registered installation or vendor installation directory discovered on inspected execution surfaces. Existing isolated Yosys0.52/ABC/family models are distinct.",
    "project_finding": {"recognized_vendor_project_or_applied_constraint_count": 0, "searched_roots": ["gateware", "hardware", "reports", "tools"], "xml_headers_examined": projects["xml_headers_examined"], "complete_adopted_IS2_CNC3_motherboard_top": False},
    "pin_finding": {"native_balls_accounted": 256, "native_connected_GPIO_including_configuration": 147, "user_function_GPIO_including_clock": 135, "reserved_configuration_GPIO": 12, "unconnected_GPIO": 48, "VCCIO_source_pad_count": 14, "VCCIO_source_rail": "IO_3V3", "vendor_Interface_Designer_checked": False, "bank_IO_standard_pad_default_legality_qualified": False, "source_dictionary_omissions": "20 unused LVDS GPIO +REF_RES; native netlist explicitly unconnected, full256-ball ledger preserved"},
    "timing_finding": {"nominal_clock_hz": 50000000, "nominal_clock_period_ns": 20, "clock_ball": "H3", "manufacturer_clock_pin": "GPIOL_24_CLK0", "clock_bank": "BANK1B", "clock_source": "ASE-50.000MHZ-L-C-T through33R source resistor", "applied_SDC_found": False, "external_IO_delay_CDC_reset_constraints_qualified": False, "routed_setup_hold_recovery_removal_checked": False, "physical_clock_measured": False},
    "executed_family_mapping_only": {"status": mapping["status"], "tool": "Yosys0.52 synth_efinix", "source": "Five current gateware/v3/rtl Verilog sources", "top": "cnc3_frame_endpoint", "primitive_counts_not_vendor_utilization": stats["design"]["num_cells_by_type"], "port_count": len(ports), "port_bit_positions": sum(len(p["bits"]) for p in ports.values()), "scope": "Structural CRC/frame validation/packing boundary with wide internal buses; no complete stateful twelve-motion/provider/IS2 board top", "receipt": "structural-family-r01/receipt.json", "receipt_sha256": sha(HERE / "structural-family-r01/receipt.json")},
    "separate_current_IOL1_mapping": {"receipt": "../rtl/current-iol1-r01/receipt.json", "receipt_sha256": sha(iol1_path), "scope": "Historical six-motion/two-encoder plus four read-only IOL1 lanes; not complete twelve-axis IS2; actual C/HDL replay is separately classified"},
    "blockers": preflight["blockers"],
    "actionable_unblocking_work": ["Make real T20-supporting Efinity install/version/patch and validated local entitlement available", "Adopt complete source-bound IS2 CNC3 physical motherboard wrapper with truthful providers", "Create real T20F256I4 Interface Designer pad/bank/config/default project from exact native ledger", "Complete justified primary/externalIO/reset/CDC constraints, then run actual interface/map/pnr/static timing and inspect all reports"],
    "source_ledger_hashes": source_ledger,
    "source_unchanged_at_finalization": unchanged,
    "evidence_artifact_sha256": {p.relative_to(HERE).as_posix(): sha(p) for p in HERE.rglob("*") if p.is_file() and p != HERE / "receipt.json" and "__pycache__" not in p.parts},
}
(HERE / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
print(json.dumps({"status": receipt["status"], "actual_device": receipt["actual_device"], "executed_vendor_flow": False, "source_unchanged": unchanged, "receipt": str(HERE / "receipt.json"), "sha256": sha(HERE / "receipt.json")}))
