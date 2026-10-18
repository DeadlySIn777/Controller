"""Scoped exact current LOGIC projection after ONLY the R230 owned B3 correction."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import fast_contacts as F
import contact_layout as C
import physical_reference_losses_r1 as REF
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
O=H/'B3-envelope-scoped-LOGIC-projection-r231'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def root(groups):return next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs))
def main():
 assert not O.exists();O.mkdir()
 baseline=H/'R54-native-wider-IO3-monitor-joint-audit-r214';subset=H/'REG-safe-subset-on-current-R214-full-audit-r227';correction=H/'B3-outward-reference-envelope-correction-r230'
 assert sha(baseline/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
 assert sha(correction/'receipt.json')=='8d1b2c446f2bf71e0d4567cda7d38ffba0a295f230d59c5e0e4516598b48ae82'
 bg,bh,bb,bz,bc=pickle.loads((baseline/'model.pkl').read_bytes());restore_bound_generated_precision_states(bb,bz)
 g,h,b,z,_=pickle.loads((subset/'model.pkl').read_bytes());restore_bound_generated_precision_states(b,z)
 newq=pickle.loads((correction/'proposed-corrected-zone.pkl').read_bytes())[0]
 prior=next(q for q in z if q['uuid']==newq['uuid']);changed=[]
 for role in ('shape','zone_outline_shape'):
  before=P.digest(prior[role]);raw=newq[role].wkb;newq[role]=set_precision(newq[role],1e-6,mode='pointwise');assert raw==newq[role].wkb
  changed.append({'role':role,'old_sha256':before,'new_sha256':P.digest(newq[role]),'grid_mm':get_precision(newq[role])})
 z=[newq if q['uuid']==newq['uuid'] else q for q in z]
 b['generated_precision_state_ledger']=[{'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True} for q in z for role in ('shape','zone_outline_shape')]
 b['restored_generated_grid_UUIDs']=sorted(q['uuid'] for q in z)
 oldgroups=F.graph(bc,'/LOGIC_GND');oldroot=root(oldgroups)
 hs={**h,'zones':[q for q in h['zones'] if C.norm(q['net'])=='/LOGIC_GND']}
 print('R231 only native LOGIC zones, all foreign exact primitives retained',flush=True)
 after,cutledger=P.projected(g,hs,z);groups=F.graph(after,'/LOGIC_GND');newroot=root(groups)
 losses=F.losses(oldgroups,groups);source_lost=sorted(F.discrete_keys(oldroot)-F.discrete_keys(newroot))
 oldrefs={out:unary_union([q['shape'] for q in oldroot if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]}
 newrefs={out:unary_union([q['shape'] for q in newroot if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]}
 removed={t['uuid'] for t in bh['tracks']}-{t['uuid'] for t in h['tracks']};ref,stats=REF.audit(bc,oldrefs,newrefs,'/LOGIC_GND',removed=removed)
 (O/'derived-full-input-model.pkl').write_bytes(pickle.dumps((g,h,b,z,None),protocol=5));(O/'scoped-projected-model.pkl').write_bytes(pickle.dumps((g,hs,b,z,after),protocol=5));(O/'scoped-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5))
 write(O/'reference-losses.json',ref);write(O/'native-LOGIC-fill-cut-ledger.json',cutledger)
 receipt={'verdict':'SCOPED_LOGIC_SOURCE_CONTACT_REFERENCE_PASS' if not losses and not source_lost and not ref else 'SCOPED_LOGIC_REPAIR_REQUIRED','baseline_model_sha256':sha(baseline/'model.pkl'),'subset_model_sha256':sha(subset/'model.pkl'),'owned_B3_correction_receipt_sha256':sha(correction/'receipt.json'),'only_B3_q_replaced':changed,'required_guards_unchanged':True,'all_foreign_proposed_copper_and_changed_discrete_in_scope':True,'LOGIC_old_group_losses':losses,'prior_source_keys_lost':source_lost,'old_outer_reference_losses':len(ref),'reference_stats':stats,'reference_loss_file_sha256':sha(O/'reference-losses.json'),'full_input_model_sha256':sha(O/'derived-full-input-model.pkl'),'full77_geometry_current_native_gates':'OPEN','native_jobs':0,'board_written':False}
 write(O/'receipt.json',receipt);print(json.dumps(receipt),flush=True);print('R231 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
