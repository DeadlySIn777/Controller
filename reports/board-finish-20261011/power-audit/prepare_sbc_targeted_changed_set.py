"""Bounded explicit five-power-segment/five-part prospective change set.

Only JSON evidence is emitted. Every removed item is an ownership proposal;
no native board, original copper, project, rules, reservations or source is edited.
"""
import hashlib
import json
import math
from pathlib import Path
from shapely.geometry import Point, box, mapping
from shapely.ops import unary_union
import prepare_sbc_targeted_stage as T

p,v,six,stage=T.p,T.v,T.six,T.stage
SBC=p.NET
CORE=stage.caps.CORE
REMOVED={
 "3a1a5daa-b4b6-4fd5-8d80-54acc7d85288":(CORE,1.25),
 "6a104e1d-0b3d-4304-a866-73d78e3048d0":(CORE,1.25),
 "d8fee387-b7bd-443b-b645-965c234d19e7":(CORE,1.2),
 "75c6a8f8-b95a-4a20-8e88-f8b2b502d17e":(p.norm(SBC),.5),
 "9c6ab5f6-e6d7-4182-a0ee-cb8c8c7703e9":(p.norm(SBC),.3),
}
POSES={"U11012":[116.,161.5,-90.],"C11061":[119.5,160.4,90.],
       "C11062":[116.775,161.75,0.],"C11063":[112.975,162.475,180.],
       "C15001":[114.602,164.725,90.]}
GROUND_VIA="45617979-cdc6-42db-9b78-94c762d1aff4"


def contacts(g,native,footprints,shape,net,layer,omit=(),native_vias=None):
    rows=[]
    def take(poly,identity):
        area=poly.intersection(shape).area
        if area>1e-7:rows.append({**identity,"layer":layer,"physical_overlap_mm2":area})
    for pad in g["pads"]:
        if p.norm(pad["net"])==p.norm(net):
            for poly in p.base.polygons(pad["layers"].get(layer,[])):
                take(poly,{"kind":"pad","ref":pad["ref"],"pad":pad["num"],"uuid":pad["uuid"],"parent_footprint_sha256":footprints[pad["ref"]]["sha256"]})
    for t in g["tracks"]:
        if t["uuid"] not in omit and t["layer"]==layer and p.norm(t["net"])==p.norm(net):
            take(p.base.body(t),{"kind":"segment","uuid":t["uuid"],"a":t["a"],"b":t["b"],"width_mm":t["w"],"chunk_sha256":hashlib.sha256(native[t["uuid"]]).hexdigest()})
    for via in g["vias"]:
        if p.norm(via["net"])!=p.norm(net):continue
        if native_vias is not None:
            old=native_vias.get(via["uuid"])
            if old is None or layer not in old["flashed"]:continue
        take(Point(via["x"],via["y"]).buffer(via["d"]/2),{"kind":"via","uuid":via["uuid"],"at":[via["x"],via["y"]],"dimensions_mm":[via["d"],via["drill"]],"chunk_sha256":hashlib.sha256(native[via["uuid"]]).hexdigest()})
    return rows


def landing(g,areas,net,terminal,window):
    old_p,old_base=p.NET,p.base.NET
    try:
        p.NET=p.base.NET=net
        return six.landing(g,areas,terminal,window)
    finally:p.NET,p.base.NET=old_p,old_base


def arrays(g,areas,net,terminal,window):
    region=landing(g,areas,net,terminal,window)
    return region,{"terminal":terminal,"power_via_mm":[.6,.3],"center_spacing_mm":.8,
                   "source_front_reachable_geometric_region":mapping(region),
                   "sampled_sites":p.hubs.pack_region(region,region.representative_point().coords[0]) if not region.is_empty else [],
                   "fanout_current_necks_contact_resistance_and_native_returns_qualified":False}


