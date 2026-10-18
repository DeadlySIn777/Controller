"""Bounded C11061 + owned OPI local re-layout proposal; never writes a board."""
import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import Point, LineString, box, mapping
from shapely.ops import unary_union
from shapely.prepared import prep

import prepare_sbc_c05_proposal as plan
import sbc_bottleneck_receipt as old_probe

HERE, OUT = plan.HERE, plan.OUT
NET, OPI = plan.NET, plan.OPI
WINDOW = box(216, 129, 226, 140)
VIA_WINDOW = box(219, 132, 224, 136)
MOVED_VIA = "054db295-0fcb-472e-beae-856f00d3a7c4"
FRONT_SEG = "a29ec912-eff2-4ab0-a505-52e9bcdca4ff"
B_SEGMENTS = {"1d835a44-4400-49ec-ab94-b07c57f045c5", "28e77d37-22d5-43e0-9036-25927b6219c7",
    "4e729c10-ed60-44cd-ad73-d12fdb8facf2", "71121595-8d78-463d-851c-f6f04bef8d92", "9ff4d036-0254-4c72-a6d7-354990e641bd",
    "a0034028-3ef1-46a7-b3d9-aee11765039e", "be3759ca-e239-4d9d-862e-b0f9e855cd43", "d8efc70d-ddeb-4131-ad51-8f50a1e7b4cc",
    "e1015071-a5dd-4799-afc2-a3068f2e636c"}
OWNED_TRACKS = B_SEGMENTS | {FRONT_SEG}
END_FRONT, END_BACK = (218.35, 130.25), (222.65, 137.85)


def reservations():
    reserved_path = OUT / "reserved-c05.json"
    dru_path = OUT / "reserve/board.kicad_dru"
    reserved = json.loads(plan.read(reserved_path))
    import re
    ex = {}
    for line in plan.read(dru_path).decode().splitlines():
        match = re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)', line.strip())
        if match:
            ex[match.group(1)] = {plan.norm(net) for net in re.findall(r"A\.NetName != '([^']*)'", match.group(2))}
    return [{**area, "exempt": ex.get(area["name"], set())} for area in reserved["keepouts"]]


def move_cap(g, dx):
    g = copy.deepcopy(g)
    for pad in g["pads"]:
        if pad["ref"] == "C11061":
            pad["x"] += dx
            pad["layers"] = {layer: plan.rings(translate(unary_union(plan.base.polygons(records)), xoff=dx)) for layer, records in pad["layers"].items()}
    for foot in g["footprints"]:
        if foot["ref"] == "C11061":
            foot["x"] += dx
            foot["courtyard"] = {side: plan.rings(translate(unary_union(plan.base.polygons(records)), xoff=dx)) for side, records in foot["courtyard"].items()}
    return g


def cap_connectivity(g):
    results = []
    for pad in g["pads"]:
        if pad["ref"] != "C11061":
            continue
        copper = unary_union(plan.base.polygons(pad["layers"].get("B.Cu", [])))
        contacts = []
        for track in g["tracks"]:
            if track["layer"] == "B.Cu" and plan.norm(track["net"]) == plan.norm(pad["net"]):
                overlap = copper.intersection(plan.base.body(track)).area
                if overlap > 1e-6:
                    contacts.append({"kind": "track", "uuid": track["uuid"], "overlap_mm2": overlap})
        for zone in g["zones"]:
            if plan.norm(zone["net"]) == plan.norm(pad["net"]):
                overlap = copper.intersection(unary_union(plan.base.polygons(zone["fills"].get("B.Cu", [])))).area
                if overlap > 1e-6:
                    contacts.append({"kind": "native_refilled_r06_same_net_fill", "uuid": zone["uuid"], "overlap_mm2": overlap})
        results.append({"pad_uuid": pad["uuid"], "pad_number": pad["num"], "net": pad["net"], "contacts": contacts,
                        "host_retained_copper_contact": bool(contacts)})
    return results


