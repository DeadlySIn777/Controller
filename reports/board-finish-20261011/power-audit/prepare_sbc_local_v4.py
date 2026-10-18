"""Exact interior via sampling and a bounded retained OPI-terminal escape lead."""
import copy
import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Point, LineString, mapping
from shapely.ops import unary_union, polylabel

import prepare_sbc_local_v3 as three

v, p = three.v, three.p
old = v.prior
GRID_SAMPLER = three.samples


def interior_samples(region, near, maximum=6):
    points = []
    # An additional5um beyond v3's25um planner margin avoids a boundary-centre proposal.
    robust = region.buffer(-.005)
    for part in p.hubs.components(robust):
        at = polylabel(part, tolerance=.0025)
        if region.covers(at):
            points.append((at.x, at.y))
        rp = part.representative_point()
        if region.covers(rp):
            points.append((rp.x, rp.y))
    points += GRID_SAMPLER(region, near, maximum)
    points.sort(key=lambda point: math.dist(point, near))
    selected = []
    for point in points:
        if all(math.dist(point, prior) > .05 for prior in selected):
            selected.append(point)
    return selected[:maximum]


def terminal_escape(areas, original):
    # The ledgered exemption is restricted to the last1.0mm of existing owned
    # OPI B copper + its own retained terminal via body, with .025mm margin.
    endpoint = Point(old.END_BACK)
    pieces = []
    for track in original["tracks"]:
        if track["uuid"] in old.B_SEGMENTS:
            pieces.append(p.base.body(track).intersection(endpoint.buffer(1.0)))
    via = next(x for x in original["vias"] if x["uuid"] == "d368cdae-4457-4de7-9524-fcc614837147")
    pieces.append(Point(via["x"], via["y"]).buffer(via["d"] / 2))
    old_copper = unary_union(pieces)
    cut = old_copper.buffer(.15 + .025)
    modified, ledger = [], []
    for area in areas:
        if area["name"] == "RESERVE_KEEPOUT_SBC5V" and "B.Cu" in area["layers"]:
            body = unary_union(p.base.polygons(area["outline"]))
            changed = body.difference(cut)
            modified.append({**area, "outline": p.rings(changed)})
            ledger.append({"name": area["name"], "layer": "B.Cu", "router_only_escape_cut_mm2": body.intersection(cut).area,
                "bounded_terminal_radius_mm": 1.0, "original_owned_copper_envelope": mapping(old_copper),
                "planned_reservation_cut": mapping(cut), "any_native_copper_or_rule_edited": False})
        else:
            modified.append(area)
    return modified, ledger


def return_landing(g, areas, signal_at):
    nearby = three.ground_near(g, signal_at)
    # Existing placement hints alone are not SOURCE-anchored electrical proof.
    # Screen new ground stitches in the ordinary .90–1.00mm window, all layers.
    prior_net, prior_window = old.OPI, old.VIA_WINDOW
    old.OPI, old.VIA_WINDOW = v.GND, v.VIA_WINDOW
    try:
        legal = old.via_region(g, areas)
    finally:
        old.OPI, old.VIA_WINDOW = prior_net, prior_window
    annulus = Point(signal_at).buffer(1.0).difference(Point(signal_at).buffer(.9))
    candidates = interior_samples(legal.intersection(annulus), signal_at, 4)
    return {"signal_via_at": signal_at, "existing_ground_vias_in_1mm": nearby, "new_ground_stitch_sites_0p9_to_1mm": candidates,
            "source_anchored_native_fill_and_return_proved": False}


def direct_relayout(g, areas):
    routes, checks = v.opi_routes(g, areas)
    # Translate v2's possibly-single-via result into the v3 route format.
    return [{"segments": route["segments"], "new_vias": [] if route["new_via_at"] is None else [route["new_via_at"]],
             "via_d_mm": .6, "via_drill_mm": .3, "maximum_track_layer_segments": 2,
             "return_stitch_or_source_anchor_qualified": False} for route in routes], checks


