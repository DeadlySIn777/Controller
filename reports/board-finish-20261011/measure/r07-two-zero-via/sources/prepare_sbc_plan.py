"""Read-only ROOT106/r06 SBC_5V source plan and geometry feasibility screen.

No candidate copper, native command or GPU job is launched. Field-pdn's completed
refilled r06 geometry export is used only after checking its board hash and flags.
"""
import collections
import hashlib
import json
import math
import heapq
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box, mapping
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from compose_additions import inventory, pcbtext
from reconcile_dfm import children, kind, ref_of

EXT = Path("Z:/pcb-runs/claude-finish")
BASE = EXT / "integrate/revs/r06-stitch-plane-pads-2.kicad_pcb"
BASE_SHA = "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53"
GEOM = EXT / "agent-work/field-pdn/testA3/w/geom.json"
NET = "/motherboard_power_entry{slash}SBC_5V"
WINDOW = box(206, 131, 226, 145)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def polygons(records):
    result = []
    for outer, holes in records:
        poly = Polygon(outer, holes)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            result.append(poly)
    return result


def body(track):
    if track.get("kind") == "arc":
        return unary_union(polygons(track["poly"]))
    return LineString([track["a"], track["b"]]).buffer(track["w"] / 2)


def layer_reference(geometry, layer):
    covered, own = Polygon(), Polygon()
    for zone in sorted((zone for zone in geometry["zones"] if layer in zone["layers"]),
                       key=lambda zone: zone["priority"], reverse=True):
        shape = unary_union(polygons(zone["outline"])).intersection(WINDOW)
        effective = shape.difference(covered)
        covered = covered.union(shape)
        if zone["net"] == "/LOGIC_GND":
            own = own.union(effective)
    return own


def source_screen(geometry, terminal="U11012", window=(206, 131, 226, 145)):
    global WINDOW
    WINDOW = box(*window)
    domains = geometry["nets"]
    via_obstacles, front_obstacles = [], []
    own_source = []
    for pad in geometry["pads"]:
        same = pad["net"] == NET
        clearance = 0.15 if domains.get(pad["net"]) == "DOM_LOGIC" else 0.6
        for layer, records in pad["layers"].items():
            for shape in polygons(records):
                if not shape.intersects(WINDOW.buffer(2)):
                    continue
                if not same:
                    via_obstacles.append(shape.buffer(clearance + 0.3))
                    if layer == "F.Cu":
                        front_obstacles.append(shape.buffer(clearance))
                elif pad["smd"]:
                    via_obstacles.append(shape.buffer(0.1 + 0.3))
                if same and pad["ref"] == terminal and layer == "F.Cu":
                    own_source.append(shape)
        if pad.get("hole"):
            via_obstacles.extend(shape.buffer(0.25 + 0.15) for shape in polygons(pad["hole"]))
    for track in geometry["tracks"]:
        if track["net"] == NET:
            continue
        shape = body(track)
        if not shape.intersects(WINDOW.buffer(2)):
            continue
        clearance = 0.15 if domains.get(track["net"]) == "DOM_LOGIC" else 0.6
        via_obstacles.append(shape.buffer(clearance + 0.3))
        if track["layer"] == "F.Cu":
            front_obstacles.append(shape.buffer(clearance))
    for via in geometry["vias"]:
        if via["net"] == NET:
            continue
        point = Point(via["x"], via["y"])
        if not point.intersects(WINDOW.buffer(2)):
            continue
        clearance = 0.15 if domains.get(via["net"]) == "DOM_LOGIC" else 0.6
        via_obstacles.append(point.buffer(max(via["d"] / 2 + clearance + 0.3,
                                                via["drill"] / 2 + 0.25 + 0.15)))
        front_obstacles.append(point.buffer(via["d"] / 2 + clearance))
    for zone in geometry["zones"]:
        if domains.get(zone["net"]) != "DOM_LOGIC" and zone["net"] != NET:
            for records in zone["fills"].values():
                for shape in polygons(records):
                    if shape.intersects(WINDOW.buffer(2)):
                        via_obstacles.append(shape.buffer(0.6 + 0.3))
        # A new source pour may not displace another net's existing F.Cu pour.
        if zone["net"] != NET:
            for shape in polygons(zone["fills"].get("F.Cu", [])):
                if shape.intersects(WINDOW.buffer(2)):
                    clearance = 0.15 if domains.get(zone["net"]) == "DOM_LOGIC" else 0.6
                    front_obstacles.append(shape.buffer(clearance))
    for graphic in geometry["shapes"]:
        if graphic["net"] == NET:
            continue
        clearance = 0.15 if domains.get(graphic["net"]) == "DOM_LOGIC" else 0.6
        for shape in polygons(graphic["poly"]):
            if shape.intersects(WINDOW.buffer(2)):
                via_obstacles.append(shape.buffer(clearance + 0.3))
                if graphic["layer"] == "F.Cu":
                    front_obstacles.append(shape.buffer(clearance))
    for area in geometry["rule_areas"]:
        for shape in polygons(area["outline"]):
            if shape.intersects(WINDOW.buffer(2)):
                via_obstacles.append(shape.buffer(0.3))
                front_obstacles.append(shape)
    reference = layer_reference(geometry, "In1.Cu").intersection(layer_reference(geometry, "In4.Cu")).buffer(-0.6)
    free_vias = WINDOW.intersection(reference).difference(unary_union(via_obstacles))
    front_free = WINDOW.difference(unary_union(front_obstacles))
    source = unary_union(own_source)
    components = list(front_free.geoms) if front_free.geom_type == "MultiPolygon" else [front_free]
    source_components = [component for component in components if component.intersects(source)]
    source_component = unary_union(source_components)
    landing = free_vias.intersection(source_component)
    # Sites are planning hints. Equal sharing, necks and return paths remain unproved.
    sites = []
    for iy in range(round(window[1] * 10), round(window[3] * 10) + 1):
        for ix in range(round(window[0] * 10), round(window[2] * 10) + 1):
            location = (ix / 10, iy / 10)
            if landing.contains(Point(location)) and all(math.dist(location, site) >= 0.9 - 1e-9 for site in sites):
                sites.append(location)
    source_centre = source.centroid
    sites.sort(key=lambda location: source_centre.distance(Point(location)))
    return {"terminal": terminal, "window_mm": list(window), "front_source_component_area_mm2": source_component.area,
            "via_feasible_area_mm2": free_vias.area, "front_source_reachable_via_area_mm2": landing.area,
            "host_site_count_spacing_0p9_mm": len(sites), "closest_eight_planning_sites": sites[:8],
            "all_planning_sites": sites,
            "array_sites_are_not_native_or_current_qualified": True,
            "front_source_component": mapping(source_component), "via_landing_region": mapping(landing)}


