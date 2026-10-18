"""Actual source-only In1/In3 reference pieces for R90, zero power carve.

This is an exact reference construction, not a qualified handoff. A union
can nominate where finite return stitches are necessary but supplies no
unqualified electrical/high-frequency reference credit by itself.
"""
import sys,json,pickle,time,uuid,copy
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE.parent/'sbc-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import audit_c10036_r24_full_independent_r30 as Q
import guarded_power_projection_r44 as Z
import complete_geometry_r2 as GE
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
C=A.C;GND='/LOGIC_GND'
def main():
 started=time.monotonic();directory=HERE/'di15-zero-power-carve-reference-pieces-r94';assert not directory.exists();directory.mkdir();A.read(__file__);rp=HERE/'di15-safe-root-r22-DI6-bind-r62.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];before=cur['after'];pr=HERE/'di15-adjacent-reference-handoff-geometric-nomination-r90.json';p=json.loads(A.read(pr));assert C.sha(A.read(pr))=='71e9cb9446100ddeca47f8dd2acbdd73af4703fda83501edf98d87e100b714d5';assert p['power_planes_released']==[];points=p['nominees'][0]['In2_points_mm'];line=LineString(points);body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(points,points[1:])]);wanted=Z.bounded_buffer(line,.2);domains=h['domains_normalized'];rec,trees=F.build({**h,'zones':[]});reserve,exempt=A.reservations();owned={z['uuid'] for z in cur['zones']};added=[];ledger=[]
 for layer in('In1.Cu','In3.Cu'):
  oldref=cur['source_planes'][layer];missing=body.difference(oldref);desired=wanted.difference(oldref.buffer(-.15,quad_segs=128));obs=[];cuts=[]
  for i in trees[layer].query(desired.buffer(.7),predicate='intersects'):
   q=rec[layer][int(i)];net=L.norm(q['net'])
   if net==GND:continue
   req=max(.25,.15 if domains.get(net)==domains[GND] else .6)+.025;mask=Z.bounded_buffer(q['shape'],req);obs.append(mask)
   if not desired.intersection(mask).is_empty:cuts.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'guarded_requirement_mm':req,'mask_WKB_sha256':C.sha(mask.wkb)})
  for v in h['vias']:
   if L.norm(v['net'])==GND or Point(v['x'],v['y']).distance(desired)>.7:continue
   mask=Z.bounded_disk(v,v['drill']/2+.275);obs.append(mask)
  for pad in h['pads']:
   if L.norm(pad['net'])==GND:continue
   obs.extend(Z.bounded_buffer(sh,.275) for sh in L.poly(pad.get('hole') or []) if sh.distance(desired)<.7)
  for q in h['rule_areas']:
   if layer in q['layers'] and q.get('no_zones'):obs.extend(Z.bounded_buffer(sh,.025) for sh in L.poly(q['outline']) if sh.distance(desired)<.7)
  for q in reserve['keepouts']:
   if layer in q['layers'] and GND not in exempt.get(q['name'],set()):obs.extend(Z.bounded_buffer(sh,.025) for sh in L.poly(q['outline']) if sh.distance(desired)<.7)
  for z in before['zones']:
   net=L.norm(z['net'])
   if net==GND or z['uuid'] in owned:continue
   for sh in L.poly(z['fills'].get(layer,[])):
    if sh.distance(desired)>.7:continue
    req=max(.25,float(z.get('clearance_mm',.15)),.15 if domains.get(net)==domains[GND] else .6)+.025;mask=Z.bounded_buffer(sh,req);obs.append(mask)
    if not desired.intersection(mask).is_empty:cuts.append({'kind':'original_filled_Cu_hard','UUID':z['uuid'],'raw_net':z['net'],'guarded_requirement_mm':req,'mask_WKB_sha256':C.sha(mask.wkb)})
  for z in cur['zones']:
   net=L.norm(z['net'])
   if z['layer']!=layer or net==GND or z['shape'].distance(desired)>.7:continue
   req=max(.25,float(z.get('clearance_mm',.15)),.15 if domains.get(net)==domains[GND] else .6)+.025;mask=Z.bounded_buffer(z['shape'],req);obs.append(mask)
   if not desired.intersection(mask).is_empty:cuts.append({'kind':'owned_proposed_Cu_hard','UUID':z['uuid'],'raw_net':z['net'],'guarded_requirement_mm':req,'mask_WKB_sha256':C.sha(mask.wkb)})
  strip=desired.difference(unary_union(obs));pruned=[]
  for rs in GE.records(strip):
   shape=unary_union(L.poly([rs]));required_contact=shape.intersection(missing)
   if required_contact.is_empty:pruned.append({'shape_WKB_sha256':C.sha(shape.wkb),'reason':'Exact intersection with this layer original missing body is empty'});continue
   u=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/DI15/zero-carve-reference-r94/'+layer+'/'+C.sha(shape.wkb)));added.append({'uuid':u,'net':GND,'layer':layer,'shape':shape,'clearance_mm':.25,'priority':124,'minimum_thickness_mm':.25,'island_removal_mode':0,'island_area_min_mm2':0,'thermal_gap_mm':.3,'thermal_bridge_width_mm':.3,'name':'DI15 ordinary In2 source reference zero power carve R94','owned_new':True})
  ledger.append({'layer':layer,'desired_WKB_sha256':C.sha(desired.wkb),'new_strip_WKB_sha256':C.sha(strip.wkb),'all_original_and_owned_foreign_plane_masks':cuts,'pruned_redundant_pieces':pruned,'own_net_barrel_centres_never_explicitly_drill_subtracted':True})
 fills=copy.deepcopy(before['zones'])
 for z in added:fills.append({'uuid':z['uuid'],'net':GND,'clearance_mm':.25,'priority':124,'fills':{z['layer']:GE.records(z['shape'])}})
 after={**before,'zones':fills};print('DI15_ZERO_CARVE_REFERENCE_ACTUAL_SOURCE_BEGIN',len(added),flush=True);_,groups=Q.physical(after,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==('J11001','2') for q in xs));refs={layer:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==layer]) for layer in('In1.Cu','In3.Cu')};lost=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));pieces=[{'UUID':z['uuid'],'layer':z['layer'],'shape_WKB_sha256':C.sha(z['shape'].wkb),'area_mm2':z['shape'].area,'actual_prior_root_overlap_mm2':z['shape'].intersection(cur['source_planes'][z['layer']]).area,'actual_source_connected':any(q['kind']=='fill' and q['uuid']==z['uuid'] and q['layer']==z['layer'] for q in root)} for z in added];union=unary_union(list(refs.values()));uniongap=body.difference(union);rows=[]
 for a,b in zip(points,points[1:]):
  sh=A.shape({'kind':'segment','a':a,'b':b,'w':.2});rows.append({'a':a,'b':b,'missing_by_actual_plane_mm2':{layer:sh.difference(ref).area for layer,ref in refs.items()},'missing_by_actual_union_nomination_only_mm2':sh.difference(union).area})
 proposal=directory/'proposed-zones.pkl';proposal.write_bytes(pickle.dumps(added,protocol=5));cp=directory/'source-reference-only-model.pkl';cp.write_bytes(pickle.dumps({'current':cur,'after':after,'new_zones':added,'zones':cur['zones']+added,'refs':refs,'root':root,'groups':groups,'body':body,'points':points},protocol=5));report={'verdict':'DI15_ZERO_POWER_CARVE_ACTUAL_SOURCE_PIECES_BUILT_HANDOFF_RETURN_OPEN' if uniongap.is_empty and not lost and all(q['actual_source_connected'] for q in pieces) else'DI15_ZERO_POWER_CARVE_REFERENCE_PIECES_INCOMPLETE','R62_receipt_sha256':C.sha(A.read(rp)),'R90_geometry_nominee_sha256':C.sha(A.read(pr)),'source_model_sha256':r['model_sha256'],'source_parent_sha256':r['source_parent_sha256'],'layer_mask_ledger':ledger,'new_actual_source_piece_ledger':pieces,'prior_LOGIC_GND_source_keys_lost':lost,'actual_full_body_source_union_gap_mm2_nomination_only':uniongap.area,'per_segment_actual_source_plane_body_gaps':rows,'new_native_zone_profile':{'net':GND,'clearance_mm':.25,'priority':124,'minimum_thickness_mm':.25},'zone_count':len(added),'proposed_zones_file':str(proposal),'proposed_zones_sha256':C.sha(proposal.read_bytes()),'source_only_model_file':str(cp),'source_only_model_sha256':C.sha(cp.read_bytes()),'power_Cu_planes_deleted_or_carved':0,'old_Cu_FP_source_project_rules_outlines_changed':0,'new_signal_Cu_or_holes':0,'reference_union_grants_no_handoff_or_electrical_qualification':True,'required_remaining':'Real finite actual In1/In3 handoff annuli; per-body reference assignment and actual new signal/return drill projection; every contact/current/r06/r07/neighbour/native/SI gate','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out=directory/'receipt.json';out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'actual_union_gap':uniongap.area,'prior_source_key_losses':len(lost),'pieces':pieces,'per_segment_gaps':rows}),flush=True)
if __name__=='__main__':main()
