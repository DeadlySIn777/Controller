"""Reconcile observed catalogue prices with the actual r0.3 native BOM.

This creates costing evidence only; it does not alter CAD or release procurement.
"""
from collections import defaultdict
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
NATIVE = BASE.parent / "r0_3"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def money(value):
    return float(Decimal(str(value)).quantize(Decimal("0.0001")))


def total(rows, price_key):
    return money(sum(Decimal(str(r[price_key])) * r["quantity_per_adapter"] for r in rows))


def ref_key(ref):
    prefix, number = re.fullmatch(r"([A-Z]+)(\d+)", ref).groups()
    return prefix, int(number)


native = read(NATIVE / "parts.json")
parts = {r: p for r, p in native["parts"].items() if p.get("in_bom", True)}
assert len(parts) == 52
assert len({p["mpn"] for p in parts.values()}) == 33
assert all(p["mpn"] and p["manufacturer"] for p in parts.values())
review = read(NATIVE / "evidence" / "schematic-review.json")
assert review["actual_footprint_assembly_counts"] == {
    "smt": 47, "through_hole": 5, "pcb_test_pads": 3
}

power = read(BASE / "power-cost-observations.json")
assert power["cost_revision"] == "US-direct-qty1-and100-2"
logic = read(BASE / "logic-cost-observations.json")
indicator_spec = read(BASE / "indicator_spec.json")

# Additional qty-1 observations from the same direct USD product pages, read
# 2026-10-06. These supplement, rather than mutate, the source circuit proposal.
indicator_extra = {
    "ATTINY202-SSNR": (0.52, {1: .52},
        "Page displayed 19,237 in stock. The 4,000-piece reel price is not used.",
        "Only qty-1 cut-tape pricing was displayed; no 100-piece discount is asserted."),
    "LTST-C190KRKT": (.14, {1: .14, 10: .098, 100: .0675, 500: .0534},
        "Page displayed 949,554 in stock; stock is not reserved.", ""),
    "RC0603FR-071KL": (.10, {1: .10, 10: .025, 25: .0188, 50: .015, 100: .0122, 250: .0094, 500: .00782},
        "Page displayed 3,179,272 in stock; stock is not reserved.", ""),
    "RT0603BRD07100KL": (.11, {1: .11, 10: .074, 50: .0652, 100: .0615, 500: .05402},
        "Page displayed 113,496 in stock; stock is not reserved.", ""),
    "RT0603BRD073K9L": (.10, {1: .10, 10: .07, 50: .0614, 100: .058, 500: .05096},
        "Page displayed 22,751 in stock; stock is not reserved.", ""),
    "CL10B104KB8NNNC": (.10, {1: .10, 100: .0185},
        "The refreshed power-cost observation for the same MPN shows zero stock / future delivery.", ""),
}
indicator_rows = []
for row in indicator_spec["cost_evidence"]["lines"]:
    mpn = row["mpn"]
    extra = indicator_extra[mpn]
    refs = sorted((r for r, p in parts.items()
                   if p["mpn"] == mpn and p["source_specification"] == "indicator_spec.json"), key=ref_key)
    assert len(refs) == row["quantity_per_board"]
    indicator_rows.append({
        "mpn": mpn, "references": refs, "quantity_per_adapter": len(refs),
        "catalogue_price_tier_pieces": row["observed_price_break_quantity"],
        "unit_usd": row["unit_price_usd"], "qty1_unit_usd": extra[0],
        "displayed_tiers": extra[1], "price_source": row["source"],
        "qty1_source": row["source"], "availability_note": extra[2],
        "tier_note": extra[3], "minimum_displayed_order_quantity": 1,
        "packaging": "Cut tape; minimum displayed order 1 piece; no Digi-Reel service assumed",
    })
indicator = {
    "date": "2026-10-06", "currency": "USD", "procurement_ready": False,
    "scope": "Measured-voltage indicator parts only; catalogue observations, not a basket or quotation",
    "rows": indicator_rows,
}
(BASE / "indicator-cost-observations.json").write_text(json.dumps(indicator, indent=2) + "\n", encoding="utf-8")

