"""Bounded C11062/C11063 source-only placement leads; no board or native job."""
import copy
import hashlib
import json
import math
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import Point, LineString, mapping, box
from shapely.ops import unary_union

import prepare_sbc_local_v6 as six

p, v, five = six.p, six.v, six.five
WINDOW = box(214, 133, 225, 145)
SOUTH = box(216, 139.45, 224, 145)
GND_STUB = "8fc2ac62-7601-4819-9b26-5f0e89f4b316"
CORE_STUB = "3135e75c-692d-40b1-a464-85b68a8f54ba"
CORE = "/mc_local_power/CORE_5V"
GROUND_END = (221.832566, 137.28045)


def records(poly):
    parts = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
    return [[list(x.exterior.coords), [list(h.coords) for h in x.interiors]] for x in parts]


def moved(g, changes):
    h = dict(g)
    h["pads"] = [copy.deepcopy(pad) if pad["ref"] in changes else pad for pad in g["pads"]]
    h["footprints"] = [copy.deepcopy(foot) if foot["ref"] in changes else foot for foot in g["footprints"]]
    for pad in h["pads"]:
        if pad["ref"] in changes:
            dx, dy = changes[pad["ref"]]
            pad["x"] += dx
            pad["y"] += dy
            for layer, outlines in pad["layers"].items():
                pad["layers"][layer] = records(translate(unary_union(p.base.polygons(outlines)), dx, dy))
    for foot in h["footprints"]:
        if foot["ref"] in changes:
            dx, dy = changes[foot["ref"]]
            for side, outlines in foot["courtyard"].items():
                foot["courtyard"][side] = records(translate(unary_union(p.base.polygons(outlines)), dx, dy))
    return h


def placement(g, h, changes):
    findings = []
    own = set(changes)
    for pad in h["pads"]:
        if pad["ref"] not in own:
            continue
        shapes = p.base.polygons(pad["layers"].get("B.Cu", []))
        if not shapes:
            continue
        body = unary_union(shapes)
        def check(other, net, identity):
            if net is not None and p.norm(net) == p.norm(pad["net"]):
                return
            gap = .15 if net is not None and h["domains_normalized"].get(p.norm(net)) == h["domains_normalized"].get(p.norm(pad["net"])) else .6
            gap = .25 if net is None else gap
            if body.distance(other) < gap + p.MARGIN - 1e-8:
                findings.append({"ref": pad["ref"], "pad": pad["num"], "other": identity, "distance_mm": body.distance(other), "required_with_margin_mm": gap + p.MARGIN})
        for other in h["pads"]:
            if other["ref"] == pad["ref"]:
                continue
            for poly in p.base.polygons(other["layers"].get("B.Cu", [])):
                if poly.intersects(WINDOW.buffer(3)):
                    check(poly, other["net"], {"kind": "pad", "ref": other["ref"], "number": other["num"], "uuid": other["uuid"], "net": other["net"]})
            for hole in p.base.polygons(other.get("hole") or []):
                check(hole, None, {"kind": "pad_hole", "uuid": other["uuid"]})
        for track in h["tracks"]:
            if track["layer"] == "B.Cu" and p.base.body(track).intersects(WINDOW.buffer(3)):
                check(p.base.body(track), track["net"], {"kind": "segment", "uuid": track["uuid"], "net": track["net"]})
        for via in h["vias"]:
            at = Point(via["x"], via["y"])
            if at.intersects(WINDOW.buffer(3)):
                check(at.buffer(via["d"]/2), via["net"], {"kind": "via", "uuid": via["uuid"], "net": via["net"]})
                # Same-net plated hole is allowed in its own connected pad/stub;
                # every other hole requires pad-copper to hole-edge clearance.
                if p.norm(via["net"]) != p.norm(pad["net"]):
                    check(at.buffer(via["drill"]/2), None, {"kind": "via_hole", "uuid": via["uuid"]})
        for zone in h["zones"]:
            for poly in p.base.polygons(zone["fills"].get("B.Cu", [])):
                if poly.intersects(WINDOW.buffer(3)):
                    check(poly, zone["net"], {"kind": "filled_zone", "uuid": zone["uuid"], "net": zone["net"]})
    for foot in h["footprints"]:
        if foot["ref"] not in own or not foot["courtyard"].get("B"):
            continue
        court = unary_union(p.base.polygons(foot["courtyard"]["B"]))
        for other in h["footprints"]:
            if other["ref"] != foot["ref"] and other["courtyard"].get("B"):
                foreign = unary_union(p.base.polygons(other["courtyard"]["B"]))
                if court.intersects(foreign):
                    findings.append({"ref": foot["ref"], "other": {"kind": "courtyard", "ref": other["ref"]}, "overlap_mm2": court.intersection(foreign).area})
    return {"verdict": "HOST_PAD_AND_COURTYARD_PASS" if not findings else "HOST_REJECT", "findings": findings[:30], "total_findings": len(findings)}


def pack_south(g, areas, ref):
    region = six.landing(g, areas, "U11012", p.SOURCE_WINDOW)
    branch = p.free_copper(g, areas, p.NET, "In3.Cu").buffer(-.4)
    rows = []
    for part in p.hubs.components(branch):
        sites = p.hubs.pack_region(part.intersection(region).intersection(SOUTH), (221.126875,138.968594))
        if sites:
            rows.append({"site_count": len(sites), "sites": sites})
    return {"source_via_mm": [.6,.3], "south_window": list(SOUTH.bounds), "arrays": rows,
        "maximum_sampled_south_sites": max([row["site_count"] for row in rows], default=0),
        "neck_current_return_and_full_corridor_qualified": False}


