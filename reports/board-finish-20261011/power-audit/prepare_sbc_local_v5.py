"""Exact-endpoint local paths, distinct .6/.3 and .5/.2 OPI via cases.

Never writes a native board or changes any earlier producer/receipt.
"""
import copy
import hashlib
import heapq
import json
import math
from pathlib import Path

from shapely.geometry import Point, LineString, mapping
from shapely.ops import unary_union
from shapely.prepared import prep

import prepare_sbc_local_v4 as four

three, v, p = four.three, four.v, four.p
old = v.prior


def exact_path(free, start, goal, step=.1, node_cap=50000):
    if not free.covers(Point(start)) or not free.covers(Point(goal)):
        return {"verdict": "ENDPOINT_BLOCKED_IN_PLANNING_MASK", "blocked": [list(at) for at in (start, goal) if not free.covers(Point(at))]}
    if free.covers(LineString([start, goal])):
        return {"verdict": "HOST_PATH", "points": [list(start), list(goal)], "length_mm": math.dist(start, goal), "searched_nodes": 0}
    component = next((part for part in p.hubs.components(free) if part.covers(Point(start)) and part.covers(Point(goal))), None)
    if component is None:
        return {"verdict": "DISCONNECTED_FREE_COMPONENTS_IN_WINDOW"}
    prepared, available = prep(component), {}
    def xy(node):
        return (round(node[0] * step, 8), round(node[1] * step, 8))
    def allowed(node):
        if node not in available:
            available[node] = prepared.contains(Point(xy(node)))
        return available[node]
    def connectors(at):
        origin = tuple(round(value / step) for value in at)
        rows = []
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                node = (origin[0] + dx, origin[1] + dy)
                if allowed(node) and component.covers(LineString([at, xy(node)])):
                    rows.append((math.dist(at, xy(node)), node))
        return sorted(rows)[:12]
    aa, bb = connectors(start), connectors(goal)
    if not aa or not bb:
        return {"verdict": "NO_EXACT_ENDPOINT_TO_GRID_CONNECTOR", "start_connector_count": len(aa), "goal_connector_count": len(bb)}
    targets = {node: length for length, node in bb}
    scores, prior, queue = {}, {}, []
    for length, node in aa:
        scores[node] = length
        heapq.heappush(queue, (length + math.dist(xy(node), goal), length, node))
    while queue and len(scores) <= node_cap:
        _, cost, node = heapq.heappop(queue)
        if cost > scores[node] + 1e-9:
            continue
        if node in targets:
            path = [node]
            while path[-1] in prior:
                path.append(prior[path[-1]])
            path.reverse()
            reduced = [path[0]]
            for index in range(1, len(path) - 1):
                a, b, c = path[index - 1:index + 2]
                if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]):
                    reduced.append(b)
            if len(path) > 1:
                reduced.append(path[-1])
            points = [list(start)] + [list(xy(n)) for n in reduced] + [list(goal)]
            points = [point for index, point in enumerate(points) if index == 0 or math.dist(point, points[index - 1]) > 1e-9]
            p.require(all(component.covers(LineString([a, b])) for a, b in zip(points, points[1:])), "Path or exact endpoint connector escaped mask")
            return {"verdict": "HOST_PATH", "points": points, "length_mm": LineString(points).length, "searched_nodes": len(scores),
                    "exact_native_endpoint_connectors_checked": True}
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            nxt = (node[0] + dx, node[1] + dy)
            if not allowed(nxt) or (dx and dy and (not allowed((node[0] + dx, node[1])) or not allowed((node[0], node[1] + dy)))):
                continue
            if not component.covers(LineString([xy(node), xy(nxt)])):
                continue
            candidate = cost + math.hypot(dx, dy) * step
            if candidate < scores.get(nxt, math.inf):
                scores[nxt] = candidate
                prior[nxt] = node
                heapq.heappush(queue, (candidate + math.dist(xy(nxt), goal), candidate, nxt))
    return {"verdict": "NO_PATH_AT_GRID_OR_NODE_CAP", "searched_nodes": len(scores), "node_cap": node_cap}


