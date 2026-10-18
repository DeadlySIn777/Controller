"""R523 positive and R535 owned-boundary negative redesign only on R515.

All actual original/native Cu and IO3 fills stay exact; no halo reclamation.
The controlling generated FG edges are explicitly redesigned, not waived.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,time,hashlib,traceback
from pathlib import Path
from shapely import set_precision,from_wkb
from shapely.ops import unary_union
from shapely.geometry import Polygon,Point,LineString
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import guarded_declared_settings_projection_r58 as N
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl';A=H/'FIELD5-all-source-finite-annulus-old-reference-hard-nomination-r523';D=H/'FIELD5-R525-raw-FG-gain-and-literal-boundary-attribution-r527';S=H/'FIELD5-new-cut-intersections-only-inward-native-splice-proposal-r535';E=H/'FIELD5-original-edge-cut-intersection-and-native-lattice-attribution-r531';O=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r541'
OLD='61cb8179-7754-5031-bbea-0da464bf816f';FG='e2fe644a-2849-5c69-8ebb-d1e94909cd4c'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def sm(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'sha256':dg(s)}
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def save(f,s):f.write_bytes(s.wkb);return {'file':str(f.resolve()),'file_SHA256':sha(f),**sm(s)}
def rings(s):
 for p in(s.geoms if s.geom_type=='MultiPolygon'else[s]):
  yield list(p.exterior.coords)
  for r in p.interiors:yield list(r.coords)
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862';assert sha(S/'receipt.json')=='7b783e104ab4ca9a9d7242fd868d5e41fd0bbe289f2dc44676bcaff7714d956c'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);b=copy.deepcopy(b);nominee=pickle.loads((A/'only-one-new-FIELD5-actual-source-port-nominee.pkl').read_bytes());new=copy.deepcopy(nominee['q']);uid=new['uuid'];layer='In2.Cu';raw=new['net'];free=from_wkb((A/'In2.Cu-80.0-exact-hard-body-free.wkb').read_bytes());canonical=[]
 for role in('shape','zone_outline_shape'):
  oldnew=new[role];new[role]=set_precision(oldnew,1e-6,mode='valid_output');assert free.covers(lit(new[role]));canonical.append({'role':role,'before_SHA256':dg(oldnew),'after_SHA256':dg(new[role]),'only_new_positive_canonicalized':True})
 assert new['zone_outline_shape'].covers(Point(nominee['existing_target_via']['x'],nominee['existing_target_via']['y']))
 old=next(z for z in q if z['uuid']==OLD);ground=next(z for z in q if z['uuid']==FG);assert ground['layer']==layer and old['net']==raw and old['layer']=='In4.Cu'
 cut=from_wkb((D/'actual-normal-cut.wkb').read_bytes());expected=lit(N.bounded_buffer(new['zone_outline_shape'],.1751));assert cut.wkb==expected.wkb
 newroles=pickle.loads((S/'only-proposed-FG-two-roles.pkl').read_bytes());sr=json.loads((S/'receipt.json').read_text(encoding='utf-8'));er=json.loads((E/'receipt.json').read_text(encoding='utf-8'));edgeby={tuple(r['raw_new_vertex']):r for r in er['rows']};changed=copy.deepcopy(ground);rows=[];extra_cuts=[];all_scopes=[cut]
 for role in('shape','zone_outline_shape'):
  before=lit(ground[role]);after=lit(newroles[role]);rr=next(r for r in sr['rows']if r['role']==role);assert rr['before_sha256']==dg(before)and rr['strict_gain_EMPTY']and before.difference(after).area>0;assert after.difference(before).is_empty
  rawafter=from_wkb((D/(role+'-literal_zero_direct_difference')/'after.wkb').read_bytes());moves={tuple(r['before']):tuple(r['after'])for r in rr['intersection_moves']};scopes=[];boundary_rows=[]
  for ring in rings(rawafter):
   for i,v in enumerate(ring[:-1]):
    v=tuple(v)
    if v not in moves:continue
    a=tuple(ring[i-1]if i else ring[-2]);z=tuple(ring[i+1]);m=moves[v];triangles=[Polygon([a,v,m]),Polygon([v,z,m])];scope=lit(N.bounded_buffer(unary_union(triangles),.0001));sf=O/(role+'-intersection-'+str(len(boundary_rows))+'-owned-boundary-redesign-scope.wkb');save(sf,scope);scopes.append(scope)
    boundary_rows.append({'literal_raw_intersection':v,'native_inward_replacement':m,'unchanged_incoming_vertex':a,'unchanged_outgoing_vertex':z,'original_controlling_edge':edgeby[v]['nearest_parent_edge'],'original_edge_lattice':edgeby[v],'actual_two_local_wedges':[sm(t)for t in triangles],'scope':sm(scope),'scope_file':str(sf.resolve()),'scope_SHA256':sha(sf),'scope_reserve_mm':.0001,'no_original_native_copper_or_boundary_trim':True})
  removed=before.difference(after);extra=removed.difference(cut);outside=removed.difference(unary_union([cut,*scopes]));save(O/(role+'-actual-boundary-redesign-negative.wkb'),extra);save(O/(role+'-raw-loss-outside-all-nominated-scopes.wkb'),outside);assert outside.is_empty,('loss outside exact controlling boundary redesign',role,sm(outside));nm=set_precision(after,1e-6,mode='pointwise');assert nm.wkb==after.wkb;changed[role]=nm;extra_cuts.append(extra);all_scopes+=scopes
  rows.append({'UUID':FG,'role':role,'before_SHA256':dg(before),'after_SHA256':dg(after),'removed_mm2':removed.area,'primary_mask_SHA256':dg(cut),'extra_negative':sm(extra),'negative_wedges':boundary_rows,'strict_literal_no_gain':True,'strict_literal_loss_outside_nominated_primary_and_boundary_scopes_EMPTY':True,'only_new_cut_intersections_changed_all_other_vertex_tokens_exact':True,'earlier_R525_R527_R529_R533_failures_retained':True})
 actual=copy.deepcopy(c);fillops=[];scope_union=lit(unary_union([lit(x)for x in all_scopes]))
 for z in actual['zones']:
  if z['uuid']==OLD or layer not in z['fills']or z['net']==raw:continue
  poly=unary_union(L.poly(z['fills'][layer]));req=max(float(z['clearance_mm']),.15 if h['domains_normalized'][L.norm(z['net'])]==h['domains_normalized'][L.norm(raw)]else .6)+.0251;mask=lit(N.bounded_buffer(new['zone_outline_shape'],req))
  if not poly.intersects(mask):continue
  assert z['uuid']==FG,('unexpected current foreign fill',z['uuid'],z['net']);assert mask.wkb==cut.wkb;before_records=copy.deepcopy(z['fills'][layer]);after_records,proof=IM.subtract(before_records,[mask,extra_cuts[0]],O,'FG-only-new-positive-and-boundary-redesign');afterfill=unary_union(L.poly(after_records));gain=afterfill.difference(poly);assert gain.is_empty;removed=poly.difference(afterfill);outside=removed.difference(scope_union);save(O/'actual-filled-loss-outside-all-actual-owner-scopes.wkb',outside)
  # Every helper negative must be independently localized to this same
  # controlling edge/corridor authority, with no remote scope expansion.
  reserve_scopes=[]
  for r in proof['per_original_record_operations']:
   for op in r.get('reserves',[]):
    rmask=from_wkb(Path(op['reserve_file']).read_bytes());remote=rmask.difference(lit(N.bounded_buffer(scope_union,.0001)));assert remote.is_empty,('helper reserve beyond separately nominated local100nm extension',r['record'],sm(remote));reserve_scopes.append(rmask);op['separately_nominated_actual_cutter_corner_100nm_negative_scope']=True;op['strict_outside_parent_boundary_authority_plus100nm_EMPTY']=True
  individual_witnesses=[];outside=removed.difference(unary_union([scope_union,*reserve_scopes]));save(O/'raw-actual-filled-loss-outside-prior-boundary-helper-scopes.wkb',outside)
  for iteration in range(16):
   if outside.is_empty:break
   assert outside.difference(lit(N.bounded_buffer(scope_union,.0001))).is_empty,('actual negative beyond separately nominated local boundary extension',sm(outside))
   wf=O/('actual-filled-'+str(iteration)+'-raw-individual-local-negative-witness.wkb');save(wf,outside);wm=lit(N.bounded_buffer(outside,.0001));mf=O/('actual-filled-'+str(iteration)+'-explicit-individual100nm-negative-authority.wkb');save(mf,wm);reserve_scopes.append(wm);individual_witnesses.append({'raw_witness':sm(outside),'raw_file':str(wf.resolve()),'raw_SHA256':sha(wf),'explicit_negative_scope':sm(wm),'scope_file':str(mf.resolve()),'scope_SHA256':sha(mf),'local_scope_reserve_mm':.0001,'actual_geometry_unchanged_by_witness_binding':True,'no_area_length_or_boundary_waiver':True});outside=removed.difference(unary_union([scope_union,*reserve_scopes]))
  save(O/'actual-filled-loss-outside-all-individual-declared-scopes.wkb',outside);assert outside.is_empty,('actual current fill loss outside complete individually bound scopes',sm(outside));z['fills'][layer]=after_records;fillops.append({'UUID':FG,'raw_net':z['net'],'layer':layer,'before_records':before_records,'after_records':after_records,'normal_guard_mask':mask,'exact_owned_boundary_negative':extra_cuts[0],'per_record_proof':proof,'explicit_individual_actual_negative_witnesses':individual_witnesses,'before_SHA256':dg(poly),'after_SHA256':dg(afterfill),'strict_literal_no_gain':True,'strict_literal_loss_outside_owner_scopes_EMPTY':True,'removed_mm2':removed.area});print('R541 current fill removed',removed.area,flush=True)
 assert len(fillops)==1
 native={k:new[k]for k in('uuid','net','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')};native['prospective_not_native']=True;native['fills']={layer:IM.records(lit(new['shape']))};actual['zones']=[z for z in actual['zones']if z['uuid']!=OLD]+[native];newq=[changed if z['uuid']==FG else z for z in q if z['uuid']!=OLD]+[new]
 for key in('integer_nm_physical_rings','integer_nm_native_outline_rings'):changed.pop(key,None)
 assert{k:v for k,v in actual.items()if k!='zones'}=={k:v for k,v in c.items()if k!='zones'}
 for z in actual['zones']:
  if z['uuid']not in(FG,uid):assert z==next(x for x in c['zones']if x['uuid']==z['uuid'])
 for z in newq:
  if z['uuid']not in(FG,uid):assert z==next(x for x in q if x['uuid']==z['uuid'])
 b['restored_generated_grid_UUIDs']=sorted(x['uuid']for x in newq);states=[r for r in b['generated_precision_state_ledger']if r['new_generated_UUID']!=OLD]
 for row in states:
  if row['new_generated_UUID']==FG:row['unchanged_WKB_SHA256']=dg(changed[row['role']])
 states.extend({'new_generated_UUID':uid,'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':dg(new[role])}for role in('shape','zone_outline_shape'));b['generated_precision_state_ledger']=states;b['FIELD5_owned_boundary_redesign_r541']={'exact_parent_SHA256':sha(M),'positive_UID':uid,'withdraw_only_failed_61cb':OLD,'own_new_FG_UID':FG,'original_IO3_all_roles_filled_records_exact':True,'required_guard_mm':.175,'constructor_reserve_mm':.0001,'full_FIELD5_A':.341130981,'routing_reservation_A':.36,'full_FA_source_return_A':4.58442937244,'former_failed_In4_halo_restoration':'NOT_APPLIED_ALL_RAW_FAILURES_BOUND','native_same_raw_field5_In2_union':'OPEN','adopted':False};MS.restore_bound_field_current_precision_states(b,newq)
 put(O/'owned-controlling-boundary-two-role-redesign-ledger.json',rows);put(O/'only-new-positive-canonicalization.json',canonical);packet={'exact_parent_model_SHA256':sha(M),'only_new_positive_q':new,'only_new_actual_zone':native,'only_owned_FG_role_operation':{'before_q':ground,'after_q':changed,'normal_mask':cut,'explicit_negative_boundary_scopes':all_scopes[1:],'two_role_ledgers':rows},'only_owned_FG_actual_fill_operations':fillops,'withdraw_only_old_q':old,'withdraw_only_old_actual_zone':next(z for z in c['zones']if z['uuid']==OLD),'new_tracks':[],'new_vias':[],'original_native_Cu_deletes':[]};(O/'only-one-positive-one-owned-boundary-negative-and-preview-withdrawal.pkl').write_bytes(pickle.dumps(packet,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,newq,actual),protocol=5))
 put(O/'receipt.json',{'status':'OWNED_BOUNDARY_REDESIGN_STRICT_NEGATIVE_CONSTRUCTION_PASS_ALL_SOURCE_CONTACT_REFERENCE_CURRENT_NATIVE_OPEN','model_SHA256':sha(O/'model.pkl'),'packet_SHA256':sha(O/'only-one-positive-one-owned-boundary-negative-and-preview-withdrawal.pkl'),'exact_parent_SHA256':sha(M),'R523_positive_nominee_SHA256':sha(A/'only-one-new-FIELD5-actual-source-port-nominee.pkl'),'R535_owned_intersection_splice_receipt_SHA256':sha(S/'receipt.json'),'new_positive_UID':uid,'withdraw_only_failed_In4_UID':OLD,'only_owned_FG_negative_UID':FG,'role_rows':rows,'actual_current_filled_scope_count':1,'all_original_IO3_fill_and_unrelated_native_Cu_holes_pads_q_roles_settings_arrays_exact':True,'all_three_ground_full_signed_current_source_contact_reference_mesh_loop_drop_thermal_native':'OPEN','FIELD5_full_load_A':.341130981,'FIELD5_routing_reservation_A':.36,'FAG_source_return_full_A':4.58442937244,'inherited_R15528refs_CORE_ROOT42_planner_FAIL_and_R46513refs_383IO3FAIL_not_waived':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start});print('R541',sha(O/'receipt.json'),'model',sha(O/'model.pkl'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_model_or_adoption':True})
  raise
