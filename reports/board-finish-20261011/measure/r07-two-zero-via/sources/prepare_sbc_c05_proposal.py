"""Bounded host-only compute power/current layout proposal. Never emits a board."""
import copy
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Point, LineString, Polygon, box, mapping, shape
from shapely.ops import unary_union
from shapely.prepared import prep

import prepare_sbc_plan as base
import prepare_sbc_hubs as hubs
from reconcile_dfm import pose

HERE = Path(__file__).resolve().parent
OUT = HERE / "sbc-c05-source-proposal"
C05 = HERE.parent / "recovery-composite/c05/c05-fag-e1-rollback-dfm.kicad_pcb"
C05_SHA = "95874c4275f10851f03c2f7953fdf4cf4e7e8a0c39bbe399f8aaec642bd7c77d"
NET = base.NET
DOM = "DOM_LOGIC"
WINDOW = box(107, 128, 229, 176)
SOURCE_WINDOW = box(206, 131, 226, 145)
LOAD_WINDOW = box(107, 159, 124, 175)
LOCAL = box(217, 131, 226, 140)
MARGIN = .025
READS = {}
EXT = Path("Z:/pcb-runs/claude-finish")
RULES = EXT / "integrate/measure/r06-stitch-plane-pads-2/copy/board.kicad_dru"
PART = EXT / "integrate/measure/r06-stitch-plane-pads-2/partitions.json"
BARRIERS = Path("Z:/pcb-runs/domains/barriers.json")
RESERVER = EXT / "tools/reserve_corridors.py"
OPI = "/mc_permission{slash}OPI_REARM_TX"