def via_region(g, areas, net, diameter, drill):
    window = v.VIA_WINDOW
    domain, obstacles = g["domains_normalized"].get(p.norm(net)), []
    radius = diameter / 2
    def retain(poly, gap):
        if poly.intersects(window.buffer(2)):
            obstacles.append(poly.buffer(gap + radius + p.MARGIN))
    def gap(other):
        return .15 if g["domains_normalized"].get(p.norm(other)) == domain else .6
    for pad in g["pads"]:
        for records in pad["layers"].values():
            for poly in p.base.polygons(records):
                if p.norm(pad["net"]) != p.norm(net):
                    retain(poly, gap(pad["net"]))
                if pad["smd"]:
                    retain(poly, .1)
        for poly in p.base.polygons(pad.get("hole") or []):
            if poly.intersects(window.buffer(2)):
                obstacles.append(poly.buffer(drill / 2 + .25 + p.MARGIN))
    for track in g["tracks"]:
        if p.norm(track["net"]) != p.norm(net):
            retain(p.base.body(track), gap(track["net"]))
    for via in g["vias"]:
        if p.norm(via["net"]) != p.norm(net):
            retain(Point(via["x"], via["y"]).buffer(via["d"] / 2), gap(via["net"]))
        point = Point(via["x"], via["y"])
        if point.intersects(window.buffer(2)):
            obstacles.append(point.buffer(via["drill"] / 2 + drill / 2 + .25 + p.MARGIN))
    for zone in g["zones"]:
        if g["domains_normalized"].get(p.norm(zone["net"])) != domain:
            for records in zone["fills"].values():
                for poly in p.base.polygons(records):
                    retain(poly, .6)
    for layer in g["copper_layers"]:
        obstacles += [poly.buffer(radius + p.MARGIN) for poly in p.hard_shapes(g, areas, net, layer, for_via=True)]
    p.base.WINDOW = window
    reference = p.base.layer_reference(g, "In1.Cu").intersection(p.base.layer_reference(g, "In4.Cu")).buffer(-.6 - radius)
    return window.intersection(reference).difference(unary_union(obstacles))


def via_record(at, net, diameter, drill, label, layers):
    return {"uuid": label, "net": net, "x": at[0], "y": at[1], "d": diameter, "drill": drill,
            "flashed": layers, "span": ["F.Cu", "B.Cu"]}


def rooted_ground(g):
    anchors = [pad for pad in g["pads"] if (pad["ref"], pad["num"]) in (("J11001", "2"), ("J11002", "2"))]
    result = {}
    for layer in ("In1.Cu", "In4.Cu"):
        source = unary_union([poly for pad in anchors for poly in p.base.polygons(pad["layers"].get(layer, []))])
        result[layer] = unary_union([poly for zone in g["zones"] if p.norm(zone["net"]) == v.GND
            for poly in p.base.polygons(zone["fills"].get(layer, [])) if poly.intersects(source)])
    return result


def rooted_via(rooted, at, diameter):
    disc = Point(at).buffer(diameter / 2)
    return {layer: geo.intersection(disc).area for layer, geo in rooted.items()}


def return_candidates(g, areas, at, rooted, diameter=.6, drill=.3):
    existing = []
    for via in g["vias"]:
        if p.norm(via["net"]) == v.GND and math.dist(at, (via["x"], via["y"])) <= 1.0:
            contact = rooted_via(rooted, (via["x"], via["y"]), via["d"])
            existing.append({"uuid": via["uuid"], "at": [via["x"], via["y"]], "distance_mm": math.dist(at, (via["x"], via["y"])),
                "baseline_direct_source_fill_contact_mm2": contact, "baseline_both_direct_source_pieces": all(x > 1e-6 for x in contact.values())})
    if any(row["baseline_both_direct_source_pieces"] for row in existing):
        return {"at": at, "existing": existing, "new_stitch_candidates": [], "planning_return_status": "BASELINE_SOURCE_CONNECTED_EXISTING_STITCH_HINT"}
    legal = via_region(g, areas, v.GND, diameter, drill)
    ring = Point(at).buffer(1.0).difference(Point(at).buffer(.9))
    candidates = []
    for site in four.interior_samples(legal.intersection(ring), at, 12):
        contact = rooted_via(rooted, site, diameter)
        if all(x > 1e-6 for x in contact.values()):
            candidates.append({"at": site, "diameter_mm": diameter, "drill_mm": drill, "distance_mm": math.dist(at, site),
                               "baseline_direct_source_fill_contact_mm2": contact})
    return {"at": at, "existing": existing, "new_stitch_candidates": candidates,
            "planning_return_status": "PROSPECTIVE_SOURCE_CONNECTED_RETURN_SITE" if candidates else "NO_SOURCE_CONNECTED_RETURN_SITE_AT_BOUND"}


