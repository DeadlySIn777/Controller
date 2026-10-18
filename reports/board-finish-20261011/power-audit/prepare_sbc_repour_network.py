"""Bounded split-supply screen permitting prospective outer LOGIC_GND repour.

This changes only a host obstacle model. No copper or native candidate is edited.
"""
import hashlib
import json
from pathlib import Path

from shapely.geometry import mapping
from shapely.ops import unary_union

import prepare_sbc_local_v2 as v

p = v.p


def main():
    original, overlay = p.overlay()
    areas = v.prior.reservations()
    g = v.repour_overlay(original, True)
    source = p.landing(g, areas, "U11012", p.SOURCE_WINDOW)
    load = p.landing(g, areas, "J15001", p.LOAD_WINDOW)
    print("PROSPECTIVE_GROUND_REPOUR_LANDINGS_READY", flush=True)
    rows = []
    for layer in ("F.Cu", "B.Cu"):
        for width in (1.5, 2.0):
            print("OUTER_SPLIT_WIDTH_SCREEN", layer, width, flush=True)
            row = p.layer_screen(g, areas, layer, width, source, load)
            rows.append(row)
            print(row["verdict"], row["source_branch_component_site_counts"], row["four_site_array_trunk_pairs"], flush=True)
    # Each candidate would clear only its explicitly ledgered trace/pour mask.
    # These areas are diagnostic estimates, not a grant to cut the whole GND pour.
    affected = []
    for zone in original["zones"]:
        if p.norm(zone["net"]) != v.GND:
            continue
        for layer in ("F.Cu", "B.Cu"):
            pieces = p.base.polygons(zone["fills"].get(layer, []))
            local = unary_union(pieces).intersection(p.WINDOW)
            if local.area > 1e-8:
                affected.append({"zone_uuid": zone["uuid"], "layer": layer, "native_fill_area_in_search_window_mm2": local.area})
    for path in (Path(__file__), Path(v.__file__), Path(p.__file__), Path(v.prior.__file__), Path(p.base.__file__), Path(p.hubs.__file__),
                 p.OUT / "split-network-screen.json", Path("Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md")):
        p.read(path)
    for path, expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "Read input changed")
    result = {"evidence_class": "Bounded source-only split-network geometry with prospective outer same-domain ground repour",
        "board_sha256": p.C05_SHA, "overlay": overlay, "constant_width_screens": rows,
        "source_landing_region": mapping(source), "load_landing_region": mapping(load),
        "current_sharing_model": p.resistance_bounds(), "native_outer_ground_fill_in_scope": affected,
        "read_set_sha256": p.READS, "actual_ground_cut_ledger": [], "ground_connectivity_loss_budget_proved": False,
        "native_launched": False, "GPU_jobs": 0, "board_candidate_written": False, "implemented": False,
        "qualified_3p6A_100mV": False,
        "verdict": "HOST_PATHS_REQUIRE_DISTINCT_ARRAY_FANOUT_NETWORK_AND_GROUND_GATES" if any(row["candidate_paths"] for row in rows)
                   else "NO_BOUNDED_OUTER_CONSTANT_WIDTH_SPLIT_WITH_PROSPECTIVE_GROUND_REPOUR",
        "limits": ["Only F/B LOGIC_GND is excluded from this prospective obstacle mask; every physical pad/track/hole, foreign-domain fill, critical router reservation, CORE region and isolation barrier stays protected",
            "In1/In4 references are never relaxed or routed; same-domain outer-ground repour still requires native source-anchored connectivity, no-piece-split and return validation",
            "No ground copper is removed from a file; a viable candidate must ledger only actual copper-clearance cut polygons and prove zero unintended ground losses",
            "Same .15/.6mm domain gaps plus .025mm planner margin and .8mm array spacing as strict split screen",
            "Both branches must have an explicit connected resistor graph including source/load fanout/neck spreading and all barrel currents; equal sharing is not assumed",
            "The .5A-per-via screen and3.6A/100mV operator load are preserved; single branch/full-current thermal sizing must be checked separately",
            "No-path is limited to107–229/128–176mm, F/B constant1.5/2mm trunks, sampled>=4site arrays and current reservations; intermediate-layer transitions/placement changes remain unsearched"]}
    path = p.OUT / "outer-ground-repour-network-screen.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(path), "verdict": result["verdict"]}), flush=True)


if __name__ == "__main__":
    main()