def main():
    dest=p.OUT/"targeted-changed-set-proposal.json"
    p.require(not dest.exists(),"immutable distinct receipt required")
    prior=json.loads(p.read(p.OUT/"targeted-stage-proposal.json"))
    original,overlay=p.overlay()
    native=p.base.inventory(p.read(p.C05))[3]
    exported=json.loads(p.read(p.base.GEOM))
    native_vias={r["uuid"]:r for r in exported["vias"]}
    fp={}
    for uid,ch in native.items():
        if p.base.pcbtext.chunk_kind(ch)=="footprint":
            fp[p.base.ref_of(ch)]={"uuid":uid,"sha256":hashlib.sha256(ch).hexdigest(),"pose":p.pose(p.base.children(ch)[1])}
    netlist=json.loads(p.read(p.EXT/"agent-work/field-pdn/netlist.json"))
    p.require(p.norm(netlist["pins"]["C15001"]["1"])==p.norm(SBC) and netlist["pins"]["C15001"]["2"]==v.GND,"C15001 electrical role differs")
    byuid={t["uuid"]:t for t in original["tracks"]}
    powerledger=[]
    for uid,(net,width) in REMOVED.items():
        r=byuid[uid]
        p.require(p.norm(r["net"])==p.norm(net) and r["w"]==width and r["layer"]=="F.Cu","power owner changed")
        powerledger.append({"uuid":uid,"old_chunk_sha256":hashlib.sha256(native[uid]).hexdigest(),"net":p.norm(net),"old_width_mm":width,"a":r["a"],"b":r["b"],
                            "retained_interior_and_endpoint_contacts":contacts(original,native,fp,p.base.body(r),net,"F.Cu",omit=set(REMOVED),native_vias=native_vias),
                            "treatment":"whole exact segment proposed for replacement; all recorded retained contacts must survive, no outside copper removed"})
    ground=next(r for r in original["vias"] if r["uuid"]==GROUND_VIA)
    actual=native_vias[GROUND_VIA]
    p.require(p.norm(ground["net"])==v.GND and all(ground[k]==actual[k] for k in ("x","y","d","drill")),"ground via geometry differs")
    groundcontacts={layer:contacts(original,native,fp,Point(ground["x"],ground["y"]).buffer(ground["d"]/2),v.GND,layer,native_vias=native_vias)
                    for layer in actual["flashed"]}
    ct={r["uuid"] for r in prior["whole_private_CT_old_copper_manifest"]}
    model=v.repour_overlay(original,True)
    model["tracks"]=[r for r in model["tracks"] if r["uuid"] not in set(REMOVED)|ct]
    model["vias"]=[r for r in model["vias"] if r["uuid"] not in ct]
    stage.REFS=set(POSES)
    deltas={ref:[pose[0]-fp[ref]["pose"][0],pose[1]-fp[ref]["pose"][1]] for ref,pose in POSES.items()}
    p.require(all(POSES[ref][2]==fp[ref]["pose"][2] for ref in POSES),"unsupported rotation")
    candidate=stage.caps.moved(model,deltas)
    areas=six.five.old.reservations()
    physical,courts=stage.cache(model,[])
    historic,_=stage.cache(model,areas)
    placement={"physical_native_rules_and_courtyards":T.check_placement(candidate,physical,courts),
               "including_historical_reservations":T.check_placement(candidate,historic,courts)}
    # Exact identities for any further copper/placement change are emitted; the
    # planner stops at this changed set and never silently expands ownership.
    additional=[]
    local=box(110,156,123,167)
    for pad in candidate["pads"]:
        if pad["ref"] not in stage.REFS:continue
        for layer,records in pad["layers"].items():
            if layer not in ("F.Cu","B.Cu"):continue
            body=unary_union(p.base.polygons(records))
            def check(poly,net,identity):
                if p.norm(net)==p.norm(pad["net"]):return
                gap=.15 if candidate["domains_normalized"].get(p.norm(net))==candidate["domains_normalized"].get(p.norm(pad["net"])) else .6
                if body.distance(poly)<gap+p.MARGIN-1e-8:additional.append({"moved_ref":pad["ref"],"pad":pad["num"],"layer":layer,"required_mm":gap+p.MARGIN,"distance_mm":body.distance(poly),"net":p.norm(net),"exact_retained_item":identity})
            for t in candidate["tracks"]:
                if t["layer"]==layer:
                    poly=p.base.body(t)
                    if poly.intersects(local):check(poly,t["net"],{"kind":"segment","uuid":t["uuid"],"a":t["a"],"b":t["b"],"width_mm":t["w"],"old_chunk_sha256":hashlib.sha256(native[t["uuid"]]).hexdigest()})
            for via in candidate["vias"]:
                point=Point(via["x"],via["y"])
                if point.intersects(local):check(point.buffer(via["d"]/2),via["net"],{"kind":"via","uuid":via["uuid"],"at":[via["x"],via["y"]],"dimensions_mm":[via["d"],via["drill"]],"old_chunk_sha256":hashlib.sha256(native[via["uuid"]]).hexdigest()})
            for other in candidate["pads"]:
                if other["ref"] in stage.REFS:continue
                for poly in p.base.polygons(other["layers"].get(layer,[])):
                    if poly.intersects(local):check(poly,other["net"],{"kind":"pad","ref":other["ref"],"num":other["num"],"uuid":other["uuid"],"parent_footprint_sha256":fp[other["ref"]]["sha256"]})
    packing=None;corridors=None
    if placement["physical_native_rules_and_courtyards"]["verdict"]=="HOST_BODY_PLACEMENT_PASS":
        packing=[];corridors=[]
        oldwindow=p.WINDOW
        p.WINDOW=box(103,109,249,174)
        try:
            # Both modes preserve all real native barriers, holes, foreign copper
            # and In1/In4 reference territories. Physical-only cannot waive a
            # historical reservation; a complete changed corridor ledger remains open.
            for label,screenareas in (("all_historical_reservations",areas),("physical_only_new_source_corridor_ledger_open",[])):
                source,src=arrays(candidate,screenareas,SBC,"U11012",box(110,157,122,166))
                packing.append({"case":label,"SBC_source":src,"minimum_transition_sites":8})
                if len(src["sampled_sites"])<8:continue
                for net,width,source_ref,sourcewindow,load_ref,loadwindow in (
                    (SBC,3.,"U11012",box(110,157,122,166),"J15001",box(110,164,124,172)),
                    (CORE,4.5,"R11022",box(236,109,249,123),"U11012",box(110,157,122,166))):
                    a,ar=arrays(candidate,screenareas,net,source_ref,sourcewindow)
                    b,br=arrays(candidate,screenareas,net,load_ref,loadwindow)
                    for layer in ("F.Cu","B.Cu","In2.Cu","In3.Cu"):
                        free=p.free_copper(candidate,screenareas,net,layer,window=p.WINDOW).buffer(-width/2)
                        links=[]
                        for component in p.hubs.components(free):
                            aa=p.hubs.pack_region(component.intersection(a),a.representative_point().coords[0]) if not a.is_empty else []
                            bb=p.hubs.pack_region(component.intersection(b),b.representative_point().coords[0]) if not b.is_empty else []
                            if len(aa)>=8 and len(bb)>=8:links.append({"source_sites":aa,"load_sites":bb,"source_site_count":len(aa),"load_site_count":len(bb)})
                        corridors.append({"case":label,"net":p.norm(net),"layer":layer,"width_mm":width,"source":ar,"load":br,"continuous_wide_components_with_8_at_both_ends":links,"return_and_resistor_network_qualified":False})
        finally:p.WINDOW=oldwindow
    length=math.dist((243.375,115.15),POSES["U11012"][:2])
    for source in (Path(__file__),Path(T.__file__),Path(stage.__file__),Path(stage.caps.__file__),Path(six.__file__),Path(p.__file__),p.OUT/"tps22990-census.json"):
        p.read(source)
    for path,expected in p.READS.items():p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,"input changed")
    result={"schema":"sbc-targeted-five-segment-five-part-proposal-v1","evidence_class":"Prospective explicit targeted ownership/placement/source-packing screen, not native board",
            "board_sha256":p.C05_SHA,"overlay":overlay,"old_component_manifest":{ref:fp[ref] for ref in POSES},"new_component_poses":POSES,"deltas_mm":deltas,
            "C15001_role":{"value":netlist["comps"]["C15001"]["value"],"pins":netlist["pins"]["C15001"],"role":"10uF load-side SBC_5V output decoupling; move only1mm toward compute connector, preserve loop, ESR/effective capacitance and ground contacts"},
            "power_segment_ownership_manifest":powerledger,"old_stage_shared_terminal_ledger":prior["old_stage_shared_net_contact_ledger"],"whole_private_CT_old_manifest":prior["whole_private_CT_old_copper_manifest"],
            "retained_ground_via":{"uuid":GROUND_VIA,"old_chunk_sha256":hashlib.sha256(native[GROUND_VIA]).hexdigest(),"actual_native_span":actual["span"],"actual_native_flashed":actual["flashed"],"at":[ground["x"],ground["y"]],"dimensions_mm":[ground["d"],ground["drill"]],"unchanged_contacts_by_actual_layer":groundcontacts,"treatment":"retained exactly; never silently repurposed, moved or removed"},
            "placement":placement,"additional_retained_copper_changes_required":additional,"source_packing_if_body_passes":packing,"paired_supply_corridor_geometry_if_8_source_sites":corridors,
            "preserved_current_limits":{"SBC_load_A":3.6,"SBC_budget_mV":100,"CORE_input_budget_mV":70,"per_power_via_A":.5,"power_via_mm":[.6,.3],"minimum_full_current_transition_vias":8,"equal_sharing_assumed":False,"ideal_upstream_straight_length_mm":length,"ideal_CORE_35um_60C_minimum_width_mm":.57003672*length*3.6/70},
            "maximum_ownership_scope":list(POSES)+list(REMOVED)+[r["uuid"] for r in prior["whole_private_CT_old_copper_manifest"]],"no_further_expansion":True,
            "limits":["Only this exact five-part/five-power-segment set is examined; additional actual retained blockers are recorded and ownership is not expanded","All old interior copper contacts on removed tracks must survive complete proposed replacements, not only segment endpoints","Three overlapping CORE segments form one physical1.25mm bus; duplicate track widths/current ratings are never summed","Two inherited SBC segments do not establish full3.6A capacity; unchanged current needs a dedicated actual network","Same-domain F/B LOGIC_GND repour is source planning only; references/foreign copper are retained, future fresh native0loss and complete source/return current network required","Every source and load array count is a bounded geometric sample; pad fanout widths/common necks/current sharing/contact/thermal/resistance remain open","A constant-width corridor component is only a geometry lead; no source control/PG/CT/local-cap loops or return proof inferred","Exact ROOT1064.7uF25V CT source/API correction is separate; historical1uF50V timing envelope is not inherited","No incomplete native board emitted and no manufacturing/readiness claim"],
            "implemented":False,"board_emitted":False,"native_jobs":0,"gpu_jobs":0,"qualified_power":False,"source_files_sha256":p.READS}
    dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(dest),"placement":placement,"additional_retained_copper_observations":len(additional),"packing":None if packing is None else [(r["case"],len(r["SBC_source"]["sampled_sites"])) for r in packing],"wide_corridor_leads":None if corridors is None else sum(bool(r["continuous_wide_components_with_8_at_both_ends"]) for r in corridors)}),flush=True)


if __name__=="__main__":main()