def via_region(g, areas):
    obstacles = []
    def retain(polygon, gap):
        if polygon.intersects(VIA_WINDOW.buffer(2)):
            obstacles.append(polygon.buffer(gap + .3 + plan.MARGIN))
    def gap(net):
        return .15 if g["domains_normalized"].get(plan.norm(net)) == "DOM_LOGIC" else .6
    for pad in g["pads"]:
        for records in pad["layers"].values():
            for polygon in plan.base.polygons(records):
                if plan.norm(pad["net"]) != plan.norm(OPI):
                    retain(polygon, gap(pad["net"]))
                if pad["smd"]:
                    retain(polygon, .1)
        for polygon in plan.base.polygons(pad.get("hole") or []):
            obstacles.append(polygon.buffer(.15 + .25 + plan.MARGIN))
    for track in g["tracks"]:
        if plan.norm(track["net"]) != plan.norm(OPI):
            retain(plan.base.body(track), gap(track["net"]))
    for via in g["vias"]:
        if plan.norm(via["net"]) != plan.norm(OPI):
            retain(Point(via["x"], via["y"]).buffer(via["d"] / 2), gap(via["net"]))
        obstacles.append(Point(via["x"], via["y"]).buffer(via["drill"] / 2 + .15 + .25 + plan.MARGIN))
    for zone in g["zones"]:
        # Same-domain reference antipads are ordinary via geometry; foreign-domain fill cannot be pierced.
        if g["domains_normalized"].get(plan.norm(zone["net"])) != "DOM_LOGIC":
            for records in zone["fills"].values():
                for polygon in plan.base.polygons(records):
                    retain(polygon, .6)
    for layer in g["copper_layers"]:
        for polygon in plan.hard_shapes(g, areas, OPI, layer, for_via=True):
            obstacles.append(polygon.buffer(.3 + plan.MARGIN))
    plan.base.WINDOW = VIA_WINDOW
    reference = plan.base.layer_reference(g, "In1.Cu").intersection(plan.base.layer_reference(g, "In4.Cu")).buffer(-.6 - .3)
    return VIA_WINDOW.intersection(reference).difference(unary_union([polygon for polygon in obstacles if polygon.intersects(VIA_WINDOW.buffer(2))]))


def local_path(free, start, goal):
    if not free.covers(Point(start)) or not free.covers(Point(goal)):
        return {"verdict": "ENDPOINT_BLOCKED", "blocked": [point for point in (start, goal) if not free.covers(Point(point))]}
    for component in plan.hubs.components(free):
        if component.covers(Point(start)) and component.covers(Point(goal)):
            path, nodes = plan.hubs.astar(component, start, goal, step=.1, maximum_nodes=45000)
            if path and math.dist(path[0], start) < 1e-7 and math.dist(path[-1], goal) < 1e-7:
                return {"verdict": "HOST_PATH", "points": path, "length_mm": LineString(path).length, "searched_nodes": nodes}
    return {"verdict": "NO_PATH_IN_LOCAL_WINDOW", "window_mm": list(WINDOW.bounds), "step_mm": .1, "node_cap": 45000}


def probe(g, areas, dx):
    omitted = copy.deepcopy(g)
    omitted["tracks"] = [track for track in omitted["tracks"] if track["uuid"] not in OWNED_TRACKS]
    omitted["vias"] = [via for via in omitted["vias"] if via["uuid"] != MOVED_VIA]
    # Before any route: test the physical moved cap against every retained neighbor/courtyard.
    placement = old_probe.placement_probe(omitted, [], dx, 0)
    moved = move_cap(omitted, dx)
    contacts = cap_connectivity(moved)
    result = {"delta_mm": [dx, 0], "new_cap_pose": [221 + dx, 135.16, 90], "placement": placement,
              "retained_CT_GND_contacts": contacts, "moving_only_owned_OPI_via_and_ten_tracks": True,
              "paths": [], "board_candidate_written": False}
    if placement["verdict"] != "HOST_PAD_AND_COURTYARD_SCREEN_PASS" or not all(row["host_retained_copper_contact"] for row in contacts):
        result["verdict"] = "REJECT_CAP_PLACEMENT_OR_RETAINED_CIRCUIT_CONTACT"
        return result
    legal = via_region(moved, areas)
    result["all_layer_OPI_via_landing_area_mm2"] = legal.area
    via_sites = []
    prepared = prep(legal)
    for ix in range(2190, 2241, 2):
        for iy in range(1320, 1361, 2):
            point = (ix / 10, iy / 10)
            if prepared.contains(Point(point)):
                via_sites.append(point)
    via_sites.sort(key=lambda point: math.dist(point, (222.35, 134.25)))
    result["sampled_via_sites"] = len(via_sites)
    # Own via barrels are valid trace landing endpoints; retained foreign holes stay obstacles.
    trace_g = {**moved, "vias": [via for via in moved["vias"] if plan.norm(via["net"]) != plan.norm(OPI)]}
    front_free = plan.free_copper(trace_g, areas, OPI, "F.Cu", window=WINDOW).buffer(-.1)
    back_free = plan.free_copper(trace_g, areas, OPI, "B.Cu", window=WINDOW).buffer(-.1)
    failures = Counter()
    for site in via_sites[:80]:
        front, back = local_path(front_free, END_FRONT, site), local_path(back_free, site, END_BACK)
        if front["verdict"] != "HOST_PATH" or back["verdict"] != "HOST_PATH":
            failures[front["verdict"] + "/" + back["verdict"]] += 1
            continue
        with_via = copy.deepcopy(moved)
        with_via["vias"].append({"uuid": "PROSPECTIVE_OPI_RELOCATED_054db295", "net": OPI, "x": site[0], "y": site[1],
            "d": .6, "drill": .3, "flashed": moved["copper_layers"], "span": ["F.Cu", "B.Cu"]})
        for layer, route in (("F.Cu", front), ("B.Cu", back)):
            for index, (a, b) in enumerate(zip(route["points"], route["points"][1:])):
                with_via["tracks"].append({"uuid": f"PROSPECTIVE_OPI_{layer}_{index}", "net": OPI, "layer": layer, "a": a, "b": b, "w": .2, "locked": True})
        source_landing = plan.landing(with_via, areas, "U11012", plan.SOURCE_WINDOW)
        in3 = plan.free_copper(with_via, areas, NET, "In3.Cu").buffer(-.4)
        arrays = [plan.hubs.pack_region(component.intersection(source_landing), (221.126875, 138.968594))
                  for component in plan.hubs.components(in3) if component.intersects(source_landing)]
        maximum = max([len(sites) for sites in arrays], default=0)
        result["paths"].append({"new_OPI_via_at": site, "retained_signal_endpoints": [END_FRONT, END_BACK],
            "front": front, "back": back, "signal_width_mm": .2, "new_via_d_mm": .6, "new_via_drill_mm": .3,
            "source_In3_branch_component_max_sampled_via_sites": maximum,
            "source_eight_via_array_if_present": next((sites[:8] for sites in arrays if len(sites) >= 8), []),
            "requires_fresh_native_and_signal_return_checks": True})
        if maximum >= 8:
            break
    result["via_path_failures"] = dict(failures)
    result["maximum_tested_via_sites"] = 80
    result["verdict"] = "SOURCE_ONLY_LOCAL_RELAYOUT_AND_EIGHT_SITE_LANDING_PROPOSAL" if any(
        route["source_In3_branch_component_max_sampled_via_sites"] >= 8 for route in result["paths"]) else "NO_BOUNDED_LOCAL_RELAYOUT_WITH_EIGHT_SITE_SOURCE_LANDING"
    return result


