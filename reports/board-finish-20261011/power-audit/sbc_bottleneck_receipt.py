"""Frozen host checks of a bounded C11061 placement lead and corridor blockage.

This writes a proposal receipt only. It does not move a part or produce a board.
"""
import json
import math
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import Point, LineString, shape
from shapely.ops import nearest_points, unary_union

import prepare_sbc_plan as initial
import prepare_sbc_hubs as hubs

HERE = Path(__file__).resolve().parent


def local_obstacles(geometry):
    result = []
    for pad in geometry["pads"]:
        if pad["ref"] == "C11061":
            continue
        for polygon in initial.polygons(pad["layers"].get("B.Cu", [])):
            if polygon.intersects(initial.box(217, 132, 225, 138)):
                result.append((polygon, pad["net"], {"kind": "pad", "ref": pad["ref"], "number": pad["num"], "net": pad["net"]}))
    for track in geometry["tracks"]:
        if track["layer"] == "B.Cu":
            polygon = initial.body(track)
            if polygon.intersects(initial.box(217, 132, 225, 138)):
                result.append((polygon, track["net"], {"kind": "track", "uuid": track["uuid"], "net": track["net"], "width_mm": track["w"]}))
    for via in geometry["vias"]:
        point = Point(via["x"], via["y"])
        if point.intersects(initial.box(217, 132, 225, 138)):
            result.append((point.buffer(via["d"] / 2), via["net"], {"kind": "via", "uuid": via["uuid"], "net": via["net"]}))
    for zone in geometry["zones"]:
        for polygon in initial.polygons(zone["fills"].get("B.Cu", [])):
            result.append((polygon, zone["net"], {"kind": "filled_zone", "uuid": zone["uuid"], "net": zone["net"]}))
    return result


def placement_probe(geometry, sites, dx, dy):
    obstacles = local_obstacles(geometry)
    own = [pad for pad in geometry["pads"] if pad["ref"] == "C11061"]
    findings, minimum = [], math.inf
    for pad in own:
        new = translate(unary_union(initial.polygons(pad["layers"]["B.Cu"])), xoff=dx, yoff=dy)
        for polygon, net, identity in obstacles:
            if net == pad["net"]:
                continue
            clearance = 0.15 if geometry["nets"].get(net) == "DOM_LOGIC" else 0.6
            margin = new.distance(polygon) - clearance
            minimum = min(minimum, margin)
            if margin < 0.05 - 1e-8:
                findings.append({"moved_pad": pad["num"], "obstacle": identity, "clearance_margin_mm": margin})
        for site in sites:
            margin = new.distance(Point(site)) - 0.3 - 0.15
            if margin < 0.05 - 1e-8:
                findings.append({"moved_pad": pad["num"], "obstacle": {"kind": "proposed_source_via", "at": site}, "clearance_margin_mm": margin})
    own_foot = next(foot for foot in geometry["footprints"] if foot["ref"] == "C11061")
    courtyard = translate(unary_union(initial.polygons(own_foot["courtyard"]["B"])), xoff=dx, yoff=dy)
    for footprint in geometry["footprints"]:
        if footprint["ref"] != "C11061" and "B" in footprint["courtyard"]:
            other = unary_union(initial.polygons(footprint["courtyard"]["B"]))
            if courtyard.intersects(other):
                findings.append({"obstacle": {"kind": "B_courtyard", "ref": footprint["ref"]}, "overlap_mm2": courtyard.intersection(other).area})
    return {"delta_mm": [dx, dy], "new_pose": [221 + dx, 135.16 + dy, 90], "side": "B",
            "pad_copper_min_clearance_margin_mm": minimum,
            "verdict": "HOST_PAD_AND_COURTYARD_SCREEN_PASS" if not findings else "HOST_REJECT", "findings": findings}


