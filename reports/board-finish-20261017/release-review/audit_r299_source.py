"""Read-only exact R299 source and vendor workbook reconciliation; no board load/fill."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT / "reports/board-finish-20261011/continuation-r2"
RUN = OLD / "combined-R753-one-full-native-fill-cached-DRC-r299"
sys.path.insert(0, str(ROOT / "tools"))
from hardware_validate_fpga_core import primary_pins

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

source = RUN / "filled-copy"
paths = [p for p in source.iterdir() if p.is_file() and
         (p.suffix in {".kicad_sch", ".kicad_sym", ".kicad_pro", ".kicad_dru"}
          or p.name in {"sym-lib-table", "fp-lib-table"})]
paths += [OUT / "R299-fresh-source.xml", RUN / "cached-native-DRC-command.json",
          RUN / "drc.log", RUN / "drc.json", RUN / "native-full/actual-full-refill-geometry.json",
          ROOT / "research/fpga-core/t20-pinout.xlsx",
          ROOT / "tools/hardware_validate_fpga_core.py",
          ROOT / "reports/motherboard-fpga-source-20260930/status-deallocation-r01/interface-constraint-plan.json",
          ROOT / "hardware/motherboard/fpga-allocation-proposal.json"]
before = {str(p.relative_to(ROOT)): sha(p) for p in paths}
x = ET.parse(OUT / "R299-fresh-source.xml").getroot()
all_components = {c.attrib["ref"]: c for c in x.findall("components/comp")}
components = {r: c for r, c in all_components.items()
              if not any(p.attrib["name"] == "exclude_from_board" for p in c.findall("property"))}
g = json.loads((RUN / "native-full/actual-full-refill-geometry.json").read_text())
footprints = {f["ref"]: f for f in g["footprints"]}
source_nodes = {}
for net in x.findall("nets/net"):
    for node in net.findall("node"):
        if node.attrib["ref"] in components:
            key = (node.attrib["ref"], node.attrib["pin"])
            if key in source_nodes:
                raise ValueError("Duplicate schematic pad " + str(key))
            source_nodes[key] = net.attrib["name"]
board_nodes = {}
repeated_physical_pads = []
for pad in g["pads"]:
    if not pad["num"]:
        continue
    key = pad["ref"], pad["num"]
    if key in board_nodes:
        if board_nodes[key] != pad["net"]:
            raise ValueError("Repeated physical pad number has conflicting nets " + str(key))
        repeated_physical_pads.append(key)
    board_nodes[key] = pad["net"]
# KiCad JSON geometry retains escaped path separators. Keep all raw identities,
# reject any non-injective decoding, then compare only the display spelling.
raw_spellings = collections.defaultdict(set)
for raw in board_nodes.values():
    raw_spellings[raw.replace("{slash}", "/")].add(raw)
collisions = {k: sorted(v) for k, v in raw_spellings.items() if len(v) > 1}
missing = sorted(source_nodes.keys() - board_nodes.keys())
extra = sorted(board_nodes.keys() - source_nodes.keys())
net_errors = [{"ref": k[0], "pin": k[1], "source": source_nodes[k], "board_raw": board_nodes[k]}
              for k in source_nodes.keys() & board_nodes.keys()
              if source_nodes[k] != board_nodes[k].replace("{slash}", "/")]
value_errors = [{"ref": r, "source": components[r].findtext("value"), "board": footprints[r]["value"]}
                for r in components.keys() & footprints.keys()
                if components[r].findtext("value") != footprints[r]["value"]]
vendor = primary_pins(ROOT / "research/fpga-core/t20-pinout.xlsx")
symbol = next(p for p in x.findall("libparts/libpart") if p.attrib["part"] == "T20F256I4")
symbol_pins = {p.attrib["num"]: p.attrib["name"] for p in symbol.findall("pins/pin")}
fpga_nodes = {pin: net for (ref, pin), net in source_nodes.items() if ref == "U1001"}
pin_errors = [{"ball": b, "source": symbol_pins.get(b), "vendor": p["name"]}
              for b, p in vendor.items() if symbol_pins.get(b) != p["name"]]
plan = json.loads((ROOT / "reports/motherboard-fpga-source-20260930/status-deallocation-r01/interface-constraint-plan.json").read_text())
constraints = {r["ball"]: r for r in plan["constraints"]}
reserved = json.loads((ROOT / "hardware/motherboard/fpga-allocation-proposal.json").read_text())["reserved_gpio_balls"]
rows = []
allocation_errors = []
for ball, p in vendor.items():
    net = fpga_nodes[ball]
    c = constraints.get(ball)
    user = p["name"].startswith("GPIO") and ball not in reserved
    assigned = user and not net.startswith("unconnected-")
    if assigned and (c is None or (c["native_net"], c["manufacturer_pin"], c["bank"]) != (net, p["name"], p["bank"])):
        allocation_errors.append({"ball": ball, "native_net": net, "constraint": c})
    if user and not assigned and c is not None:
        allocation_errors.append({"ball": ball, "native_net": net, "constraint_on_nc": c})
    rows.append({"ball": ball, "manufacturer_function": p["name"], "bank": p["bank"],
                 "workbook_row": p["row"], "source_net": net,
                 "board_raw_net": board_nodes.get(("U1001", ball)),
                 "general_user_ball": user, "assigned_user_ball": assigned,
                 "logical_signal": c["logical_signal"] if c else "",
                 "direction": c["direction"] if c else "",
                 "io_standard": c["io_standard"] if c else ""})
vccio_errors = [{"ball": b, "net": fpga_nodes[b]} for b, p in vendor.items()
                if p["name"].startswith("VCCIO") and fpga_nodes[b] != "/IO_3V3"]
command = json.loads((RUN / "cached-native-DRC-command.json").read_text())
drc = json.loads((RUN / "drc.json").read_text())
parity_requested = "--schematic-parity" in command["args"]
parity_logged = "Found 0 schematic parity issues" in (RUN / "drc.log").read_text()
checks = {
    "on_board_components_exact": set(components) == set(footprints),
    "all_numbered_board_pad_set_exact": not missing and not extra,
    "raw_net_display_decode_injective": not collisions,
    "all_numbered_pad_nets_exact_after_injective_KiCad_escape_decode": not net_errors,
    "all_component_values_exact": not value_errors,
    "manufacturer_256_ball_names_exact": len(symbol_pins) == len(vendor) == 256 and not pin_errors,
    "actual_256_FPGA_pad_net_names_exact": len(fpga_nodes) == 256 and not [e for e in net_errors if e["ref"] == "U1001"],
    "current_assigned_pin_bank_contract_exact": not allocation_errors,
    "all_VCCIO_pads_source_IO3V3": not vccio_errors,
    "native_schematic_parity_requested_logged_and_empty": parity_requested and parity_logged and not drc["schematic_parity"],
}
result = {"scope": "Fresh schematic export versus exact saved actual R299 native geometry; physical source and vendor workbook inspection only",
          "checks": checks, "on_board_components": len(components), "excluded_schematic_only_components": len(all_components) - len(components),
          "numbered_board_pads": len(board_nodes), "source_nodes": len(source_nodes),
          "actual_numbered_physical_pads_including_same_number_lands": sum(bool(p["num"]) for p in g["pads"]),
          "repeated_physical_pads_with_same_net": repeated_physical_pads,
          "source_sheet_count": len(x.findall("design/sheet")),
          "fpga_user_balls": sum(r["general_user_ball"] for r in rows),
          "fpga_assigned_user_balls": sum(r["assigned_user_ball"] for r in rows),
          "fpga_free_user_balls": sum(r["general_user_ball"] and not r["assigned_user_ball"] for r in rows),
          "FPGA_bank_user_counts": dict(collections.Counter(r["bank"] for r in rows if r["general_user_ball"])),
          "drc_ordinary_errors": sum(p["severity"] == "error" for p in drc["violations"]),
          "drc_ordinary_warnings": sum(p["severity"] == "warning" for p in drc["violations"]),
          "errors": {"missing_pads": missing, "extra_pads": extra, "net_spelling_collisions": collisions,
                     "pad_nets": net_errors, "values": value_errors, "vendor_pin_names": pin_errors,
                     "allocation": allocation_errors, "vccio": vccio_errors},
          "input_sha256": before, "inputs_unchanged": all(sha(ROOT / p) == v for p, v in before.items()),
          "vendor_fit": False, "vendor_timing": False, "physical_qualification": False,
          "manufacturing_ready": False, "adopted": False}
with (OUT / "R299-actual-256-ball-source-pinmap.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
(OUT / "R299-source-parity-and-bank-review.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k not in {"input_sha256", "errors"}}, indent=2))