def main():
    original, overlay = p.overlay()
    original_areas = old.reservations()
    g = copy.deepcopy(original)
    g["tracks"] = [track for track in g["tracks"] if track["uuid"] not in v.OWNED]
    g["vias"] = [via for via in g["vias"] if via["uuid"] not in v.OWNED]
    g = old.move_cap(v.repour_overlay(g, True), 1.)
    g, cap_paths = v.circuits(g, original_areas, (v.CT, v.GND))
    p.require(g is not None, "Cap paths failed reproduction")
    # Replace only the in-memory sampler; original frozen source files stay unchanged.
    prior_sampler = three.samples
    three.samples = interior_samples
    trials = []
    try:
        for escape in (False, True):
            areas, ledger = terminal_escape(original_areas, original) if escape else (original_areas, [])
            print("INTERIOR_OPI_PROBE", "terminal_escape", escape, flush=True)
            routes, checks = direct_relayout(g, areas)
            if not routes:
                routes, checks = three.three_segment(g, areas)
            proposals = []
            print("INTERIOR_OPI_PATHS", len(routes), flush=True)
            for index, route in enumerate(routes[:4]):
                candidate = copy.deepcopy(g)
                for si, segment in enumerate(route["segments"]):
                    candidate = v.append_path(candidate, p.OPI, segment["layer"], segment, f"OPI_INTERIOR_{escape}_{index}_{si}")
                for vi, (x, y) in enumerate(route["new_vias"]):
                    candidate["vias"].append({"uuid": f"PROSPECTIVE_OPI_INTERIOR_{index}_{vi}", "net": p.OPI, "x": x, "y": y,
                        "d": .6, "drill": .3, "flashed": g["copper_layers"], "span": ["F.Cu", "B.Cu"]})
                # Return landing hints are screened after all signal copper/vias exist.
                returns = [return_landing(candidate, areas, at) for at in route["new_vias"]]
                array = v.source_arrays(candidate, areas)
                proposals.append({"OPI_route": route, "source_array_after_OPI_replacement": array, "return_landing_screens": returns,
                    "new_OPI_length_mm": sum(segment["length_mm"] for segment in route["segments"]),
                    "native_no_loss_signal_return_and_power_qualification_required": True})
                print("INTERIOR_PROPOSAL_ARRAY", array["maximum_sampled_source_component_sites"], flush=True)
                if array["maximum_sampled_source_component_sites"] >= 8:
                    break
            trials.append({"terminal_escape_policy": escape, "router_only_terminal_escape_ledger": ledger, "path_checks": checks,
                           "proposals": proposals, "verdict": "HOST_COMPLETE_LOCAL_PATHS_ARRAY_AND_RETURN_OPEN" if proposals else "NO_HOST_LOCAL_PATH_AT_THIS_BOUND"})
            if any(row["source_array_after_OPI_replacement"]["maximum_sampled_source_component_sites"] >= 8 for row in proposals):
                break
    finally:
        three.samples = prior_sampler
    for path in (Path(__file__), Path(three.__file__), Path(v.__file__), Path(p.__file__), Path(old.__file__),
                 Path(p.base.__file__), Path(p.hubs.__file__), p.OUT / "local-cap-opi-v2.json", p.OUT / "local-cap-opi-v3.json"):
        p.read(path)
    for path, expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "Frozen input changed")
    receipt = {"evidence_class": "Source-only local C11061+CT/GND+OPI re-layout with exact interior via and bounded terminal policy",
        "board_sha256": p.C05_SHA, "overlay": overlay, "cap_new_pose": [222, 135.16, 90], "cap_CT_GND_paths": cap_paths,
        "owned_item_count": len(v.OWNED), "owned_item_manifest": str(p.OUT / "local-cap-opi-v2.json"),
        "trials": trials, "read_set_sha256": p.READS, "path_grid_mm": .1, "path_node_cap": 50000,
        "extra_interior_sampling_margin_mm": .005, "board_candidate_written": False, "native_launched": False,
        "GPU_jobs": 0, "implemented": False, "qualified_3p6A_100mV": False,
        "limits": ["A router-only bounded escape envelope is carved solely from RESERVE_KEEPOUT_SBC5V within original owned OPI terminal copper(last1mm) plus.175mm; no foreign copper, native rules, domain clearance or reference constraint is relaxed",
            "No actual source board is composed until every replacement, ground-return stitch/source-anchor check and source landing can coexist",
            "Prospective same-domain outer-ground repour requires a bounded actual copper-change ledger and fresh native no-loss/source-anchor/return checks; no ground fill is physically removed",
            "Exact interior sampling supplements a .2mm grid; all sampled centers retain the underlying25um geometry margin plus5um extra interior inset",
            "Power source/load neck, complete supply corridor, explicit barrel currents and100mV delivery remain unqualified regardless of a local8site landing"]}
    path = p.OUT / "local-cap-opi-v4.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(path), "proposals": sum(len(t["proposals"]) for t in trials)}), flush=True)


if __name__ == "__main__":
    main()
