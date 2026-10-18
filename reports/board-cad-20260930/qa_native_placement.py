"""Independent read-only native-placement review; writes only its scoped report.

Run with KiCad's bundled Python. This is geometry/source QA, not KiCad DRC,
land-pattern approval, a routed-board review, or manufacturing qualification.
"""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import sys
import xml.etree.ElementTree as ET

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
REV = "20260930-03"
BASE = ROOT / "hardware/board_review"
MANIFEST = BASE / "revisions" / REV / "board-view.json"
OUT = Path(__file__).with_name("PLACEMENT_QA.json")
MODEL_ROOT = Path("C:/Program Files/KiCad/10.0/share/kicad/3dmodels")
SHAPES = {
    pcbnew.PAD_SHAPE_RECT: "rect",
    pcbnew.PAD_SHAPE_ROUNDRECT: "roundrect",
    pcbnew.PAD_SHAPE_CIRCLE: "circle",
    pcbnew.PAD_SHAPE_OVAL: "oval",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mm(value):
    return round(pcbnew.ToMM(value), 6)


def bounds(item):
    box = item.GetBoundingBox()
    return (box.GetX(), box.GetY(), box.GetX() + box.GetWidth(),
            box.GetY() + box.GetHeight())


def union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def intersects(a, b):
    # Strict positive-area bounding-envelope intersection: conservative, not DRC.
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def outside(box, width, height):
    return box[0] < 0 or box[1] < 0 or box[2] > width or box[3] > height


document = json.loads(MANIFEST.read_text(encoding="utf-8"))
placement = json.loads((BASE / "placement.json").read_text(encoding="utf-8"))
errors = []
warnings = []
boards = []


def expect(test, message):
    if not test:
        errors.append(message)


expect(document["current_revision"] == REV, "Manifest current_revision differs")
expect((BASE / "board-view.json").read_bytes() == MANIFEST.read_bytes(),
       "Published and immutable revision manifests differ")
expect(document["placement_hash"] == sha(BASE / "placement.json"), "Placement input hash differs")
expect(document["generator_hash"] == sha(ROOT / "tools/build_board_review.py"), "Generator input hash differs")
expect(document["interface_spec"]["sha256"] == sha(document["interface_spec"]["path"]),
       "Frozen interface spec input hash differs")
expect(all("build-incomplete" not in str(r) for r in document["revisions"]),
       "Failed incomplete build is exposed in published revision list")

for entry in document["boards"]:
    name = entry["id"]
    board_path = BASE / entry["board_file"]
    board = pcbnew.LoadBoard(str(board_path))
    source = ROOT / "hardware" / entry["source_block"]
    xml = ET.parse(source / "netlist.xml").getroot()
    rows = list(csv.DictReader((source / "bom.csv").open(encoding="utf-8-sig", newline="")))
    physical_rows = {r["Reference"]: r for r in rows if r.get("Scope") != "schematic_boundary_not_orderable"}
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    manifest_parts = {p["reference"]: p for p in entry["components"]}
    spec = next(s for s in placement["boards"] if s["id"] == name)
    expect(len(footprints) == len(list(board.GetFootprints())), name + ": duplicate references")
    expect(set(footprints) == set(physical_rows) == set(manifest_parts), name + ": physical reference set differs")
    node_nets = {}
    for net in xml.findall("./nets/net"):
        for node in net.findall("node"):
            key = (node.attrib["ref"], node.attrib["pin"])
            expect(key not in node_nets, name + ": source node appears on multiple nets " + str(key))
            node_nets[key] = net.attrib["name"]
    libpins = {(p.attrib["lib"], p.attrib["part"]):
               {pin.attrib["num"] for pin in p.findall("./pins/pin")}
               for p in xml.findall("./libparts/libpart")}
    component_pins = {}
    for c in xml.findall("./components/comp"):
        lib = c.find("libsource")
        component_pins[c.attrib["ref"]] = libpins[(lib.attrib["lib"], lib.attrib["part"])]

    for path, digest in entry["source_hashes"].items():
        expect(sha(ROOT / path) == digest, name + ": source input changed " + path)
    for path, digest in entry["footprint_hashes"].items():
        expect(sha(path) == digest, name + ": footprint input changed " + path)
        if "CNC_IS1.pretty" in path:
            copied = board_path.parent / "CNC_IS1.pretty" / Path(path).name
            expect(copied.is_file() and sha(copied) == digest, name + ": copied custom footprint differs")

    all_pads, component_boxes, courtyard_boxes = [], {}, {}
    missing_courtyards, missing_models = [], []
    actual_pad_nets, actual_physical_pins = {}, {}
    for ref, footprint in footprints.items():
        view = manifest_parts[ref]
        bom = physical_rows[ref]
        native_name = str(footprint.GetFPID().GetLibNickname()) + ":" + str(footprint.GetFPID().GetLibItemName())
        approved_name = bom["Footprint"] or spec["placement_only_footprints"][ref]
        expect(native_name == approved_name == view["footprint"], name + ": footprint assignment differs " + ref)
        expect(view["placement_only_candidate"] == (not bool(bom["Footprint"])), name + ": candidate flag differs " + ref)
        expect(view["value"] == bom["Value"] and view["mpn"] == bom["MPN"], name + ": BOM metadata differs " + ref)
        position = footprint.GetPosition()
        expect((mm(position.x), mm(position.y), footprint.GetOrientationDegrees()) ==
               (view["x_mm"], view["y_mm"], view["rotation_deg"]), name + ": native/manifest position differs " + ref)
        native_pads = {}
        pin_set = set()
        for pad in footprint.Pads():
            number = pad.GetNumber()
            expect(number not in pin_set, name + ": duplicate physical pad number " + ref + "." + number)
            pin_set.add(number)
            net = pad.GetNetname()
            expect(net == node_nets.get((ref, number), ""), name + ": native source net mismatch " + ref + "." + number)
            actual_pad_nets[ref + "." + number] = net
            pos, size = pad.GetPosition(), pad.GetSize()
            native_pads[number] = {"number": number, "net": net, "x": mm(pos.x), "y": mm(pos.y),
                                  "width": mm(size.x), "height": mm(size.y),
                                  "shape": SHAPES.get(pad.GetShape(), "unsupported"),
                                  "angle": pad.GetOrientationDegrees()}
            all_pads.append((ref, number, bounds(pad)))
        actual_physical_pins[ref] = sorted(pin_set)
        expect(pin_set == component_pins[ref], name + ": physical pad/source symbol pin set differs " + ref)
        expect(native_pads == {p["number"]: p for p in view["pads"]}, name + ": native/manifest pad geometry differs " + ref)
        box = footprint.GetBoundingBox(False, False)
        actual_box = {"x": mm(box.GetX()), "y": mm(box.GetY()),
                      "width": mm(box.GetWidth()), "height": mm(box.GetHeight())}
        expect(actual_box == view["bbox"], name + ": native/manifest component bbox differs " + ref)
        component_boxes[ref] = (box.GetX(), box.GetY(), box.GetX() + box.GetWidth(), box.GetY() + box.GetHeight())
        courtyards = [bounds(g) for g in footprint.GraphicalItems()
                     if isinstance(g, pcbnew.PCB_SHAPE) and g.GetLayer() == pcbnew.F_CrtYd]
        if courtyards:
            courtyard_boxes[ref] = union(courtyards)
        else:
            missing_courtyards.append(ref)
        native_models = [{"path": model.m_Filename,
                          "available": Path(model.m_Filename.replace("${KICAD10_3DMODEL_DIR}", str(MODEL_ROOT))).is_file()}
                         for model in footprint.Models()]
        expect(native_models == view["models"], name + ": native/manifest model metadata differs " + ref)
        if not any(model["available"] for model in native_models):
            missing_models.append(ref)

    width, height = pcbnew.FromMM(entry["width_mm"]), pcbnew.FromMM(entry["height_mm"])
    edge_segments = [g for g in board.GetDrawings() if g.GetLayer() == pcbnew.Edge_Cuts]
    edge_pairs = {tuple(sorted(((g.GetStart().x, g.GetStart().y), (g.GetEnd().x, g.GetEnd().y)))) for g in edge_segments}
    corners = [(0, 0), (width, 0), (width, height), (0, height)]
    expected_edges = {tuple(sorted((corners[i], corners[(i + 1) % 4]))) for i in range(4)}
    expect(len(edge_segments) == 4 and edge_pairs == expected_edges and
           all(g.GetShape() == pcbnew.SHAPE_T_SEGMENT for g in edge_segments), name + ": outline differs")
    expect(mm(board.GetDesignSettings().GetBoardThickness()) == entry["thickness_mm"], name + ": thickness differs")
    tracks = list(board.GetTracks())
    zones = list(board.Zones())
    expect(not tracks and not zones, name + ": unexpected native copper tracks/vias/zones")
    pad_collisions = [(a[0] + "." + a[1], b[0] + "." + b[1])
                      for a, b in itertools.combinations(all_pads, 2) if intersects(a[2], b[2])]
    envelope_collisions = [(a, b) for a, b in itertools.combinations(component_boxes, 2)
                          if intersects(component_boxes[a], component_boxes[b])]
    courtyard_collisions = [(a, b) for a, b in itertools.combinations(courtyard_boxes, 2)
                           if intersects(courtyard_boxes[a], courtyard_boxes[b])]
    outside_pads = [ref + "." + pin for ref, pin, box in all_pads if outside(box, width, height)]
    outside_components = [ref for ref, box in component_boxes.items() if outside(box, width, height)]
    outside_courtyards = [ref for ref, box in courtyard_boxes.items() if outside(box, width, height)]
    expect(not pad_collisions, name + ": intersecting pad bounding envelopes")
    expect(not envelope_collisions, name + ": intersecting component bounding envelopes")
    expect(not courtyard_collisions, name + ": intersecting courtyard bounding envelopes")
    expect(not outside_pads and not outside_components and not outside_courtyards, name + ": geometry outside outline")
    if missing_courtyards:
        warnings.append(name + ": no native courtyard shape for " + ", ".join(sorted(missing_courtyards)))
    omitted = sorted([[ref, pin, net] for (ref, pin), net in node_nets.items() if ref not in footprints])
    expect(omitted == sorted(entry["boundary_nodes_not_fitted"]), name + ": omitted boundary-node manifest differs")
    stats = {
        "components": len(footprints), "pads": len(all_pads),
        "nets": len({n for n in actual_pad_nets.values() if n}),
        "routed_tracks": len(tracks),
        "source_fitted_footprints": sum(bool(r["Footprint"]) for r in physical_rows.values()),
        "placement_only_candidates": sum(not bool(r["Footprint"]) for r in physical_rows.values()),
        "available_3d_models": len(footprints) - len(missing_models),
    }
    expect(stats == entry["stats"], name + ": manifest summary counts differ")
    expect(all(entry["evidence"][k] is False for k in
               ("routing", "drc_pass", "physical_measurement", "manufacturing_ready")),
           name + ": manifest overstates completion")
    boards.append({"id": name, "pcb_sha256": sha(board_path), "board_file": str(board_path.relative_to(ROOT)),
                   "dimensions_mm": [entry["width_mm"], entry["height_mm"]], "thickness_mm": entry["thickness_mm"],
                   "native_copper_layer_count": board.GetCopperLayerCount(), "stats": stats,
                   "courtyards_present": len(courtyard_boxes), "courtyards_absent": sorted(missing_courtyards),
                   "available_3d_models_absent": sorted(missing_models), "omitted_source_nodes": len(omitted),
                   "pad_bbox_intersections": pad_collisions, "component_bbox_intersections": envelope_collisions,
                   "courtyard_bbox_intersections": courtyard_collisions,
                   "pads_outside_outline": outside_pads, "components_outside_outline": outside_components,
                   "courtyards_outside_outline": outside_courtyards,
                   "actual_pad_nets": actual_pad_nets, "actual_pin_sets": actual_physical_pins})

result = {"review": "Read-only native placement/source/manifest QA", "revision": REV,
          "native_api_version": pcbnew.GetBuildVersion(), "manifest_sha256": sha(MANIFEST),
          "qa_script_sha256": sha(__file__), "passed": not errors, "errors": errors,
          "warnings": warnings, "boards": boards,
          "limitations": ["Bounding-envelope checks are conservative; they are not native DRC.",
                          "Missing courtyards, BGA escape, land patterns and mechanical fit require review.",
                          "Two-layer default and 1.6 mm thickness are study state, not a qualified stackup.",
                          "No electrical source, board or manifest was modified; no physical measurements performed."]}
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "boards"}, indent=2))
for item in boards:
    print(json.dumps({k: v for k, v in item.items() if k not in ("actual_pad_nets", "actual_pin_sets")}, indent=2))
sys.exit(0 if result["passed"] else 1)
