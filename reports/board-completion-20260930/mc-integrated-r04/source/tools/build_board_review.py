"""Build source-backed, unrouted KiCad placement studies and their side-panel data.

Run with KiCad's bundled Python (pcbnew). This never changes electrical sources,
assigns production footprints, routes copper or writes fabrication files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "hardware" / "board_review"
KICAD = Path("C:/Program Files/KiCad/10.0/share/kicad")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def natural(ref):
    return (re.sub(r"\d+", "", ref), int(re.search(r"\d+", ref).group()))


def xy(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def mm(value):
    return round(pcbnew.ToMM(value), 5)


def text(board, value, x, y, size=1.2, layer=pcbnew.F_SilkS):
    item = pcbnew.PCB_TEXT(board)
    item.SetText(value)
    item.SetPosition(xy(x, y))
    item.SetTextSize(xy(size, size))
    item.SetTextThickness(pcbnew.FromMM(0.15))
    item.SetLayer(layer)
    board.Add(item)


def line(board, x1, y1, x2, y2, layer):
    item = pcbnew.PCB_SHAPE(board)
    item.SetShape(pcbnew.SHAPE_T_SEGMENT)
    item.SetStart(xy(x1, y1))
    item.SetEnd(xy(x2, y2))
    item.SetWidth(pcbnew.FromMM(0.15))
    item.SetLayer(layer)
    board.Add(item)


def box(board, x, y, width, height, layer):
    for p in ((x, y, x+width, y), (x+width, y, x+width, y+height),
              (x+width, y+height, x, y+height), (x, y+height, x, y)):
        line(board, *p, layer)


def json_write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def get_footprint(name, source_block):
    library, item = name.split(":", 1)
    paths = [ROOT / "hardware" / source_block / (library + ".pretty"),
             KICAD / "footprints" / (library + ".pretty")]
    for path in paths:
        if (path / (item + ".kicad_mod")).exists():
            fp = pcbnew.FootprintLoad(str(path), item)
            if fp is None:
                raise ValueError("KiCad could not load " + name)
            fp.SetFPID(pcbnew.LIB_ID(library, item))
            return fp, path / (item + ".kicad_mod")
    raise FileNotFoundError(name)


def build_board(spec, revision_dir):
    block = spec["source_block"]
    source = ROOT / "hardware" / block
    with (source / "bom.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    xml = ET.parse(source / "netlist.xml").getroot()
    node_nets = {}
    for net in xml.findall("./nets/net"):
        for node in net.findall("node"):
            node_nets[(node.attrib["ref"], node.attrib["pin"])] = net.attrib["name"]

    board = pcbnew.BOARD()
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(spec["thickness_mm"]))
    board.SetCopperLayerCount(spec.get("copper_layers", 2))
    rules = spec.get("layout_rules", {})
    if rules:
        settings = board.GetDesignSettings()
        settings.m_MinClearance = pcbnew.FromMM(rules["clearance_mm"])
        default = settings.m_NetSettings.GetDefaultNetclass()
        default.SetClearance(pcbnew.FromMM(rules["clearance_mm"]))
        default.SetTrackWidth(pcbnew.FromMM(rules["signal_track_width_mm"]))
    width, height = spec["width_mm"], spec["height_mm"]
    box(board, 0, 0, width, height, pcbnew.Edge_Cuts)
    text(board, "PLACEMENT STUDY - UNROUTED / NOT FOR MANUFACTURE", width/2, 4,
         min(1.2, width/60))
    for zone in spec["zones"]:
        box(board, zone["x"], zone["y"], zone["width"], zone["height"], pcbnew.Dwgs_User)
        text(board, zone["label"], zone["x"]+zone["width"]/2, zone["y"]+2,
             0.9, pcbnew.Dwgs_User)

    all_nets = sorted(set(node_nets.values()))
    nets = {}
    for code, name in enumerate(all_nets, start=1):
        net = pcbnew.NETINFO_ITEM(board, name, code)
        board.Add(net)
        nets[name] = net

    components = []
    unresolved = []
    inputs = {"hardware/"+block+"/"+name: sha(source/name)
              for name in ("bom.csv", "netlist.xml", "design.json")}
    footprint_inputs = {}
    missing_source_pads = []
    omitted_nodes = []
    for row in rows:
        reference = row["Reference"]
        if row.get("Scope") == "schematic_boundary_not_orderable":
            unresolved.append({"reference": reference, "value": row["Value"],
                               "reason": "Logical schematic boundary; no selected physical connector."})
            continue
        fp_name = row["Footprint"]
        candidate = not bool(fp_name)
        if candidate:
            fp_name = spec.get("placement_only_footprints", {}).get(reference)
        if not fp_name:
            raise ValueError("No declared source or placement-only footprint for " + reference)
        fp, fp_path = get_footprint(fp_name, block)
        footprint_inputs[str(fp_path)] = sha(fp_path)
        fp.SetReference(reference)
        fp.SetValue(row["MPN"] or row["Value"])
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(xy(0.8, 0.8))
        fp.Reference().SetTextThickness(pcbnew.FromMM(0.12))
        if spec.get("assembly_reference_layer") == "F.Fab":
            # Namespace-expanded designators are assembly-review annotation.
            # Production silkscreen designators are a separate unfinished task.
            fp.Reference().SetLayer(pcbnew.F_Fab)
        board.Add(fp)
        pos = spec["positions"][reference]
        fp.SetPosition(xy(pos[0], pos[1]))
        fp.SetOrientationDegrees(pos[2] if len(pos) > 2 else 0)
        pads = []
        numbers = set()
        for pad in fp.Pads():
            number = pad.GetNumber()
            numbers.add(number)
            name = node_nets.get((reference, number), "")
            if name:
                pad.SetNet(nets[name])
            p, size = pad.GetPosition(), pad.GetSize()
            shape = {pcbnew.PAD_SHAPE_RECT:"rect", pcbnew.PAD_SHAPE_ROUNDRECT:"roundrect",
                     pcbnew.PAD_SHAPE_CIRCLE:"circle", pcbnew.PAD_SHAPE_OVAL:"oval"}.get(pad.GetShape(), "rect")
            pads.append({"number":number, "net":name, "x":mm(p.x), "y":mm(p.y),
                         "width":mm(size.x), "height":mm(size.y), "shape":shape,
                         "angle":pad.GetOrientation().AsDegrees()})
        for ref, pin in node_nets:
            if ref == reference and pin not in numbers:
                missing_source_pads.append([ref, pin])
        # Courtyard/fabrication graphics are native KiCad geometry, never invented bodies.
        graphics = []
        for item in fp.GraphicalItems():
            if not isinstance(item, pcbnew.PCB_SHAPE):
                continue
            if item.GetLayer() not in (pcbnew.F_Fab, pcbnew.F_CrtYd, pcbnew.F_SilkS):
                continue
            start, end = item.GetStart(), item.GetEnd()
            kind = {pcbnew.SHAPE_T_SEGMENT:"line", pcbnew.SHAPE_T_RECT:"rect",
                    pcbnew.SHAPE_T_CIRCLE:"circle"}.get(item.GetShape())
            if kind:
                graphics.append({"kind":kind, "x1":mm(start.x), "y1":mm(start.y),
                                 "x2":mm(end.x), "y2":mm(end.y),
                                 "layer":board.GetLayerName(item.GetLayer())})
        bounds = fp.GetBoundingBox(False, False)
        model_info = []
        for model in fp.Models():
            model_path = Path(model.m_Filename.replace("${KICAD10_3DMODEL_DIR}", str(KICAD/"3dmodels"))
                              .replace("${KIPRJMOD}", str(revision_dir)))
            model_info.append({"path":model.m_Filename, "available":model_path.exists()})
        components.append({"reference":reference, "value":row["Value"], "mpn":row["MPN"],
                           "footprint":fp_name, "x_mm":pos[0], "y_mm":pos[1],
                           "rotation_deg":pos[2] if len(pos)>2 else 0,
                           "placement_only_candidate":candidate,
                           "highlight":reference in spec.get("highlight", []),
                           "bbox":{"x":mm(bounds.GetX()),"y":mm(bounds.GetY()),
                                   "width":mm(bounds.GetWidth()),"height":mm(bounds.GetHeight())},
                           "pads":pads,"graphics":graphics,"models":model_info,
                           "source":"hardware/"+block+"/bom.csv",
                           "status":row["Status"]})
    fitted = {p["reference"] for p in components}
    omitted_nodes = [[ref,pin,net] for (ref,pin),net in node_nets.items() if ref not in fitted]
    if missing_source_pads:
        raise ValueError("Source pins absent from footprint: " + repr(missing_source_pads))
    # A real placement study still must keep fitted pad geometry within its outline.
    outside = [p["reference"] for p in components if p["bbox"]["x"] < 0 or p["bbox"]["y"] < 0
               or p["bbox"]["x"]+p["bbox"]["width"] > width
               or p["bbox"]["y"]+p["bbox"]["height"] > height]
    if outside:
        raise ValueError("Footprints outside proposed outline: " + repr(outside))
    file_name = spec["id"]+"-placement.kicad_pcb"
    pcbnew.SaveBoard(str(revision_dir / file_name), board)
    if rules:
        project = {"meta":{"filename":file_name.replace(".kicad_pcb", ".kicad_pro"),"version":1},
                   "board":{"design_settings":{"rule_severities":{
                       "missing_courtyard":"warning", "track_not_centered_on_via":"warning",
                       "tuning_profile_track_geometries":"warning", "footprint_filters_mismatch":"warning",
                       "footprint_type_mismatch":"warning"}}},
                   "net_settings":{"classes":[{"name":"Default","clearance":rules["clearance_mm"],
                     "track_width":rules["signal_track_width_mm"],"via_diameter":0.6,"via_drill":0.3}],
                     "meta":{"version":4}}}
        json_write(revision_dir/file_name.replace(".kicad_pcb", ".kicad_pro"), project)
    # Round-trip native file: make sure actual saved copper retains imported source nets.
    reopened = pcbnew.LoadBoard(str(revision_dir / file_name))
    actual = {(fp.GetReference(),pad.GetNumber()):pad.GetNetname()
              for fp in reopened.GetFootprints() for pad in fp.Pads()}
    for (ref,pin),name in node_nets.items():
        if ref in fitted and actual.get((ref,pin)) != name:
            raise ValueError("Native PCB net round-trip mismatch: " + ref+"."+pin)
    if len(reopened.GetTracks()):
        raise ValueError("Study must remain unrouted")
    result = {k:v for k,v in spec.items() if k not in ("positions","placement_only_footprints","highlight")}
    relative = revision_dir.relative_to(REVIEW).as_posix()+"/"
    result.update({"board_file":relative+file_name, "image_3d":relative+spec["id"]+"-3d.png",
                   "components":components,"unresolved":unresolved,
                   "source_hashes":inputs,"footprint_hashes":footprint_inputs,
                   "boundary_nodes_not_fitted":omitted_nodes,
                   "stats":{"components":len(components), "pads":sum(len(p["pads"]) for p in components),
                            "nets":len({pad["net"] for p in components for pad in p["pads"] if pad["net"]}),
                            "routed_tracks":0,"source_fitted_footprints":sum(not p["placement_only_candidate"] for p in components),
                            "placement_only_candidates":sum(p["placement_only_candidate"] for p in components),
                            "available_3d_models":sum(any(m["available"] for m in p["models"]) for p in components)},
                   "evidence":{"native_save_reload":True,"imported_source_pad_nets_match":True,
                               "fitted_geometry_within_proposed_outline":True,
                               "routing":False,"drc_pass":False,"physical_measurement":False,
                               "manufacturing_ready":False}})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--staging", action="store_true", help="Build an immutable candidate without changing the live published revision")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.revision):
        parser.error("Revision must be a safe file name")
    config_path = REVIEW / "placement.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    folder = REVIEW / "revisions" / args.revision
    folder.mkdir(parents=True, exist_ok=False)
    sources = {ROOT/"hardware"/spec["source_block"]/name
               for spec in config["boards"] for name in
               ("bom.csv","netlist.xml","design.json",spec["source_block"]+".kicad_sch")}
    before = {str(p):sha(p) for p in sources}
    # Bind copied custom footprints locally, so the native files also open on
    # another KiCad installation without editing the original source libraries.
    libraries = {}
    for spec in config["boards"]:
        for library in (ROOT/"hardware"/spec["source_block"]).glob("*.pretty"):
            destination = folder/library.name
            if not destination.exists():
                shutil.copytree(library, destination)
            libraries[library.stem] = library.name
        models = ROOT/"hardware"/spec["source_block"]/"3dmodels"
        if models.exists():
            target = folder/"3dmodels"
            target.mkdir(exist_ok=True)
            for model in models.iterdir():
                if model.is_file():
                    dest = target/model.name
                    if dest.exists() and dest.read_bytes() != model.read_bytes():
                        raise ValueError("Conflicting project model: " + model.name)
                    shutil.copyfile(model, dest)
    if libraries:
        entries = [f'  (lib (name "{name}")(type "KiCad")(uri "${{KIPRJMOD}}/{path}")(options "")(descr "Copied candidate source library"))'
                   for name,path in sorted(libraries.items())]
        (folder/"fp-lib-table").write_text("(fp_lib_table\n"+"\n".join(entries)+"\n)\n", encoding="utf-8")
    boards = [build_board(spec, folder) for spec in config["boards"]]
    after = {str(p):sha(p) for p in sources}
    if before != after:
        raise ValueError("Electrical source changed during review build")
    previous = REVIEW / "board-view.json"
    previous_document = json.loads(previous.read_text(encoding="utf-8")) if previous.exists() else {}
    previous_boards = {b["id"]:b for b in previous_document.get("boards", [])}
    for board in boards:
        old_parts = {p["reference"]:p for p in previous_boards.get(board["id"], {}).get("components", [])}
        changes = []
        for part in board["components"]:
            old = old_parts.get(part["reference"])
            geometry = ("x_mm", "y_mm", "rotation_deg")
            electrical = ("value", "mpn", "footprint", "placement_only_candidate", "pads")
            if old is None:
                status, reason = "added", "Added to this CAD study."
            elif any(part[key] != old[key] for key in geometry):
                status, reason = "moved", "Placement changed from the previous published CAD revision."
            elif any(part[key] != old[key] for key in electrical):
                status, reason = "changed", "Part, footprint or pin-net geometry changed from the previous CAD revision."
            elif part["highlight"]:
                status, reason = "review-focus", "Current engineering review focus; unchanged from the preceding CAD revision."
            else:
                status, reason = "unchanged", "Unchanged from the previous published CAD revision."
            part.update({"change_status":status,"change_reason":reason,
                         "highlight":status != "unchanged"})
            if status in ("added", "moved", "changed"):
                changes.append({"reference":part["reference"],"status":status,"reason":reason})
        removed = sorted(set(old_parts)-{p["reference"] for p in board["components"]})
        board["change_summary"] = {"compared_to":previous_document.get("current_revision"),
                                   "parts":changes,"removed_references":removed}
    spec_path = Path(config["interface_spec"])
    document = {"schema_version":1,"current_revision":args.revision,"revision_label":args.label,
                "scope":"Editable unrouted placement studies. No routed board or fabrication release.",
                "boards":boards,"placement_hash":sha(config_path),
                "generator_hash":sha(Path(__file__)),
                "interface_spec":{"path":str(spec_path),"sha256":sha(spec_path)},
                "electrical_sources_unchanged":True}
    history = previous_document.get("revisions", [])
    history.append({"id":args.revision,"label":args.label,
                    "path":"revisions/"+args.revision+"/board-view.json"})
    document["revisions"] = history
    json_write(folder / "board-view.json", document)
    # Publish atomically, after source integrity and native-board checks pass.
    if not args.staging:
        temporary = REVIEW / "board-view.next.json"
        json_write(temporary, document)
        temporary.replace(previous)
    print(json.dumps({"revision":args.revision,"boards":[b["stats"] for b in boards],
                      "sources_unchanged":True,"published":not args.staging,"manufacturing_ready":False}, indent=2))


if __name__ == "__main__":
    main()
