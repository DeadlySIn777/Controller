"""Minimal four-part switch-stage near compute: bounded host source plan only."""
import copy
import hashlib
import json
import math
from pathlib import Path
from shapely.geometry import Point, box
from shapely.ops import unary_union

import prepare_sbc_south_caps as caps

p,v,six=caps.p,caps.v,caps.six
REFS={"U11012","C11061","C11062","C11063"}
TARGET=box(103,143,143,165)
CT=v.CT


def cache(g,areas):
    cu={"F.Cu":{},"B.Cu":{}}
    holes=[]
    for pad in g["pads"]:
        if pad["ref"] in REFS:
            continue
        net=p.norm(pad["net"])
        for layer in cu:
            cu[layer].setdefault(net,[]).extend(poly for poly in p.base.polygons(pad["layers"].get(layer,[])) if poly.intersects(TARGET.buffer(3)))
        holes.extend(poly for poly in p.base.polygons(pad.get("hole") or []) if poly.intersects(TARGET.buffer(3)))
    for track in g["tracks"]:
        if track["layer"] in cu:
            poly=p.base.body(track)
            if poly.intersects(TARGET.buffer(3)):
                cu[track["layer"]].setdefault(p.norm(track["net"]),[]).append(poly)
    for via in g["vias"]:
        at=Point(via["x"],via["y"])
        if at.intersects(TARGET.buffer(3)):
            for layer in cu:
                cu[layer].setdefault(p.norm(via["net"]),[]).append(at.buffer(via["d"]/2))
            holes.append(at.buffer(via["drill"]/2))
    for zone in g["zones"]:
        for layer in cu:
            cu[layer].setdefault(p.norm(zone["net"]),[]).extend(poly for poly in p.base.polygons(zone["fills"].get(layer,[])) if poly.intersects(TARGET.buffer(3)))
    for graphic in g["shapes"]:
        if graphic["layer"] in cu:
            cu[graphic["layer"]].setdefault(p.norm(graphic["net"]),[]).extend(poly for poly in p.base.polygons(graphic["poly"]) if poly.intersects(TARGET.buffer(3)))
    nets={p.norm(pad["net"]) for pad in g["pads"] if pad["ref"] in REFS}
    masks={}
    for layer,groups in cu.items():
        groups={net:unary_union(polys) for net,polys in groups.items()}
        for net in nets:
            domain=g["domains_normalized"].get(net)
            obstacles=[poly.buffer((.15 if g["domains_normalized"].get(other)==domain else .6)+p.MARGIN)
                for other,poly in groups.items() if other!=net]
            obstacles += [hole.buffer(.25+p.MARGIN) for hole in holes]
            # Kept explicit electrical reservations/barriers, even when copper
            # and courtyards appear physically vacant in a source snapshot.
            obstacles += [poly.buffer(p.MARGIN) for poly in p.hard_shapes(g,areas,net,layer)]
            masks[(layer,net)]=unary_union(obstacles)
    courts={side:[(f["ref"],unary_union(p.base.polygons(f["courtyard"].get(side,[]))))
        for f in g["footprints"] if f["ref"] not in REFS and f["courtyard"].get(side)] for side in ("F","B")}
    return masks,courts


def placement(g,delta,masks,courts):
    candidate=caps.moved(g,{ref:delta for ref in REFS})
    findings=[]
    for pad in candidate["pads"]:
        if pad["ref"] not in REFS:
            continue
        for layer,records in pad["layers"].items():
            if layer not in ("F.Cu","B.Cu"):
                continue
            body=unary_union(p.base.polygons(records))
            overlap=body.intersection(masks[(layer,p.norm(pad["net"]))]).area
            if overlap>1e-9:
                findings.append({"kind":"retained_copper_hole_or_hard_mask","ref":pad["ref"],"pad":pad["num"],"layer":layer,"overlap_mm2":overlap})
    for foot in candidate["footprints"]:
        if foot["ref"] not in REFS:
            continue
        for side,records in foot["courtyard"].items():
            court=unary_union(p.base.polygons(records))
            for ref,other in courts[side]:
                if court.intersects(other):
                    findings.append({"kind":"retained_courtyard","ref":foot["ref"],"other_ref":ref,"side":side,"overlap_mm2":court.intersection(other).area})
    return candidate,{"verdict":"HOST_FOUR_PART_PLACEMENT_PASS" if not findings else "HOST_REJECT", "finding_count":len(findings),"findings":findings[:12]}


