"""Generate the PCBWay quotation BOM from parts and verify native PCB parity.

Run with KiCad's bundled Python. This reads the PCB; it never changes it.
The result is a source/assembly-data check, not a fabrication release.
"""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import pcbnew as p


ROOT = Path(__file__).resolve().parent
EXPECTED_THT = {"J1", "J2", "J3", "J4", "SW1"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref_key(ref):
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", ref)
    return match[1], int(match[2])


def build():
    source = ROOT / "parts.json"
    pcb = ROOT / "adapter.kicad_pcb"
    before = {source.name: sha(source), pcb.name: sha(pcb)}
    parts = json.loads(source.read_text(encoding="utf-8"))["parts"]
    board = p.LoadBoard(str(pcb))
    footprints = list(board.GetFootprints())
    fps = {fp.GetReference(): fp for fp in footprints}
    errors = []
    if len(fps) != len(footprints):
        errors.append("Duplicate native PCB reference")
    if set(fps) != set(parts):
        errors.append("Native PCB and parts.json references differ")

    rows = {}
    reviewed_pins = 0
    for ref in sorted(parts, key=ref_key):
        spec = parts[ref]
        for field in ("mpn", "manufacturer", "footprint", "value"):
            if not isinstance(spec.get(field), str) or not spec[field].strip():
                errors.append(f"{ref}: missing {field}")
        if ref not in fps:
            continue
        fp = fps[ref]
        fields = {f.GetName(): f.GetText() for f in fp.GetFields()}
        native_id = fp.GetFPID()
        full_id = f"{native_id.GetLibNickname()}:{native_id.GetLibItemName()}"
        for label, actual, expected in (
            ("MPN", fields.get("MPN"), spec["mpn"]),
            ("Manufacturer", fields.get("Manufacturer"), spec["manufacturer"]),
            ("footprint", full_id, spec["footprint"]),
            ("value", fp.GetValue(), spec["value"]),
        ):
            if actual != expected:
                errors.append(f"{ref}: {label} mismatch: {actual!r} != {expected!r}")
        attr = fp.GetAttributes()
        if attr & p.FP_THROUGH_HOLE:
            mount = "THT"
        elif attr & p.FP_SMD:
            mount = "SMT"
        else:
            mount = "UNKNOWN"
            errors.append(f"{ref}: missing native mounting attribute")
        expected_mount = "THT" if ref in EXPECTED_THT else "SMT"
        if mount != expected_mount:
            errors.append(f"{ref}: mounting type {mount}, expected {expected_mount}")
        side = {p.F_Cu: "Top", p.B_Cu: "Bottom"}.get(fp.GetLayer(), "UNKNOWN")
        if side == "UNKNOWN":
            errors.append(f"{ref}: footprint is not on an outer side")
        for pad in fp.Pads():
            if not pad.GetNumber():
                continue
            number = pad.GetNumber()
            if number not in spec["pins"]:
                errors.append(f"{ref}.{number}: pad absent from parts.json")
                continue
            net = pad.GetNetname()
            expected = spec["pins"][number]
            if expected is None:
                if not net.startswith("unconnected-("):
                    errors.append(f"{ref}.{number}: expected explicit unconnected net, got {net}")
            elif net != "/" + expected:
                # All functional labels are on the sole root schematic sheet.
                errors.append(f"{ref}.{number}: native net {net}, expected /{expected}")
            reviewed_pins += 1
        pad_numbers = {pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()}
        if pad_numbers != set(spec["pins"]):
            errors.append(f"{ref}: native pad number set differs from parts.json")
        rows[ref] = dict(spec, mounting=mount, side=side)

    tht_refs = sorted((ref for ref, row in rows.items() if row["mounting"] == "THT"), key=ref_key)
    if set(tht_refs) != EXPECTED_THT:
        errors.append("Native THT set is not the five required connectors/switch")
    if len(rows) != 50 or sum(x["mounting"] == "SMT" for x in rows.values()) != 45:
        errors.append("Expected 50 fitted components, 45 SMT and 5 THT")
    groups = defaultdict(list)
    for ref, row in rows.items():
        groups[row["manufacturer"], row["mpn"], row["footprint"], row["mounting"]].append(ref)
    if len(groups) != 32:
        errors.append("Expected 32 unique board BOM lines")

    # Edge centerlines give the designed outline; the displayed bbox includes line width.
    corners = []
    for drawing in board.GetDrawings():
        if drawing.GetLayer() == p.Edge_Cuts:
            for xy in (drawing.GetStart(), drawing.GetEnd()):
                corners.append((p.ToMM(xy.x), p.ToMM(xy.y)))
    width = round(max(x for x, y in corners) - min(x for x, y in corners), 5)
    height = round(max(y for x, y in corners) - min(y for x, y in corners), 5)
    if [width, height] != [15.24, 38.1]:
        errors.append(f"Native outline dimensions differ: {width} x {height}")
    if board.GetCopperLayerCount() != 4:
        errors.append("Native PCB is not four copper layers")

    after = {source.name: sha(source), pcb.name: sha(pcb)}
    if before != after:
        errors.append("Source changed while reviewing; rerun on a stable snapshot")
    if errors:
        raise RuntimeError("\n".join(errors))

    output = ROOT / "BOM.csv"
    headings = ["Item", "Designators", "Quantity per board", "Quantity for 5 boards",
                "Manufacturer", "Manufacturer part number", "Description / value",
                "Footprint", "Mounting", "Assembly side by reference", "Fit", "Assembly notes"]
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headings)
        writer.writeheader()
        for index, refs in enumerate(sorted(groups.values(), key=lambda rs: ref_key(min(rs, key=ref_key))), 1):
            refs = sorted(refs, key=ref_key)
            exemplar = rows[refs[0]]
            note = "No substitutions without engineering approval."
            if any(ref in {"J1", "J2"} for ref in refs):
                note += " Long male mating posts face down into host; do not trim mating posts."
            if any(ref in {"J3", "J4", "SW1"} for ref in refs):
                note += " Controlled underside tail trimming per assembly drawing."
            writer.writerow({
                "Item": index, "Designators": ", ".join(refs),
                "Quantity per board": len(refs), "Quantity for 5 boards": 5 * len(refs),
                "Manufacturer": exemplar["manufacturer"], "Manufacturer part number": exemplar["mpn"],
                "Description / value": "; ".join(dict.fromkeys(rows[ref]["value"] for ref in refs)),
                "Footprint": exemplar["footprint"], "Mounting": exemplar["mounting"],
                "Assembly side by reference": "; ".join(f"{ref}: {rows[ref]['side']}" for ref in refs),
                "Fit": "Yes", "Assembly notes": note,
            })

    check = {
        "schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS - BOM and native assembly data only; not a manufacturing release",
        "source_sha256": before, "bom_sha256": sha(output),
        "board_quantity": 5, "parts_per_board": len(rows), "bom_lines": len(groups),
        "components_for_five_boards": 5 * len(rows),
        "mounting_counts": dict(Counter(row["mounting"] for row in rows.values())),
        "side_counts": dict(Counter(row["side"] for row in rows.values())),
        "mounting_side_counts": dict(Counter(f"{row['side']} {row['mounting']}" for row in rows.values())),
        "tht_references": tht_refs, "native_pin_assignments_checked": reviewed_pins,
        "native_dimensions_mm": [width, height], "native_copper_layers": board.GetCopperLayerCount(),
        "native_board_thickness_mm": p.ToMM(board.GetDesignSettings().GetBoardThickness()),
        "verified_fields": ["Reference", "Manufacturer", "MPN", "Value", "Footprint", "Mounting", "Assembly side", "Pad numbers and net assignments"],
        "scope": "All 50 board components fitted. Separate five finished harnesses are specified in ASSEMBLY_AND_WIRING.txt and QUOTE_SCOPE.txt, not counted as PCB components.",
        "not_verified": ["Sourcing availability", "Physical part dimensions or assembly fit", "Gerber or drill exports", "Copper connectivity or clearance DRC", "Physical operation, EMC or thermal limits"],
    }
    (ROOT / "bom-pcb-review.json").write_text(json.dumps(check, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: check[k] for k in ("status", "parts_per_board", "bom_lines", "mounting_counts", "mounting_side_counts", "native_pin_assignments_checked")}, indent=2))


if __name__ == "__main__":
    build()