subsystems = {"power": power["rows"], "logic_and_connectors": logic["rows"], "indicator": indicator_rows}
expected_counts = {"power": 27, "logic_and_connectors": 14, "indicator": 11}
grouped = defaultdict(list)
covered_refs = set()
subtotals = {}
for system, rows in subsystems.items():
    assert sum(len(r["references"]) for r in rows) == expected_counts[system]
    normalized = []
    for original in rows:
        row = dict(original)
        row["qty1_unit_usd"] = row.get("qty1_unit_usd", row.get("unit_usd_qty1"))
        assert row["qty1_unit_usd"] is not None
        assert row["quantity_per_adapter"] == len(row["references"])
        for ref in row["references"]:
            assert ref not in covered_refs, f"Double-counted {ref}"
            assert parts[ref]["mpn"] == row["mpn"], (ref, row["mpn"])
            covered_refs.add(ref)
        grouped[row["mpn"]].append((system, row))
        normalized.append(row)
    subtotals[system] = {
        "fitted_parts": expected_counts[system],
        "consumed_parts_usd_per_adapter_at_100_scale": total(normalized, "unit_usd"),
        "consumed_parts_usd_at_qty1_unit_tiers": total(normalized, "qty1_unit_usd"),
    }
assert covered_refs == set(parts)

consolidated = []
for mpn, observations in sorted(grouped.items()):
    prices = {(r["unit_usd"], r["catalogue_price_tier_pieces"], r["qty1_unit_usd"]) for _, r in observations}
    assert len(prices) == 1, f"Conflicting prices for {mpn}: {prices}"
    bulk, tier, single = prices.pop()
    refs = sorted((ref for _, r in observations for ref in r["references"]), key=ref_key)
    manufacturers = {parts[ref]["manufacturer"] for ref in refs}
    assert len({name.casefold() for name in manufacturers}) == 1
    quantity = len(refs)
    notes = list(dict.fromkeys(r["availability_note"] for _, r in observations))
    tier_notes = list(dict.fromkeys(r["tier_note"] for _, r in observations if r.get("tier_note")))
    first = observations[0][1]
    package = first.get("packaging", first.get("package"))
    row = {
        "mpn": mpn, "manufacturer": sorted(manufacturers)[0], "references": refs,
        "values": sorted({parts[ref]["value"] for ref in refs}),
        "subsystems": [system for system, _ in observations],
        "quantity_per_adapter": quantity, "pieces_for_100_adapters_without_spares": quantity * 100,
        "prototype_qty1_unit_usd": single,
        "prototype_consumed_usd_at_qty1_unit_tier": money(Decimal(str(single)) * quantity),
        "prototype_minimum_displayed_order_quantity": 1,
        "prototype_package": package,
        "unit_usd_for_100_board_scale": bulk,
        "observed_tier_used_pieces": tier,
        "consumed_usd_per_adapter_at_100_scale": money(Decimal(str(bulk)) * quantity),
        "consumed_usd_for_100_adapters": money(Decimal(str(bulk)) * quantity * 100),
        "sources": list(dict.fromkeys(r["price_source"] for _, r in observations)),
        "availability_notes": notes, "tier_notes": tier_notes,
    }
    for _, observation in observations:
        if "displayed_tiers" in observation:
            row["additional_displayed_unit_price_tiers_usd"] = observation["displayed_tiers"]
        for key in ("catalogue_name", "mpn_mapping_note", "manufacturer_mapping_source"):
            if key in observation:
                row[key] = observation[key]
    consolidated.append(row)

assert len(consolidated) == 33
bulk_total = money(sum(Decimal(str(r["consumed_usd_per_adapter_at_100_scale"])) for r in consolidated))
prototype_total = money(sum(Decimal(str(r["prototype_consumed_usd_at_qty1_unit_tier"])) for r in consolidated))
assert bulk_total == money(sum(Decimal(str(s["consumed_parts_usd_per_adapter_at_100_scale"])) for s in subtotals.values()))
assert bulk_total == 7.231
assert prototype_total == 14.70

