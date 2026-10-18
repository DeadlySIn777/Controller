"""Exact final one-wall SENSE endpoint/source-reference obstruction witness."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_single_SENSE_wall_legal_F_In3_F_r368.py';s=base.read_text(encoding='utf-8-sig').split('ground_ok=')[0].replace('Q0-four-wall-two-port-route-constructor-r368','Q0-one-SENSE-wall-final-reference-diagnosis-r376');exec(compile(s,str(base),'exec'))
fr=free(SENSE,'B.Cu',refs['In4.Cu']);partrows=[];ends=[[228.96,156.39],[228.96,159.6]];points=[]
for at in ends:
 p=Point(at);disk=K.Z.bounded_disk({'x':at[0],'y':at[1]},.105);gap=disk.difference(refs['In4.Cu']);row={'at_mm':at,'actual_after_source_full_cap_gap_mm2':gap.area,'actual_after_source_full_cap_gap_empty':gap.is_empty,'actual_after_ref_distance_mm':p.distance(refs['In4.Cu']),'reference_eroded_contains':refs['In4.Cu'].buffer(-.105,quad_segs=128).covers(p),'exact_physical_reference_free_contains':fr.covers(p),'physical_free_distance_mm':p.distance(fr)};points.append(row);(out/('endpoint-'+str(len(points))+'-full-cap-reference-gap.wkb')).write_bytes(gap.wkb)
for i,part in enumerate(K.RF.parts(fr)):
 inside=[part.covers(Point(at))for at in ends]
 if any(inside):partrows.append({'index':i,'contains_endpoints':inside,'bounds':part.bounds,'area_mm2':part.area});(out/('SENSE-attachment-component-'+str(i)+'.wkb')).write_bytes(part.wkb)
# Old Cu contact/ref causal rows at the upper anchor, without any Boolean
# recomputation of remote source planes.
at=ends[0];p=Point(at);rr=[]
for r in discrete['B.Cu']:
 if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==SENSE:continue
 d=p.distance(r['shape'])-.105;need=req(SENSE,r['net'])+.030
 if d<need:rr.append({'kind':r['kind'],'uuid':r['uuid'],'net':r['net'],'gap_minus_new_body_radius_mm':d,'required_mm':need})
for z in q:
 if z['layer']!='B.Cu'or K.L.norm(z['net'])in(SENSE,GND):continue
 d=p.distance(z['shape'])-.105;need=max(req(SENSE,z['net']),float(z['clearance_mm']))+.030
 if d<need:rr.append({'kind':'owned_plane','uuid':z['uuid'],'net':z['net'],'gap_minus_new_body_radius_mm':d,'required_mm':need})
for r in reserve['keepouts']:
 if'B.Cu'in r['layers']and SENSE not in exempt.get(r['name'],set()):
  for shape in K.L.poly(r['outline']):
   if shape.distance(p)<.130:rr.append({'kind':'frozen_reserved','name':r['name'],'centre_to_polygon_mm':shape.distance(p),'guarded_new_body_radius_mm':.130})
put(out/'endpoint-components-and-actual-blocker-rows.json',{'endpoints':points,'components':partrows,'upper_endpoint_actual_Cu_and_rule_blockers':rr});report={'verdict':'CONCRETE_Q0_ONE_SENSE_WALL_SOURCE_REFERENCE_CAUSAL_DIAGNOSIS','model_sha256':sha(model),'Q0_R368_receipt_sha256':sha(H/'Q0-four-wall-two-port-route-constructor-r368/receipt.json'),'operator_sha256':sha(operator),'endpoints':points,'attachment_component_rows':partrows,'upper_actual_blockers':rr,'no_reference_expansion_no_area_threshold_no_own_neighbor_disk':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',report);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**report}),flush=True)