def routes(g, opi_areas, diameter, drill):
    start, end = old.END_FRONT, old.END_BACK
    free = {layer: v.free_trace(g, opi_areas, p.OPI, layer) for layer in v.LAYERS}
    starts = {layer: unary_union([part for part in p.hubs.components(geo) if part.covers(Point(start))]) for layer, geo in free.items()}
    ends = {layer: unary_union([part for part in p.hubs.components(geo) if part.covers(Point(end))]) for layer, geo in free.items()}
    found, checks = [], []
    for layer in v.LAYERS:
        route = exact_path(free[layer], start, end)
        checks.append({"strategy": "DIRECT_BETWEEN_RETAINED_VIAS", "layer": layer, **route})
        if route["verdict"] == "HOST_PATH":
            found.append({"segments": [{"layer": layer, **route}], "new_vias": []})
    if found:
        return found, checks
    legal = via_region(g, opi_areas, p.OPI, diameter, drill)
    for la in v.LAYERS:
        for lb in v.LAYERS:
            if la == lb:
                continue
            bridge = legal.intersection(starts[la]).intersection(ends[lb])
            for site in four.interior_samples(bridge, (222.35, 134.25), 6):
                aa, bb = exact_path(free[la], start, site), exact_path(free[lb], site, end)
                if aa["verdict"] == bb["verdict"] == "HOST_PATH":
                    found.append({"segments": [{"layer": la, **aa}, {"layer": lb, **bb}], "new_vias": [site]})
                    break
    if found:
        return found[:4], checks
    for outer in ("F.Cu", "B.Cu"):
        for middle in v.LAYERS:
            if outer == middle:
                continue
            for index, part in enumerate(p.hubs.components(free[middle])):
                aa = four.interior_samples(legal.intersection(starts[outer]).intersection(part), start, 6)
                bb = four.interior_samples(legal.intersection(ends[outer]).intersection(part), end, 6)
                if not aa or not bb:
                    continue
                failures = []
                for va in aa:
                    ra = exact_path(free[outer], start, va)
                    if ra["verdict"] != "HOST_PATH":
                        failures.append({"first": va, "reason": ra})
                        continue
                    for vb in bb:
                        if math.dist(va, vb) < .8:
                            continue
                        rm, rb = exact_path(part, va, vb), exact_path(free[outer], vb, end)
                        if rm["verdict"] == rb["verdict"] == "HOST_PATH":
                            found.append({"segments": [{"layer": outer, **ra}, {"layer": middle, **rm}, {"layer": outer, **rb}], "new_vias": [va, vb]})
                            break
                        failures.append({"first": va, "second": vb, "middle": rm, "last": rb})
                    if found:
                        break
                checks.append({"strategy": "SINGLE_DIVE_RETURN", "layers": [outer, middle, outer], "component_index": index,
                               "first_sites": aa, "second_sites": bb, "failures": failures[:8]})
                if found:
                    return found[:4], checks
    return found, checks


