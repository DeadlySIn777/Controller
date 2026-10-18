"""Append only the frozen T4 owned delta; pending R7 roles stay excluded."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,copy,sys,time
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for x in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/x))
import audit_aux_exact_raw as A
import contact_layout as L
import immutable_local_fill_subtraction_r254 as IM
import construct_T4_R7_sparse_R250_diagnostic_r261 as SB
from inventory import sha
O=H/'REG-U25-corrected-DIC262-plus-only-T4-current-composition-r361'
B=H/'REG-U25-corrected-DIC262-sparse-current-composition-r359'
S=H.parent/'sbc-power/T4-R7-exact-sparse-owned-native-and-negative-fill-recipe-r268'
T=H.parent/'sbc-power/T4-duplicate-CORE5-fullwidth-detour-nominee-r256'
def write(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def dg(x):return A.C.sha(x.wkb)
def restore(b,z):
 m={q['uuid']:q for q in z}
 for r in b['generated_precision_state_ledger']:
  q=m[r['new_generated_UUID']];role=r['role'];assert dg(q[role])==r['unchanged_WKB_SHA256'];w=q[role].wkb;q[role]=set_precision(q[role],r['grid_mm'],mode=r['mode']);assert q[role].wkb==w
def main():
 assert not O.exists();O.mkdir();start=time.monotonic()
 assert sha(B/'model.pkl')=='52076bd44490e66b73dbd06994eea58a13f80152abdb7643cf2c3ae05e055739'
 assert sha(S/'receipt.json')=='a89ae74f70f1798d4fa3b5e831a5140829850b5b7d58abec65fa80a8eba5f467'
 assert sha(T/'proposed-discrete.pkl')=='9b8150b8daa7bff3b51e3381a1654d0629294dcdef41d2919555f63313fb9c8d'
 g,h0,b0,z0,c0=pickle.loads((B/'model.pkl').read_bytes());restore(b0,z0)
 h=copy.deepcopy(h0);b=copy.deepcopy(b0);z=copy.deepcopy(z0);restore(b,z)
 td=pickle.loads((T/'proposed-discrete.pkl').read_bytes());assert(len(td['tracks']),len(td['vias']),len(td['removed']))==(7,0,2)
 sd=pickle.loads((S/'only-owned-new-discrete-and-four-exact-deletes.pkl').read_bytes())
 assert {r['uuid']:r for r in td['tracks']}=={r['uuid']:r for r in sd['tracks'] if r['uuid'] in {t['uuid']for t in td['tracks']}}
 raw=A.read(H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb');iv=A.C.inventory(raw);native=A.N.SourceNets(raw)
 old={t['uuid']:t for t in h['tracks']};rows=[]
 for r in json.loads((S/'exact-sparse-operation-ledger.json').read_text()):
  if r['action']!='remove' or r['uuid'] not in td['removed']:continue
  path=Path(r['exact_chunk_path']);assert sha(path)==r['exact_chunk_sha256'];ch=path.read_bytes();assert iv[3][r['uuid']]==ch
  pp=A.G.parse(r['uuid'],ch,{});t=old[r['uuid']];assert(pp['net'],pp['layer'],pp['w'],pp['a'],pp['b'])==(L.norm(t['net']),t['layer'],t['w'],t['a'],t['b']);rows.append(r)
 assert len(rows)==2
 for t in td['tracks']:assert t['uuid'] not in old and native.raw(L.norm(t['net']))==t['net']
 h['tracks']=[t for t in h['tracks']if t['uuid']not in td['removed']]+td['tracks']
 oldbody={}
 for key in {(L.norm(old[u]['net']),old[u]['layer'])for u in td['removed']}:
  oldbody[key]=unary_union([SB.Z.bounded_buffer(SB.LineString([old[u]['a'],old[u]['b']]),old[u]['w']/2)for u in td['removed']if(L.norm(old[u]['net']),old[u]['layer'])==key])
 def cuts(net,layer,local,outline=False):return SB.cutters(td['tracks'],oldbody,net,layer,local,h,outline)
 zm={q['uuid']:q for q in z};oldzm={q['uuid']:q for q in z0};role_rows=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   prior=q[role];cc=[r['shape']for r in cuts(q['net'],q['layer'],q.get('clearance_mm',.15),role=='zone_outline_shape')if r['shape'].intersects(prior)]
   if not cc:continue
   # No gained copper is permitted, even below an area tolerance.
   literal=set_precision(prior,0);cut=unary_union(cc);after=set_precision(literal.difference(set_precision(cut,0)),1e-6,mode='pointwise')
   for k in range(32):
    gain=set_precision(after,0).difference(literal)
    if gain.is_empty:break
    after=set_precision(set_precision(after,0).difference(set_precision(SB.Z.bounded_buffer(gain,.0000001),0)),1e-6,mode='pointwise')
   else:raise AssertionError('strict local negative-only T4 role construction failed')
   assert set_precision(after,0).difference(literal).is_empty;q[role]=after
   role_rows.append({'UUID':q['uuid'],'role':role,'before_sha256':dg(prior),'after_sha256':dg(after),'literal_gain_empty':True,'only_new_T4_novel_body_guards':True})
 actual=[];fills=[]
 for oldq in c0['zones']:
  qq=copy.deepcopy(oldq)
  for layer,recs in oldq['fills'].items():
   body=unary_union(L.poly(recs));cc=[r['shape']for r in cuts(oldq['net'],layer,oldq.get('clearance_mm',.15))if r['shape'].intersects(body)]
   if oldq['uuid']in oldzm:
    withdrawal=set_precision(oldzm[oldq['uuid']]['shape'],0).difference(set_precision(zm[oldq['uuid']]['shape'],0))
    if not withdrawal.is_empty:cc.append(withdrawal)
   if not cc:continue
   result,proof=IM.subtract(recs,cc,O,oldq['uuid']+'-'+layer);qq['fills'][layer]=result;fills.append({'UUID':oldq['uuid'],'layer':layer,'per_record_immutable_subset_proof':proof})
  actual.append(qq)
 current={**h,'zones':actual};states=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   grid=0 if q['uuid']in('ed7b6af5-93e5-5f20-8977-d10ca721564d','d8d8bdad-3845-5659-b172-4d0e231cdadc')and role=='shape'else 1e-6
   w=q[role].wkb;q[role]=set_precision(q[role],grid,mode='pointwise');assert q[role].wkb==w;states.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':grid,'mode':'pointwise','unchanged_WKB_SHA256':dg(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=states;b['only_T4_sparse_owned_current_replay']={'parent_sha256':sha(B/'model.pkl'),'T4_discrete_sha256':sha(T/'proposed-discrete.pkl'),'exact_removed':td['removed'],'R7_excluded':True}
 write(O/'exact-before-only-T4-delete-ledger.json',rows);write(O/'only-T4-current-owned-role-replay.json',role_rows);write(O/'only-T4-actual-current-filled-record-subtractions.json',fills);write(O/'generated-precision-state-ledger.json',states)
 (O/'only-T4-owned-discrete.pkl').write_bytes(pickle.dumps(td,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,current),protocol=5))
 receipt={'verdict':'EXPLORATORY_ONLY_FROZEN_T4_SPARSE_REPLAY_FULL_CURRENT_JOINT_GATES_OPEN','parent_sha256':sha(B/'model.pkl'),'new_tracks':7,'new_vias':0,'exact_before_deletes':2,'new_planes':0,'owned_role_changes':len(role_rows),'actual_filled_delta_rows':len(fills),'R7_role_masks_not_appended':True,'inherited_CORE93_041959_and_REG_two_planning_deficits_retained':True,'model_sha256':sha(O/'model.pkl'),'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start}
 write(O/'receipt.json',receipt);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'model_sha256':receipt['model_sha256'],'role_changes':len(role_rows),'fill_rows':len(fills)}),flush=True)
if __name__=='__main__':main()
