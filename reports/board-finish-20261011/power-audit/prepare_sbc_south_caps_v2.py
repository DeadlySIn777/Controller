"""All four permitted routing-layer south screens, distinct frozen receipt."""
import copy
import hashlib
import json
from pathlib import Path
from shapely.geometry import Point, shape
from shapely.ops import unary_union
import prepare_sbc_south_caps as caps

p,v,six=caps.p,caps.v,caps.six


def screen(g,areas):
    legal=six.landing(g,areas,"U11012",p.SOURCE_WINDOW).intersection(caps.SOUTH)
    out={"legal_front_reachable_all_layer_power_via_area_mm2":legal.area,"layers":{}}
    for layer in v.LAYERS:
        branch=p.free_copper(g,areas,p.NET,layer).buffer(-.4)
        arrays=[]
        for part in p.hubs.components(branch):
            sites=p.hubs.pack_region(part.intersection(legal),(221.126875,138.968594))
            if sites:
                arrays.append({"site_count":len(sites),"sites":sites})
        out["layers"][layer]={"maximum_sampled_component_sites":max([row["site_count"] for row in arrays],default=0),"arrays":arrays,
            "branch_width_mm":.8,"source_neck_current_qualified":False}
    return out


def obstruction_attribution(g,areas):
    rows=[]
    domain=g["domains_normalized"].get(p.norm(p.NET))
    def retain(poly,identity):
        area=poly.intersection(caps.SOUTH).area
        if area>1e-5:
            rows.append({**identity,"overlap_with_south_window_mm2":area})
    def gap(net):
        return .15 if g["domains_normalized"].get(p.norm(net))==domain else .6
    for pad in g["pads"]:
        for layer,records in pad["layers"].items():
            for poly in p.base.polygons(records):
                if p.norm(pad["net"])!=p.norm(p.NET):
                    retain(poly.buffer(.3+gap(pad["net"])+p.MARGIN),{"kind":"pad_copper","uuid":pad["uuid"],"ref":pad["ref"],"pad":pad["num"],"net":pad["net"],"layer":layer})
                elif pad["smd"]:
                    retain(poly.buffer(.3+.1+p.MARGIN),{"kind":"same_net_smd_via_exclusion","uuid":pad["uuid"],"ref":pad["ref"],"pad":pad["num"],"layer":layer})
    for t in g["tracks"]:
        if p.norm(t["net"])!=p.norm(p.NET):
            retain(p.base.body(t).buffer(.3+gap(t["net"])+p.MARGIN),{"kind":"segment","uuid":t["uuid"],"net":t["net"],"layer":t["layer"],"width_mm":t["w"],"a":t["a"],"b":t["b"]})
    for via in g["vias"]:
        at=Point(via["x"],via["y"])
        retain(at.buffer(via["drill"]/2+.3+.25+p.MARGIN),{"kind":"existing_hole_to_prospective_copper","uuid":via["uuid"],"net":via["net"],"at":[via["x"],via["y"]]})
        if p.norm(via["net"])!=p.norm(p.NET):
            retain(at.buffer(via["d"]/2+.3+gap(via["net"])+p.MARGIN),{"kind":"via_copper","uuid":via["uuid"],"net":via["net"],"at":[via["x"],via["y"]]})
    for layer in g["copper_layers"]:
        for poly in p.hard_shapes(g,areas,p.NET,layer,for_via=True):
            retain(poly.buffer(.3+p.MARGIN),{"kind":"retained_rule_reservation_barrier_or_CORE_mask","layer":layer})
    p.base.WINDOW=p.SOURCE_WINDOW
    reference=p.base.layer_reference(g,"In1.Cu").intersection(p.base.layer_reference(g,"In4.Cu")).buffer(-.9)
    return {"largest_all_layer_via_blockers":sorted(rows,key=lambda x:-x["overlap_with_south_window_mm2"])[:24],
        "south_outside_retained_logic_reference_edge_budget_mm2":caps.SOUTH.difference(reference).area,
        "scope":"Obstacle overlaps are not exclusive and identify masks, not a proven minimal removal set"}


def main():
    prior=json.loads(p.read(p.OUT/"south-cap-comparison.json"))
    original,overlay=p.overlay()
    g=v.repour_overlay(original,True)
    areas=six.five.old.reservations()
    models=[("BASELINE_REPOUR_HOST_VIEW",g)]
    for row in prior["trials"]:
        if row["moved_ref"]=="C11062" and row["reconnects"] and all(x.get("verdict")=="HOST_PATH" for x in row["reconnects"]):
            h=dict(g)
            h["tracks"]=[t for t in g["tracks"] if t["uuid"]!=caps.GND_STUB]
            h=caps.moved(h,{"C11062":row["delta_mm"]})
            for path in row["reconnects"]:
                h=v.append_path(h,path["net"],"B.Cu",path,"SOUTH_C62_"+str(path["pad"]),path["width_mm"])
            models.append(("C62_"+str(row["delta_mm"]),h))
    h=dict(g)
    h["pads"]=[pad for pad in g["pads"] if pad["ref"] not in {"C11062","C11063"}]
    h["tracks"]=[t for t in g["tracks"] if t["uuid"]!=caps.GND_STUB]
    models.append(("COUNTERFACTUAL_TWO_CAP_PADS_ABSENT_NOT_CANDIDATE",h))
    cases=[]
    for name,model in models:
        print("SOUTH_ALL_LAYER_SCREEN",name,flush=True)
        cases.append({"case":name,"screen":screen(model,areas)})
    attribution=obstruction_attribution(h,areas)
    native=p.base.inventory(p.read(p.C05))[3]
    footprint_manifest=[]
    for ref in ("C11062","C11063"):
        uid,chunk=next((uid,c) for uid,c in native.items() if p.base.pcbtext.chunk_kind(c)=="footprint" and p.base.ref_of(c)==ref)
        footprint_manifest.append({"ref":ref,"uuid":uid,"chunk_sha256":hashlib.sha256(chunk).hexdigest(),"original_pose":p.pose(p.base.children(chunk)[1])})
    for path in (Path(__file__),Path(caps.__file__),Path(six.__file__),Path(v.__file__),p.OUT/"local-cap-opi-v6.json",p.OUT/"tps22990-census.json"):
        p.read(path)
    for path,expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,"input changed")
    receipt={"evidence_class":"Source-only south via-array layer comparison and actual blocker attribution","board_sha256":p.C05_SHA,"overlay":overlay,
        "cases":cases,"attribution":attribution,"owned_footprints":footprint_manifest,"prior_cap_placement_and_reconnects":str(p.OUT/"south-cap-comparison.json"),
        "power_via_mm":[.6,.3],"power_via_current_limit_a":.5,"array_spacing_mm":.8,"prospective_hole_to_copper_mm":.25,"planner_margin_mm":.025,
        "implemented":False,"qualified_3p6A_100mV":False,"native_launched":False,"board_candidate_written":False,"read_set_sha256":p.READS,
        "limits":["All retained CORE feed contacts remain; no input current reduction or equal branch sharing is assumed","Actual source neck and fanout/current topology remain open even where legal sites exist","Counterfactual cap removal is obstacle attribution, never an electrically viable board","All interface/foreign/critical copper and In1/In4 reference fills stay pinned","C11061 16V CT rating requires separate verified25V-minimum BOM/timing correction","0.8mm source branches only test physical local access; complete power corridors still require actual resistor/current network and native/return/no-loss proof"]}
    path=p.OUT/"south-cap-all-layer-comparison.json"
    path.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"cases":cases}),flush=True)

if __name__=="__main__":
    main()