def read(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    READS[str(path)] = hashlib.sha256(data).hexdigest()
    return data


def require(condition, message):
    if not condition:
        raise ValueError(message)


def norm(net):
    return net.replace("{slash}", "/")


def rings(geometry):
    parts = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
    return [[list(part.exterior.coords)[:-1], [list(ring.coords)[:-1] for ring in part.interiors]]
            for part in parts if part.geom_type == "Polygon" and not part.is_empty]


def numbers(chunk, field):
    match = re.search(rb'\(' + field.encode() + rb' ([-0-9.eE]+) ([-0-9.eE]+)\)', chunk)
    require(match is not None, "Missing direct native coordinate")
    return [float(number) for number in match.groups()]


def scalar(chunk, field):
    return float(re.search(rb'\(' + field.encode() + rb' ([-0-9.eE]+)\)', chunk).group(1))


def netname(chunk):
    return json.loads(re.search(rb'\(net ("(?:[^"\\]|\\.)*")\)', chunk).group(1))


def overlay():
    original = read(base.BASE)
    current = read(C05)
    require(hashlib.sha256(original).hexdigest() == base.BASE_SHA and hashlib.sha256(current).hexdigest() == C05_SHA,
            "Frozen board changed")
    g = json.loads(read(base.GEOM))
    require(g["sha256"] == base.BASE_SHA and g["refilled"] is True and not g["api_errors"], "Invalid frozen native geometry")
    before, after = base.inventory(original), base.inventory(current)
    arcs = {record["uuid"]: record for record in g["tracks"] if record.get("kind") == "arc"}
    tracks, vias = [], []
    for uid, chunk in after[4].items():
        item_kind = base.pcbtext.chunk_kind(chunk)
        if item_kind == "segment":
            tracks.append({"uuid": uid, "net": netname(chunk), "a": numbers(chunk, "start"), "b": numbers(chunk, "end"),
                           "w": scalar(chunk, "width"), "layer": base.pcbtext.chunk_layer(chunk), "locked": b"(locked yes)" in chunk})
        elif item_kind == "via":
            require(b'(layers "F.Cu" "B.Cu")' in chunk and b'(via blind' not in chunk, "Unsupported non-through via")
            x, y = numbers(chunk, "at")
            vias.append({"uuid": uid, "net": netname(chunk), "x": x, "y": y, "d": scalar(chunk, "size"),
                         "drill": scalar(chunk, "drill"), "flashed": g["copper_layers"], "span": ["F.Cu", "B.Cu"]})
        else:
            require(uid in arcs and before[4].get(uid) == chunk, "New/changed arc is not modeled by pinned native export")
            tracks.append(arcs[uid])
    native_fp = {base.ref_of(chunk): chunk for chunk in after[3].values() if base.pcbtext.chunk_kind(chunk) == "footprint"}
    old_fp = {base.ref_of(chunk): chunk for chunk in before[3].values() if base.pcbtext.chunk_kind(chunk) == "footprint"}
    require(set(native_fp) == set(old_fp), "Footprint set changed")
    moves = {}
    for ref, chunk in old_fp.items():
        old_nodes, new_nodes = base.children(chunk)[1], base.children(native_fp[ref])[1]
        require([node for node in old_nodes if base.kind(node) == b"pad"] ==
                [node for node in new_nodes if base.kind(node) == b"pad"], "Native local pad definitions changed: " + ref)
        old_pose, new_pose = pose(old_nodes), pose(new_nodes)
        require(old_pose[2] == new_pose[2], "Unsupported rotated footprint")
        if old_pose != new_pose:
            moves[ref] = [new_pose[0] - old_pose[0], new_pose[1] - old_pose[1]]
    for pad in g["pads"]:
        if pad["ref"] in moves:
            dx, dy = moves[pad["ref"]]
            pad["x"] += dx
            pad["y"] += dy
            pad["layers"] = {layer: rings(translate(unary_union(base.polygons(records)), xoff=dx, yoff=dy)) for layer, records in pad["layers"].items()}
            pad["hole"] = rings(translate(unary_union(base.polygons(pad.get("hole") or [])), xoff=dx, yoff=dy))
    for foot in g["footprints"]:
        if foot["ref"] in moves:
            dx, dy = moves[foot["ref"]]
            foot["x"] += dx
            foot["y"] += dy
            foot["courtyard"] = {side: rings(translate(unary_union(base.polygons(records)), xoff=dx, yoff=dy)) for side, records in foot["courtyard"].items()}
    g["tracks"], g["vias"] = tracks, vias
    g["board"], g["sha256"], g["refilled"] = str(C05), C05_SHA, False
    # New DFM keepout is far outside the bounded search; every other zone definition is retained.
    new_zones = [chunk for uid, chunk in after[3].items() if base.pcbtext.chunk_kind(chunk) == "zone" and uid not in before[3]]
    require(len(new_zones) == 1 and b"FID_KEEPOUT_FIDB1_FIDF1" in new_zones[0], "Unmodeled zone/rule-area addition")
    pts = base.pcbtext.polygon_points(new_zones[0])
    require(not Polygon(pts).intersects(WINDOW.buffer(3)), "New keepout intersects search scope")
    domains = {norm(net): domain for net, domain in g["nets"].items()}
    g["domains_normalized"] = domains
    return g, {"moved_native_footprints_mm": moves, "actual_tracks": len(tracks), "actual_vias": len(vias),
               "pad_definitions_unchanged": True, "no_new_or_changed_arc": True,
               "fill_policy": "Conservative pinned r06 native foreign fills retained; c05 tracks/vias and exact translated pads overlaid. No c05 fresh fill claimed"}


def reservations(g):
    compat = {"pads": [], "tracks": [], "keepouts": [], "vias": [], "zones": []}
    for pad in g["pads"]:
        layers = list(pad["layers"])
        compat["pads"].append({key: pad[key] for key in ("ref", "num", "net", "x", "y", "smd")}
                              | {"layers": layers, "poly": pad["layers"][layers[0]] if layers else []})
    compat["tracks"] = [{key: track[key] for key in ("net", "layer", "w", "a", "b")} for track in g["tracks"] if track.get("kind") != "arc"]
    input_path, output_path = OUT / "compat-c05.json", OUT / "reserved-c05.json"
    input_path.write_text(json.dumps(compat), encoding="utf-8")
    for path in (PART, RULES, RESERVER, BARRIERS, EXT / "tools/pairs.json", EXT / "tools/fix/power_reinforce_spec.json"):
        read(path)
    cmd = [sys.executable, str(RESERVER), str(input_path), str(PART), str(RULES), str(output_path), str(OUT / "reserve")]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    (OUT / "reserve-host.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, "Host reservation generation failed")
    reserved = json.loads(output_path.read_text())
    dru = (OUT / "reserve/board.kicad_dru").read_text()
    exemptions = {}
    for line in dru.splitlines():
        match = re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)', line.strip())
        if match:
            exemptions[match.group(1)] = {norm(net) for net in re.findall(r"A\.NetName != '([^']*)'", match.group(2))}
    areas = [{**area, "exempt": exemptions.get(area["name"], set())} for area in reserved["keepouts"]]
    return areas


def hard_shapes(g, areas, net, layer, for_via=False):
    output = []
    for area in g["rule_areas"]:
        if layer in area["layers"] and (area.get("no_vias") if for_via else area.get("no_tracks") or area.get("no_zones")):
            output += base.polygons(area["outline"])
    for area in areas:
        if layer in area["layers"] and norm(net) not in area["exempt"]:
            output += base.polygons(area["outline"])
    barrier_refs = {record["refdes"] for record in json.loads(read(BARRIERS))["barriers"]}
    for foot in g["footprints"]:
        if foot["ref"] in barrier_refs:
            for records in foot["courtyard"].values():
                output += [polygon.buffer(.6) for polygon in base.polygons(records)]
    if layer == "In3.Cu":
        for zone in g["zones"]:
            if norm(zone["net"]) == "/CORE_1V2" and layer in zone["layers"]:
                output += base.polygons(zone["outline"])
    return [polygon for polygon in output if polygon.intersects(WINDOW.buffer(3))]


def free_copper(g, areas, net, layer, window=WINDOW, omit=()):
    domain = g["domains_normalized"].get(norm(net))
    obstacles = []
    def retain(polygon, gap):
        if polygon.intersects(window.buffer(3)):
            obstacles.append(polygon.buffer(gap + MARGIN))
    def gap(other):
        return .15 if g["domains_normalized"].get(norm(other)) == domain else .6
    for track in g["tracks"]:
        if track["uuid"] not in omit and track["layer"] == layer and norm(track["net"]) != norm(net):
            retain(base.body(track), gap(track["net"]))
    for pad in g["pads"]:
        if norm(pad["net"]) != norm(net):
            for polygon in base.polygons(pad["layers"].get(layer, [])):
                retain(polygon, gap(pad["net"]))
        for polygon in base.polygons(pad.get("hole") or []):
            retain(polygon, .25)
    for via in g["vias"]:
        if norm(via["net"]) != norm(net):
            retain(Point(via["x"], via["y"]).buffer(via["d"] / 2), gap(via["net"]))
        retain(Point(via["x"], via["y"]).buffer(via["drill"] / 2), .25)
    for zone in g["zones"]:
        if norm(zone["net"]) != norm(net):
            for polygon in base.polygons(zone["fills"].get(layer, [])):
                retain(polygon, gap(zone["net"]))
    for graphic in g["shapes"]:
        if graphic["layer"] == layer and norm(graphic["net"]) != norm(net):
            for polygon in base.polygons(graphic["poly"]):
                retain(polygon, gap(graphic["net"]))
    obstacles += [polygon.buffer(MARGIN) for polygon in hard_shapes(g, areas, net, layer)]
    base.WINDOW = window
    reference = base.layer_reference(g, "In1.Cu").intersection(base.layer_reference(g, "In4.Cu")).buffer(-.6)
    return window.intersection(reference).difference(unary_union(obstacles))


def landing(g, areas, terminal, window):
    old = base.source_screen(g, terminal=terminal, window=window.bounds)
    region = shape(old["via_landing_region"])
    # A through via must satisfy all source reservations and all existing holes, even same-net holes.
    blockers = []
    for layer in g["copper_layers"]:
        blockers += [polygon.buffer(.3 + MARGIN) for polygon in hard_shapes(g, areas, NET, layer, for_via=True)]
    for via in g["vias"]:
        blockers.append(Point(via["x"], via["y"]).buffer(via["drill"] / 2 + .15 + .25 + MARGIN))
    for pad in g["pads"]:
        blockers += [polygon.buffer(.15 + .25 + MARGIN) for polygon in base.polygons(pad.get("hole") or [])]
    return region.difference(unary_union([polygon for polygon in blockers if polygon.intersects(window.buffer(2))]))


def layer_screen(g, areas, layer, width, source_landing, load_landing):
    free = free_copper(g, areas, NET, layer)
    branch = free.buffer(-.4)
    trunk = free.buffer(-width / 2)
    source_parts, load_parts = [], []
    for part in hubs.components(branch):
        if part.intersects(source_landing):
            sites = hubs.pack_region(part.intersection(source_landing), (221.126875, 138.968594))
            if sites:
                source_parts.append((part, sites))
        if part.intersects(load_landing):
            sites = hubs.pack_region(part.intersection(load_landing), (116.852, 167.175))
            if sites:
                load_parts.append((part, sites))
    result = {"layer": layer, "width_mm": width, "window_mm": list(WINDOW.bounds),
              "source_branch_component_site_counts": sorted([len(sites) for _, sites in source_parts], reverse=True),
              "load_branch_component_site_counts": sorted([len(sites) for _, sites in load_parts], reverse=True),
              "four_site_array_trunk_pairs": 0, "candidate_paths": [], "bounded_search_node_cap": 180000}
    for part in hubs.components(trunk):
        choices = []
        for sp, ss in source_parts:
            if len(ss) < 4 or not sp.intersects(part):
                continue
            sh = hubs.grid_point_near(sp.intersection(part), (221.126875, 138.968594), radius=12)
            if sh is None:
                continue
            for lp, ls in load_parts:
                if len(ls) < 4 or not lp.intersects(part):
                    continue
                lh = hubs.grid_point_near(lp.intersection(part), (116.852, 167.175), radius=12)
                if lh is not None:
                    choices.append((math.dist(sh, lh), sh, lh, ss, ls))
        result["four_site_array_trunk_pairs"] += len(choices)
        for _, sh, lh, ss, ls in sorted(choices)[:1]:
            path, searched = hubs.astar(part, sh, lh, maximum_nodes=180000)
            if path:
                result["candidate_paths"].append({"points": path, "trunk_length_mm": LineString(path).length,
                    "source_sites_available": ss, "load_sites_available": ls, "searched_nodes": searched})
    result["verdict"] = "HOST_TRUNK_PATH_ARRAY_FANOUT_AND_CURRENT_UNPROVED" if result["candidate_paths"] else "NO_BOUNDED_CONSTANT_WIDTH_SOURCE_LOAD_NETWORK"
    return result


def resistance_bounds():
    rho = 1.7241e-8 * (1 + .00393 * 40)
    sheet = rho / 35e-6
    via = rho * 1.6e-3 / (math.pi * .3e-3 * 25e-6)
    pairs = []
    for wa, wb, na, nb in ((1.5, 1.5, 4, 4), (2., 1.5, 4, 4), (2., 1.5, 5, 3), (2., 1.5, 6, 2)):
        ia_min = max(0., 3.6 - .5 * nb)
        ia_max = min(3.6, .5 * na)
        pairs.append({"widths_mm": [wa, wb], "source_load_vias_per_branch": [na, nb],
            "branch_A_current_allowed_a": [ia_min, ia_max],
            "required_RB_over_RA": [ia_min / (3.6 - ia_min), ia_max / (3.6 - ia_max)],
            "strip_resistance_mohm_per_mm": [sheet / wa * 1000, sheet / wb * 1000],
            "two_transition_series_via_mohm_per_branch": [2 * via / na * 1000, 2 * via / nb * 1000]})
    return {"copper_temp_c": 60, "copper_um": 35, "barrel_plating_um_assumed": 25, "board_thickness_mm_assumed": 1.6,
        "rho_ohm_m": rho, "sheet_ohm_per_square": sheet, "one_via_ohm": via,
        "current_a": 3.6, "drop_budget_v": .1, "total_network_resistance_max_ohm": .1 / 3.6,
        "parallel_formula": "IA=3.6*RB/(RA+RB); IB=3.6*RA/(RA+RB); drop=3.6*(Rcommon+RA*RB/(RA+RB))",
        "branch_formula": "RA=sheet*LA/WA+2*Rvia/nA+source_fanoutA+load_fanoutA; likewise B. Every individual barrel current must be solved, not just the aggregate array",
        "branch_bounds": pairs, "equal_sharing_assumed": False}


def main():
    OUT.mkdir(exist_ok=True)
    g, overlay_receipt = overlay()
    print("C05_OVERLAY_READY", flush=True)
    areas = reservations(g)
    print("HOST_RESERVATIONS_READY", len(areas), flush=True)
    source, load = landing(g, areas, "U11012", SOURCE_WINDOW), landing(g, areas, "J15001", LOAD_WINDOW)
    results = []
    for layer in ("In3.Cu", "B.Cu", "In2.Cu", "F.Cu"):
        for width in (1.5, 2.0):
            print("BOUNDED_SPLIT_SCREEN", layer, width, flush=True)
            result = layer_screen(g, areas, layer, width, source, load)
            results.append(result)
            print(result["verdict"], result["source_branch_component_site_counts"], result["four_site_array_trunk_pairs"], flush=True)
    for path in (Path(__file__), Path(base.__file__), Path(hubs.__file__), HERE.parent / "reconcile_dfm.py",
                 HERE.parent / "compose_additions.py", Path(base.pcbtext.__file__), EXT / "tools/verify/rail_model.json"):
        read(path)
    model = json.loads(read(EXT / "tools/verify/rail_model.json"))["rails"]["/motherboard_power_entry/SBC_5V"]
    require(model["cases"]["operator_3p6"]["only"] == {"J15001": 3.6} and model["cases"]["operator_3p6"]["budget_mv"] == 100,
            "Operator current/load/budget changed")
    for path, expected in READS.items():
        require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "Frozen read input changed")
    report = {"evidence_class": "Bounded host-only source proposal; no native board candidate", "board_sha256": C05_SHA,
        "overlay": overlay_receipt, "source_landing_region": mapping(source), "load_landing_region": mapping(load),
        "constant_width_screens": results, "resistance_model": resistance_bounds(), "read_set_sha256": READS,
        "current_and_load_unchanged": True, "qualified_3p6A_100mV": False, "native_launched": False,
        "board_modified": False, "gpu_jobs": 0, "adopted": False,
        "limits": ["Pinned r06 native pads/fills are host-overlaid with exact c05 copper and translated pad/courtyard poses; no fresh c05 geometric export is claimed",
            "All foreign fills, same/cross-domain clearances, holes, board/rule reservations, core region and galvanic barrier courtyards are retained conservatively",
            "Generated reservations use exact existing exemption policy including documented mutual/foreign-pad exemptions; crossing those areas still requires SI/return review",
            "Four-site branch screens test trunk connectivity; global distinct eight-via packing, source/load fanout, individual barrel current, pad/neck spreading/contact/return/transient/thermal gates remain open",
            "A no-path result applies only to the stated bounded window, layers, widths, reservations and sampled .8mm branch array landing; it is not global routing impossibility"]}
    (OUT / "split-network-screen.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT / "split-network-screen.json"), "candidate_path_count": sum(len(row["candidate_paths"]) for row in results)}), flush=True)


if __name__ == "__main__":
    main()