def corridor_wall(geometry, plan):
    free = hubs.free_copper(geometry, "In3.Cu").buffer(-1.5)
    source_hub = Point(220.2, 132.4)
    source_parts = [part for part in hubs.components(free) if part.contains(source_hub)]
    load_region = shape(plan["load_array_screen"]["via_landing_region"])
    load_parts = [part for part in hubs.components(free) if part.intersects(load_region)]
    if not source_parts or not load_parts:
        return {"verdict": "NO_HOST_WIDE_SOURCE_OR_LOAD_COMPONENT"}
    a, b = min(((a, b) for a in source_parts for b in load_parts), key=lambda pair: pair[0].distance(pair[1]))
    pa, pb = nearest_points(a, b)
    segment = LineString([pa, pb])
    blockers = []
    for track in geometry["tracks"]:
        if track["layer"] == "In3.Cu" and track["net"] != initial.NET:
            gap = 0.15 if geometry["nets"].get(track["net"]) == "DOM_LOGIC" else 0.6
            forbidden = initial.body(track).buffer(gap + 1.5 + 0.05)
            length = segment.intersection(forbidden).length
            if length > 1e-7:
                blockers.append({"kind": "track", "uuid": track["uuid"], "net": track["net"], "domain": geometry["nets"].get(track["net"]),
                                 "width_mm": track["w"], "a": track["a"], "b": track["b"], "blocked_connection_length_mm": length,
                                 "locked": track["locked"]})
    initial.WINDOW = hubs.WINDOW
    reference = initial.layer_reference(geometry, "In1.Cu").intersection(initial.layer_reference(geometry, "In4.Cu")).buffer(-2.1)
    return {"verdict": "DISCONNECTED_3MM_SOURCE_LOAD_FREE_COMPONENTS", "nearest_wide_component_gap_mm": a.distance(b),
            "nearest_boundary_points_mm": [list(pa.coords[0]), list(pb.coords[0])],
            "outside_retained_logic_reference_along_gap_mm": segment.difference(reference).length,
            "track_blockers_across_nearest_gap": sorted(blockers, key=lambda record: -record["blocked_connection_length_mm"]),
            "scope": "Attribution along nearest geometric gap only; removing these tracks is not authorized or sufficient proof of a route"}


def main():
    geometry = json.loads(initial.GEOM.read_text())
    if geometry["sha256"] != initial.BASE_SHA or initial.sha(initial.BASE) != initial.BASE_SHA:
        raise ValueError("current frozen geometry changed")
    attribution_path = HERE / "sbc-local-change-attribution.json"
    attribution = json.loads(attribution_path.read_text())
    c61 = next(probe for probe in attribution["probes"] if probe["ignored_pad_obstacle_ref"] == "C11061")
    component = next(component for component in c61["in3_probe"]["source_component_details"] if len(component["sampled_via_sites"]) >= 8)
    sites = component["sampled_via_sites"][:8]
    proposals = [placement_probe(geometry, sites, dx, dy) for dx, dy in ((0.25, 0), (0.5, 0), (0.75, 0), (1, 0), (1.5, 0), (2, 0), (2.4, 0))]
    original = json.loads((HERE / "sbc-root106-plan.json").read_text())
    report = {"evidence_class": "frozen host source re-layout lead; no board candidate", "base_sha256": initial.BASE_SHA,
              "source_hashes": {str(path): initial.sha(path) for path in (initial.BASE, initial.GEOM, attribution_path, Path(__file__), Path(initial.__file__), Path(hubs.__file__))},
              "source_component": "C11061, B side, pose(221,135.16,90), CT pad1 at(221,136.11), LOGIC_GND pad2 at(221,134.21)",
              "eight_sampled_source_array_sites_if_old_C11061_pad_obstacle_relocated": sites, "placement_proposals": proposals,
              "remaining_corridor": corridor_wall(geometry, original), "native_launched": False, "board_changed": False,
              "required_before_any_candidate": ["Owned reconnect geometry for C11061 CT/GND, exact original-net connectivity and capacitor ramp/return constraints",
                                                "Adequate full-current source/local copper neck, actual 3mm-or-qualified-width route and load array",
                                                "Explicit source/load/trunk/via resistor network at3.6A, no assumed equal sharing, <=100mV plus thermal gate",
                                                "Native refill and all-severity DRC, uncapped pad partitions/no losses, API parity, return/isolation and source-freeze checks"],
              "split_path_status": "OPEN_NO_BOUNDED_NETWORK: disconnected wide components, so no split-branch current-share model or native candidate was forced",
              "qualified_3p6A_100mV": False, "adopted": False}
    (HERE / "sbc-bottleneck-receipt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"proposal_verdicts": [(probe["delta_mm"], probe["verdict"]) for probe in proposals],
                      "wide_corridor_gap_mm": report["remaining_corridor"].get("nearest_wide_component_gap_mm")}))


if __name__ == "__main__":
    main()
