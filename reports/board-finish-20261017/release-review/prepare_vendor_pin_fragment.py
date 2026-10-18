"""Emit real Efinity ISF package-pin/voltage commands from audited R299 source.

This advances peripheral assignment only. No vendor API execution, full RTL
wrapper, clock-I/O timing budget or complete electrical defaults are asserted.
"""
from pathlib import Path
import ast
import collections
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = HERE / "vendor-constraints-r1"
sys.path.insert(0, str(ROOT / "tools"))
from hardware_validate_fpga_core import primary_pins

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
csv_path = HERE / "R299-actual-256-ball-source-pinmap.csv"
xml_path = HERE / "R299-fresh-source.xml"
workbook = ROOT / "research/fpga-core/t20-pinout.xlsx"
api_pdf = OUT / "efinity-python-api-v8.7.pdf"
assert sha(api_pdf) == "55e1a80d0b015c0e78ad954492a4588d99ec5ca4b46af1cb0590319b77fb1a7a"
input_paths = [csv_path, xml_path, workbook, api_pdf, Path(__file__),
               ROOT / "tools/hardware_validate_fpga_core.py"]
inputs = {str(p): sha(p) for p in input_paths}
rows = list(csv.DictReader(csv_path.open(newline="")))
assigned = [r for r in rows if r["assigned_user_ball"] == "True"]
assert len(assigned) == 135
assert len({r["logical_signal"] for r in assigned}) == 135
assert collections.Counter(r["direction"] for r in assigned) == {"input": 64, "output": 71}
vendor = primary_pins(workbook)
x = ET.parse(xml_path).getroot()
actual_nodes = {n.attrib["pin"]: net.attrib["name"] for net in x.findall("nets/net")
                for n in net.findall("node") if n.attrib["ref"] == "U1001"}
assert len(actual_nodes) == 256
physical_banks = {}
for ball, p in vendor.items():
    if p["name"].startswith("VCCIO"):
        assert actual_nodes[ball] == "/IO_3V3"
        physical_banks.setdefault(p["name"].removeprefix("VCCIO"), []).append(ball)
assert set(physical_banks) == {"1A", "1B_1C", "1D_1E", "3A_3B_3C", "3D_3E", "4A", "4B"}
assert sum(map(len, physical_banks.values())) == 14
logical_to_physical = {"BANK" + logical: physical for physical in physical_banks
                       for logical in physical.split("_")}
assert all(r["bank"] in logical_to_physical for r in assigned)
enum = "3.3_V_LVTTL_/_LVCMOS"
lines = [
    "# Efinity Interface Scripting File: R299 exact physical GPIO assignment fragment",
    "# Device/package T20F256; actual fitted MPN T20F256I4, industrial/speed4.",
    "# Import into a NEW EMPTY T20F256 Interface Designer design only.",
    "# Same3.3V electrical intent; Trion enum from Efinity Python APIv8.7 Table61.",
    "# 135 assigned user functions; 48 NC/12 configuration GPIO remain unassigned.",
    "# Complete RTL binding, pad defaults/drive/slew and timing still require qualification.",
    "# No bitstream-generation, device configuration or license actions in this file.",
    "",
]
for physical in physical_banks:
    lines.append('design.set_iobank_voltage(' + repr(physical) + ", '3.3')")
lines.append("")
for r in assigned:
    name, ball = r["logical_signal"], r["ball"]
    assert actual_nodes[ball] == r["source_net"]
    assert vendor[ball]["name"] == r["manufacturer_function"]
    assert vendor[ball]["bank"] == r["bank"]
    kind = "create_input_clock_gpio" if name == "FPGA_CLK_50M" else "create_" + r["direction"] + "_gpio"
    if name == "FPGA_CLK_50M":
        assert ball == "H3" and vendor[ball]["name"] == "GPIOL_24_CLK0"
    lines += [
        "# " + ball + " / " + vendor[ball]["name"] + " / " + logical_to_physical[r["bank"]] + " / " + actual_nodes[ball],
        "design." + kind + "(" + repr(name) + ")",
        "design.assign_pkg_pin(" + repr(name) + ", " + repr(ball) + ")",
        "design.set_property(" + repr(name) + ", 'IO_STANDARD', " + repr(enum) + ")",
        "",
    ]
