"""One targeted four-part pose, with independent CT cap placement.

Source planning only. No native board, refill, DRC, GPU, copper removal or
reservation edits. All original load/current limits remain unchanged.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
from shapely.geometry import Point, box, mapping
from shapely.ops import unary_union
import prepare_sbc_stage_placement as stage

p,v,six=stage.p,stage.v,stage.six
POSES={"U11012":[116.,161.5,-90.],"C11061":[118.5,160.4,90.],
       "C11062":[116.775,161.75,0.],"C11063":[113.475,162.475,180.]}


def check_placement(candidate,masks,courts):
    findings=[]
    ownpads=[r for r in candidate["pads"] if r["ref"] in stage.REFS]
    ownfeet=[r for r in candidate["footprints"] if r["ref"] in stage.REFS]
    for pad in ownpads:
        for layer,records in pad["layers"].items():
            if layer not in ("F.Cu","B.Cu"):continue
            body=unary_union(p.base.polygons(records))
            overlap=body.intersection(masks[(layer,p.norm(pad["net"]))]).area
            if overlap>1e-9:
                findings.append({"kind":"retained_copper_hole_or_hard_mask","ref":pad["ref"],"pad":pad["num"],"layer":layer,"overlap_mm2":overlap})
    for foot in ownfeet:
        for side,records in foot["courtyard"].items():
            body=unary_union(p.base.polygons(records))
            for ref,other in courts[side]:
                if body.intersects(other):
                    findings.append({"kind":"retained_courtyard","ref":foot["ref"],"other_ref":ref,"side":side,"overlap_mm2":body.intersection(other).area})
    # Independent CT pose no longer inherits the original mutual cap geometry.
    for a,b in itertools.combinations(ownfeet,2):
        for side in ("F","B"):
            pa=unary_union(p.base.polygons(a["courtyard"].get(side,[])))
            pb=unary_union(p.base.polygons(b["courtyard"].get(side,[])))
            if pa.intersects(pb):findings.append({"kind":"proposed_owned_courtyard","a":a["ref"],"b":b["ref"],"side":side,"overlap_mm2":pa.intersection(pb).area})
    for a,b in itertools.combinations(ownpads,2):
        if a["ref"]==b["ref"] or p.norm(a["net"])==p.norm(b["net"]):continue
        for layer in ("F.Cu","B.Cu"):
            pa=unary_union(p.base.polygons(a["layers"].get(layer,[])))
            pb=unary_union(p.base.polygons(b["layers"].get(layer,[])))
            if not pa.is_empty and not pb.is_empty and pa.distance(pb)<.15+p.MARGIN-1e-8:
                findings.append({"kind":"proposed_owned_pad_clearance","a_ref":a["ref"],"a_pad":a["num"],"b_ref":b["ref"],"b_pad":b["num"],"layer":layer,"distance_mm":pa.distance(pb),"minimum_mm":.15+p.MARGIN})
    return {"verdict":"HOST_BODY_PLACEMENT_PASS" if not findings else "HOST_BODY_WITHHELD","findings":findings,"finding_count":len(findings)}


def main():
    destination=p.OUT/"targeted-stage-proposal.json"
    p.require(not destination.exists(),"distinct immutable receipt required")
    previous=json.loads(p.read(p.OUT/"larger-stage-owned-diagnosis.json"))
    si_path=Path("Z:/pcb-runs/impedance/controlled-nets.json")
    si=json.loads(p.read(si_path))["nets"]
    original,overlay=p.overlay()
    g=v.repour_overlay(original,True)
    areas=six.five.old.reservations()
    physical,courts=stage.cache(g,[])
    historical,_=stage.cache(g,areas)
    oldparts={r["ref"]:r for r in previous["owned_component_manifest"]}
    deltas={ref:[pose[0]-oldparts[ref]["old_pose"][0],pose[1]-oldparts[ref]["old_pose"][1]] for ref,pose in POSES.items()}
    candidate=stage.caps.moved(g,deltas)
    placements={"physical_native_rules_and_courtyards":check_placement(candidate,physical,courts),
                "including_historical_routing_reservations":check_placement(candidate,historical,courts)}
    native=p.base.inventory(p.read(p.C05))[3]
    window=box(110,154,122,166)
    blockers=[]
    def blocker(pad,layer,body,poly,net,identity):
        if p.norm(net)==p.norm(pad["net"]):return
        same=g["domains_normalized"].get(p.norm(net))==g["domains_normalized"].get(p.norm(pad["net"]))
        gap=.15 if same else .6
        if body.distance(poly)>=gap+p.MARGIN-1e-8:return
        hint=si.get(p.norm(net))
        uid=identity.get("uuid")
        blockers.append({"proposed_ref":pad["ref"],"pad":pad["num"],"layer":layer,"retained_item":identity,"net":p.norm(net),
                         "distance_mm":body.distance(poly),"required_mm":gap+p.MARGIN,
                         "native_chunk_sha256":hashlib.sha256(native[uid]).hexdigest() if uid in native else None,
                         "role":"galvanic barrier/protected foreign domain" if not same else "full-current power rail; actual resistor/current network must retain capacity" if p.norm(net) in (stage.caps.CORE,p.norm(p.NET),"/motherboard_compute/CM_AUX_3V3") else "controlled signal; preserve current source/SI/return contract" if hint and hint["class"]!="NONE" else "signal or ground; source circuit and return/no-loss checks required",
                         "historical_SI_hint":None if hint is None else {k:hint[k] for k in ("class","group","pair_partner","t_r_ns")}})
    for pad in candidate["pads"]:
        if pad["ref"] not in stage.REFS:continue
        for layer,records in pad["layers"].items():
            if layer not in ("F.Cu","B.Cu"):continue
            body=unary_union(p.base.polygons(records))
            for other in g["pads"]:
                if other["ref"] in stage.REFS:continue
                for poly in p.base.polygons(other["layers"].get(layer,[])):
                    if poly.intersects(window):blocker(pad,layer,body,poly,other["net"],{"kind":"pad","ref":other["ref"],"number":other["num"],"uuid":other["uuid"]})
            for t in g["tracks"]:
                if t["layer"]==layer:
                    poly=p.base.body(t)
                    if poly.intersects(window):blocker(pad,layer,body,poly,t["net"],{"kind":"segment","uuid":t["uuid"],"a":t["a"],"b":t["b"],"actual_width_mm":t["w"]})
            for via in g["vias"]:
                at=Point(via["x"],via["y"])
                if at.intersects(window):blocker(pad,layer,body,at.buffer(via["d"]/2),via["net"],{"kind":"via","uuid":via["uuid"],"at":[via["x"],via["y"]],"dimensions_mm":[via["d"],via["drill"]]})
    # Only screen source packing after every owned body/courtyard passes. No
    # blocked source pose is used to infer power/via-array feasibility.
    packing=None
    if placements["physical_native_rules_and_courtyards"]["verdict"]=="HOST_BODY_PLACEMENT_PASS":
        landing_window=box(110,157,122,166)
        packing=[]
        for label,screenareas in (("all_historical_reservations",areas),("physical_only_source_corridor_ledger_open",[])):
            region=six.landing(candidate,screenareas,"U11012",landing_window)
            for layer in ("F.Cu","B.Cu","In2.Cu","In3.Cu"):
                branch=p.free_copper(candidate,screenareas,p.NET,layer,window=landing_window).buffer(-.4)
                groups=[]
                for part in p.hubs.components(branch):
                    sites=p.hubs.pack_region(part.intersection(region),(117.126875,162.383594))
                    if sites:groups.append({"sampled_sites":sites,"count":len(sites)})
                packing.append({"case":label,"layer":layer,"sampled_arrays":groups,"maximum_sampled_sites":max([r["count"] for r in groups],default=0),"landing_region":mapping(region)})
    length=math.dist((243.375,115.15),POSES["U11012"][:2])
    for path in (Path(__file__),Path(stage.__file__),Path(stage.caps.__file__),Path(six.__file__),Path(p.__file__),p.OUT/"tps22990-census.json",p.EXT/"tools/verify/rail_model.json"):
        p.read(path)
    for path,expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,"input changed")
    unique={r["retained_item"].get("uuid"):r["retained_item"] for r in blockers}
    result={"schema":"sbc-targeted-four-part-source-pose-v1","evidence_class":"One bounded source-only four-part targeted pose, independently placed CT cap",
            "board_sha256":p.C05_SHA,"overlay":overlay,"exact_old_component_manifest":previous["owned_component_manifest"],"new_component_poses":POSES,"component_deltas_mm":deltas,
            "whole_private_CT_old_copper_manifest":previous["whole_private_CT_copper_manifest"],"old_stage_shared_net_contact_ledger":previous["old_source_exact_contact_ledger"],
            "placement":placements,"exact_retained_copper_blocker_observations":blockers,"unique_retained_copper_blockers":unique,"source_packing_if_body_passes":packing,
            "upstream_full_current":{"CORE_source":"R11022.2","preserved_load_A":3.6,"VIN_budget_mV":70,"ideal_straight_source_to_new_switch_mm":length,"ideal_35um_60C_minimum_width_mm":.57003672*length*3.6/70,"extra_vias_necks_contacts_actual_detours_and_other_absolute_loads_open":True},
            "SBC_output":{"source":"U11012.8/9/10","load":"J15001.77/79/81/83/85/87","preserved_load_A":3.6,"budget_mV":100,"power_via_mm":[.6,.3],"per_via_limit_A":.5,"minimum_full_current_transition_vias":8,"current_sharing_not_assumed_equal":True},
            "source_stage_scope":"Exactly U11012+C11061+C11062+C11063 and private CT network may move; each affected CORE/GND/ON/PG/SBC retained copper terminal requires reconnect proof. No whole shared net removal authorized by this receipt.",
            "proposed_copper_removals":[],"implemented":False,"board_emitted":False,"native_jobs":0,"gpu_jobs":0,"qualified_3p6A_100mV":False,
            "limits":["One concrete near-load pose, not a broad sweep or a global impossibility claim","Original relative input/output cap poses retained; C61 independently placed to avoid U15016 and must preserve CT trace/timing/ground requirements","Old C61 16V byte geometry is pinned historical input; isolated corrected 4.7uF25V source/API parity is separate and does not prove timing","Historical reservations are diagnosed separately; no native barrier or current/SI/ground/copper exception granted","None/absence in ROOT104 SI catalog is not current ROOT106 noncritical qualification","No native board until all external terminal reconnections, actual CORE/SBC corridors, source arrays, local cap loops, source-rooted returns and no-loss proof are established","All In1/In4 references, other native copper, all12 interfaces and absolute loads remain protected"],"source_files_sha256":p.READS}
    destination.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(destination),"placement":placements,"retained_blocker_count":len(unique),"source_packing":None if packing is None else [(r["case"],r["layer"],r["maximum_sampled_sites"]) for r in packing]}),flush=True)


if __name__=="__main__":main()
