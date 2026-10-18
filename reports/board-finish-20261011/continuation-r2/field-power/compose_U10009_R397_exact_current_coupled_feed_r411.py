"""Materialize only the U10009 coupled proposal on immutable R155 current.

The prior fifteen VS tracks have exact owned deletions. Every new primitive
receives ordinary foreign antipads; only newly owned foreign planes can be
withdrawn. No original zone definition, native Cu or unrelated role is reset.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,time,copy,traceback
from pathlib import Path
from shapely import set_precision
from shapely.geometry import LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_aux_exact_raw as A
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as N
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as MS
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
B=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155'
P=H/'U10009-retained-lower-VS-ordinary-barrel-coupled-nomination-r397'
O=H/'U10009-R397-exact-R155-coupled-source-feed-construction-r411'
ZERO={('ed7b6af5-93e5-5f20-8977-d10ca721564d','shape'),('d8d8bdad-3845-5659-b172-4d0e231cdadc','shape')}
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def dg(s):return A.C.sha(s.wkb)
def literal(s):
 x=set_precision(s,0);assert x.wkb==s.wkb;return x
def main():
 assert not O.exists();O.mkdir();started=time.monotonic()
 assert sha(B/'model.pkl')=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 assert sha(P/'only-coupled-ordinary-and-inner-plane-nominee.pkl')=='319a00281919278dfd8ce0a7f123215925899971ca4f22d5bff83e5f9d9dec86'
 g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());MS.restore_bound_field_current_precision_states(b,z);b=copy.deepcopy(b);prior_z=copy.deepcopy(z);MS.restore_bound_field_current_precision_states(b,prior_z)
 d=pickle.loads((P/'only-coupled-ordinary-and-inner-plane-nominee.pkl').read_bytes());removed=set(d['removed']);tm={t['uuid']:t for t in h['tracks']}
 assert {t['uuid']:t for t in d['exact_original_tracks']}=={u:tm[u]for u in removed};assert len(removed)==15
 nt=d['tracks'];nv=d['vias'];new=d['planes'];assert len(nv)==len(new)==1;plane=new[0]
 for role in ('shape','zone_outline_shape'):
  w=plane[role].wkb;plane[role]=set_precision(plane[role],1e-6,mode='pointwise');assert w==plane[role].wkb
 assert not ({t['uuid']for t in nt}&set(tm));assert nv[0]['uuid']not in{v['uuid']for v in h['vias']}
 h={**h,'tracks':[t for t in h['tracks']if t['uuid']not in removed]+nt,'vias':h['vias']+nv};z.append(plane);cache={};roleops=[]
 def masks(net,layer,local,physical=True):
  rows=[]
  for v in nv:
   same=L.norm(net)==L.norm(v['net'])
   if same and not physical:continue
   radius=v['drill']/2+.00000002 if same else max(v['drill']/2+.275+.0001,v['d']/2+max(local,G.gap(h,net,v['net']))+.025+.0001)
   key=('via',v['uuid'],radius)
   if key not in cache:cache[key]=literal(N.bounded_disk(v,radius))
   rows.append((v['uuid'],'same_raw_physical_drill_only'if same else'new_ordinary_foreign_antipad',cache[key],radius))
  for t in nt:
   if t['layer']!=layer or L.norm(net)==L.norm(t['net']):continue
   radius=t['w']/2+max(local,G.gap(h,net,t['net']))+.025+.0001;key=('track',t['uuid'],radius)
   if key not in cache:cache[key]=literal(N.bounded_buffer(LineString([t['a'],t['b']]),radius))
   rows.append((t['uuid'],'new_track_true_outward_guard',cache[key],radius))
  if plane['layer']==layer and L.norm(net)!=L.norm(plane['net']):
   radius=max(local,plane['clearance_mm'],G.gap(h,net,plane['net']))+.025+.0001;key=('plane',plane['uuid'],radius)
   if key not in cache:cache[key]=literal(N.bounded_buffer(plane['zone_outline_shape'],radius))
   rows.append((plane['uuid'],'new_positive_plane_guard',cache[key],radius))
  return rows
 for q in z[:-1]:
  for role in ('shape','zone_outline_shape'):
   before=literal(q[role]);mr=[r for r in masks(q['net'],q['layer'],q.get('clearance_mm',.15),role=='shape')if r[2].intersects(before)]
   if not mr:continue
   mask=unary_union([r[2]for r in mr]);remain=before.difference(mask);reserves=[]
   after=remain if(q['uuid'],role)in ZERO else set_precision(remain,1e-6,mode='pointwise')
   for i in range(32):
    gain=literal(after).difference(before)
    if gain.is_empty:break
    gf=O/(q['uuid']+'-'+role+'-'+str(i)+'-literal-gain.wkb');gf.write_bytes(gain.wkb);reserve=literal(N.bounded_buffer(gain,.0001));rf=O/(q['uuid']+'-'+role+'-'+str(i)+'-explicit-100nm-negative.wkb');rf.write_bytes(reserve.wkb)
    after=literal(after).difference(reserve);after=after if(q['uuid'],role)in ZERO else set_precision(after,1e-6,mode='pointwise');reserves.append({'gain_file':str(gf.resolve()),'gain_sha256':sha(gf),'negative_file':str(rf.resolve()),'negative_sha256':sha(rf)})
   else:raise AssertionError('owned literal subset did not converge')
   assert literal(after).difference(before).is_empty;q[role]=after;mf=O/(q['uuid']+'-'+role+'-new-U10009-only-mask.wkb');mf.write_bytes(mask.wkb)
   roleops.append({'UUID':q['uuid'],'role':role,'before_sha256':dg(before),'after_sha256':dg(after),'literal_gain_empty':True,'removed_mm2':before.difference(literal(after)).area,'mask_file':str(mf.resolve()),'mask_sha256':sha(mf),'primitive_rows':[{'UUID':r[0],'kind':r[1],'radius_mm':r[3],'WKB_sha256':dg(r[2])}for r in mr],'explicit_canonical_negative_reserves':reserves})
 previous={q['uuid']:q for q in prior_z};current={q['uuid']:q for q in z};actual=[];fillops=[]
 for old in c['zones']:
  qq=copy.deepcopy(old)
  for layer,recs in old['fills'].items():
   before=unary_union(L.poly(recs));mr=[r for r in masks(old['net'],layer,old.get('clearance_mm',.15))if r[2].intersects(before)];cut=[r[2]for r in mr]
   if old['uuid']in previous:
    wd=literal(previous[old['uuid']]['shape']).difference(literal(current[old['uuid']]['shape']))
    if not wd.is_empty:cut.append(wd)
   if not cut:continue
   rr,proof=IM.subtract(recs,cut,O,old['uuid']+'-'+layer+'-U10009-only-new-primitives');after=unary_union(L.poly(rr));assert after.difference(before).is_empty;qq['fills'][layer]=rr
   fillops.append({'UUID':old['uuid'],'layer':layer,'before_sha256':dg(before),'after_sha256':dg(after),'removed_mm2':before.difference(after).area,'literal_gain_empty':True,'new_primitive_masks':[{'UUID':r[0],'kind':r[1],'radius_mm':r[3],'WKB_sha256':dg(r[2])}for r in mr],'strict_per_record_operation':proof})
  actual.append(qq)
 actual.append({k:v for k,v in plane.items()if k not in('shape','zone_outline_shape')}|{'fills':{plane['layer']:IM.records(literal(plane['shape']))}});final={**h,'zones':actual};states=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   grid=0 if(q['uuid'],role)in ZERO else 1e-6;w=q[role].wkb;q[role]=set_precision(q[role],grid,mode='pointwise');assert q[role].wkb==w
   states.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':grid,'mode':'pointwise','unchanged_WKB_SHA256':dg(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=states;b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in z);b['U10009_R397_coupled_minimal']={'parent_model_sha256':sha(B/'model.pkl'),'nominee_packet_sha256':sha(P/'only-coupled-ordinary-and-inner-plane-nominee.pkl'),'exact_removed_VS_track_UUIDs':sorted(removed),'all_old_lower_VS_source_contacts':'MANDATORY_FULL_GATES_OPEN'};MS.restore_bound_field_current_precision_states(b,z)
 put(O/'only-new-owned-role-withdrawal-ledger.json',roleops);put(O/'only-local-actualfilled-new-primitive-negative-ledger.json',fillops);(O/'only-new-discrete-and-exact-old-delete.pkl').write_bytes(pickle.dumps({k:d[k]for k in('tracks','vias','removed','exact_original_tracks')},protocol=5));(O/'only-new-plane.pkl').write_bytes(pickle.dumps(new,protocol=5));(O/'only-changed-owned-roles.pkl').write_bytes(pickle.dumps([q for q in z[:-1]if any(q[r].wkb!=previous[q['uuid']][r].wkb for r in('shape','zone_outline_shape'))],protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,final),protocol=5))
 # Exact source relationships of both the original upper bank and removed
 # lower cycle are required, independent of nominal planner attachments.
 nets=[L.norm(plane['net']),L.norm(nt[0]['net'])];groups={}
 for net in nets:_,groups[net]=K.physical(final,net,K.hole_context(final))
 proot=K.root(groups[nets[0]],'U11004','17');vroot=K.root(groups[nets[1]],'U11017','1');pp={(r['ref'],str(r['pin']))for r in proot if r['kind']=='pad'};vp={(r['ref'],str(r['pin']))for r in vroot if r['kind']=='pad'};required=[('U10009',str(i))for i in(14,15,16,17,34,35,36,37)]+[('C10017','1')];missing=[p for p in required if p not in pp]
 put(O/'coupled-actual-source-targets.json',{'protected_required':required,'protected_missing':missing,'VDD_U10009_4_source_rooted':('U10009','4')in vp})
 (O/'actual-two-net-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));rec={'verdict':'U10009_COUPLED_CONSTRUCTION_SOURCE_TARGETS_PASS_FULL_GATES_OPEN'if not missing and('U10009','4')in vp else'U10009_COUPLED_CONSTRUCTION_SOURCE_TARGET_REPAIR_REQUIRED','parent_R155_sha256':sha(B/'model.pkl'),'model_sha256':sha(O/'model.pkl'),'new_track_count':len(nt),'new_via_count':len(nv),'exact_old_VS_track_deletes':len(removed),'new_plane_count':1,'owned_role_edits':len(roleops),'actualfilled_scopes':len(fillops),'protected_required_targets_missing':missing,'VDD_U10009_4_source_rooted':('U10009','4')in vp,'all109_lower_retained_keys_all_old_contacts_refs_full_signed_mesh_barrel_thermal_native':'OPEN_MANDATORY','rejected_R379_never_adopted':True,'inherited_parent28oldrefs_CORE93_ROOT42_planner_FAIL_OPEN_preserved':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'model_sha256':rec['model_sha256'],'targets_missing':missing,'VDD_source':rec['VDD_U10009_4_source_rooted']}),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc()})
  raise
