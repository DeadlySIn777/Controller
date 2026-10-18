"""One bounded three-segment OPI dive/return plus hard-blocker attribution.

Only source-only JSON is written. Native copper, project, rules and fills stay intact.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from shapely.prepared import prep

import prepare_sbc_local_v2 as v
import prepare_sbc_local_proposal as old

p = v.p


def endpoint_obstacles(g, areas, net, layer, at):
    point = Point(at)
    rows = []
    domain = g["domains_normalized"].get(p.norm(net))
    def retain(polygon, gap, identity):
        # .2mm track, .025mm planner margin.
        margin = point.distance(polygon) - gap - .1 - p.MARGIN
        if margin < 1e-7:
            rows.append({**identity, "required_copper_gap_mm": gap, "trace_center_clearance_margin_mm": margin})
    def gap(other):
        return .15 if g["domains_normalized"].get(p.norm(other)) == domain else .6
    for pad in g["pads"]:
        if p.norm(pad["net"]) != p.norm(net):
            for poly in p.base.polygons(pad["layers"].get(layer, [])):
                retain(poly, gap(pad["net"]), {"kind": "pad", "uuid": pad["uuid"], "ref": pad["ref"], "number": pad["num"], "net": pad["net"]})
        for poly in p.base.polygons(pad.get("hole") or []):
            retain(poly, .25, {"kind": "pad_hole", "uuid": pad["uuid"], "ref": pad["ref"]})
    for track in g["tracks"]:
        if track["layer"] == layer and p.norm(track["net"]) != p.norm(net):
            retain(p.base.body(track), gap(track["net"]), {"kind": "track", "uuid": track["uuid"], "net": track["net"]})
    for via in g["vias"]:
        if p.norm(via["net"]) != p.norm(net):
            retain(Point(via["x"], via["y"]).buffer(via["d"] / 2), gap(via["net"]), {"kind": "via", "uuid": via["uuid"], "net": via["net"], "at": [via["x"], via["y"]]})
            retain(Point(via["x"], via["y"]).buffer(via["drill"] / 2), .25, {"kind": "via_hole", "uuid": via["uuid"], "net": via["net"]})
    for zone in g["zones"]:
        if p.norm(zone["net"]) != p.norm(net):
            for poly in p.base.polygons(zone["fills"].get(layer, [])):
                retain(poly, gap(zone["net"]), {"kind": "pinned_r06_filled_zone", "uuid": zone["uuid"], "net": zone["net"]})
    for area in areas:
        if layer in area["layers"] and p.norm(net) not in area["exempt"]:
            for poly in p.base.polygons(area["outline"]):
                retain(poly, 0., {"kind": "router_reservation", "name": area["name"]})
    p.base.WINDOW = v.WINDOW
    reference = p.base.layer_reference(g, "In1.Cu").intersection(p.base.layer_reference(g, "In4.Cu")).buffer(-.6)
    if not reference.buffer(-.1).covers(point):
        rows.append({"kind": "outside_retained_effective_LOGIC_GND_reference_planning_territory"})
    return rows


def samples(region, near, maximum=6):
    if region.is_empty:
        return []
    prepared = prep(region)
    points = [(ix / 10, iy / 10) for ix in range(2120, 2301, 2) for iy in range(1270, 1431, 2)
              if prepared.contains(Point(ix / 10, iy / 10))]
    points.sort(key=lambda point: math.dist(point, near))
    return points[:maximum]


def ground_near(g, at):
    return [{"uuid": via["uuid"], "at": [via["x"], via["y"]], "distance_mm": math.dist(at, (via["x"], via["y"])),
             "source_anchored_both_reference_pieces_proved": False}
            for via in g["vias"] if p.norm(via["net"]) == v.GND and math.dist(at, (via["x"], via["y"])) <= 1.0]


def three_segment(g, areas):
    free = {layer: v.free_trace(g, areas, p.OPI, layer) for layer in v.LAYERS}
    start_parts = {layer: unary_union([part for part in p.hubs.components(geo) if part.covers(Point(old.END_FRONT))]) for layer, geo in free.items()}
    end_parts = {layer: unary_union([part for part in p.hubs.components(geo) if part.covers(Point(old.END_BACK))]) for layer, geo in free.items()}
    old.VIA_WINDOW = v.VIA_WINDOW
    legal = old.via_region(g, areas)
    checks, routes = [], []
    for outer in ("F.Cu", "B.Cu"):
        if start_parts[outer].is_empty or end_parts[outer].is_empty:
            checks.append({"outer": outer, "verdict": "RETAINED_ENDPOINT_NOT_IN_FREE_OUTER_COMPONENT"})
            continue
        for middle in v.LAYERS:
            if middle == outer:
                continue
            for index, component in enumerate(p.hubs.components(free[middle])):
                a = legal.intersection(start_parts[outer]).intersection(component)
                b = legal.intersection(end_parts[outer]).intersection(component)
                if a.is_empty or b.is_empty:
                    continue
                aa, bb = samples(a, old.END_FRONT), samples(b, old.END_BACK)
                checks.append({"outer": outer, "middle": middle, "component_index": index, "first_via_area_mm2": a.area,
                               "second_via_area_mm2": b.area, "first_via_sampled_sites": aa, "second_via_sampled_sites": bb})
                for va in aa:
                    ra = v.path_in(free[outer], old.END_FRONT, va)
                    if ra["verdict"] != "HOST_PATH":
                        continue
                    for vb in bb:
                        if math.dist(va, vb) < .8:
                            continue
                        rm, rb = v.path_in(component, va, vb), v.path_in(free[outer], vb, old.END_BACK)
                        if rm["verdict"] != "HOST_PATH" or rb["verdict"] != "HOST_PATH":
                            continue
                        route = {"segments": [{"layer": outer, **ra}, {"layer": middle, **rm}, {"layer": outer, **rb}],
                                 "new_vias": [va, vb], "via_d_mm": .6, "via_drill_mm": .3, "maximum_track_layer_segments": 3,
                                 "existing_GND_vias_in_1mm": [ground_near(g, va), ground_near(g, vb)],
                                 "return_stitch_or_source_anchor_qualified": False}
                        routes.append(route)
                        if len(routes) >= 4:
                            return routes, checks
                        break
                    if routes:
                        break
    return routes, checks


def main():
    original, overlay = p.overlay()
    areas = old.reservations()
    g = copy.deepcopy(original)
    g["tracks"] = [track for track in g["tracks"] if track["uuid"] not in v.OWNED]
    g["vias"] = [via for via in g["vias"] if via["uuid"] not in v.OWNED]
    g = old.move_cap(v.repour_overlay(g, True), 1.0)
    g, circuits = v.circuits(g, areas, (v.CT, v.GND))
    p.require(g is not None, "Previously proved cap paths did not reproduce")
    print("CAP_PATHS_REPRODUCED", flush=True)
    blockers = {layer: endpoint_obstacles(g, areas, p.OPI, layer, old.END_BACK) for layer in v.LAYERS}
    print("ENDPOINT_BLOCKERS_READY", flush=True)
    routes, checks = three_segment(g, areas)
    print("THREE_SEGMENT_PATHS", len(routes), flush=True)
    proposals = []
    for index, route in enumerate(routes):
        with_routes = copy.deepcopy(g)
        for si, segment in enumerate(route["segments"]):
            with_routes = v.append_path(with_routes, p.OPI, segment["layer"], segment, f"OPI_DIVE_{index}_{si}")
        for vi, (x, y) in enumerate(route["new_vias"]):
            with_routes["vias"].append({"uuid": f"PROSPECTIVE_OPI_DIVE_{index}_{vi}", "net": p.OPI, "x": x, "y": y,
                "d": .6, "drill": .3, "flashed": g["copper_layers"], "span": ["F.Cu", "B.Cu"]})
        arrays = v.source_arrays(with_routes, areas)
        proposals.append({"OPI_route": route, "source_array_after_OPI_replacement": arrays})
        print("RETAINED_ARRAY_SITES", arrays["maximum_sampled_source_component_sites"], flush=True)
        if arrays["maximum_sampled_source_component_sites"] >= 8:
            break
    for path in (Path(__file__), Path(v.__file__), Path(p.__file__), Path(old.__file__), Path(p.base.__file__), Path(p.hubs.__file__),
                 p.OUT / "local-cap-opi-v2.json"):
        p.read(path)
    for path, expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "Frozen input changed")
    receipt = {"evidence_class": "Bounded source-only maximum-three-layer-segment single dive-and-return OPI screen",
        "board_sha256": p.C05_SHA, "overlay": overlay, "window_mm": list(v.WINDOW.bounds), "cap_new_pose": [222, 135.16, 90],
        "cap_CT_GND_routes": circuits, "retained_OPI_target_endpoint": old.END_BACK, "endpoint_mask_attribution": blockers,
        "three_segment_checks": checks, "proposals": proposals,
        "verdict": "HOST_LOCAL_DIVE_RETURN_WITH_EIGHT_ARRAY_SITES_RETURN_UNQUALIFIED" if any(
            row["source_array_after_OPI_replacement"]["maximum_sampled_source_component_sites"] >= 8 for row in proposals) else "NO_COMPLETE_THREE_SEGMENT_PROPOSAL_IN_BOUND",
        "read_set_sha256": p.READS, "implemented": False, "qualified_3p6A_100mV": False, "native_launched": False,
        "board_candidate_written": False, "GPU_jobs": 0,
        "limits": ["Eight-source-site screen still excludes original owned OPI1via/10tracks and4cap tracks; every replacement must be represented before any candidate",
            "Two prospective through-vias can carry OPI onto one middle layer and return to the same outer layer, with at most3 track-layer segments; original2 through-via endpoints stay fixed",
            "Existing ground vias within1mm are only placement hints; both reference-piece contact and physical source-anchor connection must be proved, or a legal new.9–1mm return stitch must be added",
            "Repour policy relaxes only F/B same-domain LOGIC_GND stale fills; exact original native polygons are unchanged, and ground continuity/no-loss/return budget remains open",
            "A failed bounded strategy does not establish global routing impossibility; no compound-layer or protected foreign reroute is attempted",
            "No source power neck, explicit complete current-sharing graph, load array, transient/thermal or100mV delivery is qualified"]}
    path = p.OUT / "local-cap-opi-v3.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(path), "verdict": receipt["verdict"]}), flush=True)


if __name__ == "__main__":
    main()