def main():
    g, overlay = p.overlay()
    areas = five.old.reservations()
    # A prospective same-domain B/F ground repour is isolated in this host view.
    h = v.repour_overlay(g, True)
    native = p.base.inventory(p.read(p.C05))[3]
    c62_ground = next(t for t in h["tracks"] if t["uuid"] == GND_STUB)
    p.require(p.norm(c62_ground["net"]) == v.GND, "C62 GND owner mismatch")
    trials, valid = [], []
    for ref in ("C11062", "C11063"):
        for delta in ((0,-.5),(0,.5),(0,1),(0,1.5),(-.5,0),(-1,0),(.5,0),(1,0),(-.5,.5),(.5,.5)):
            model = dict(h)
            model["tracks"] = [t for t in h["tracks"] if ref != "C11062" or t["uuid"] != GND_STUB]
            candidate = moved(model, {ref: delta})
            row = {"moved_ref": ref, "delta_mm": list(delta), "ownership": [GND_STUB] if ref == "C11062" else [],
                "placement": placement(model, candidate, {ref: delta}), "reconnects": []}
            if row["placement"]["verdict"] == "HOST_PAD_AND_COURTYARD_PASS":
                if ref == "C11062":
                    for num, net, end, width in ((1, CORE, (220.,138.335),1.25),(2,v.GND,GROUND_END,.2)):
                        pad = next(x for x in candidate["pads"] if x["ref"] == ref and x["num"] == str(num))
                        route = five.exact_path(v.free_trace(candidate, areas, net,"B.Cu",width), end,(pad["x"],pad["y"]))
                        row["reconnects"].append({"pad": num,"net": net,"width_mm":width,"retained_endpoint":list(end),**route})
                        if route["verdict"] == "HOST_PATH":
                            candidate = v.append_path(candidate,net,"B.Cu",route,"SOUTH_C62_"+str(num),width)
                else:
                    row["reconnects"] = [{"net":v.GND,"status":"OPEN_SOURCE_ANCHORED_GROUND_AND_OUTPUT_CONNECTION_REQUIRED"}]
                valid.append((row,candidate))
            trials.append(row)
            print("SOUTH_CAP_PLACEMENT",ref,delta,row["placement"]["verdict"],flush=True)
    # Compare physical first: bound full through-via packing to baseline, a best
    # actual reconnected C62 lead, and the strongest cap-removal counterfactual.
    comparisons = [{"case":"BASELINE_REPOUR_HOST_VIEW","screen":pack_south(h,areas,"baseline")}]
    complete = [(row,candidate) for row,candidate in valid if row["moved_ref"]=="C11062" and all(r["verdict"]=="HOST_PATH" for r in row["reconnects"])]
    for row,candidate in complete[:2]:
        comparisons.append({"case":"C62_COMPLETE_OWNED_STUB_HOST_PATHS","delta_mm":row["delta_mm"],"screen":pack_south(candidate,areas,"C62")})
    strongest = dict(h)
    strongest["pads"] = [pad for pad in h["pads"] if pad["ref"] not in {"C11062","C11063"}]
    strongest["tracks"] = [t for t in h["tracks"] if t["uuid"] != GND_STUB]
    comparisons.append({"case":"COUNTERFACTUAL_BOTH_CAP_PADS_AND_C62_GROUND_STUB_ABSENT","screen":pack_south(strongest,areas,"counterfactual"),
        "is_viable_candidate":False,"retained_CORE_5V_3135_stub_and_all_foreign_copper":True})
    ownership = []
    for uid in (GND_STUB,CORE_STUB):
        ownership.append({"uuid":uid,"chunk_sha256":hashlib.sha256(native[uid]).hexdigest(),"treatment":"proposed-owned-GND-stub-replacement" if uid==GND_STUB else "retained-shared-CORE-feed-contacts"})
    for path in (Path(__file__),Path(six.__file__),Path(five.__file__),Path(v.__file__),p.OUT/"stage-source-inspection.json"):
        p.read(path)
    for path, expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,"input changed")
    receipt = {"evidence_class":"Bounded host source-only south-cap comparison; no native board", "board_sha256":p.C05_SHA,"overlay":overlay,
        "component_roles":{"C11062":"CORE_5V input decoupler; retain input-loop requirements","C11063":"SBC_5V output decoupler; retain load-switch output requirements"},
        "retained_old_CORE_cap_pad_contact":[220,138.335],"owned_item_manifest":ownership,"trials":trials,"comparisons":comparisons,"read_set_sha256":p.READS,
        "board_candidate_written":False,"native_launched":False,"implemented":False,"qualified_3p6A_100mV":False,
        "limits":["No waveform/input/output-cap-loop or thermal/current proof is inferred from short placement","All retained CORE_5V copper remains; its contact under the old C62 pad cannot be discarded","C63 connection and relocation readiness remain open","Only bounded short translations and the south window were examined; failure does not exclude a larger joint layout","Counterfactual missing capacitors are obstacle attribution, not an electrical candidate","All proposed source power vias remain .6/.3 and .5A capacity; no equal sharing assumed","Same-domain F/B LOGIC_GND relaxation is planning only; actual repour/loss/return proof remains open"]}
    path=p.OUT/"south-cap-comparison.json"
    path.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"placements_pass":len(valid),"C62_complete_stubs":len(complete),"comparisons":comparisons}),flush=True)

if __name__ == "__main__":
    main()
