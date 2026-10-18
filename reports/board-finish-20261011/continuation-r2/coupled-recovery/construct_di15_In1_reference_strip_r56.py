"""Freeze an exact reference-only coupled proposal; no design adoption.

Only two owned positive In1 planes may be carved. All original Cu/outlines,
source poses and the 11 DI6 items remain exact. Mesh/current rebuilding is
owned by the peers, and all new signal/return/native gates remain open.
"""
import sys,json,pickle,time,copy,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE.parent/'sbc-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import audit_di6_direct_latest_power_r8 as D
import audit_c10036_r24_full_independent_r30 as Q
import guarded_power_projection_r44 as Z
import complete_geometry_r2 as GE
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
C=A.C;GND='/LOGIC_GND';CORE='84b085e3-5361-596d-bea3-6b51cc9bcfb3';FB='882c6aaa-4aa1-5c66-b57e-a1a963dc3817'
def save(path,b):assert not path.exists();path.write_bytes(b);return {'file':str(path),'sha256':C.sha(b)}
def main():
 started=time.monotonic();directory=HERE/'di15-In1-reference-strip-r56';assert not directory.exists();directory.mkdir();out=directory/'receipt.json';A.read(__file__);rp=HERE/'di15-root-LG-r18-DI6-bind-r50.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='e372e8ea1a703619f6c6e1002050624a070d01216b8d26f6f9f16b0de2c8114e';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];before=cur['after'];rootplane=cur['source_planes']['In1.Cu'];pathr=json.loads(A.read(HERE/'di15-In2-physical-reference-diagnostic-r48.json'));pts=pathr['physical_paths_reference_not_qualified'][0]['In2_points_mm'];line=LineString(pts);body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(pts,pts[1:])]);wanted=Z.bounded_buffer(line,.20);desired=wanted.difference(rootplane.buffer(-.15,quad_segs=128));domains=h['domains_normalized'];rec,trees=F.build({**h,'zones':[]});obstacles=[];foreign_rows=[]
 for i in trees['In1.Cu'].query(desired.buffer(.7),predicate='intersects'):
  q=rec['In1.Cu'][int(i)];n=L.norm(q['net'])
  if n==GND:continue
  required=max(.15 if domains.get(n)==domains.get(GND) else .6,.25)+.025;mask=q['shape'].buffer(required,quad_segs=128);obstacles.append(mask);overlap=desired.intersection(mask)
  if not overlap.is_empty:foreign_rows.append({'UUID':q['uuid'],'kind':q['kind'],'net':q['net'],'guarded_required_mm':required,'desired_overlap_mm2':overlap.area,'shape_WKB_sha256':C.sha(q['shape'].wkb)})
 for p in h['pads']:
  for sh in L.poly(p.get('hole') or []):
   if sh.distance(desired)>.7:continue
   if L.norm(p['net'])==GND:obstacles.append(sh)
   else:obstacles.append(sh.buffer(.275,quad_segs=128))
 for v in h['vias']:
  if Point(v['x'],v['y']).distance(desired)>.7:continue
  if L.norm(v['net'])==GND:obstacles.append(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))
  else:obstacles.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=128))
 reserve,exempt=A.reservations();rule_rows=[]
 for q in h['rule_areas']:
  if 'In1.Cu' in q['layers'] and q.get('no_zones'):
   for sh in L.poly(q['outline']):
    if sh.distance(desired)<.025:obstacles.append(sh.buffer(.025,quad_segs=128));rule_rows.append(q['uuid'])
 for q in reserve['keepouts']:
  if 'In1.Cu' in q['layers'] and GND not in exempt.get(q['name'],set()):
   for sh in L.poly(q['outline']):
    if sh.distance(desired)<.025:obstacles.append(sh.buffer(.025,quad_segs=128));rule_rows.append(q['name'])
 preserved_planes=[]
 for z in cur['zones']:
  if z['layer']!='In1.Cu' or L.norm(z['net'])==GND or z['uuid'] in(CORE,FB):continue
  required=max(.15 if domains.get(L.norm(z['net']))==domains.get(GND) else .6,.25,float(z.get('clearance_mm',.15)))+.025;mask=Z.bounded_buffer(z['shape'],required);obstacles.append(mask)
  if not desired.intersection(mask).is_empty:preserved_planes.append({'UUID':z['uuid'],'net':z['net'],'desired_overlap_mm2':desired.intersection(mask).area,'WKB_sha256':C.sha(z['shape'].wkb)})
 strip=desired.difference(unary_union(obstacles));gap=body.difference(rootplane.union(strip));strip_pin=save(directory/'source-reference-strip.wkb',strip.wkb);body_pin=save(directory/'DI15-saved-In2-body.wkb',body.wkb);masks={CORE:Z.bounded_buffer(strip,.275),FB:Z.bounded_buffer(strip,.625)};corrections=[];zone_ops=[];zby={z['uuid']:z for z in cur['zones']}
 for u in(CORE,FB):
  z=zby[u];assert z['layer']=='In1.Cu';old=z['shape'];new=old.difference(masks[u]);operation={'UUID':u,'raw_net':z['net'],'layer':z['layer'],'owned_new_proposal_only':True,'old_shape':save(directory/(u+'-before.wkb'),old.wkb),'outward_reference_mask':save(directory/(u+'-mask.wkb'),masks[u].wkb),'new_shape':save(directory/(u+'-after.wkb'),new.wkb),'guarded_separation_mm':.275 if u==CORE else .625,'new_reference_zone_local_mm':.25,'old_proposal_local_mm':float(z.get('clearance_mm',.15)),'area_removed_mm2':old.difference(new).area,'old_components':len(A.polys([old])) if False else len(GE.records(old)),'new_components':len(GE.records(new)),'source_current_native_acceptance':'OPEN_NO_MESH_REBUILD_CREDIT'};corrections.append(operation);zone_ops.append({**z,'shape':new})
 added=[];all_pieces=GE.records(strip)
 for i,rs in enumerate(all_pieces):
  shape=unary_union(L.poly([rs]));u=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/DI15/reference-r56/'+C.sha(shape.wkb)));added.append({'uuid':u,'net':GND,'layer':'In1.Cu','shape':shape,'clearance_mm':.25,'priority':124,'minimum_thickness_mm':.25,'island_removal_mode':0,'island_area_min_mm2':0,'thermal_gap_mm':.3,'thermal_bridge_width_mm':.3,'name':'DI15 ordinary In2 adjacent source reference R56','owned_new':True});zone_ops.append(added[-1])
 zones=copy.deepcopy(cur['zones']);zones=[z for z in zones if z['uuid'] not in(CORE,FB)]+zone_ops;fills=[]
 for z in before['zones']:
  nz={**z,'fills':dict(z['fills'])}
  if z['uuid'] in(CORE,FB):nz['fills']['In1.Cu']=GE.records(zby[z['uuid']]['shape'].difference(masks[z['uuid']]))
  fills.append(nz)
 for z in added:fills.append({'uuid':z['uuid'],'net':GND,'clearance_mm':.25,'priority':124,'fills':{'In1.Cu':GE.records(z['shape'])}})
 after={**before,'zones':fills};print('DI15_NEW_REFERENCE_STRIP_SOURCE_GRAPH_BEGIN',len(added),flush=True);refs,uf,groups,root=D.root_reference(after);actual_gap=body.difference(refs['F.Cu']);lost=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));pieces=[{'UUID':z['uuid'],'shape_WKB_sha256':C.sha(z['shape'].wkb),'area_mm2':z['shape'].area,'actual_prior_root_overlap_mm2':z['shape'].intersection(rootplane).area,'source_connected_after_projection':any(q['kind']=='fill' and q['uuid']==z['uuid'] for q in root)} for z in added]
 proposal=save(directory/'proposed-zone-corrections-and-reference.pkl',pickle.dumps(zone_ops,protocol=5));cp=save(directory/'reference-only-current-model.pkl',pickle.dumps({'current':cur,'after':after,'zones':zones,'new_reference':added,'coupled_masks':masks,'refs':refs,'root':root,'groups':groups,'body':body,'gap':actual_gap},protocol=5));report={'verdict':'DI15_EXACT_REFERENCE_ONLY_COUPLED_PROPOSAL_SOURCE_PASS_MESH_CURRENT_NATIVE_OPEN' if actual_gap.area<1e-10 and not lost else'DI15_EXACT_REFERENCE_ONLY_COUPLED_PROPOSAL_INCOMPLETE','R50_receipt_sha256':C.sha(A.read(rp)),'source_model_sha256':r['model_sha256'],'source_parent_sha256':r['source_parent_sha256'],'path_points_mm':pts,'path_width_mm':.2,'path_length_mm':line.length,'prospective_reference_strip_nominal_width_mm':.4,'new_native_zone_profile':{'layer':'In1.Cu','net':GND,'clearance_mm':.25,'priority':124,'minimum_thickness_mm':.25},'source_reference_strip':strip_pin,'saved_signal_body':body_pin,'foreign_discrete_obstacle_trims':foreign_rows,'real_rule_area_trims':rule_rows,'other_owned_planes_preserved_hard':preserved_planes,'pregraph_full_body_uncovered_mm2':gap.area,'actual_drilled_source_graph_full_body_uncovered_mm2':actual_gap.area,'actual_LOGIC_GND_J11001_2_prior_source_keys_lost':lost,'source_connected_new_pieces':pieces,'only_owned_new_plane_corrections':corrections,'proposed_corrections':proposal,'saved_reference_only_model':cp,'old_native_discrete_FP_source_project_rules_outlines_changed':0,'new_holes':0,'new_signal_routes_added':0,'signed_supply_load_mesh_oldcontact_whole_reference_current_native_SI':'OPEN','protectedFB_solved_route_core_must_not_be_narrowed_or_cut_without_rebuild_and_signed_load_proof':True,'root_R20_27_FBG_old_reference_losses_remain_open':True,'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'pregraph_gap':gap.area,'actual_gap':actual_gap.area,'source_lost':len(lost),'pieces':pieces,'corrections':corrections}),flush=True)
if __name__=='__main__':main()
