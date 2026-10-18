"""Independent exclusive physical-pad obligations, without source changes."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIMARY = {
    "modules.json": ROOT / "reports/motherboard-is2-contract-20260930/inputs/spec/modules.json",
    "iso1212.pdf": ROOT / "research/digital-inputs/iso1212.pdf",
    "iso1212.txt": ROOT / "research/digital-inputs/iso1212.txt",
    "tps2663.pdf": ROOT / "reports/motherboard-power-entry-20260930/sources/tps2663.pdf",
    "tps2663.txt": ROOT / "reports/motherboard-power-entry-20260930/sources/tps2663.txt",
    "tps62901.pdf": ROOT / "reports/motherboard-power-entry-20260930/load-closure/tps62901.pdf",
    "tps62901.txt": ROOT / "reports/motherboard-power-entry-20260930/load-closure/tps62901.txt",
    "tps62902.pdf": ROOT / "reports/motherboard-power-entry-20260930/load-closure/tps62902.pdf",
    "tps62902.txt": ROOT / "reports/motherboard-power-entry-20260930/load-closure/tps62902.txt",
    "watchdog_bringup.v": ROOT / "gateware/motherboard_bringup/cnc_motherboard_watchdog_bringup.v",
    "motion_bringup.v": ROOT / "gateware/motherboard_bringup/cnc_motherboard_motion_bringup.v",
}
LEGACY_MACHINE = {
    "H13": "DOOR_STATUS_FPGA", "G14": "SPINDLE_FAULT_FPGA",
    "H14": "SPINDLE_READY_FPGA", "H15": "FEED_HOLD_FPGA",
    "H16": "CYCLE_START_FPGA", "J15": "LUBE_STATUS_FPGA", "K14": "SPARE_FPGA",
}
FAULT_OUTPUTS = {
    "A3": "FPGA_LINK_FAULT", "C6": "FPGA_WATCHDOG_FAULT",
    "A4": "FPGA_INHIBIT_FAULT", "E5": "FPGA_TIMING_FAULT",
}
PCIE_PINS = {
    "2": "CM_PCIE_CLKREQ_N", "9": "CM_PCIE_PERST_N",
    "10": "CM_PCIE_REFCLK_P", "12": "CM_PCIE_REFCLK_N",
    "16": "CM_PCIE_RX_P", "18": "CM_PCIE_RX_N",
    "22": "CM_PCIE_TX_P", "24": "CM_PCIE_TX_N",
}


def main():
    archive = HERE / "semantic-inputs"
    archive.mkdir(exist_ok=True)
    hashes = {}
    for name, source in PRIMARY.items():
        raw = source.read_bytes()
        destination = archive / name
        if destination.exists():
            assert destination.read_bytes() == raw, name + " changed after archive"
        else:
            shutil.copy2(source, destination)
        hashes[name] = {"source": str(source.relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest()}
    (HERE / "semantic-input-hashes.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    design = json.loads((HERE / "inputs/source/design.json").read_text(encoding="utf-8"))
    components = design["components"]
    native = ET.parse(HERE / "inputs/source/netlist.xml")
    rows = []
    for net in native.findall("./nets/net"):
        name = net.attrib["name"]
        nodes = [n for n in net.findall("node") if n.attrib["ref"] in components]
        if name.startswith("unconnected-") or len(nodes) != 1:
            continue
        node = nodes[0]
        ref, pin = node.attrib["ref"], node.attrib["pin"]
        c = components[ref]
        short = name.rsplit("/", 1)[-1]
        record = {"net": name, "ref": ref, "pin": pin, "function": node.attrib.get("pinfunction"),
                  "native_electrical_type": node.attrib.get("pintype"), "MPN": c["mpn"], "source_block": c["source_block"]}
        if ref == "U1001" and LEGACY_MACHINE.get(pin) == short:
            record.update(category="obsolete_dedicated_machine_status_input", manufacturer_pin_meaning="Retained bidirectional FPGA user GPIO, intended input in allocation",
                frozen_evidence="modules.json changes_to_codex_drawn_hardware: homes and machine status move to DI24 with IOL1 identity/sequence/CRC checks; lines5805-5807",
                disposition="Propose exact seven-ball native NC reconciliation after zero-copper proof. Retain all24 general DI and their real transport. No machine-status capability is removed.",
                source_change_required=True, ready_to_ignore=False)
        elif ref == "U1001" and FAULT_OUTPUTS.get(pin) == short:
            record.update(category="live_diagnostic_FPGA_output", manufacturer_pin_meaning="FPGA user GPIO; actual diagnostic RTL output",
                frozen_evidence="watchdog_bringup.v output ports; motion_bringup.v live fault assignments and feedback fault bits",
                disposition="Preserve signal; add one real accessible bare diagnostic testpad per output, explicitly test-only. No motion authority or external field port.",
                source_change_required=True, ready_to_ignore=False)
        elif ref == "J15002" and PCIE_PINS.get(pin) == short:
            record.update(category="optional_unimplemented_PCIE_compute_endpoint", manufacturer_pin_meaning="Exact CM bay PCIe sideband/differential contact; optional NVMe circuitry not populated or qualified",
                frozen_evidence="Compute r05 exact eight contact map; motherboard storage contract permits base operation using implemented SD/eMMC without optional NVMe",
                disposition="Propose exact eight-pad native NC on compute child; remove unused page ports. No SD/eMMC change, no claim of existing M.2 slot.",
                source_change_required=True, ready_to_ignore=False)
        elif c["mpn"] == "ISO1212DBQR" and pin in ("12", "13"):
            record.update(category="manufacturer_required_independent_floating_substrate_island", manufacturer_pin_meaning="Pin12 SUB2 or pin13 SUB1: internal connection to that input-chip substrate",
                primary_evidence="TI ISO1212 pin-functions table, PDF page4, text lines368-378; layout section9.4.1: retain unconnected except own floating2x2mm thermal plane",
                disposition="Keep each substrate net electrically isolated; no field/logic/common bond and no routing to another pad. Implement/document its individual floating2x2mm plane where recommended. It is not a return or supply-health signal.",
                source_change_required=False, ready_to_ignore=True, PCB_island_geometry_still_requires_check=True)
        elif ref in ("U2001", "U2002") and pin == "1":
            record.update(category="unused_regulator_builtin_power_good_output", manufacturer_pin_meaning="TPS62901/02 PG open-drain output; requires pullup for useful observation; VIN loss is not guaranteed LOW",
                primary_evidence="TPS62901 section6.3.6 / TPS62902 section7.3.6",
                disposition="Propose documented NC only after exact existing independent LTC2962/TPS3700 window monitor is confirmed as required rail-health source; do not represent this unpulled pin as observed PG.",
                source_change_required=True, ready_to_ignore=False)
        elif ref in ("U11002", "U11004", "U11006") and pin == "14":
            record.update(category="unused_eFuse_FLT_open_drain_output", manufacturer_pin_meaning="TPS26630 FLT active-low open-drain fault-event indicator; unused pin may float or connect GND",
                primary_evidence="TPS2663 pin-functions table, PDF page4, text lines533-539",
                disposition="Can be explicitly NC if no flag telemetry is promised; protection still operates. A readable fault flag needs a real pullup/receiver in its own ground domain. Required supply-health/fault-history equivalence must be demonstrated separately.",
                source_change_required=True, ready_to_ignore=False)
        elif ref == "U11006" and pin == "16":
            record.update(category="unimplemented_FIELD_B_entry_PGOOD_observation", manufacturer_pin_meaning="TPS26630 PGOOD active-high open-drain output: internalFET enhanced and sensedPGTH threshold crossed; unused pin may float",
                primary_evidence="TPS2663 pin-functions table PDF page4; modules.json PSM groups retain F_PGOOD_A/B",
                disposition="Inherited FIELD_B entry health obligation is not closed by this floating pin. Connect a real observation/qualification path or provide exact versioned equivalent from existing bank-B supply sensing before permitting NC.",
                source_change_required=True, ready_to_ignore=False, inherited_requirement_missing_at_this_endpoint=True)
        else:
            raise AssertionError("Unclassified single physical-pad net: " + name)
        rows.append(record)
    assert len(rows) == 69
    counts = Counter(r["category"] for r in rows)
    result = {"schema_version": 1, "source_revision": "r20b-2663", "physical_reference_scope": "All actual source footprints, not nonphysical schematic boundary connectors",
              "rows": rows, "category_counts": dict(counts), "single_physical_pad_named_nets": len(rows),
              "known_one_pad_floating_substrate_islands": counts["manufacturer_required_independent_floating_substrate_island"],
              "source_change_proposals_only": True, "source_mutated": False, "PCB_mutated": False, "manufacturing_ready": False}
    (HERE / "single-pad-semantic-classification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
