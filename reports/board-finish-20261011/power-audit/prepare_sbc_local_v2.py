"""Bounded owned C11061/CT/GND/OPI prospective re-layout; no board output.

Normal same-domain LOGIC_GND repour on F/B is a separate prospective policy.
All native ground polygons are retained in the receipt and remain unmodified.
"""
import copy
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Point, LineString, box, mapping
from shapely.ops import unary_union
from shapely.prepared import prep

import prepare_sbc_c05_proposal as p
import prepare_sbc_local_proposal as prior
import sbc_bottleneck_receipt as placement

OUT = p.OUT
WINDOW = box(212, 127, 230, 143)
VIA_WINDOW = WINDOW
CT = "/motherboard_power_entry/SBC_RAMP_CT"
GND = "/LOGIC_GND"
CT_ITEMS = {"6655d6b3-3d91-4c02-b098-adc4e4ad633d", "f9b8acc5-950d-4143-a6a3-aa60a25505bf", "fd853274-86ee-4f29-81f4-dfb32648e1a1"}
GND_ITEMS = {"91879e41-087d-4503-bbd4-e17d21ec9e1b"}
OWNED = prior.OWNED_TRACKS | CT_ITEMS | GND_ITEMS | {prior.MOVED_VIA}
CT_ENDPOINTS = ((220.35, 136.049999), (221.15, 136.45))
GND_ENDPOINT = (221.0, 135.159991)
LAYERS = ("F.Cu", "B.Cu", "In2.Cu", "In3.Cu")


def repour_overlay(g, allowed):
    out = copy.deepcopy(g)
    if allowed:
        for zone in out["zones"]:
            if p.norm(zone["net"]) == GND:
                # Source planning only: preserve native zone outlines and In1/In4 fills.
                for layer in ("F.Cu", "B.Cu"):
                    zone["fills"][layer] = []
    return out


def free_trace(g, areas, net, layer, width=.2):
    # Same-net plated endpoints conduct the trace and are not foreign holes.
    h = {**g, "vias": [v for v in g["vias"] if p.norm(v["net"]) != p.norm(net)]}
    return p.free_copper(h, areas, net, layer, window=WINDOW).buffer(-width / 2)


def path_in(free, start, end):
    missing = [list(x) for x in (start, end) if not free.covers(Point(x))]
    if missing:
        return {"verdict": "ENDPOINT_BLOCKED_IN_PLANNING_MASK", "blocked": missing}
    if free.covers(LineString([start, end])):
        return {"verdict": "HOST_PATH", "points": [list(start), list(end)], "length_mm": math.dist(start, end), "searched_nodes": 0}
    for part in p.hubs.components(free):
        if part.covers(Point(start)) and part.covers(Point(end)):
            route, nodes = p.hubs.astar(part, start, end, step=.1, maximum_nodes=50000)
            if route and math.dist(route[0], start) < 1e-7 and math.dist(route[-1], end) < 1e-7:
                return {"verdict": "HOST_PATH", "points": route, "length_mm": LineString(route).length, "searched_nodes": nodes}
            return {"verdict": "NO_PATH_AT_GRID_AND_NODE_CAP", "searched_nodes": nodes}
    return {"verdict": "DISCONNECTED_FREE_COMPONENTS_IN_WINDOW"}


def append_path(g, net, layer, path, label, width=.2):
    out = copy.deepcopy(g)
    for i, (a, b) in enumerate(zip(path["points"], path["points"][1:])):
        out["tracks"].append({"uuid": f"PROSPECTIVE_{label}_{i}", "net": net, "layer": layer, "a": a, "b": b, "w": width, "locked": True})
    return out


def pad_center(g, num):
    pad = next(x for x in g["pads"] if x["ref"] == "C11061" and x["num"] == str(num))
    return (pad["x"], pad["y"])


def circuits(g, areas, order):
    result = {"order": order, "routes": []}
    for net in order:
        endpoints, target = (CT_ENDPOINTS, pad_center(g, 1)) if net == CT else ((GND_ENDPOINT,), pad_center(g, 2))
        # Both retained CT vias must remain connected, including the former leaf.
        for index, endpoint in enumerate(endpoints):
            route = path_in(free_trace(g, areas, net, "B.Cu"), endpoint, target)
            row = {"net": net, "layer": "B.Cu", "width_mm": .2, "retained_endpoint": endpoint, "new_pad_center": target, **route}
            result["routes"].append(row)
            if route["verdict"] != "HOST_PATH":
                result["verdict"] = "CAP_CIRCUIT_PATH_NOT_FOUND_IN_BOUND"
                return None, result
            g = append_path(g, net, "B.Cu", route, f"CAP_{'CT' if net == CT else 'GND'}_{index}")
    result["verdict"] = "HOST_CAP_CT_AND_GND_PATHS"
    return g, result