excluded = [
    "One finished, tested 500 mm mating four-wire harness per adapter",
    "Component freight, tax, tariffs, spares and manufacturing losses",
    "Solder paste, stencil, reflow equipment, hand soldering and inspection",
    "UPDI programmer, programming/calibration fixture, firmware loading and per-unit testing",
    "Physical prototype qualification, rework and rejected boards",
    "Packaging, marketplace/payment fees, outbound delivery, warranty/returns and profit",
]
inputs = [NATIVE / "parts.json", NATIVE / "evidence" / "schematic-review.json",
          BASE / "power-cost-observations.json", BASE / "logic-cost-observations.json",
          BASE / "indicator-cost-observations.json", BASE / "indicator_spec.json"]
result = {
    "schema_version": 1, "date": "2026-10-06", "currency": "USD",
    "status": "COSTING OBSERVATIONS ONLY - NOT A PROCUREMENT OR MANUFACTURING RELEASE",
    "source_basis": "Actual r0.3 native parts.json reconciled with direct US distributor catalogue observations",
    "native_counts": {"purchased_components": 52, "unique_mpns": 33, "smt": 47,
                      "through_hole": 5, "pcb_features_excluded_from_bom": 3},
    "quantity_basis": {
        "production_scenario_adapters": 100,
        "method": "Multiply actual fitted quantities by observed conservative catalogue tiers; shared MPNs consolidated once. No inferred discounts.",
        "tier_exceptions": "Phoenix 1725656 uses its observed 10-piece tier; ATTINY202-SSNR uses its observed 1-piece tier. Other rows use observed 100-piece tiers even when 100 adapters consume more pieces.",
        "prototype_method": "Qty-1 unit price multiplied by exact board consumption; every listed offer has displayed minimum order 1. This is not a completed checkout, not optimized pack buying, and not a promise of stock.",
    },
    "subsystem_subtotals": subtotals,
    "consumed_bom_usd_per_adapter_at_100_scale": bulk_total,
    "consumed_bom_usd_for_100_adapters": money(Decimal(str(bulk_total)) * 100),
    "consumed_bom_usd_at_qty1_unit_tiers_for_one_adapter": prototype_total,
    "pcb_scenario": {
        "source": "Parent's observed PCBWay website calculator; not an accepted manufacturing quote",
        "quantity": 100, "width_mm": 15.24, "length_mm": 50,
        "layers": 2, "solder_mask": "purple", "finish": "HASL",
        "usd_per_adapter": .9876, "includes": "Prior calculator scenario included DHL; before tax",
        "status": "Earlier provisional outline scenario; refresh against the final routed outline and manufacturing selections",
    },
    "consumed_bom_plus_prior_pcb_scenario_usd_per_adapter": money(Decimal(str(bulk_total)) + Decimal("0.9876")),
    "usd_15_resale_target": {
        "status": "NOT ESTABLISHED",
        "unallocated_usd_after_bom_and_prior_pcb_scenario": money(Decimal("15") - Decimal(str(bulk_total)) - Decimal("0.9876")),
        "note": "The unallocated amount must cover all remaining costs and profit. A sub-$15 materials sum does not establish a $15 assembled adapter plus cable selling price.",
    },
    "excluded_unquoted_costs": excluded,
    "procurement_ready": False, "amazon_basket_verified": False,
    "known_procurement_constraints": [
        "Several exact offers showed no stock: BZT52C12-7-F, PMEG6010CEH,115, CL10B104KB8NNNC, CL31A226KAHNNNE, BZT52C5V1-7-F, BAT46W-7-F and AP7375-33SA-7.",
        "PMV100EPAR displayed only 3 pieces, insufficient for 100 adapters.",
        "NX6008NBKR direct and cached results conflicted; refresh availability at checkout.",
        "CL21B225KAFNNNE was flagged NRND in the catalogue; review lifecycle or qualify a replacement before production.",
        "No generic diode, MOSFET, capacitor or connector substitute has been approved by this cost calculation.",
    ],
    "rows": consolidated,
    "input_sha256": {str(p.relative_to(BASE.parent)).replace("\\", "/"): sha256(p.read_bytes()).hexdigest() for p in inputs},
}
(BASE / "full-bom-cost.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

lines = [
    "OEA r0.3 complete fitted BOM costing - 6 October 2026 - USD",
    "Catalogue observations only. Not an order, quote acceptance or manufacturing release.", "",
    f"Native BOM: 52 purchased parts, 33 MPNs; 47 SMT + 5 through-hole. Three bare test pads are excluded.",
    f"Consumed components per adapter, conservative 100-board scale: ${bulk_total:.4f}",
    f"Components for 100 adapters, without spares: ${bulk_total * 100:.2f}",
    f"One adapter's component consumption at displayed qty-1 unit prices: ${prototype_total:.2f}",
    "Every offer has a displayed minimum order of one piece. Prices do not prove current stock.",
    "The qty-1 column is not an optimized pack-buying plan or the cash total of a populated cart.", "",
    "Subsystem amounts per adapter at the conservative bulk tiers:",
]
for system, values in subtotals.items():
    lines.append(f"  {system.replace('_', ' ')}: ${values['consumed_parts_usd_per_adapter_at_100_scale']:.4f}")
lines += [
    "", "PCB estimate and $15 resale target:",
    "Earlier PCBWay calculator scenario: 100 boards, 15.24 x 50 mm, 2 layers, purple mask, HASL.",
    "It was $0.9876 per board including the quoted DHL allocation, before tax. A final routed outline",
    "has not been released; refresh this scenario before treating it as a manufacturing quote.",
    f"Components plus that provisional PCB amount: ${result['consumed_bom_plus_prior_pcb_scenario_usd_per_adapter']:.4f}.",
    f"That leaves ${result['usd_15_resale_target']['unallocated_usd_after_bom_and_prior_pcb_scenario']:.4f} of a $15 selling price for ALL remaining costs and profit.",
    "The $15 assembled-adapter-plus-finished-cable target is NOT ESTABLISHED.", "",
    "Unpriced / excluded:", *[f"  - {item}" for item in excluded], "",
    "Per-MPN prices (all values USD):",
    "MPN                         Qty/board    Unit qty-1    Unit used @100 boards    Tier used    Board cost",
]
for row in consolidated:
    lines.append(f"{row['mpn']:<28} {row['quantity_per_adapter']:>8} {row['prototype_qty1_unit_usd']:>13.4f} {row['unit_usd_for_100_board_scale']:>24.4f} {row['observed_tier_used_pieces']:>12} {row['consumed_usd_per_adapter_at_100_scale']:>13.4f}")
lines += ["", "Tier interpretation:",
    "J4 uses the observed 10-piece price because no 100-piece discount was displayed.",
    "U50 uses the observed qty-1 cut-tape price; the 4,000-piece reel price is not applicable.",
    "Repeated MPNs share one row. The other rows conservatively retain their observed 100-piece tier",
    "even where a 100-board build would consume 200, 300, 400 or 600 pieces. No unobserved discount is assumed.",
    "", "Known procurement limitations:",
    *[f"  - {item}" for item in result["known_procurement_constraints"]], "",
    "Source and packaging details (observed 6 October 2026; refresh before buying):",
]
for row in consolidated:
    lines += ["", f"{row['mpn']} | {row['manufacturer']} | {', '.join(row['references'])}",
              f"  Prototype offer: {row['prototype_package']}; required pieces for one board: {row['quantity_per_adapter']}."]
    lines.extend(f"  {url}" for url in row["sources"])
    lines.extend(f"  Availability: {note}" for note in row["availability_notes"])
    lines.extend(f"  Tier: {note}" for note in row["tier_notes"])
    if "mpn_mapping_note" in row:
        lines += [f"  Name mapping: {row['mpn_mapping_note']}", f"  {row['manufacturer_mapping_source']}"]
lines += ["", "The JSON companion records exact references, tier quantities, input hashes and source URLs.",
          "No purchase, Amazon cart, PCBWay submission or CAD change was made by this costing calculation."]
(BASE / "full-bom-cost.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"rows": len(consolidated), "purchased_parts": len(parts),
                  "bulk_bom_usd": bulk_total, "qty1_consumed_usd": prototype_total,
                  "subsystems": subtotals,
                  "bom_plus_prior_pcb_usd": result["consumed_bom_plus_prior_pcb_scenario_usd_per_adapter"]}, indent=2))