def main():
    original, overlay = p.overlay()
    areas = old.reservations()
    g = copy.deepcopy(original)
    g["tracks"] = [track for track in g["tracks"] if track["uuid"] not in v.OWNED]
    g["vias"] = [via for via in g["vias"] if via["uuid"] not in v.OWNED]
    g = old.move_cap(v.repour_overlay(g, True), 1.)
    g, cap_paths = v.circuits(g, areas, (v.CT, v.GND))
    p.require(g is not None, "Cap circuit paths failed")
    rooted = rooted_ground(g)
    trials = []
    for diameter, drill in ((.6, .3), (.5, .2)):
        for escape in (False, True):
            opi_areas, ledger = four.terminal_escape(areas, original) if escape else (areas, [])
            print("EXACT_ENDPOINT_SCREEN", diameter, drill, escape, flush=True)
            paths, checks = routes(g, opi_areas, diameter, drill)
            proposals = []
            print("EXACT_ENDPOINT_PATHS", len(paths), flush=True)
            for index, route in enumerate(paths[:2]):
                candidate = copy.deepcopy(g)
                for si, segment in enumerate(route["segments"]):
                    candidate = v.append_path(candidate, p.OPI, segment["layer"], segment, f"OPI_EXACT_{diameter}_{index}_{si}")
                for vi, at in enumerate(route["new_vias"]):
                    candidate["vias"].append(via_record(at, p.OPI, diameter, drill, f"PROSPECTIVE_OPI_EXACT_{index}_{vi}", g["copper_layers"]))
                # Changes of joined layer also recheck BOTH retained endpoint vias.
                returns = []
                all_returns_possible = True
                new_stitches = []
                for vi, at in enumerate([old.END_FRONT, old.END_BACK] + route["new_vias"]):
                    row = return_candidates(candidate, areas, at, rooted)
                    if row["planning_return_status"] == "PROSPECTIVE_SOURCE_CONNECTED_RETURN_SITE":
                        site = next((s for s in row["new_stitch_candidates"] if all(math.dist(s["at"], prior["at"]) >= .8 for prior in new_stitches)), None)
                        if site is None:
                            all_returns_possible = False
                        else:
                            new_stitches.append(site)
                            candidate["vias"].append(via_record(site["at"], v.GND, .6, .3, f"PROSPECTIVE_OPI_RETURN_{index}_{vi}", g["copper_layers"]))
                    elif row["planning_return_status"] == "NO_SOURCE_CONNECTED_RETURN_SITE_AT_BOUND":
                        all_returns_possible = False
                    returns.append(row)
                array = v.source_arrays(candidate, areas)
                proposals.append({"OPI_route": route, "signal_via_diameter_mm": diameter, "signal_via_drill_mm": drill,
                    "new_return_stitches": new_stitches, "all_old_and_new_via_return_placement_screens_pass": all_returns_possible,
                    "return_screens": returns, "source_array_after_all_signal_and_return_copper": array,
                    "new_OPI_length_mm": sum(seg["length_mm"] for seg in route["segments"]),
                    "future_native_no_loss_signal_return_and_power_qualification_required": True})
                print("EXACT_COEXISTENCE", array["maximum_sampled_source_component_sites"], all_returns_possible, flush=True)
                if all_returns_possible and array["maximum_sampled_source_component_sites"] >= 8:
                    break
            trials.append({"signal_via_diameter_mm": diameter, "signal_via_drill_mm": drill, "terminal_escape_policy": escape,
                "OPI_only_router_terminal_escape_ledger": ledger, "path_checks": checks, "proposals": proposals})
            if any(row["all_old_and_new_via_return_placement_screens_pass"] and row["source_array_after_all_signal_and_return_copper"]["maximum_sampled_source_component_sites"] >= 8 for row in proposals):
                break
    for path in (Path(__file__), Path(four.__file__), Path(three.__file__), Path(v.__file__), Path(p.__file__), Path(old.__file__),
                 Path(p.base.__file__), Path(p.hubs.__file__), p.OUT / "local-cap-opi-v2.json", p.OUT / "local-cap-opi-v4.json"):
        p.read(path)
    for path, expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "Read input changed")
    result = {"evidence_class": "Source-only exact-endpoint local re-layout and conservative return/source-array coexistence screen",
        "board_sha256": p.C05_SHA, "overlay": overlay, "cap_new_pose": [222, 135.16, 90], "cap_CT_GND_paths": cap_paths,
        "owned_manifest": str(p.OUT / "local-cap-opi-v2.json"), "owned_copper_item_count": len(v.OWNED),
        "trials": trials, "read_set_sha256": p.READS, "earlier_v2_v3_v4_detour_negatives_superseded": True,
        "grid_endpoint_method": "Exact native and via-site endpoint connectors <=.43mm to .1mm A* grid, each line checked inside the same free component",
        "board_candidate_written": False, "native_launched": False, "GPU_jobs": 0, "implemented": False, "qualified_3p6A_100mV": False,
        "limits": ["Only OPI prospective signal vias vary(.6/.3 vs.5/.2); power arrays and proposed ground-return stitches remain.6/.3, .8mm spacing and all domain/hole/margin rules remain exact",
            "Router-only bounded terminal cut applies to OPI view only; CT/GND/power and return-via legality use unchanged reservation geometry",
            "Rooted-return host screen uses direct filled-piece contact to physical J11001.2/J11002.2 ground pads in pinnedr06 nativeIn1/In4; it is conservative and not a fresh candidate return proof",
            "Adding signal/return vias can alter native reference and IO_3V3 necks; fresh source-anchored fill, no-piece-split, bounded zone-loss and return gates are still necessary",
            "No power source neck, complete corridor, barrel-current/spreading/contact network, thermal/transient or100mV delivery is qualified",
            "Failure is limited to owned15-item edit set,1mmcapmove,212–230/127–143window,3layer-segment limit, sampled via/return sites and50knode bound"]}
    path = p.OUT / "local-cap-opi-v5.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(path), "proposals": sum(len(t["proposals"]) for t in trials)}), flush=True)


if __name__ == "__main__":
    main()