def main():
    g, overlay = plan.overlay()
    areas = reservations()
    native = plan.base.inventory(plan.read(plan.C05))[3]
    removed = OWNED_TRACKS | {MOVED_VIA}
    for uid in removed:
        plan.require(uid in native and plan.norm(plan.netname(native[uid])) == plan.norm(OPI), "Local owned item missing/foreign")
    cap_uid = next(uid for uid, chunk in native.items() if plan.base.pcbtext.chunk_kind(chunk) == "footprint" and plan.base.ref_of(chunk) == "C11061")
    source_items = [{"uuid": uid, "kind": plan.base.pcbtext.chunk_kind(native[uid]), "net": plan.netname(native[uid]),
                    "chunk_sha256": hashlib.sha256(native[uid]).hexdigest(), "exact_original_chunk": native[uid].decode()}
                   for uid in sorted(removed)]
    results = []
    for dx in (.5, .75, 1.0):
        print("LOCAL_CAP_OPI_PROBE", dx, flush=True)
        result = probe(g, areas, dx)
        results.append(result)
        print(result["verdict"], len(result["paths"]), flush=True)
    for path in (Path(__file__), Path(plan.__file__), Path(old_probe.__file__), Path(plan.base.__file__), Path(plan.hubs.__file__)):
        plan.read(path)
    for path, expected in plan.READS.items():
        plan.require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "Frozen local proposal read changed")
    report = {"evidence_class": "Bounded frozen-source local compute power lead; no board candidate", "board_sha256": plan.C05_SHA,
        "current_load_case_a": 3.6, "drop_budget_mv": 100, "overlay": overlay,
        "cap": {"reference": "C11061", "uuid": cap_uid, "old_pose": [221, 135.16, 90], "side": "B",
            "chunk_sha256": hashlib.sha256(native[cap_uid]).hexdigest(), "pads_value_nets_orientation_preserved": True},
        "old_owned_signal_items_proposed_for_replacement": source_items,
        "retained_signal_via_endpoints": [{"uuid": "d0bcba36-b7c1-476d-88c3-0b3ec55dce27", "at": END_FRONT},
            {"uuid": "d368cdae-4457-4de7-9524-fcc614837147", "at": END_BACK}],
        "placement_probes": results, "read_set_sha256": plan.READS,
        "native_launched": False, "gpu_jobs": 0, "board_changed": False, "source_pins_or_loads_changed": False,
        "qualified_3p6A_100mV": False, "implemented": False,
        "limits": ["One source-only proposal: C11061 translation plus ten owned OPI tracks and one owned through-via; all unrelated source items remain outside the edit set",
            "No proposed KiCad UUID is minted; prospective geometry labels are diagnostic and are not native board evidence",
            "CT/GND contact is a retained-copper overlap screen, not native connectivity/fault/ramp qualification",
            "Via legality preserves foreign-domain fills and every-layer pad/track/hole/barrier/reservation constraints; same-domain reference antipads remain prospective and need native/SI review",
            "OPI path search keeps every retained foreign filled copper, uses0.1mm grid and45000node cap; failure is bounded rather than global routing impossibility",
            "Even a local8site landing does not qualify source neck/current sharing, full supply corridor, load array, return, transient or100mV delivery"]}
    out = OUT / "local-cap-opi-proposal.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "verdicts": [row["verdict"] for row in results]}), flush=True)


if __name__ == "__main__":
    main()
