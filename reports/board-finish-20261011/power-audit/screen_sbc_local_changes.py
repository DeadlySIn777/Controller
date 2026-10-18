"""Host counterfactual attribution for SBC source-array blockers.

No part is moved and no copper is removed in a board. Each counterfactual only
ignores one footprint's existing pad obstacles, while keeping ALL existing
tracks, vias, zones and graphics. It identifies a re-layout lead, not a recipe.
"""
import json
from pathlib import Path
import prepare_sbc_plan as initial
import prepare_sbc_hubs as hubs

HERE = Path(__file__).resolve().parent


def main():
    geometry = json.loads(initial.GEOM.read_text())
    if initial.sha(initial.BASE) != initial.BASE_SHA or geometry["sha256"] != initial.BASE_SHA or geometry["refilled"] is not True or geometry["api_errors"]:
        raise ValueError("pinned current geometry changed")
    original = json.loads((HERE / "sbc-root106-plan.json").read_text())
    results = []
    for ref in ("C11061", "C11062", "C11063"):
        print("PAD_OBSTACLE_ATTRIBUTION", ref, flush=True)
        probe = {**geometry, "pads": [pad for pad in geometry["pads"] if pad["ref"] != ref]}
        plan = {**original, "source_array_screen": initial.source_screen(probe)}
        layer = hubs.screen_layer(probe, plan, "In3.Cu")
        source_footprint = next(footprint for footprint in geometry["footprints"] if footprint["ref"] == ref)
        pads = [{"number": pad["num"], "net": pad["net"], "x": pad["x"], "y": pad["y"],
                 "copper_bbox_mm": {name: initial.unary_union(initial.polygons(records)).bounds for name, records in pad["layers"].items()}}
                for pad in geometry["pads"] if pad["ref"] == ref]
        results.append({"ignored_pad_obstacle_ref": ref, "source_footprint": source_footprint, "native_pad_obstacles": pads,
                        "front_connected_via_landing_area_mm2": plan["source_array_screen"]["front_source_reachable_via_area_mm2"],
                        "in3_probe": layer, "no_new_location_checked": True, "no_incident_copper_removed": True})
        print(ref, layer["verdict"], layer["all_source_component_site_counts"], flush=True)
    report = {"base_sha256": initial.BASE_SHA,
              "source_hashes": {str(path): initial.sha(path) for path in (initial.BASE, initial.GEOM, Path(__file__), Path(hubs.__file__), Path(initial.__file__))},
              "evidence_class": "source-frozen host obstacle attribution only", "probes": results,
              "native_launched": False, "board_changed": False, "current_qualification": "OPEN",
              "limits": ["Ignoring old pad geometry is not a completed relocation; new pad/courtyard/copper clearance and owned reconnect geometry require fresh verification",
                         "All existing copper is retained, so a pad-removal counterfactual may understate gains requiring a bounded owned-stub re-layout",
                         "3.6 A current sharing, local necks, actual IR and thermal/fault/transient/return gates remain open"]}
    (HERE / "sbc-local-change-attribution.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
