"""Withdraw only rejected FIELD5 In4; replay one In2 feed on exact current.

Old filled copper is restored ONLY from the immutable DIC262 record, ONLY
inside the withdrawn feed's former mask, and AFTER all retained sparse
guards and bound role withdrawals. Native source arrays are never snapped.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,copy,sys,time,traceback
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.geometry import LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for x in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/x))
import audit_aux_exact_raw as A
import contact_layout as L
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as N
import immutable_local_fill_subtraction_r254 as IM
import restore_SAFE_generated_precision_states_r168 as PS
import restore_field_current_mixed_precision_states_r366 as MS
import construct_T4_R7_sparse_R250_diagnostic_r261 as SB
from inventory import sha
B=H.parent/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262'
C=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155'
R=H/'REG7-native-support-minimal-current-delta-r312'
U=H/'U11025-exact-health-ground-native-owned-recipe-r350'
S=H.parent/'sbc-power/T4-R7-exact-sparse-owned-native-and-negative-fill-recipe-r273'
P=H/'FIELD5-inner-source-barrel-native-fill-retreat-replacement-nomination-r385'
O=H/'FIELD5-R385-minimal-R155-local-immutable-restoration-composition-r387'
OLD='61cb8179-7754-5031-bbea-0da464bf816f'
ED='ed7b6af5-93e5-5f20-8977-d10ca721564d'
ZERO={('ed7b6af5-93e5-5f20-8977-d10ca721564d','shape'),('d8d8bdad-3845-5659-b172-4d0e231cdadc','shape')}
def dg(s):return A.C.sha(s.wkb)
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def literal(s):
 x=set_precision(s,0);assert x.wkb==s.wkb;return x
def canon_subset(s,allowed,key):
 """Canonical boundary, exact literal allowed-set test, explicit reserves."""
 allowed=literal(allowed);a=set_precision(literal(s),1e-6,mode='pointwise');rows=[]
 for i in range(32):
  gain=literal(a).difference(allowed)
  if gain.is_empty:break
  reserve=literal(N.bounded_buffer(gain,.0001));gf=O/(key+'-'+str(i)+'-literal-gain.wkb');rf=O/(key+'-'+str(i)+'-explicit-100nm-negative.wkb');gf.write_bytes(gain.wkb);rf.write_bytes(reserve.wkb)
  a=set_precision(literal(a).difference(reserve),1e-6,mode='pointwise');rows.append({'iteration':i,'literal_gain_file':str(gf.resolve()),'gain_sha256':sha(gf),'gain_mm2':gain.area,'negative_reserve_file':str(rf.resolve()),'negative_reserve_sha256':sha(rf)})
 else:raise AssertionError(('canonical allowed-region failure',key))
 assert literal(a).difference(allowed).is_empty
 return a,rows
def main():
 assert not O.exists();O.mkdir();started=time.monotonic()
 assert sha(B/'model.pkl')=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'
 assert sha(C/'model.pkl')=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 assert sha(P/'receipt.json')=='0f2643dfb0b2dbd5628b1494c4df6f17155ef0bc5dee278332ed82d7e3cef40b'
 g0,h0,b0,z0,c0=pickle.loads((B/'model.pkl').read_bytes());PS.restore_bound_generated_precision_states(b0,z0)
 g,h,b,z,c=pickle.loads((C/'model.pkl').read_bytes());MS.restore_bound_field_current_precision_states(b,z);b=copy.deepcopy(b)
 prior_z=copy.deepcopy(z);MS.restore_bound_field_current_precision_states(b,prior_z)
 base={q['uuid']:q for q in z0};current={q['uuid']:q for q in prior_z};working={q['uuid']:q for q in z};assert OLD in current and ED in base
 rejected=current[OLD];new=pickle.loads((P/'one-new-field5-replacement-plane.pkl').read_bytes());assert len(new)==1;new=new[0]
 assert new['net']==rejected['net'] and new['layer']=='In2.Cu' and rejected['layer']=='In4.Cu'
 for role in ('shape','zone_outline_shape'):
  w=new[role].wkb;new[role]=set_precision(new[role],1e-6,mode='pointwise');assert w==new[role].wkb
 rd=pickle.loads((R/'new-REG-discrete.pkl').read_bytes());ud=pickle.loads((U/'proposed-discrete.pkl').read_bytes());sd=pickle.loads((S/'only-owned-new-discrete-and-four-exact-deletes.pkl').read_bytes())
 nt=rd['tracks']+ud['tracks'];nv=rd['vias']+ud['vias'];retained=[q for q in z if q['uuid']not in base and q['uuid']!=OLD];assert len(retained)==6
 nz=retained+[new];cache={};role_rows=[]
 oldtracks={t['uuid']:t for t in h0['tracks']};removed=set(oldtracks)-{t['uuid']for t in h['tracks']};added=[t for t in h['tracks']if t['uuid']not in oldtracks];av=[v for v in h['vias']if v['uuid']not in{v['uuid']for v in h0['vias']}]
 assert len(removed)==18 and len(added)==26 and len(av)==6
 assert {t['uuid']for t in added}=={t['uuid']for t in nt+sd['tracks']};assert {v['uuid']for v in av}=={v['uuid']for v in nv+sd['vias']}
 oldbody={}
 for net,layer in {(L.norm(oldtracks[u]['net']),oldtracks[u]['layer'])for u in sd['removed']}:
  oldbody[net,layer]=unary_union([SB.Z.bounded_buffer(LineString([oldtracks[u]['a'],oldtracks[u]['b']]),oldtracks[u]['w']/2)for u in sd['removed']if(L.norm(oldtracks[u]['net']),oldtracks[u]['layer'])==(net,layer)])
 def zone_mask(q,net,local,layer):
  if q['layer']!=layer or L.norm(q['net'])==L.norm(net):return None
  gap=max(G.gap(h,net,q['net']),local,q.get('clearance_mm',.15))+.025;key=('plane',q['uuid'],gap)
  if key not in cache:cache[key]=literal(N.bounded_buffer(q['zone_outline_shape'],gap))
  return cache[key]
 def masks(net,local,layer,physical=True):
  out=[]
  for v in nv:
   same=L.norm(net)==L.norm(v['net'])
   if same and not physical:continue
   radius=v['drill']/2 if same else max(v['drill']/2+.275+.0001,v['d']/2+max(G.gap(h,net,v['net']),local)+.025+.0001);key=('via',v['uuid'],radius)
   if key not in cache:cache[key]=literal(N.bounded_disk(v,radius))
   out.append((v['uuid'],'same_raw_physical_drill_only'if same else'new_foreign_via_guard',cache[key]))
  for t in nt:
   if t['layer']!=layer or L.norm(t['net'])==L.norm(net):continue
   radius=t['w']/2+max(G.gap(h,net,t['net']),local)+.025+.0001;key=('track',t['uuid'],radius)
   if key not in cache:cache[key]=literal(N.bounded_buffer(LineString([t['a'],t['b']]),radius))
   out.append((t['uuid'],'retained_REG_U25_track_guard',cache[key]))
  for q in nz:
   mask=zone_mask(q,net,local,layer)
   if mask is not None:out.append((q['uuid'],'new_REG_intended_outline_guard',mask))
  out += [(r['new_UUID'],r['kind'],r['shape'])for r in SB.cutters(sd['tracks']+sd['vias'],oldbody,net,layer,local,h,not physical)]
  return out
 # Restore ONLY the former rejected plane halo in the ED owned roles.
 # Every admitted point must also lie in the immutable pre-REG role and
 # outside all current retained primitive/frozen local guards.
 ed=working[ED];localcuts=pickle.loads((R/'only-two-local-owned-correction-cutters.pkl').read_bytes())
 oldmask=zone_mask(rejected,ed['net'],ed.get('clearance_mm',.15),ed['layer']);assert oldmask is not None
 for role in ('shape','zone_outline_shape'):
  prior=ed[role];orig=literal(base[ED][role]);ms=[r for r in masks(ed['net'],ed.get('clearance_mm',.15),ed['layer'],role=='shape')if r[2].intersects(orig)];cc=[r[2]for r in ms]+[literal(x['shape'])for x in localcuts if x['owned_UUID']==ED]
  allowed=orig.difference(unary_union(cc));restore=allowed.intersection(oldmask).difference(literal(prior));union=literal(prior).union(restore)
  if role=='shape':after=union;reserves=[]
  else:after,reserves=canon_subset(union,union,'ED-'+role+'-local-restore')
  gain=literal(after).difference(literal(prior));assert gain.difference(oldmask).is_empty and gain.difference(orig).is_empty
  for title,sh in [('former_rejected_mask',oldmask),('exact_restore_only',gain)]:f=O/(ED+'-'+role+'-'+title+'.wkb');f.write_bytes(sh.wkb)
  ed[role]=after;role_rows.append({'UUID':ED,'role':role,'operation':'immutable_role_restore_inside_withdrawn_plane_mask_only','before_sha256':dg(prior),'after_sha256':dg(after),'immutable_before_sha256':dg(orig),'restored_mm2':gain.area,'restore_inside_original_and_old_rejected_mask':True,'other_retained_guard_UUIDs':[r[0]for r in ms],'explicit_canonical_negative_reserves':reserves})
 # New In2 guard cuts only truly intersecting current owned foreign roles.
 for q in z:
  if q['uuid']==OLD:continue
  mask=zone_mask(new,q['net'],q.get('clearance_mm',.15),q['layer'])
  if mask is None:continue
  for role in ('shape','zone_outline_shape'):
   prior=q[role]
   if not mask.intersects(prior):continue
   remain=literal(prior).difference(mask)
   if (q['uuid'],role)in ZERO:after=remain;reserves=[]
   else:after,reserves=canon_subset(remain,literal(prior),q['uuid']+'-'+role+'-new-feed-cut')
   assert literal(after).difference(literal(prior)).is_empty;q[role]=after;f=O/(q['uuid']+'-'+role+'-new-feed-only-cut.wkb');f.write_bytes(mask.wkb)
   role_rows.append({'UUID':q['uuid'],'role':role,'operation':'only_new_FIELD5_In2_guard_remove_only','before_sha256':dg(prior),'after_sha256':dg(after),'removed_mm2':literal(prior).difference(literal(after)).area,'literal_gain_empty':True,'cut_file':str(f.resolve()),'cut_sha256':sha(f),'explicit_canonical_negative_reserves':reserves})
 # Physical owned ED stays inside its final native intended boundary; no
 # physical point is granted by the serializer or the old local vertex fix.
 prior=ed['shape'];ed['shape']=literal(prior).intersection(literal(ed['zone_outline_shape']))
 role_rows.append({'UUID':ED,'role':'shape','operation':'physical_inside_new_native_intended_only','before_sha256':dg(prior),'after_sha256':dg(ed['shape']),'literal_gain_empty':True,'removed_mm2':literal(prior).difference(ed['shape']).area})
 z=[new if q['uuid']==OLD else q for q in z];zm={q['uuid']:q for q in z};immutablefills={q['uuid']:q for q in c0['zones']};actual=[];filled=[]
 for old in c['zones']:
  if old['uuid']==OLD:continue
  qq=copy.deepcopy(old)
  for layer,recs in old['fills'].items():
   body=unary_union(L.poly(recs));former=zone_mask(rejected,old['net'],old.get('clearance_mm',.15),layer);fresh=zone_mask(new,old['net'],old.get('clearance_mm',.15),layer)
   origzone=immutablefills.get(old['uuid']);restorepieces=[];restoreproof=[]
   if former is not None and origzone is not None and layer in origzone['fills']:
    originalrecs=origzone['fills'][layer];origparts=L.poly(originalrecs);origwhole=unary_union(origparts)
    if former.intersects(origwhole):
     allmask=[r[2]for r in masks(old['net'],old.get('clearance_mm',.15),layer,True)if r[2].intersects(origwhole)]
     if old['uuid']in base:
      withdrawal=literal(base[old['uuid']]['shape']).difference(literal(zm[old['uuid']]['shape']))
      if not withdrawal.is_empty:allmask.append(withdrawal)
     mask=unary_union(allmask)
     for idx,part in enumerate(origparts):
      if not former.intersects(part):continue
      support=literal(part).intersection(former).difference(mask);restorepieces.extend(IM.records(support));restoreproof.append({'immutable_original_record':idx,'immutable_original_WKB_sha256':dg(part),'only_former_rejected_guard_support_WKB_sha256':dg(support),'support_mm2':support.area,'within_original_empty_gain':support.difference(literal(part)).is_empty})
   restorebody=unary_union(L.poly(restorepieces)) if restorepieces else unary_union([])
   additions=restorebody.difference(body)
   cc=[]
   if fresh is not None and fresh.intersects(body.union(restorebody)):cc.append(fresh)
   # Exact newly changed owned-role withdrawals only; retain all inherited
   # current filled-outside-role evidence instead of globally clipping.
   if old['uuid']in current and old['uuid']in zm and old['uuid']!=ED:
    prior=current[old['uuid']]['shape'];after=zm[old['uuid']]['shape'];wd=literal(prior).difference(literal(after))
    if not wd.is_empty:cc.append(wd)
   if not cc and additions.is_empty:continue
   # Preserve unrelated current record arrays. Existing records receive
   # only new masks; newly restored records receive the identical masks.
   rr,proof=IM.subtract(recs+restorepieces,cc or [unary_union([])],O,old['uuid']+'-'+layer+'-local-sparse-replay');after=unary_union(L.poly(rr));gained=after.difference(body)
   if not gained.difference(restorebody).is_empty:
    bad=gained.difference(restorebody);f=O/(old['uuid']+'-'+layer+'-unbound-gain.wkb');f.write_bytes(bad.wkb);raise AssertionError(('literal restoration scope gain',old['uuid'],layer,bad.area))
   if origzone is not None and layer in origzone['fills']:
    baseline=unary_union(L.poly(origzone['fills'][layer]));assert after.difference(baseline).is_empty,('immutable actual record gain',old['uuid'],layer)
   qq['fills'][layer]=rr;filled.append({'UUID':old['uuid'],'layer':layer,'former_rejected_mask_sha256':dg(former)if former is not None else None,'new_feed_mask_sha256':dg(fresh)if fresh is not None else None,'before_literal_WKB_sha256':dg(body),'after_literal_WKB_sha256':dg(after),'actual_restored_mm2':gained.area,'only_immutable_old_mask_support_restored':True,'immutable_original_record_supports':restoreproof,'strict_current_plus_bound_restore_record_proof':proof})
  actual.append(qq)
 actual.append({k:v for k,v in new.items()if k not in ('shape','zone_outline_shape')}|{'fills':{new['layer']:IM.records(literal(new['shape']))}})
 final={**h,'zones':actual};states=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   grid=0 if(q['uuid'],role)in ZERO else 1e-6;w=q[role].wkb;q[role]=set_precision(q[role],grid,mode='pointwise');assert w==q[role].wkb;states.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':grid,'mode':'pointwise','unchanged_WKB_SHA256':dg(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=states;b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in z);b['FIELD5_R385_minimal_current_composition']={'exact_current_R155_model_sha256':sha(C/'model.pkl'),'immutable_DIC262_record_sha256':sha(B/'model.pkl'),'R385_receipt_sha256':sha(P/'receipt.json'),'withdrawn_only_NEW_UUID':OLD,'new_only_UUID':new['uuid'],'no_discrete_changes':True,'restore_only_bound_original_record_within_rejected_guard':True,'all_unrelated_current_roles_retained':True,'R155_187_intended_only_correction_retained':True,'source_reference_current_native':'OPEN'}
 MS.restore_bound_field_current_precision_states(b,z)
 put(O/'only-owned-role-local-operation-ledger.json',role_rows);put(O/'only-local-current-filled-operation-ledger.json',filled);put(O/'exhaustive-mixed-precision-state-ledger.json',states)
 (O/'only-new-plane.pkl').write_bytes(pickle.dumps([new],protocol=5));(O/'only-changed-existing-owned-roles.pkl').write_bytes(pickle.dumps([q for q in z if q['uuid']in current and any(q[r].wkb!=current[q['uuid']][r].wkb for r in ('shape','zone_outline_shape'))],protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,final),protocol=5))
 receipt={'verdict':'EXPLORATORY_MINIMAL_R155_FIELD5_IN4_WITHDRAWAL_IN2_REPLACEMENT_CONSTRUCTOR_COMPLETE_FULL_GATES_OPEN','current_R155_sha256':sha(C/'model.pkl'),'immutable_DIC262_sha256':sha(B/'model.pkl'),'R385_nomination_sha256':sha(P/'receipt.json'),'only_withdrawn_new_plane':OLD,'only_added_plane':new['uuid'],'discrete_and_original_source_and_native_outline_rule_changes':0,'owned_role_operations':len(role_rows),'actual_filled_scopes_changed':len(filled),'model_sha256':sha(O/'model.pkl'),'native_jobs':0,'adopted':False,'inherited_CORE_body_and_ROOT42_current_native_planner_FAIL_OPEN_retained':True,'all_contact_source_reference_true_geometry_current_and_native_gates':'OPEN','elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',receipt);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'model_sha256':receipt['model_sha256'],'filled_scopes':len(filled),'role_operations':len(role_rows)}),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