def in3_corridor(geometry, source, load, width=3.0):
    global WINDOW
    WINDOW = box(108, 128, 229, 176)
    domains = geometry["nets"]
    obstacles = []
    radius = width / 2
    for track in geometry["tracks"]:
        if track["net"] != NET and track["layer"] == "In3.Cu":
            shape = body(track)
            if shape.intersects(WINDOW.buffer(2)):
                clearance = 0.15 if domains.get(track["net"]) == "DOM_LOGIC" else 0.6
                obstacles.append(shape.buffer(clearance + radius + 0.05))
    for pad in geometry["pads"]:
        if pad["net"] != NET:
            clearance = 0.15 if domains.get(pad["net"]) == "DOM_LOGIC" else 0.6
            for shape in polygons(pad["layers"].get("In3.Cu", [])):
                if shape.intersects(WINDOW.buffer(2)):
                    obstacles.append(shape.buffer(clearance + radius + 0.05))
        if pad.get("hole"):
            for shape in polygons(pad["hole"]):
                if shape.intersects(WINDOW.buffer(2)):
                    obstacles.append(shape.buffer(0.25 + radius + 0.05))
    for via in geometry["vias"]:
        if via["net"] != NET:
            point = Point(via["x"], via["y"])
            if point.intersects(WINDOW.buffer(2)):
                clearance = 0.15 if domains.get(via["net"]) == "DOM_LOGIC" else 0.6
                obstacles.append(point.buffer(max(via["d"] / 2 + clearance,
                                                  via["drill"] / 2 + 0.25) + radius + 0.05))
    for area in geometry["rule_areas"]:
        if "In3.Cu" in area["layers"] and (area.get("no_tracks") or area.get("no_zones")):
            obstacles.extend(shape.buffer(radius + 0.05) for shape in polygons(area["outline"]))
    for graphic in geometry["shapes"]:
        if graphic["layer"] == "In3.Cu" and graphic["net"] != NET:
            clearance = 0.15 if domains.get(graphic["net"]) == "DOM_LOGIC" else 0.6
            obstacles.extend(shape.buffer(clearance + radius + 0.05) for shape in polygons(graphic["poly"]))
    reference = layer_reference(geometry, "In1.Cu").intersection(layer_reference(geometry, "In4.Cu")).buffer(-0.6 - radius)
    free = WINDOW.intersection(reference).difference(unary_union(obstacles))
    sources = [tuple(round(value * 5) for value in point) for point in source["all_planning_sites"]
               if free.contains(Point(point))]
    targets = {tuple(round(value * 5) for value in point) for point in load["all_planning_sites"]
               if free.contains(Point(point))}
    report = {"evidence_class": "host constant-width corridor search; native and array-neck/sharing proof still required",
              "width_mm": width, "source_site_centres_with_trunk_width_clearance": len(sources),
              "load_site_centres_with_trunk_width_clearance": len(targets), "path": [], "length_mm": None}
    if not sources or not targets:
        report["verdict"] = "NO_TRUNK_ENDPOINT_WITH_RETAINED_WIDTH"
        return report
    bounds = [round(value * 5) for value in WINDOW.bounds]
    available = {}
    def allowed(node):
        if node not in available:
            available[node] = bounds[0] <= node[0] <= bounds[2] and bounds[1] <= node[1] <= bounds[3] and free.contains(Point(node[0] / 5, node[1] / 5))
        return available[node]
    def heuristic(node):
        return min(math.dist(node, target) for target in targets)
    queue = [(heuristic(node), 0.0, node) for node in sources]
    heapq.heapify(queue)
    scores, predecessors = {node: 0.0 for node in sources}, {}
    final = None
    while queue:
        _, cost, node = heapq.heappop(queue)
        if cost > scores[node] + 1e-9:
            continue
        if node in targets:
            final = node
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            nxt = (node[0] + dx, node[1] + dy)
            if not allowed(nxt) or (dx and dy and (not allowed((node[0] + dx, node[1])) or not allowed((node[0], node[1] + dy)))):
                continue
            if not free.covers(LineString([(node[0] / 5, node[1] / 5), (nxt[0] / 5, nxt[1] / 5)])):
                continue
            candidate = cost + math.hypot(dx, dy)
            if candidate < scores.get(nxt, math.inf):
                scores[nxt] = candidate
                predecessors[nxt] = node
                heapq.heappush(queue, (candidate + heuristic(nxt), candidate, nxt))
    report["searched_grid_nodes"] = len(scores)
    if final is None:
        report["verdict"] = "NO_3MM_CORRIDOR_WITH_EXISTING_COPPER_AND_REFERENCE"
        return report
    path = [final]
    while path[-1] in predecessors:
        path.append(predecessors[path[-1]])
    path.reverse()
    report.update(verdict="HOST_CORRIDOR_EXISTS", path=[[x / 5, y / 5] for x, y in path], length_mm=scores[final] / 5)
    return report


