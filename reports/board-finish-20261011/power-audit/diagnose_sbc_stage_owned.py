"""Separate exact source owners, physical walls and historical reservations."""
import hashlib
import json
import math
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
import prepare_sbc_stage_placement as stage

p,v,six=stage.p,stage.v,stage.six


def main():
    prior=json.loads(p.read(p.OUT/"larger-stage-placement-proposal.json"))
    si_path=Path("Z:/pcb-runs/impedance/controlled-nets.json")
    historical_si=json.loads(p.read(si_path))
    original,overlay=p.overlay()
    g=v.repour_overlay(original,True)
    areas=six.five.old.reservations()
    # This diagnostic removes synthetic reservations only. Native rule areas,
    # galvanic barriers and all retained copper/courtyards remain exact.
    physical_masks,courts=stage.cache(g,[])
    native=p.base.inventory(p.read(p.C05))[3]
    trials=[]
    for oldrow in prior["bounded_placement_trials"]:
        _,physical=stage.placement(g,oldrow["delta_mm"],physical_masks,courts)
        trials.append({"U11012_new_pose":oldrow["U11012_new_pose"],"delta_mm":oldrow["delta_mm"],"stage_poses":oldrow["stage_poses"],"with_all_historical_reservations":oldrow["finding_count"],"physical_with_native_rules_barriers_and_courtyards":physical})
    trials.sort(key=lambda row:row["physical_with_native_rules_barriers_and_courtyards"]["finding_count"])
    # Removal ownership is prospective: each old part is untouched. The private
    # CT group has no external terminal other than C61.1/U12.1. Shared CORE and
    # control nets have only affected exact contacts recorded, never blanket ownership.
    source_contacts=[]
    for pad in original["pads"]:
        if pad["ref"] not in stage.REFS:continue
        for layer,records in pad["layers"].items():
            body=unary_union(p.base.polygons(records))
            touching=[]
            for t in original["tracks"]:
                if t["layer"]==layer and p.norm(t["net"])==p.norm(pad["net"]) and body.intersection(p.base.body(t)).area>1e-7:
                    touching.append({"uuid":t["uuid"],"net":t["net"],"a":t["a"],"b":t["b"],"width_mm":t["w"],"chunk_sha256":hashlib.sha256(native[t["uuid"]]).hexdigest(),"ownership":"whole-private-CT" if p.norm(t["net"])==v.CT else "exact-affected-contact-only; shared net copper retained pending explicit reconnect plan"})
            if touching:source_contacts.append({"ref":pad["ref"],"pad":pad["num"],"pad_uuid":pad["uuid"],"net":pad["net"],"layer":layer,"old_center":[pad["x"],pad["y"]],"native_track_contacts":touching})
    diagnoses=[]
    for row in trials[:3]:
        candidate=stage.caps.moved(g,{ref:row["delta_mm"] for ref in stage.REFS})
        blockers=[]
        affected_reservations=[]
        for pad in candidate["pads"]:
            if pad["ref"] not in stage.REFS:continue
            for layer,records in pad["layers"].items():
                if layer not in ("F.Cu","B.Cu"):continue
                body=unary_union(p.base.polygons(records))
                net=p.norm(pad["net"])
                domain=g["domains_normalized"].get(net)
                def check(poly,other,identity):
                    if p.norm(other)==net:return
                    gap=.15 if g["domains_normalized"].get(p.norm(other))==domain else .6
                    if body.distance(poly)<gap+p.MARGIN-1e-8:
                        catalog=historical_si["nets"].get(p.norm(other))
                        blockers.append({"moved_ref":pad["ref"],"pad":pad["num"],"layer":layer,"other":identity,"net":p.norm(other),"domain":g["domains_normalized"].get(p.norm(other)),"distance_mm":body.distance(poly),"required_mm":gap+p.MARGIN,
                            "historical_SI_catalog_hint":None if catalog is None else {k:catalog[k] for k in ("class","group","pair_partner","t_r_ns")},
                            "criticality":"protected-galvanic" if gap==.6 else "protected-controlled-impedance" if catalog and catalog["class"]!="NONE" else "electrical-signal/current/return rechecks required; NONE/absent is not noncritical proof"})
                for other in g["pads"]:
                    if other["ref"] in stage.REFS:continue
                    for poly in p.base.polygons(other["layers"].get(layer,[])):
                        if poly.intersects(stage.TARGET.buffer(3)):
                            check(poly,other["net"],{"kind":"pad","ref":other["ref"],"number":other["num"],"uuid":other["uuid"]})
                for t in g["tracks"]:
                    if t["layer"]==layer:
                        poly=p.base.body(t)
                        if poly.intersects(stage.TARGET.buffer(3)):
                            check(poly,t["net"],{"kind":"segment","uuid":t["uuid"],"a":t["a"],"b":t["b"],"width_mm":t["w"],"chunk_sha256":hashlib.sha256(native[t["uuid"]]).hexdigest()})
                for via in g["vias"]:
                    at=Point(via["x"],via["y"])
                    if at.intersects(stage.TARGET.buffer(3)):
                        check(at.buffer(via["d"]/2),via["net"],{"kind":"via","uuid":via["uuid"],"at":[via["x"],via["y"]],"via_mm":[via["d"],via["drill"]]})
                for area in areas:
                    if layer in area["layers"] and net not in area["exempt"]:
                        overlap=body.intersection(unary_union(p.base.polygons(area["outline"]))).area
                        if overlap>1e-9:
                            reservation={**area,"exempt":sorted(area["exempt"])}
                            affected_reservations.append({"source_ref":pad["ref"],"source_pad":pad["num"],"layer":layer,"reservation":reservation,"overlap_mm2":overlap,"treatment":"prospective source/corridor ledger required; no reservation altered"})
        diagnoses.append({"new_U11012_pose":row["U11012_new_pose"],"physical_score":row["physical_with_native_rules_barriers_and_courtyards"],"retained_copper_blockers":blockers,"historical_reservation_conflicts":affected_reservations,
            "ideal_CORE_5V_70mV_full_current_route_min_width_mm":.57003672*math.dist((243.375,115.15),row["U11012_new_pose"][:2])*3.6/70})
    for path in (Path(__file__),Path(stage.__file__),p.OUT/"tps22990-census.json",p.OUT/"local-cap-opi-v6.json",p.OUT/"south-cap-all-layer-comparison.json"):
        p.read(path)
    for path,expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,"input changed")
    result={"evidence_class":"Bounded prospective minimal source-stage ownership and physical-vs-reservation diagnosis","board_sha256":p.C05_SHA,"overlay":overlay,"owned_component_manifest":prior["owned_components"],"whole_private_CT_copper_manifest":prior["whole_private_CT_copper_manifest"],"old_source_exact_contact_ledger":source_contacts,
        "same18poses_no_window_expansion":True,"physical_trials":trials,"best_three_pose_diagnoses":diagnoses,"physical_placement_pass_count":sum(row["physical_with_native_rules_barriers_and_courtyards"]["verdict"]=="HOST_FOUR_PART_PLACEMENT_PASS" for row in trials),
        "source_owner_policy":"C11061/C11062/C11063/U11012 and whole private CT network only; shared CORE/GND/control copper has exact affected contacts, never whole-net ownership","implemented":False,"board_emitted":False,"native_jobs":0,"GPU_jobs":0,"qualified_power":False,
        "limits":["Historical reservations are separately diagnosed, not asserted immutable electrical barriers and not waived","A larger stage move still requires complete new CORE_5V and SBC_5V corridor ledger/resistor-current network, controls/returns/caps/courtyards plus future fullnative0loss/DRC","Criticality is conservative: oldROOT104 SI hints cannot certify current ROOT106 signal treatment","CT cap ROOT1064.7uF25V timing is distinct from historical1uF50V standalone source","No blind broad reroute or different-domain/reference-plane copper removal proposed"] ,"read_set_sha256":p.READS}
    path=p.OUT/"larger-stage-owned-diagnosis.json"
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"physical_placement_pass_count":result["physical_placement_pass_count"],"best_poses":[(r['U11012_new_pose'],r['physical_with_native_rules_barriers_and_courtyards']['finding_count']) for r in trials[:3]]}),flush=True)

if __name__=="__main__":main()
