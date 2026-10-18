"""Read-only constant-width SBC route/hub screen on pinned refilled r06.

This preserves every foreign filled-copper shape and both LOGIC_GND reference
territories. Eight 0.8 mm branches carry an assumed equal 0.45 A each; this is a
prospective geometry test, not current-sharing or IR qualification.
"""
import hashlib
import heapq
import json
import math
from pathlib import Path

from shapely.geometry import Point, LineString, Polygon, box, mapping, shape
from shapely.ops import unary_union
from shapely.prepared import prep

import prepare_sbc_plan as initial

HERE = Path(__file__).resolve().parent
WINDOW = box(107, 128, 229, 176)
BRANCH_W = 0.8
TRUNK_W = 3.0
ARRAY_SPACING = 0.8  # 0.6 mm copper diameter + 0.15 mm separation + 0.05 mm planning margin


def components(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == "Polygon":
        return [shape]
    return [part for part in shape.geoms if part.geom_type == "Polygon" and not part.is_empty]


def pack_region(region, centre, spacing=ARRAY_SPACING):
    """Sample the whole retained landing region, not the earlier greedy hints."""
    if region.is_empty:
        return []
    prepared, candidates = prep(region), []
    x0, y0, x1, y1 = region.bounds
    for x in range(math.ceil(x0 * 10), math.floor(x1 * 10) + 1):
        for y in range(math.ceil(y0 * 10), math.floor(y1 * 10) + 1):
            point = (x / 10, y / 10)
            if prepared.contains(Point(point)):
                candidates.append(point)
    if not candidates:
        return []
    # Multiple sweep orientations and grid seeds avoid assuming that the first
    # greedy placement establishes a packing limit. This still is not a proof
    # of exhaustive continuous packing impossibility.
    seeds = [centre] + candidates[::max(1, len(candidates) // 48)]
    orders = [sorted(candidates, key=lambda point: (math.dist(point, seed), point)) for seed in seeds]
    for angle in range(0, 360, 30):
        a = math.radians(angle)
        orders.append(sorted(candidates, key=lambda point: (point[0] * math.cos(a) + point[1] * math.sin(a), point)))
    best = []
    for order in orders:
        result = []
        for candidate in order:
            if all(math.dist(candidate, chosen) >= spacing - 1e-9 for chosen in result):
                result.append(candidate)
        if len(result) > len(best) or (len(result) == len(best) and sum(math.dist(site, centre) for site in result) < sum(math.dist(site, centre) for site in best)):
            best = result
    return best


def free_copper(geometry, layer):
    initial.WINDOW = WINDOW
    reference = initial.layer_reference(geometry, "In1.Cu").intersection(initial.layer_reference(geometry, "In4.Cu")).buffer(-0.6)
    domains, obstacles = geometry["nets"], []
    def retain(shape, clearance):
        if shape.intersects(WINDOW.buffer(2)):
            obstacles.append(shape.buffer(clearance + 0.05))
    def gap(net):
        return 0.15 if domains.get(net) == "DOM_LOGIC" else 0.6
    for track in geometry["tracks"]:
        if track["net"] != initial.NET and track["layer"] == layer:
            retain(initial.body(track), gap(track["net"]))
    for pad in geometry["pads"]:
        if pad["net"] != initial.NET:
            for shape in initial.polygons(pad["layers"].get(layer, [])):
                retain(shape, gap(pad["net"]))
        for shape in initial.polygons(pad.get("hole") or []):
            retain(shape, 0.25)
    for via in geometry["vias"]:
        if via["net"] != initial.NET:
            retain(Point(via["x"], via["y"]).buffer(via["d"] / 2), gap(via["net"]))
        retain(Point(via["x"], via["y"]).buffer(via["drill"] / 2), 0.25)
    for zone in geometry["zones"]:
        if zone["net"] != initial.NET:
            for shape in initial.polygons(zone["fills"].get(layer, [])):
                retain(shape, gap(zone["net"]))
    for area in geometry["rule_areas"]:
        if layer in area["layers"] and (area.get("no_tracks") or area.get("no_zones")):
            for shape in initial.polygons(area["outline"]):
                retain(shape, 0)
    for graphic in geometry["shapes"]:
        if graphic["layer"] == layer and graphic["net"] != initial.NET:
            for shape in initial.polygons(graphic["poly"]):
                retain(shape, gap(graphic["net"]))
    return WINDOW.intersection(reference).difference(unary_union(obstacles))


def grid_point_near(shape, desired, step=0.2, radius=12):
    prepared = prep(shape)
    x0, y0 = (round(value / step) for value in desired)
    candidates = []
    n = math.ceil(radius / step)
    for dx in range(-n, n + 1):
        for dy in range(-n, n + 1):
            point = ((x0 + dx) * step, (y0 + dy) * step)
            distance = math.dist(point, desired)
            if distance <= radius and prepared.contains(Point(point)):
                candidates.append((distance, point))
    return min(candidates)[1] if candidates else None


def astar(free, start, goal, step=0.2, maximum_nodes=450000):
    s = tuple(round(value / step) for value in start)
    target = tuple(round(value / step) for value in goal)
    shape = prep(free)
    available, predecessor = {}, {}
    def allowed(node):
        if node not in available:
            available[node] = shape.contains(Point(node[0] * step, node[1] * step))
        return available[node]
    if not allowed(s) or not allowed(target):
        return None, 0
    queue, scores = [(math.dist(s, target), 0.0, s)], {s: 0.0}
    while queue and len(scores) <= maximum_nodes:
        _, cost, node = heapq.heappop(queue)
        if cost > scores[node] + 1e-9:
            continue
        if node == target:
            path = [node]
            while path[-1] in predecessor:
                path.append(predecessor[path[-1]])
            path.reverse()
            # Collinear grid steps are merged; the exact segment is still checked.
            merged = [path[0]]
            for index in range(1, len(path) - 1):
                a, b, c = path[index - 1:index + 2]
                if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
                    merged.append(b)
            if len(path) > 1:
                merged.append(path[-1])
            points = [[round(x * step, 4), round(y * step, 4)] for x, y in merged]
            if any(not free.covers(LineString([a, b])) for a, b in zip(points, points[1:])):
                raise ValueError("merged route escaped the exact free region")
            return points, len(scores)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            nxt = node[0] + dx, node[1] + dy
            if not allowed(nxt) or (dx and dy and (not allowed((node[0] + dx, node[1])) or not allowed((node[0], node[1] + dy)))):
                continue
            if not free.covers(LineString([(node[0] * step, node[1] * step), (nxt[0] * step, nxt[1] * step)])):
                continue
            value = cost + math.hypot(dx, dy)
            if value < scores.get(nxt, math.inf):
                scores[nxt] = value
                predecessor[nxt] = node
                heapq.heappush(queue, (value + math.dist(nxt, target), value, nxt))
    return None, len(scores)


def screen_layer(geometry, plan, layer):
    free = free_copper(geometry, layer)
    branch_free = free.buffer(-BRANCH_W / 2)
    trunk_free = free.buffer(-TRUNK_W / 2)
    source_landing = shape(plan["source_array_screen"]["via_landing_region"])
    load_landing = shape(plan["load_array_screen"]["via_landing_region"])
    source_centre, load_centre = (221.126875, 138.968594), (116.852, 167.175)
    branches = components(branch_free)
    source_groups = [(part, pack_region(part.intersection(source_landing), source_centre)) for part in branches
                     if part.intersects(source_landing)]
    load_groups = [(part, pack_region(part.intersection(load_landing), load_centre)) for part in branches
                   if part.intersects(load_landing)]
    source_counts = sorted((len(sites) for part, sites in source_groups), reverse=True)
    load_counts = sorted((len(sites) for part, sites in load_groups), reverse=True)
    source_detail = [{"sampled_via_sites": sites, "landing_area_mm2": part.intersection(source_landing).area,
                      "branch_component_area_mm2": part.area,
                      "nearest_3mm_hub_within_12mm": grid_point_near(part.intersection(trunk_free), source_centre)}
                     for part, sites in source_groups if sites]
    source_groups = [(part, sites) for part, sites in source_groups if len(sites) >= 8]
    load_groups = [(part, sites) for part, sites in load_groups if len(sites) >= 8]
    result = {"layer": layer, "trunk_width_mm": TRUNK_W, "individual_branch_width_mm": BRANCH_W,
              "source_components_with_eight_sites": [len(sites) for part, sites in source_groups],
              "load_components_with_eight_sites": [len(sites) for part, sites in load_groups],
              "all_source_component_site_counts": source_counts,
              "all_load_component_site_counts": load_counts,
              "source_component_details": source_detail,
              "site_search_policy": "Whole landing region sampled at 0.1 mm; up to 49 seed and 12 sweep greedy packings; empty result is not an exhaustive geometric packing impossibility",
              "array_centre_spacing_mm": ARRAY_SPACING,
              "array_spacing_basis": "0.6 mm copper diameter + retained 0.15 mm separation + 0.05 mm planning margin; hole gap >=0.5 mm",
              "existing_foreign_filled_copper_preserved": True,
              "reference_policy": "Within effective LOGIC_GND outlines on both In1 and In4, 0.6 mm inset; no borrowed FIELD domains",
              "native_launched": False, "verdict": "NO_EIGHT_SITE_SOURCE_BRANCH_COMPONENT"}
    if not source_groups:
        return result
    if not load_groups:
        result["verdict"] = "NO_EIGHT_SITE_LOAD_BRANCH_COMPONENT"
        return result
    choices = []
    for trunk in components(trunk_free):
        for sp, ss in source_groups:
            reachable_source = sp.intersection(trunk)
            if reachable_source.is_empty:
                continue
            hub_s = grid_point_near(reachable_source, source_centre)
            if hub_s is None:
                continue
            for lp, ls in load_groups:
                reachable_load = lp.intersection(trunk)
                if reachable_load.is_empty:
                    continue
                hub_l = grid_point_near(reachable_load, load_centre)
                if hub_l is not None:
                    choices.append((math.dist(hub_s, source_centre) + math.dist(hub_l, load_centre), trunk, sp, ss, lp, ls, hub_s, hub_l))
    result["wide_hub_pair_choices"] = len(choices)
    if not choices:
        result["verdict"] = "NO_SHARED_3MM_TRUNK_COMPONENT_WITH_BOTH_EIGHT_SITE_ARRAY_HUBS"
        return result
    for _, trunk, sp, ss, lp, ls, hub_s, hub_l in sorted(choices, key=lambda choice: choice[0])[:4]:
        path, searched = astar(trunk, hub_s, hub_l)
        result["trunk_searched_nodes"] = searched
        if path is None:
            continue
        arrays, okay = [], True
        for component, sites, hub, name in ((sp, ss, hub_s, "source"), (lp, ls, hub_l, "load")):
            chosen = sorted(sites, key=lambda site: math.dist(site, hub))[:8]
            routes = []
            for site in chosen:
                branch, _ = astar(component, site, hub, step=0.1, maximum_nodes=150000)
                if branch is None:
                    okay = False
                    break
                routes.append({"via": site, "width_mm": BRANCH_W, "path": branch, "assumed_equal_share_a": 3.6 / 8})
            arrays.append({"name": name, "hub": hub, "sites": chosen, "branches": routes})
        if okay:
            result.update(verdict="PROSPECTIVE_HOST_GEOMETRY_ROUTE", trunk_path=path,
                          trunk_length_mm=sum(math.dist(a, b) for a, b in zip(path, path[1:])), arrays=arrays,
                          current_sharing_verdict="OPEN_EQUAL_SHARE_ASSUMPTION", source_load_pour_ir_verdict="OPEN")
            return result
    result["verdict"] = "NO_GRID_RESOLVED_ROUTE_FOR_REVIEWED_WIDE_HUBS"
    return result


def main():
    plan_path = HERE / "sbc-root106-plan.json"
    plan = json.loads(plan_path.read_text())
    geometry = json.loads(initial.GEOM.read_text())
    if initial.sha(initial.BASE) != initial.BASE_SHA or geometry["sha256"] != initial.BASE_SHA or geometry["refilled"] is not True or geometry["api_errors"]:
        raise ValueError("geometry/base changed or export incomplete")
    results = []
    for layer in ("In3.Cu", "In2.Cu", "B.Cu"):
        print("SCREENING", layer, flush=True)
        result = screen_layer(geometry, plan, layer)
        print(layer, result["verdict"], flush=True)
        results.append(result)
    report = {"evidence_class": "host polygon and constant-width route planning only", "base_sha256": initial.BASE_SHA,
              "source_hashes": {str(path): initial.sha(path) for path in (initial.BASE, initial.GEOM, plan_path, Path(__file__), Path(initial.__file__))},
              "net": initial.NET, "current_case_a": 3.6, "budget_mv": 100, "via_arrays": "eight 0.6/0.3 mm vias at both source and load",
              "layers": results, "native_launched": False, "new_gpu_jobs": 0, "adopted": False,
              "limits": ["Equal eight-way sharing is assumed, not guaranteed; shared branch merges and local pours need extracted IR/thermal review",
                         "Foreign filled copper, rule areas and LOGIC reference territory are retained geometrically; native refill must verify this",
                         "Existing root106 model concerns converter/core delivery and return separately; no result is borrowed from another rail",
                         "A host route does not qualify 3.6 A, 100 mV, source/load pad necks, actual return paths, switch/contact or transient limits"]}
    (HERE / "sbc-root106-hubs.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
