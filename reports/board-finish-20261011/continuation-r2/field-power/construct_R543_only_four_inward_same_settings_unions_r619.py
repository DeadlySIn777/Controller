"""Compose only the declared overlapping new roles with explicit inward wedges.

Current filled records are retained individually, with only the exact named
owned-edge negatives replayed per record. No native or whole-board projection.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,time,copy,sys,traceback
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.geometry import Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('coupled-recovery','sbc-power'):sys.path.insert(0,str(H.parent/d))
import restore_field_current_mixed_precision_states_r366 as MS
import guarded_power_projection_r44 as Z
import immutable_local_fill_subtraction_r254 as IM
import contact_layout as L
OUT=H/'R543-only-four-current-inward-same-nine-settings-unions-r619'
M=H/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl'
D=H/'R543-overlap-exact-inward-intersection-native-splice-diagnostic-r617'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hs(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic()
 assert sha(M)=='474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416'
 assert sha(D/'receipt.json')=='1af065a702b8f29b14aa47fb9fc16d95eebba9cd5dc40a6bfd9a7e7ad1df139f'
 g,h,b,qs,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,qs)
 pk=D/'only-four-exact-member-raw-integer-union-candidates-NOT_MODEL.pkl';plans=pickle.loads(pk.read_bytes());by={q['uuid']:q for q in qs};actualby={q['uuid']:q for q in c['zones']};outq=[];withdraw=set();replacements=[];rows=[];ops=[]
 for i,plan in enumerate(plans):
  members=plan['exact_before_members'];new=copy.deepcopy(plan['raw_integer_proposed_q_NOT_ADOPTED']);uids=[q['uuid']for q in members];withdraw.update(uids);profile=plan['cluster']['nine_setting_owner_authority'];role_rows=[]
  for a in members:
   current=by[a['uuid']];assert current.keys()==a.keys()
   assert all(current[k].wkb==a[k].wkb if k in('shape','zone_outline_shape')else current[k]==a[k]for k in current)
  for role in ('shape','zone_outline_shape'):
   original=unary_union([zero(a[role])for a in members]);after=zero(new[role]);gain=after.difference(original);loss=original.difference(after)
   assert gain.is_empty,('literal union gain remains',i,role,ds(gain))
   led=json.loads((D/f'cluster-{i}-{role}-exact-new-intersection-inward-ledger.json').read_bytes());wedges=[];wedgerows=[]
   for j,row in enumerate(led):
    v=row['literal_intersection_mm'];n=row['new_integer_mm'];prev=row['incoming_exact_old_edge_mm'][0];nxt=row['outgoing_exact_old_edge_mm'][1];triangles=[Polygon([prev,v,n]),Polygon([v,nxt,n])]
    for side,t in enumerate(triangles):
     assert t.is_valid and not t.is_empty;mask=zero(Z.bounded_buffer(t,.0001));f=OUT/f'cluster-{i}-{role}-intersection-{j}-edge-{side}-named-negative-wedge.wkb';f.write_bytes(mask.wkb);wedges.append(mask);wedgerows.append({'intersection_index':j,'edge_side':side,'exact_old_edge_mm':row['incoming_exact_old_edge_mm']if side==0 else row['outgoing_exact_old_edge_mm'],'new_integer_vertex_mm':n,'primary_exact_inward_triangle':ds(t),'explicit100nm_owned_edge_scope':ds(mask),'scope_file':str(f.resolve()),'scope_SHA256':sha(f),'no_other_vertex_or_original_native_change':True})
   scope=unary_union(wedges);outside=loss.difference(scope);f=OUT/f'cluster-{i}-{role}-loss-outside-exact-named-wedge-scopes.wkb';f.write_bytes(outside.wkb)
   assert outside.is_empty,('integer inward loss outside named edge scopes',i,role,ds(outside))
   tag=set_precision(after,1e-6,mode='pointwise');assert tag.wkb==after.wkb,('tag restoration changes tokens',i,role);new[role]=tag
   role_rows.append({'role':role,'before_member_WKBs':{a['uuid']:hs(a[role])for a in members},'literal_before_union':ds(original),'new_role':ds(after),'literal_gain_EMPTY':True,'exact_removed_owned_Cu':ds(loss),'loss_outside_explicit_old_edge_wedge_scopes_EMPTY':True,'wedge_rows':wedgerows,'scope':ds(scope)})
  # Physical holes remain separate from source-containing native intent.
  outside_intent=zero(new['shape']).difference(zero(new['zone_outline_shape']));(OUT/f'cluster-{i}-physical-outside-intended.wkb').write_bytes(outside_intent.wkb);assert outside_intent.is_empty,('physical outside native intention',i,ds(outside_intent))
  mapping={'local_clearance_mm':'clearance_mm'}
  for name,value in profile.items():
   field=mapping.get(name,name)
   if field in new:assert new[field]==value,('changed declared native profile',i,field,new[field],value)
   new[field]=value
  layer=new['layer'];allfill=[];memberops=[];loss=unary_union([zero(a['shape'])for a in members]).difference(zero(new['shape']))
  for member in members:
   z=actualby[member['uuid']];assert z.get('prospective_not_native')and set(z['fills'])=={layer}
   rs=z['fills'][layer];rr,proof=IM.subtract(rs,[loss],OUT,f'cluster-{i}-{member["uuid"]}')
   old=unary_union(L.poly(rs));final=unary_union(L.poly(rr));gain=final.difference(old);removed=old.difference(final);scope=unary_union([Polygon()]+[zero(Z.bounded_buffer(loss,.0001))])
   # Every extra per-record negative is separately declared by IM and must
   # stay within the already named old-edge neighborhood.
   for step in proof['per_original_record_operations']:
    for r in step.get('reserves',[]):
     from shapely import from_wkb
     mask=from_wkb(Path(r['reserve_file']).read_bytes());assert mask.difference(unary_union([zero(Z.bounded_buffer(loss,.0002))])).is_empty,('nonlocal current record reserve',i,member['uuid'],r)
     scope=unary_union([scope,mask])
   outside=removed.difference(scope);(OUT/f'cluster-{i}-{member["uuid"]}-actual-loss-outside-scope.wkb').write_bytes(outside.wkb)
   assert gain.is_empty and outside.is_empty,('current fill gain/nonlocal negative',i,member['uuid'],ds(gain),ds(outside))
   memberops.append({'old_UUID':member['uuid'],'before_records':copy.deepcopy(rs),'after_records':rr,'immutable_per_record_proof':proof,'literal_gain_EMPTY':True,'actual_removed':ds(removed),'outside_local_named_scope_EMPTY':True});allfill+=rr
  header=copy.deepcopy(actualby[uids[0]]);header['uuid']=new['uuid'];header['name']=new['label'];header['fills']={layer:allfill};header['prospective_not_native']=True
  for name,value in profile.items():header[mapping.get(name,name)]=value
  outq.append(new);replacements.append(header);ops.append({'members_before_UUIDs':uids,'exact_before_q':members,'new_q':new,'new_actual_zone':header,'actual_current_record_operations':memberops})
  rows.append({'index':i,'new_UUID':new['uuid'],'members':uids,'raw_net':new['net'],'layer':layer,'all_nine_profile_authority':profile,'role_rows':role_rows,'physical_within_intended':True,'current_records_concatenated_only_after_local_negative_replay_no_global_union':True})
 finalq=[q for q in qs if q['uuid']not in withdraw]+outq;actual={**c,'zones':[z for z in c['zones']if z['uuid']not in withdraw]+replacements}
 assert{k:v for k,v in actual.items()if k!='zones'}=={k:v for k,v in c.items()if k!='zones'}
 for q in finalq:
  if q['uuid']in by:assert q==by[q['uuid']]
 for z in actual['zones']:
  if z['uuid']in actualby:assert z==actualby[z['uuid']]
 b=copy.deepcopy(b);b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in finalq);b['generated_precision_state_ledger']=[{'new_generated_UUID':q['uuid'],'role':role,'grid_mm':0 if(q['uuid'],role)in MS.ZERO else 1e-6,'mode':'pointwise','unchanged_WKB_SHA256':hs(q[role])}for q in finalq for role in ('shape','zone_outline_shape')]
 ledger=OUT/'four-exact-inward-owned-edge-union-and-current-record-ledger.json';put(ledger,rows);b['native_overlap_only_R543_four_clusters_r619']={'parent_model_SHA256':sha(M),'current_R601_plan_SHA256':'4667e4a3af868d7a3093714187da7292466638682978b04be541ad0980d0dcbb','ledger_file':str(ledger.resolve()),'ledger_SHA256':sha(ledger),'raw_R611_R615_FAILs_preserved':True,'full_actual_contact_source_reference_current_native':'OPEN','native_overlap_errors_NOT_YET_REMEASURED':8}
 MS.restore_bound_field_current_precision_states(b,finalq);packet=OUT/'only-four-current-member-to-inward-union-and-local-current-record-operations.pkl';packet.write_bytes(pickle.dumps(ops,protocol=5));mp=OUT/'model.pkl';mp.write_bytes(pickle.dumps((g,h,b,finalq,actual),protocol=5))
 put(OUT/'receipt.json',{'status':'FOUR_MINIMAL_SAME_NINE_SETTINGS_OWNED_UNIONS_NEGATIVE_ONLY_CONSTRUCTED_SOURCE_REFERENCE_NATIVE_OPEN','parent_model_SHA256':sha(M),'model_SHA256':sha(mp),'packet_SHA256':sha(packet),'ledger_SHA256':sha(ledger),'old_q_count':len(qs),'new_q_count':len(finalq),'withdraw_only_owned_members':sorted(withdraw),'new_union_count':len(outq),'all_untouched_q_roles_settings_and_current_record_arrays_exact':True,'all_original_native_discrete_Cu_FP_holes_outlines_rules_sources_exact':True,'all_gained_Cu_EMPTY_and_losses_bound_to_explicit_named_own_old_edges':True,'no_area_waiver_or_global_regrid':True,'raw_eight_native_errors_and_parent_reference_current_failures_retained':True,'fresh_contact_direct_source_reference_true_geometry_native_fill_DRC':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st});print('R619',sha(OUT/'receipt.json'),'model',sha(mp),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if OUT.exists():put(OUT/'failure.json',{'status':'FAILED_MINIMAL_UNION_NO_PROMOTION','traceback':traceback.format_exc(),'no_native_or_live_source_edit':True})
  raise