def opi_routes(g, areas):
    start, end = prior.END_FRONT, prior.END_BACK
    frees = {layer: free_trace(g, areas, p.OPI, layer) for layer in LAYERS}
    report, routes = [], []
    # The two retained through-vias are already valid all-layer endpoints.
    for layer in LAYERS:
        route = path_in(frees[layer], start, end)
        report.append({"strategy": "ONE_LAYER_BETWEEN_RETAINED_THROUGH_VIAS", "layer": layer, **route})
        if route["verdict"] == "HOST_PATH":
            routes.append({"segments": [{"layer": layer, **route}], "new_via_at": None,
                           "additional_through_vias": 0, "retained_endpoints": [start, end]})
    if routes:
        return routes, report
    # One relocated owned through-via; at most two new track-layer segments.
    prior.VIA_WINDOW = VIA_WINDOW
    legal = prior.via_region(g, areas)
    report.append({"strategy": "ONE_OWNED_RELOCATED_VIA", "legal_all_layer_landing_area_mm2": legal.area})
    start_parts = {layer: unary_union([x for x in p.hubs.components(free) if x.covers(Point(start))]) for layer, free in frees.items()}
    end_parts = {layer: unary_union([x for x in p.hubs.components(free) if x.covers(Point(end))]) for layer, free in frees.items()}
    for la, sa in start_parts.items():
        for lb, eb in end_parts.items():
            if la == lb or sa.is_empty or eb.is_empty:
                continue
            bridge = legal.intersection(sa).intersection(eb)
            if bridge.is_empty:
                continue
            pp = prep(bridge)
            sites = [(ix / 10, iy / 10) for ix in range(2120, 2301, 2) for iy in range(1270, 1431, 2) if pp.contains(Point(ix / 10, iy / 10))]
            sites.sort(key=lambda point: math.dist(point, (222.35, 134.25)))
            report.append({"strategy": "ONE_OWNED_RELOCATED_VIA", "layers": [la, lb], "sampled_sites": sites[:12], "total_grid_sites": len(sites)})
            for site in sites[:12]:
                ra, rb = path_in(frees[la], start, site), path_in(frees[lb], site, end)
                if ra["verdict"] == rb["verdict"] == "HOST_PATH":
                    routes.append({"segments": [{"layer": la, **ra}, {"layer": lb, **rb}], "new_via_at": site,
                                   "additional_through_vias": 1, "retained_endpoints": [start, end]})
                    break
    return routes, report


def source_arrays(g, areas):
    landing = p.landing(g, areas, "U11012", p.SOURCE_WINDOW)
    branch = p.free_copper(g, areas, p.NET, "In3.Cu").buffer(-.4)
    rows = []
    for component in p.hubs.components(branch):
        if component.intersects(landing):
            sites = p.hubs.pack_region(component.intersection(landing), (221.126875, 138.968594))
            if sites:
                rows.append({"sampled_via_sites": sites, "site_count": len(sites)})
    rows.sort(key=lambda row: -row["site_count"])
    return {"maximum_sampled_source_component_sites": max([r["site_count"] for r in rows], default=0), "arrays": rows,
            "source_neck_or_current_sharing_qualified": False}


def restore_opi(g, route):
    for i, seg in enumerate(route["segments"]):
        g = append_path(g, p.OPI, seg["layer"], seg, f"OPI_{i}")
    if route["new_via_at"] is not None:
        x, y = route["new_via_at"]
        g["vias"].append({"uuid": "PROSPECTIVE_RELOCATED_OPI_054db295", "net": p.OPI, "x": x, "y": y, "d": .6,
                           "drill": .3, "flashed": g["copper_layers"], "span": ["F.Cu", "B.Cu"]})
    return g


def probe(g, areas, dx, repour):
    h = copy.deepcopy(g)
    h["tracks"] = [t for t in h["tracks"] if t["uuid"] not in OWNED]
    h["vias"] = [v for v in h["vias"] if v["uuid"] not in OWNED]
    h = repour_overlay(h, repour)
    place = placement.placement_probe(h, [], dx, 0)
    result = {"dx_mm": dx, "new_cap_pose": [221 + dx, 135.16, 90], "outer_LOGIC_GND_repour_prospective": repour,
              "placement": place, "cap_routes": [], "OPI_path_checks": [], "feasible_local_proposals": []}
    if place["verdict"] != "HOST_PAD_AND_COURTYARD_SCREEN_PASS":
        result["verdict"] = "REJECT_CAP_PAD_OR_COURTYARD_PLACEMENT"
        return result
    h = prior.move_cap(h, dx)
    result["source_array_before_owned_reroutes"] = source_arrays(h, areas)
    for order in ((CT, GND), (GND, CT)):
        circuit_g, circuit_report = circuits(copy.deepcopy(h), areas, order)
        result["cap_routes"].append(circuit_report)
        if circuit_g is None:
            continue
        opi, checks = opi_routes(circuit_g, areas)
        result["OPI_path_checks"].append({"cap_route_order": order, "checks": checks})
        for route in opi[:4]:
            arrays = source_arrays(restore_opi(copy.deepcopy(circuit_g), route), areas)
            result["feasible_local_proposals"].append({"cap_route_order": order, "cap_circuit_routes": circuit_report["routes"],
                "OPI_route": route, "source_array": arrays, "new_CT_plus_GND_route_length_mm": sum(r["length_mm"] for r in circuit_report["routes"]),
                "new_OPI_route_length_mm": sum(r["length_mm"] for r in route["segments"]),
                "signal_return_and_ramp_circuit_requalification_required": True})
        if any(row["source_array"]["maximum_sampled_source_component_sites"] >= 8 for row in result["feasible_local_proposals"]):
            break
    result["verdict"] = "HOST_OWNED_LOCAL_RELAYOUT_WITH_EIGHT_SOURCE_SITES" if any(
        row["source_array"]["maximum_sampled_source_component_sites"] >= 8 for row in result["feasible_local_proposals"]) else "NO_COMPLETE_PROPOSAL_IN_BOUNDED_EDIT_SET_AND_SEARCH"
    return result


