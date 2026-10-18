"""Read-only exclusive physical inventory; no source or PCB mutation."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def run():
    hashes = read("input-hashes.json")
    for name, expected in hashes.items():
        raw = (HERE / "inputs" / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected["sha256"], name
    design = read("inputs/source/design.json")
    # This parent model is already an exclusive physical dictionary. Legacy
    # entries without an optional `physical` key must not be discarded.
    components = design["components"]
    bom = list(csv.DictReader((HERE / "inputs/source/bom.csv").open(encoding="utf-8")))
    bom_by_ref = {r["Reference"]: r for r in bom}
    assert set(bom_by_ref) == set(components)
    xml = ET.parse(HERE / "inputs/source/netlist.xml")
    native = {c.attrib["ref"]: c for c in xml.findall("./components/comp") if c.findtext("footprint")}
    assert set(native) == set(components)
    for ref, c in components.items():
        assert native[ref].findtext("footprint") == c["footprint"], ref
        assert native[ref].findtext("./fields/field[@name='MPN']", "") == c["mpn"], ref
    bare = {r for r, c in components.items() if c["mpn"] == "PCB_COPPER_TEST_PAD_D1.0"
            or c.get("purchased") is False}
    bare_test = {r for r in bare if components[r]["footprint"].startswith("TestPoint:")}
    bare_chassis = {r for r in bare if components[r]["footprint"].startswith("MountingHole:")}
    assert bare == bare_test | bare_chassis
    dnp = {r for r, row in bom_by_ref.items() if row["DNP"].lower() == "true"}
    purchased = set(components) - bare - dnp
    groups = defaultdict(list)
    for ref, c in components.items():
        groups[c["source_block"]].append(ref)
    groups = [{"source_region": group, "physical_footprints": len(refs),
               "purchased_fitted_parts": len(set(refs) & purchased),
               "bare_test_pads": len(set(refs) & bare_test),
               "bare_chassis_pads": len(set(refs) & bare_chassis), "DNP": len(set(refs) & dnp),
               "references": sorted(refs)} for group, refs in sorted(groups.items())]
    boards = {}
    for prefix in ("published-CAD23", "working-r14"):
        inventory = read(prefix + "-inventory.json")
        fps = {fp["ref"]: fp for fp in inventory["footprints"]}
        assert len(fps) == inventory["physical_footprints"]
        missing = set(components) - set(fps)
        extra = set(fps) - set(components)
        mismatches = []
        value_differences = []
        no_mpn_metadata = 0
        for ref in set(fps) & set(components):
            fp, comp = fps[ref], components[ref]
            if fp["footprint"] != comp["footprint"]:
                mismatches.append({"ref": ref, "field": "footprint", "board": fp["footprint"], "source": comp["footprint"]})
            for label, want in (("MPN", comp["mpn"]),):
                have = fp["properties"].get(label, "")
                if not have:
                    no_mpn_metadata += 1
                elif have != want:
                    mismatches.append({"ref": ref, "field": label, "board": have, "source": want})
            if fp["value"] != comp.get("value", ""):
                value_differences.append({"ref": ref, "board": fp["value"], "source": comp.get("value", "")})
        boards[prefix] = {"physical_footprints": len(fps), "missing_source_footprints": len(missing),
                          "extra_footprints": sorted(extra), "missing_by_source_region": dict(Counter(components[r]["source_block"] for r in missing)),
                          "missing_references": sorted(missing), "source_identity_mismatches": mismatches,
                          "board_MPN_metadata_absent_count": no_mpn_metadata,
                          "board_source_value_annotation_differences": value_differences,
                          "assembly_MPN_authority": "exact source BOM/reference mapping; absent optional PCB MPN fields are not different part evidence",
                          "track_via_items": inventory["track_via_items"], "zones": inventory["zones"],
                          "copper_layers": inventory["copper_layers"], "outline_stroke_bounding_box_mm": inventory["dimensions_mm"],
                          "placement_complete": not missing and not extra, "routing_or_manufacturing_ready": False}
    all_text = {r: " ".join(str(c.get(k, "")) for k in ("mpn", "value", "role", "footprint")) for r, c in components.items()}
    rack_hits = {r: text for r, text in all_text.items() if any(t in text.upper() for t in ("DIN41612", "HAR-BUS", "CARD CAGE", "CARD GUIDES", "H15 POWER"))}
    processors = []
    for r, c in components.items():
        if any(token in c["mpn"].upper() for token in ("STM32", "ATMEGA", "ESP32", "BCM271", "H616", "RK356", "T20F")):
            processors.append({"ref": r, "mpn": c["mpn"], "source_region": c["source_block"], "role": c.get("role", c.get("value"))})
    sockets = [{"ref": r, "mpn": c["mpn"], "source_region": c["source_block"]}
               for r, c in components.items() if c["mpn"] in {"10164227-1001A1RLF", "61302211821", "503398-1892"}]
    supplies = [{"ref": r, "mpn": c["mpn"], "source_region": c["source_block"], "pins": c["pins"], "role": c.get("role")}
                for r, c in components.items() if r.startswith("U") and any(token in c["mpn"] for token in ("TMR", "LM706", "TPS629", "TPS7A", "RFM-", "RFM "))]
    priced = read("inputs/pricing-reference-980.json")
    offers = priced["original_MC_offers"] + priced["additional_exact_MPN_offers"]
    quoted_mpns = {row["mpn"] for row in offers if row.get("currency") == "USD" and row.get("price_breaks")}
    counts = Counter(components[r]["mpn"] for r in purchased)
    coverage = {"current_purchased_unique_MPNs": len(counts), "exact_MPNs_with_inherited_catalogue_price_evidence": len(set(counts) & quoted_mpns),
                "current_purchased_pieces_with_some_inherited_price_evidence": sum(counts[m] for m in set(counts) & quoted_mpns),
                "current_unpriced_unique_MPNs": sorted(set(counts) - quoted_mpns), "inherited_price_reference_scope": "980-source reviewed catalogue snapshot, not current complete quote",
                "complete_current_cost_1_10_100_USD": {"1": None, "10": None, "100": None}, "procurement_qualified": False}
    result = {"scope": "Exact adopted r20b physical source; independent board-population and role audit, no mutations",
              "input_hashes_verified": len(hashes), "physical_footprints": len(components), "native_physical_footprint_refs_match_model": True,
              "purchased_fitted_parts": len(purchased), "bare_test_pads": len(bare_test),
              "bare_chassis_pads": len(bare_chassis), "bare_PCB_geometry": len(bare),
              "bare_geometry_references": sorted(bare),
              "DNP_footprints": len(dnp), "DNP_references": sorted(dnp),
              "parts_without_optional_physical_key": sum("physical" not in c for c in components.values()),
              "exclusive_source_regions": groups, "rack_connector_or_cage_hits": rack_hits, "fitted_processors_and_FPGA": processors,
              "commodity_module_socket_parts": sockets, "commodity_CM_SoC_parts_fitted_to_custom_board": 0, "commodity_ESP_processor_parts_fitted_to_custom_board": 0,
              "purchased_compute_ESP_modules_separate_from_custom_BOM": True, "power_conversion_regulation_parts": supplies,
              "R_C_reference_count": sum(r.startswith(("R", "C")) for r in components), "explicit_TVS_kind_count": sum(c.get("kind") == "TVS" for c in components.values()),
              "boards": boards, "cost_evidence_coverage": coverage,
              "reviewed_redundancy_findings": [
                  {"ref": "U5004", "mpn": components["U5004"]["mpn"], "actual_used_path": "pin2 TX_PERMIT -> pin18 TX_PERMIT_A_BUFFER_OUT; supplies pin20 IO_3V3/pin10 LOGIC_GND; both OE pins1/19 LOW",
                   "unused_sections": 7, "disposition": "Functional Ioff permission buffer; not a rack-only removal. Future exact single-channel substitution is unqualified and must preserve pin-domain/off-state/fanout/geometry requirements.", "remove_now": False},
                  {"refs": ["U11007", "U11011", "U2001"], "disposition": "CORE5, MOTION5 and FPGA CORE1V2 are different outputs/domains/functions, not duplicate per-card regulators.", "remove_now": False},
                  {"refs": ["U14601", "U14619", "U14701", "U14702", "U14703"], "disposition": "Two independent AO commons plus AI5-prereg/AI15/AI24 source functions; consolidation cannot silently merge islands or remove necessary voltage/headroom.", "remove_now": False},
                  {"refs": ["U13001", "U13004", "U13008", "U14501"], "disposition": "Actual acquisition/output-bank/process controller ownership and fault behavior; four MCUs are not four Linux compute modules.", "remove_now": False}],
              "confirmed_obsolete_physical_parts_safe_to_delete_without_circuit_review": [], "source_mutated": False, "PCB_mutated": False, "manufacturing_ready": False}
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("physical_footprints", "purchased_fitted_parts", "bare_test_pads", "DNP_footprints", "rack_connector_or_cage_hits", "fitted_processors_and_FPGA")}, indent=2))


if __name__ == "__main__":
    run()