path = OUT / "R299-T20F256-physical-pin-voltage.isf"
assert not path.exists()
source = "\n".join(lines)
tree = ast.parse(source)
compile(tree, str(path), "exec")
calls = []
for statement in tree.body:
    assert isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
    call = statement.value
    assert isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == "design"
    assert not call.keywords
    calls.append((call.func.attr, tuple(ast.literal_eval(a) for a in call.args)))
assigned_calls = [args for kind, args in calls if kind == "assign_pkg_pin"]
assert len(assigned_calls) == 135 and len({b for _, b in assigned_calls}) == 135
assert set(assigned_calls) == {(r["logical_signal"], r["ball"]) for r in assigned}
assert sum(kind == "create_input_clock_gpio" for kind, _ in calls) == 1
assert sum(kind == "create_input_gpio" for kind, _ in calls) == 63
assert sum(kind == "create_output_gpio" for kind, _ in calls) == 71
assert set(args for kind, args in calls if kind == "set_iobank_voltage") == {(b, "3.3") for b in physical_banks}
assert all(args[1:] == ("IO_STANDARD", enum) for kind, args in calls if kind == "set_property")
path.write_text(source)
report = {
    "verdict": "PASS_HOST135_PIN_SEVEN_BANK_SOURCE_BOUND_FRAGMENT_VENDOR_EXECUTION_OPEN",
    "artifact": str(path), "artifact_SHA256": sha(path),
    "format": "Efinity Interface Scripting File .isf using documented DesignAPI calls",
    "actual_device": "T20F256I4", "interface_device_name": "T20F256",
    "135_actual_native_source_balls_unique_and_exact": True,
    "GPIO_modes": {"input_clock": 1, "input": 63, "output": 71},
    "physical_IO3V3_merged_banks_and_native_power_balls": physical_banks,
    "abstract_electrical_standard": "3.3_V_LVCMOS",
    "vendor_Trion_enum": enum,
    "translation_changes_no_bank_voltage_or_electrical_intent": True,
    "Python_AST_syntax_and_exact_pin_call_coverage_PASS": True,
    "vendor_native_parse_design_check_generate_or_fit_executed": False,
    "native_Interface_Designer_bank_names_legality_default_pull_drive_slew_check": "OPEN",
    "full_current_RTL_wrapper_binding": "OPEN",
    "135_function_runtime_fit_timing": "OPEN",
    "complete_external_IO_delay_CDC_reset_timing": "OPEN",
    "purpose": "Replace missing package-pin and physical merged-bank voltage assignment input; this fragment does not claim a complete qualified implementation",
    "official_sources": [
        {"url": "https://www.efinixinc.com/docs/efinity-python-api-v8.7.pdf", "pages": [6, 28, 29, 30, 43, 74, 77], "local_pdf_SHA256": inputs[str(api_pdf)]},
        {"file": str(workbook), "sheet": "T20F256", "SHA256": inputs[str(workbook)]},
        {"file": "research/fpga-core/trion20-ds-v6.0.txt", "section": "Table16 I/O Banks by Package F256"},
    ],
    "input_sha256": inputs, "inputs_unchanged": all(sha(Path(p)) == v for p, v in inputs.items()),
    "tools_or_licenses_downloaded_or_installed": False,
    "official_API_reference_PDF_downloaded_only_after_local_tools_check": True,
    "bitstream_generated": False, "adopted": False, "manufacturing_ready": False,
}
(OUT / "constraint-fragment-receipt.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k not in {"input_sha256", "official_sources"}}, indent=2))
