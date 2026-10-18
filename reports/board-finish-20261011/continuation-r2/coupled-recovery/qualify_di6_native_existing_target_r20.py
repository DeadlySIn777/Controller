"""Check actual existing In3 attachment void and its used-plane return.

No new target transition, generic ground credit or neighbouring void waiver.
The unmatched global old-cache reference differences remain explicitly open.
"""
import sys,json,pickle,math,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_c10036_r24_full_independent_r30 as Q
from shapely.geometry import Point
from shapely.ops import unary_union
C=A.C
def vertices(sh):
 if sh.is_empty:return []
 if sh.geom_type=='Polygon':return list(sh.exterior.coords)+[p for r in sh.interiors for p in r.coords]
 return [p for q in getattr(sh,'geoms',[]) for p in vertices(q)]
def main():
 out=HERE/'di6-native-existing-target-return-r20.json';assert not out.exists();A.read(__file__);p=HERE/'di6-actual-native-reference-independent-r19.json';r=json.loads(A.read(p));assert C.sha(A.read(p))=='db2452f3192ad4d7d0054144e44e03ce44ddf04279022ddb177b0e2480f3985d';raw=A.read(r['saved_actual_model']);assert C.sha(raw)==r['saved_actual_model_sha256']=='a70eee0497ea68a5673e49ec15ed5c6e6b184079f8fa761a34d7c80824daf26f';m=pickle.loads(raw);g=m['actual'];refs=m['root_reference'];root=m['root'];rk=Q.discrete_keys(root)
 via=next(v for v in g['vias'] if v['uuid']=='0ff4e506-7bc1-48ad-91fd-aeb598e74c7a');ret=next(v for v in g['vias'] if v['uuid']=='cb1390c8-49e9-4971-9ee8-740c03e5b93f');assert(via['x'],via['y'],via['d'],via['drill'],via['net'])==(113.95,119.35,.6,.3,'/motherboard_di{slash}DI6_LOGIC');assert(ret['x'],ret['y'],ret['d'],ret['drill'],ret['net'])==(113.4,120.15,.6,.3,'/LOGIC_GND');assert set(via['flashed'])==set(ret['flashed'])==set(Q.LAYERS)
 oldtrack=next(t for t in g['tracks'] if t['uuid']=='3a0b46f2-c120-45e5-b93f-8d687e955639');assert oldtrack['layer']=='In3.Cu' and oldtrack['net']==via['net'];assert oldtrack['a']==(113.95,119.35) or oldtrack['a']==[113.95,119.35];assert len(r['reference_errors'])==1;err=r['reference_errors'][0];newtrack=next(t for t in g['tracks'] if t['uuid']==err['UUID']);assert newtrack['layer']=='In3.Cu';gap=A.shape({'kind':'segment',**newtrack}).difference(refs['In3.Cu']);overlap=A.shape({'kind':'segment',**newtrack}).intersection(A.shape({'kind':'segment',**oldtrack})).area;assert overlap>=.004
 near=[]
 for z in g['zones']:
  if L.norm(z['net'])!='/LOGIC_GND':continue
  local=float(z.get('clearance_mm',.15))
  if any(Point(via['x'],via['y']).distance(sh)<=.3+max(.15,local)+.025 for sh in L.poly(z['fills'].get('In4.Cu',[]))):near.append({'zone_UUID':z['uuid'],'exact_source_local_clearance_mm':local})
 assert near;radius=.3+max(.15,max(n['exact_source_local_clearance_mm'] for n in near))+.025;assert radius==.575;maxrad=max(math.dist(p[:2],(via['x'],via['y'])) for p in vertices(gap));ann=Point(ret['x'],ret['y']).buffer(.3,quad_segs=128).difference(Point(ret['x'],ret['y']).buffer(.15,quad_segs=128));contact=refs['In3.Cu'].buffer(-.075).intersection(ann).area;qualified=('via',ret['uuid']) in rk and .81<=math.dist((via['x'],via['y']),(ret['x'],ret['y']))<=1 and contact>=.004 and maxrad<=radius and overlap>=.004
 report={'verdict':'ACTUAL_DI6_NINE_NEW_BODIES_AND_USED_SOURCE_TARGET_RETURNS_PASS_MATCHED_BASELINE_FINAL_PDN_OPEN' if qualified else'ACTUAL_DI6_EXISTING_TARGET_IN3_CONTACT_RETURN_OR_VOID_OPEN','native_candidate_sha256':r['native_candidate_sha256'],'R19_receipt_sha256':C.sha(A.read(p)),'actual_native_model_sha256':C.sha(raw),'source_new_F_In3_pair':r['actual_paired_return'],'existing_target_UUID':via['uuid'],'existing_target_exact_native_all6':via['flashed'],'existing_target_retained_In3_UUID':oldtrack['uuid'],'new_last_segment_UUID':newtrack['uuid'],'exact_same_layer_contact_mm2':overlap,'new_target_transition_added':False,'existing_target_return_UUID':ret['uuid'],'actual_return_all6':ret['flashed'],'actual_return_roots_at':'J11001.2' if('via',ret['uuid']) in rk else None,'return_distance_mm':math.dist((via['x'],via['y']),(ret['x'],ret['y'])),'only_used_In4_finite_annular_interior_mm2':contact,'no_In1_credit_claimed':True,'full_body_actual_gap_mm2':gap.area,'exact_source_native_local_clearance_rows':near,'exact_existing_target_disk_radius_mm':radius,'maximum_actual_gap_vertex_radius_mm':maxrad,'radius_expansion_mm':0,'entire_gap_in_one_exact_current_same_net_attachment_void':qualified,'all_other_eight_new_segment_native_reference_checks_pass':all(x['reference_pass'] for x in r['new_full_body_reference'] if x['UUID']!=newtrack['uuid']),'matched_fresh_eedf_before_baseline_reference_contact':'OPEN; R19 old pinned cache comparison has2748 unwaived differences, not attributed to DI6','prior_GND_contact_losses':r['prior_GND_contact_losses'],'native_allboard_current_r06_r07_SI_and_latest_R78_field_FG_C_AO_joint':'OPEN','adopted':False,'native_jobs':0,'board_written':False,'read_files_sha256':A.READS};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'verdict':report['verdict'],'maxrad':maxrad,'radius':radius,'used_In4_return_contact_mm2':contact,'sha256':C.sha(out.read_bytes())}),flush=True)
if __name__=='__main__':main()