def main():
    geometry = json.loads(GEOM.read_text())
    if sha(BASE) != BASE_SHA or geometry["sha256"] != BASE_SHA or geometry["refilled"] is not True or geometry["api_errors"]:
        raise ValueError("geometry is not the complete pinned refilled r06 export")
    model_path = EXT / "tools/verify/rail_model.json"
    rail = json.loads(model_path.read_text())["rails"]["/motherboard_power_entry/SBC_5V"]
    if rail["cases"]["operator_3p6"]["only"] != {"J15001": 3.6} or rail["cases"]["operator_3p6"]["budget_mv"] != 100:
        raise ValueError("SBC operator current/drop case changed")
    selected_pads = [{"ref": pad["ref"], "num": pad["num"], "net": pad["net"], "x": pad["x"], "y": pad["y"],
                      "copper_area_mm2": {layer: unary_union(polygons(records)).area for layer, records in pad["layers"].items()}}
                     for pad in geometry["pads"] if pad["net"] == NET]
    tracks = [track for track in geometry["tracks"] if track["net"] == NET]
    lengths = collections.defaultdict(float)
    for track in tracks:
        lengths[(track["layer"], track["w"])] += math.dist(track["a"], track["b"])
    native_items = inventory(BASE.read_bytes())[3]
    inspected = {}
    for chunk in native_items.values():
        if pcbtext.chunk_kind(chunk) == "footprint" and ref_of(chunk) in {"U11012", "J15001"}:
            ref = ref_of(chunk)
            _, nodes = children(chunk)
            inspected[ref] = {"native_sha256": hashlib.sha256(chunk).hexdigest(),
                              "source_vout_pad_definitions": [node.decode() for node in nodes if kind(node) == b"pad" and
                                                             node.startswith((b'(pad "8"', b'(pad "9"', b'(pad "10"'))]
                              if ref == "U11012" else []}
    screening = source_screen(geometry)
    load_screening = source_screen(geometry, terminal="J15001", window=(107, 159, 124, 175))
    corridor = in3_corridor(geometry, screening, load_screening)
    rho60 = 1.7241e-8 * (1 + 0.00393 * 40)
    sheet = rho60 / (35e-6)
    barrel = rho60 * 1.6e-3 / (math.pi * 0.3e-3 * 25e-6)
    via_drop = 3.6 * 2 * barrel / 8
    plan = {"evidence_class": "ROOT106/r06 source and host geometry planning; no new native candidate yet",
            "source_hashes": {str(path): sha(path) for path in (BASE, GEOM, model_path,
                                EXT / "agent-work/sbc5v-r3/refq.py", EXT / "agent-work/sbc5v-r3/base/board.kicad_pcb")},
            "old_sbc_r3_status": "Only inspection plots/ref-query/base DRC attempt exist; no applied candidate or <=100mV native/extracted IR proof",
            "current_board_scope": "r06 fixed footprint/native source, no borrowed ROOT10x result",
            "operator_case": rail["cases"]["operator_3p6"], "rail_sources": rail["sources"], "rail_loads": rail["loads"],
            "source_and_load_native": inspected, "sbc_pads": selected_pads,
            "r06_existing_tracks": len(tracks), "r06_track_length_by_layer_width_mm": {f"{layer}:{width}": length for (layer, width), length in lengths.items()},
            "r06_existing_vias": [via for via in geometry["vias"] if via["net"] == NET],
            "source_array_screen": screening,
            "load_array_screen": load_screening, "in3_3mm_corridor_screen": corridor,
            "proposed_current_path": ["U11012 VOUT8/9/10 -> dedicated local F.Cu SBC copper reaching source array",
                                      "At least8 adequately connected0.6/0.3mm vias for any full3.6A transition at retained0.5A/via screen",
                                      "Dedicated3mm-or-current-model-wider In3 SBC path within DOM_LOGIC reference territory",
                                      "At least8 vias at load landing -> all six J15001 SBC pins77/79/81/83/85/87 on F.Cu",
                                      "Source/core delivery, LOGIC_GND return and all actual converter/switch/contact/transient limits qualified separately"],
            "ideal_uniform_strip_planning_bound": {"current_a": 3.6, "budget_mv": 100, "copper_um": 35,
                "copper_temp_c": 60, "two_eight_via_transition_drop_mv": via_drop * 1000,
                "max_3mm_strip_length_mm_after_ideal_two_arrays": (0.100 - via_drop) * 3e-3 / (3.6 * sheet) * 1000,
                "meaning": "Only an ideal uniform strip bound; actual necks, contacts, current sharing, return and thermal effects are excluded"},
            "next_action": "Hold extra native jobs until existing four slots drain; obtain current load-side via landing and In3 width/neck feasibility, then build bounded isolated candidate if adequate. Refuse a broad pour that displaces foreign-domain or other-current-path copper.",
            "native_launched": False, "new_gpu_jobs": 0, "full_delivery_qualified": False, "manufacturing_ready": False}
    (HERE / "sbc-root106-plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps({"source_host_sites": screening["host_site_count_spacing_0p9_mm"],
                      "load_host_sites": load_screening["host_site_count_spacing_0p9_mm"], "corridor_verdict": corridor["verdict"],
                      "source_reachable_via_area_mm2": screening["front_source_reachable_via_area_mm2"],
                      "max_ideal_3mm_length_mm": plan["ideal_uniform_strip_planning_bound"]["max_3mm_strip_length_mm_after_ideal_two_arrays"],
                      "native_launched": False}))


if __name__ == "__main__":
    main()
