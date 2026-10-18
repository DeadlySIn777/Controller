"""Review proposal schema and real footprint pads; does not create CAD or run ERC."""
from pathlib import Path
import hashlib
import json
import pcbnew

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "indicator_spec.json"
LIB = Path("C:/Program Files/KiCad/10.0/share/kicad/footprints")
spec = json.loads(SOURCE.read_text(encoding="utf-8"))
required = {"reference", "value", "mpn", "manufacturer", "footprint", "pins",
            "pin_labels", "pin_types", "source", "notes"}
checked = []
for group in (spec["parts"], spec["pcb_features"]):
    for ref, part in group.items():
        assert required <= part.keys(), ref
        lib, name = part["footprint"].split(":")
        fp = pcbnew.FootprintLoad(str(LIB / (lib + ".pretty")), name)
        assert fp is not None, ref
        pads = {pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}
        assert pads == set(part["pins"]) == set(part["pin_labels"]) == set(part["pin_types"]), ref
        checked.append({"reference": ref, "footprint": part["footprint"], "pads": sorted(pads)})
assert len(spec["parts"]) == 11
assert len({p["mpn"] for p in spec["parts"].values()}) == 6
assert all(p["mpn"] and p["manufacturer"] for p in spec["parts"].values())
assert all(p["mpn"] is None and not p["in_bom"] for p in spec["pcb_features"].values())
assert spec["parts"]["U50"]["pins"] == {
    "1": "V_IND_3V3", "2": "IND_LED_5V", "3": "IND_LED_12V", "4": "IND_ADC",
    "5": "IND_LED_24V", "6": "IND_UPDI", "7": None, "8": "GND"}
assert spec["adc"]["adc_max_at_26_4_v_from_resistor_tolerance_only"] < 1.045
assert spec["firmware_requirements"]["maximum_cpu_clock_hz"] <= 5000000
assert not spec["implemented_firmware"] and not spec["native_erc_performed"]
assert not spec["physical_measurements_performed"]
actual_cost = sum(line["quantity_per_board"] * line["unit_price_usd"]
                  for line in spec["cost_evidence"]["lines"])
assert abs(actual_cost - spec["cost_evidence"]["computed_material_usd_per_board"]) < 1e-9
report = {
    "status": "PASS - source and footprint parity only",
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "purchased_components": 11, "unique_mpns": 6, "pcb_test_pads": 3,
    "footprints_loaded": checked, "issues": 0,
    "mcu_pin_map_primary_source": "Microchip DS40002318A section4.1, printed page13; read from manufacturer PDF with layout preserved",
    "native_schematic_erc": "NOT PERFORMED", "native_board_drc": "NOT PERFORMED",
    "firmware_or_physical_verification": "NOT PERFORMED",
    "open_items": spec["release_gates"]
}
(BASE / "indicator-source-review.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"issues": 0, "components": 11, "pcb_test_pads": 3,
                  "native_footprints_loaded": len(checked), "price_usd": round(actual_cost, 4)}))
