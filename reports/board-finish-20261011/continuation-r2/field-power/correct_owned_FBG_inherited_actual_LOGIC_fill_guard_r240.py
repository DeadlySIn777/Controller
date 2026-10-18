"""Trim only the owned FBG primitive against exact frozen actual LOGIC fill."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import contact_layout as C
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
O=H/'B3-subset-inherited-FBG-native-LOGIC-guard-correction-r240'
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'R54-native-wider-IO3-monitor-joint-audit-r214';candidate=H/'B3-envelope-scoped-LOGIC-projection-r233';g,h,b,z,_=pickle.loads((candidate/'derived-full-input-model.pkl').read_bytes());restore_bound_generated_precision_states(b,z);bg,bh,bb,bz,bc=pickle.loads((base/'model.pkl').read_bytes());restore_bound_generated_precision_states(bb,bz)
 q=next(q for q in z if q['uuid']=='d8d8bdad-3845-5659-b172-4d0e231cdadc');old=copy.deepcopy(q);oldfields=[];near=q['zone_outline_shape'].buffer(.676)
 for native in bc['zones']:
  if C.norm(native['net'])!='/LOGIC_GND' or 'In1.Cu' not in native['fills']:continue
  shape=unary_union(C.poly(native['fills']['In1.Cu']))
  if shape.intersects(near):oldfields.append((native['uuid'],shape.intersection(near)))
 mask=unary_union([shape for uid,shape in oldfields]);cutter=P.bounded_buffer(mask,.625+.00005);ledger=[]
 for role in ('shape','zone_outline_shape'):
  prior=q[role];q[role]=set_precision(prior.difference(cutter),1e-6);rf=O/(role+'.removed.wkb');rf.write_bytes(prior.difference(q[role]).wkb);ledger.append({'role':role,'before_sha256':P.digest(prior),'after_sha256':P.digest(q[role]),'removed_mm2':prior.difference(q[role]).area,'added_mm2':q[role].difference(prior).area,'removed_file_sha256':sha(rf)})
 checks=[]
 for uid,shape in oldfields:
  gap=q['shape'].distance(shape);checks.append({'old_actual_zone_UUID':uid,'required_gap_mm':.625,'actual_gap_mm':gap,'PASS':gap+1e-10>=.625})
 assert all(r['PASS'] for r in checks),[r for r in checks if not r['PASS']]
 (O/'exact-frozen-old-LOGIC-mask.wkb').write_bytes(mask.wkb);(O/'exact-outward-construction-cutter.wkb').write_bytes(cutter.wkb);(O/'corrected-owned-FBG-zone.pkl').write_bytes(pickle.dumps([q],protocol=5));write(O/'actual-old-fill-guard-checks.json',checks);receipt={'verdict':'OWNED_FBG_INHERITED_GUARD_CORRECTION_NOMINEE_FULL_GATES_OPEN','baseline_sha256':sha(base/'model.pkl'),'candidate_parent_sha256':sha(candidate/'derived-full-input-model.pkl'),'only_owned_zone_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'required_gap_mm':.625,'explicit_additional_constructor_reserve_mm':.00005,'B3_constructor_100nm_reserve_unchanged':True,'role_operations':ledger,'old_native_definitions_discrete_and_all_other_owned_q_unchanged':True,'actual_old_fill_guard_errors':sum(not r['PASS'] for r in checks),'actual_old_fill_guard_min_mm':min(r['actual_gap_mm'] for r in checks),'corrected_zone_sha256':sha(O/'corrected-owned-FBG-zone.pkl'),'source_contact_reference_current_native':'OPEN','native_jobs':0,'board_written':False};write(O/'receipt.json',receipt);print(json.dumps(receipt),flush=True);print('R240 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
