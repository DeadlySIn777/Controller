"""Independent true-Cu gate and exact delta/state contract for local R290.

Does not promote the alternative fill projection or waive inherited guards.
The two changed physical roles retain explicit floating effective boundaries;
the native intended outlines remain integer-nm geometry.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy,hashlib
from pathlib import Path
from shapely import set_precision,get_precision,get_coordinates
from shapely.geometry import LineString,Point
import numpy as np
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent
for name in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/name))
import regional_guarded_declared_projection_r140 as P
import complete_geometry_r2 as G
N=H/'REG-seven-cached-exact-analytic-guard-audit-r262'
R=H/'REG-exact-reference-local-owned-guard-repair-r290'
O=H/'REG-local-reference-true-copper-and-state-contract-r292'
CHANGED={'ed7b6af5-93e5-5f20-8977-d10ca721564d','d8d8bdad-3845-5659-b172-4d0e231cdadc'}
NATIVE_CHANGED={'58c55cd5-98e6-4467-88e3-146ceeee361a','c1d27fa1-452b-4e27-985d-5ad23644d800'}
def write(path,obj):path.write_text(json.dumps(obj,indent=1)+'\n',encoding='utf-8')
def signature(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
def main():
 assert not O.exists();O.mkdir();rr=json.loads((R/'receipt.json').read_text(encoding='utf-8'));assert rr['actual_guard_errors']==[] and rr['strict_old_reference_losses']==0 and rr['ground_contact_losses']==0 and rr['prior_source_keys_lost']==0
 assert sha(R/'model.pkl')==rr['model_SHA256'];_,nh,nb,nz,nc=pickle.loads((N/'model.pkl').read_bytes());g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());nzm={q['uuid']:q for q in nz};czm={q['uuid']:q for q in z}
 assert set(nzm)==set(czm)
 for uid,q in czm.items():
  old=nzm[uid];meta={k:v for k,v in q.items() if k not in ('shape','zone_outline_shape')};prior={k:v for k,v in old.items() if k not in ('shape','zone_outline_shape')};assert meta==prior,('changed owned metadata',uid)
  if uid not in CHANGED:
   for role in ('shape','zone_outline_shape'):assert q[role].wkb==old[role].wkb,('unrelated owned geometry changed',uid,role)
 for name in ('pads','vias','tracks','zones','rule_areas','outline'):
  assert signature(h[name])==signature(nh[name]),('host original or discrete geometry changed',name)
 ncm={q['uuid']:q for q in nc['zones']};cm={q['uuid']:q for q in c['zones']};assert set(ncm)==set(cm)
 for uid,q in cm.items():
  if uid in CHANGED|NATIVE_CHANGED:
   assert {k:v for k,v in q.items() if k!='fills'}=={k:v for k,v in ncm[uid].items() if k!='fills'},('native definition changed',uid)
  else:assert q==ncm[uid],('unrelated effective fill changed',uid)
 print('R292 exact native definitions/discrete/unrelated owned role scope PASS',flush=True)
 rec,trees=F.build({**h,'zones':[]});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};checks=[]
 for uid in sorted(CHANGED):
  q=czm[uid];sh=q['shape'];layer=q['layer']
  for index in trees[layer].query(sh.buffer(.627),predicate='intersects'):
   item=rec[layer][int(index)]
   if C.norm(item['net'])==C.norm(q['net']):continue
   gap=sh.distance(item['shape'])
   if item['kind']=='track':t=tm[item['uuid']];gap=sh.distance(LineString([t['a'],t['b']]))-t['w']/2
   elif item['kind']=='via':v=vm[item['uuid']];gap=sh.distance(Point(v['x'],v['y']))-v['d']/2
   required=max(G.gap(h,q['net'],item['net']),float(q.get('clearance_mm',.15)))+.025
   checks.append({'owned_UUID':uid,'foreign_UUID':item['uuid'],'kind':'plane_to_actual_'+item['kind'],'layer':layer,'required_mm':required,'actual_mm':gap,'PASS':gap+1e-10>=required})
  for area in h['rule_areas']:
   if area.get('no_zones') and layer in area['layers']:
    for region in C.poly(area['outline']):
     overlap=sh.intersection(region).area;checks.append({'owned_UUID':uid,'foreign_UUID':area.get('uuid',area.get('name')),'kind':'hard_native_no_zones','layer':layer,'overlap_mm2':overlap,'PASS':overlap<=1e-12})
  for other in z:
   if other['uuid']==uid or other['layer']!=layer or C.norm(other['net'])==C.norm(q['net']):continue
   required=max(G.gap(h,q['net'],other['net']),float(q.get('clearance_mm',.15)),float(other.get('clearance_mm',.15)))+.025;gap=sh.distance(other['shape'])
   if gap<required+.01:checks.append({'owned_UUID':uid,'foreign_UUID':other['uuid'],'kind':'foreign_owned_plane','layer':layer,'required_mm':required,'actual_mm':gap,'PASS':gap+1e-10>=required})
 write(O/'true-copper-and-hard-area-checks.json',checks);errors=[q for q in checks if not q['PASS']];print('R292 true-Cu/hard-area',len(checks),len(errors),flush=True)
 # Explicit strict adapter ledger. Pickle drops GEOS precision metadata;
 # restoring a tag is allowed only with byte-identical coordinates and WKB.
 states=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;grid=0.0 if q['uuid'] in CHANGED and role=='shape' else 1e-6
   q[role]=set_precision(q[role],grid,mode='pointwise');assert q[role].wkb==raw,('precision restore changed coordinates',q['uuid'],role)
   if role=='zone_outline_shape':
    coords=get_coordinates(q[role]);fraction=np.abs(coords*1e6-np.rint(coords*1e6));assert float(fraction.max())<1e-5,('noninteger native outline',q['uuid'])
   states.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':grid,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True,'explicit_effective_physical_float_role':grid==0.0})
 b=copy.deepcopy(b);prior_ledger=copy.deepcopy(b.get('generated_precision_state_ledger'));b['superseded_R262_generated_precision_state_ledger']=prior_ledger;b['generated_precision_state_ledger']=states;b['restored_generated_grid_UUIDs']=sorted(q['uuid'] for q in z);b['R292_explicit_scoped_precision_adapter_required']={'grid_zero_role_pairs':[[uid,'shape'] for uid in sorted(CHANGED)],'every_other_bound_role_grid_mm':1e-6,'unknown_missing_changed_WKB_rejected':True,'old_R168_must_not_be_used_for_zero_roles':True};write(O/'exact-scoped-generated-precision-states.json',states)
 # Verify the exact saved object loss of grid tags and the proposed adapter.
 blob=pickle.dumps((g,h,b,z,c),protocol=5);_,_,testbinding,testzones,_=pickle.loads(blob);loaded={q['uuid']:q for q in testzones};pickle_rows=[]
 for state in states:
  q=loaded[state['new_generated_UUID']];sh=q[state['role']];grid_before=get_precision(sh);assert P.digest(sh)==state['unchanged_WKB_SHA256'];sh=set_precision(sh,state['grid_mm'],mode='pointwise');assert P.digest(sh)==state['unchanged_WKB_SHA256'];q[state['role']]=sh;pickle_rows.append({'UUID':q['uuid'],'role':state['role'],'grid_after_pickle_mm':grid_before,'restored_bound_grid_mm':get_precision(sh),'exact_WKB_preserved':True})
 (O/'model.pkl').write_bytes(blob);(O/'only-two-owned-replacements.pkl').write_bytes(pickle.dumps([czm[uid] for uid in sorted(CHANGED)],protocol=5));write(O/'pickle-grid-state-replay-proof.json',pickle_rows)
 scope={'only_owned_changed_UUIDs':sorted(CHANGED),'only_native_effective_fill_changed_UUIDs':sorted(NATIVE_CHANGED),'unrelated_owned_roles_WKB_exact':True,'all_old_native_definition_fields_exact':True,'all_h_discrete_pads_rule_areas_outline_exact_R262':True,'all_74_unaffected_contact_graphs_exact_candidate_reuse_scope_proved':True,'three_ground_graphs_fresh_R290_checked':True,'old_contacts_all77_zero_from_R262_scope_and_R290':True,'old_source_all5_zero_from_R262_scope_and_R290':True,'strict_refs_all3_zero_fresh_R290':True,'full_fresh_global_projection_not_claimed':True};write(O/'strict-owned-delta-scope.json',scope)
 rec={'verdict':'SCOPED_TRUE_COPPER_STATE_DELTA_PASS_INHERITED_PROJECTION_NATIVE_CURRENT_GATES_OPEN' if not errors else 'SCOPED_TRUE_COPPER_STATE_DELTA_REJECTED','R290_receipt_SHA256':sha(R/'receipt.json'),'R290_model_SHA256':sha(R/'model.pkl'),'R262_failed_model_SHA256':sha(N/'model.pkl'),'true_Cu_checks':len(checks),'true_Cu_errors':errors,'strict_delta_scope_SHA256':sha(O/'strict-owned-delta-scope.json'),'generated_state_ledger_SHA256':sha(O/'exact-scoped-generated-precision-states.json'),'explicit_grid_replay_SHA256':sha(O/'pickle-grid-state-replay-proof.json'),'model_SHA256':sha(O/'model.pkl'),'owned_replacements_SHA256':sha(O/'only-two-owned-replacements.pkl'),'inherited_full_row_guard_errors_preserved':rr['unchanged_inherited_full_row_guard_errors'],'all_original_definition_discrete_and_unrelated_owned_bytes_preserved':True,'alternative_projection_no_native_qualification_or_adoption':True,'current_fault_startup_thermal_native_ALLseverity_GATES':'OPEN','native_jobs':0,'board_written':False,'adopted':False};write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'verdict':rec['verdict'],'checks':len(checks),'errors':len(errors),'model':rec['model_SHA256']}),flush=True)
if __name__=='__main__':main()