def main():
    original,overlay=p.overlay()
    areas=six.five.old.reservations()
    g=v.repour_overlay(original,True)
    masks,courts=cache(g,areas)
    native=p.base.inventory(p.read(p.C05))[3]
    manifest=[]
    for ref in sorted(REFS):
        uid,chunk=next((uid,c) for uid,c in native.items() if p.base.pcbtext.chunk_kind(c)=="footprint" and p.base.ref_of(c)==ref)
        manifest.append({"ref":ref,"uuid":uid,"chunk_sha256":hashlib.sha256(chunk).hexdigest(),"old_pose":p.pose(p.base.children(chunk)[1])})
    # Exact private ramp network can move only as a whole source-owned group.
    ct_owned=[{"uuid":uid,"kind":p.base.pcbtext.chunk_kind(chunk),"chunk_sha256":hashlib.sha256(chunk).hexdigest()}
        for uid,chunk in native.items() if p.base.pcbtext.chunk_kind(chunk) in ("segment","via") and p.norm(p.netname(chunk))==CT]
    trials=[]
    for x in (111,116,121,126,131,136):
        for y in (150,155,160):
            delta=(x-220,y-138.085)
            _,row=placement(g,delta,masks,courts)
            row.update({"U11012_new_pose":[x,y,-90],"delta_mm":list(delta),"stage_poses":[{"ref":part["ref"],"new_pose":[part["old_pose"][0]+delta[0],part["old_pose"][1]+delta[1],part["old_pose"][2]]} for part in manifest]})
            trials.append(row)
            print("FOUR_PART_STAGE",x,y,row["verdict"],flush=True)
    feasible=[row for row in trials if row["verdict"]=="HOST_FOUR_PART_PLACEMENT_PASS"]
    # Source feasible placement is separate from complete power, control, ground
    # and ramp re-routing. Do not synthesize an incomplete native board.
    rho_sheet_mohm=.57003672
    upstream=[]
    for row in feasible:
        new=row["U11012_new_pose"][:2]
        length=math.dist((243.375,115.15),new)
        upstream.append({"U11012_new_pose":row["U11012_new_pose"],"ideal_straight_CORE_5V_route_length_mm":length,
            "ideal_minimum_35um_60C_width_for_70mV_3p6A_mm":rho_sheet_mohm*length*3.6/70,
            "all_necks_vias_contacts_ground_and_actual_detour_extra":True})
    for path in (Path(__file__),Path(caps.__file__),Path(six.__file__),p.OUT/"stage-source-inspection.json",p.OUT/"tps22990-census.json",p.EXT/"tools/verify/rail_model.json",p.EXT/"agent-work/field-pdn/netlist.json"):
        p.read(path)
    for path,expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,"input changed")
    receipt={"evidence_class":"Bounded minimal SBC four-component source-placement proposal; no native candidate","board_sha256":p.C05_SHA,"overlay":overlay,
        "owned_components":manifest,"whole_private_CT_copper_manifest":ct_owned,"minimum_switch_local_set_excludes_other_motor_or_CORE_converter_parts":sorted(REFS),"bounded_placement_trials":trials,"placement_leads":len(feasible),
        "CORE_5V_upstream_constraints":upstream,"all_original_current_limits_kept":{"J15001_a":3.6,"VOUT_budget_mv":100,"CORE_to_VIN_budget_mv":70,"via_a":.5,"power_via_mm":[.6,.3]},
        "CORE_converter_larger_dependencies":["U11007","L11001","R11022","C11022","C11023","C11024","C11025","C11026","R11023","R11024","R11025","R11026","R11029"],
        "CORE_converter_dependency_scope":"Private CORE_CORE_* nets identify a minimum source inspection set; CORE_5V output and CORE supply input capacitors/sense return/PG/enable dependents still require complete SMPS loop audit before any larger placement",
        "external_connections_still_required":["CORE_5V wide full-current input from retainedR11022.2; source array/current sharing and<=70mV","MC_RAILS_OK_5V unchanged U11012.5 enable circuit and inhibited restart","SBC_SWITCH_PG unchanged U11012.7 open-drain pullup/supervisor chain","All four component LOGIC_GND paths directly anchored to physical source with complete return/thermal proof","Whole CT network exact local reconnection; signal vias/returns and25V-minimum CT-cap effective timing check","Full SBC_5V VOUT8–10 to J15001.77–87 <=100mV at3.6A plus other absolute loads retained"],
        "limits":["Eighteen stage translations are a bounded physical screen; no global placement impossibility claim","The four-part move preserves original package sides/rotations and relative local capacitor poses; it has no fresh source/local copper/current proof","Moving U11012 alone or this stage near J15001 moves a large current path upstream; it cannot qualify compute power without CORE_5V source-to-input geometry","No source/native schematic or board mutated; no broad protected-copper ownership asserted","In1/In4 reference fills and all12motor/foreign/critical interfaces remain protected","Original stage value16V CT cap retained only as frozen geometry; separate same-footprint25V-minimum electrical correction remains required"],
        "read_set_sha256":p.READS,"implemented":False,"native_launched":False,"board_candidate_written":False,"qualified_3p6A_100mV":False}
    path=p.OUT/"larger-stage-placement-proposal.json"
    path.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"placement_leads":len(feasible),"CORE_constraints":upstream}),flush=True)

if __name__=="__main__":
    main()