def main():
    g, overlay = p.overlay()
    areas = prior.reservations()
    native = p.base.inventory(p.read(p.C05))[3]
    for uid in OWNED:
        p.require(uid in native, "Owned item absent")
        expected = CT if uid in CT_ITEMS else GND if uid in GND_ITEMS else p.OPI
        p.require(p.norm(p.netname(native[uid])) == p.norm(expected), "Owned foreign copper")
    cap_uid = next(uid for uid, chunk in native.items() if p.base.pcbtext.chunk_kind(chunk) == "footprint" and p.base.ref_of(chunk) == "C11061")
    tests = []
    for repour in (False, True):
        for dx in (1., 1.5, 2., 2.4):
            print("EXTENDED_LOCAL_PROBE", dx, "outer_ground_repour", repour, flush=True)
            row = probe(g, areas, dx, repour)
            tests.append(row)
            print(row["verdict"], len(row["feasible_local_proposals"]), flush=True)
    for path in (Path(__file__), Path(p.__file__), Path(prior.__file__), Path(placement.__file__), Path(p.base.__file__), Path(p.hubs.__file__),
                 p.EXT / "tools/verify/rail_model.json", Path("Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md")):
        p.read(path)
    for path, expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "Frozen input changed")
    receipt = {"evidence_class": "Source-only prospective owned re-layout and explicit same-domain outer-ground repour screen",
        "board_sha256": p.C05_SHA, "window_mm": list(WINDOW.bounds), "path_grid_mm": .1, "path_node_cap": 50000,
        "via_grid_mm": .2, "maximum_via_sites_per_layer_pair": 12, "cap_side": "B", "cap_original_pose": [221, 135.16, 90],
        "cap_uuid": cap_uid, "cap_original_chunk_sha256": hashlib.sha256(native[cap_uid]).hexdigest(),
        "owned_items": [{"uuid": uid, "kind": p.base.pcbtext.chunk_kind(native[uid]), "net": p.netname(native[uid]),
                         "chunk_sha256": hashlib.sha256(native[uid]).hexdigest(), "exact_original_chunk": native[uid].decode()} for uid in sorted(OWNED)],
        "retained_CT_endpoints_mm": CT_ENDPOINTS, "retained_GND_endpoint_mm": GND_ENDPOINT,
        "retained_OPI_endpoints_mm": [prior.END_FRONT, prior.END_BACK], "overlay": overlay, "probes": tests,
        "resistance_model": p.resistance_bounds(), "read_set_sha256": p.READS, "board_candidate_written": False,
        "native_launched": False, "GPU_jobs": 0, "implemented": False, "qualified_3p6A_100mV": False,
        "limits": ["Every changed source item is confined to one cap pose and explicitly hashed CT/GND/OPI owned copper; no source pins, current or load are changed",
            "The cap moves preserve side/orientation/local pad definitions/capacitance/nets; native part-placement/circuit/ramp qualification remains necessary",
            "Same-domain outer LOGIC_GND repour is only a prospective geometric policy; no native fill was removed and no ground continuity/return budget is proved",
            "In1/In4 effective LOGIC_GND reference territories remain protected; no alternate domain fill, CORE region, barrier or reservation exemption is invented",
            "Host paths retain .2mm original CT/GND/OPI width and .6/.3mm via if relocated, with .15mm same-domain/.6mm foreign-domain clearance plus .025mm margin",
            "A sampled eight-site array is a landing lead only; full-current source-neck, barrel current sharing, copper spreading, load fanout, complete supply and return paths remain unqualified",
            "No-path means no complete proposal in this edit set/window/grid/node cap; it does not establish global layout impossibility",
            "Any later source candidate requires exact hash freeze, all-pad no-loss guard, native refill/DRC, parity, signal return/EMI and power network/transient/thermal verification"]}
    path = OUT / "local-cap-opi-v2.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(path), "results": [(r["dx_mm"], r["outer_LOGIC_GND_repour_prospective"], r["verdict"]) for r in tests]}), flush=True)


if __name__ == "__main__":
    main()
