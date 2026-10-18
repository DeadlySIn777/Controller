"""Literal zero-tag rendering check: correct only intended snap gains."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,copy
from pathlib import Path
from shapely import set_precision,get_precision
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import regional_guarded_declared_projection_r140 as P
R=H/'REG-local-reference-true-copper-and-state-contract-r292';B=H/'R54-native-wider-IO3-monitor-joint-audit-r214';O=H/'REG-two-native-intents-literal-gain-correction-r302'
IDS={'d8d8bdad-3845-5659-b172-4d0e231cdadc','ed7b6af5-93e5-5f20-8977-d10ca721564d'}
def write(path,v):path.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();prior=json.loads((R/'receipt.json').read_text());assert sha(R/'model.pkl')==prior['model_SHA256'];g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());_,_,_,bz,_=pickle.loads((B/'model.pkl').read_bytes());old={q['uuid']:q for q in bz};ledger=[]
 for q in z:
  if q['uuid'] not in IDS:continue
  baseline=set_precision(old[q['uuid']]['zone_outline_shape'],0);current=set_precision(q['zone_outline_shape'],0);physical=q['shape'].wkb;rows=[];initial_gain=current.difference(baseline);initial_SHA=P.digest(current)
  for iteration in range(24):
   gain=set_precision(current,0).difference(baseline)
   if gain.area<=1e-12:break
   cut=set_precision(P.bounded_buffer(set_precision(gain,0),.000003),0);path=O/(q['uuid']+'-intended-positive-gain-cutter-'+str(iteration)+'.wkb');path.write_bytes(cut.wkb);nextshape=set_precision(current.difference(cut),1e-6,mode='pointwise');nextzero=set_precision(nextshape,0);rows.append({'iteration':iteration,'actual_zero_tag_positive_area_mm2':gain.area,'actual_gain_WKB_SHA256':P.digest(gain),'cutter_file':str(path.resolve()),'cutter_file_SHA256':sha(path),'guard_constructor_distance_mm':.000003,'actual_before_SHA256':P.digest(current),'actual_after_SHA256':P.digest(nextzero),'local_removed_mm2':current.difference(nextzero).area});current=nextzero
  else:raise AssertionError(('native integer outline gain did not converge',q['uuid'],gain.area))
  final=set_precision(current,1e-6,mode='pointwise');assert final.wkb==current.wkb;assert set_precision(final,0).difference(baseline).area<=1e-12;assert physical==q['shape'].wkb;q['zone_outline_shape']=final
  ledger.append({'owned_UUID':q['uuid'],'native_intended_before_SHA256':initial_SHA,'native_intended_after_SHA256':P.digest(final),'literal_R214_native_intended_SHA256':P.digest(baseline),'initial_actual_positive_gain_mm2':initial_gain.area,'final_actual_positive_gain_mm2':set_precision(final,0).difference(baseline).area,'only_native_intended_locally_removed_mm2':set_precision(from_before:=next(x for x in pickle.loads((R/'only-two-owned-replacements.pkl').read_bytes()) if x['uuid']==q['uuid'])['zone_outline_shape'],0).difference(set_precision(final,0)).area,'physical_role_WKB_exact_R292':True,'all_executed_local_cuts':rows})
 # Bind every generated role explicitly; do not retain stale hash rows.
 states=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   grid=0.0 if q['uuid'] in IDS and role=='shape' else 1e-6;raw=q[role].wkb;q[role]=set_precision(q[role],grid,mode='pointwise');assert raw==q[role].wkb;states.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':grid,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True,'explicit_effective_physical_float_role':grid==0.0})
 b=copy.deepcopy(b);b['generated_precision_state_ledger']=states;b['restored_generated_grid_UUIDs']=sorted(q['uuid'] for q in z);b['R302_intended_literal_gain_correction_ledger_file']=str((O/'native-intended-local-gain-ledger.json').resolve());write(O/'native-intended-local-gain-ledger.json',ledger);b['R302_intended_literal_gain_correction_ledger_SHA256']=sha(O/'native-intended-local-gain-ledger.json');(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,c),protocol=5));(O/'only-two-owned-replacements.pkl').write_bytes(pickle.dumps([q for q in z if q['uuid'] in IDS],protocol=5));write(O/'exact-scoped-generated-precision-states.json',states)
 rec=copy.deepcopy(prior);rec.update({'verdict':'LITERAL_NATIVE_INTENDED_REMOVE_ONLY_RENDER_PASS_FULL_CURRENT_BASE_NATIVE_GATES_OPEN','parent_R292_receipt_SHA256':sha(R/'receipt.json'),'parent_R292_model_SHA256':sha(R/'model.pkl'),'model_SHA256':sha(O/'model.pkl'),'owned_replacements_SHA256':sha(O/'only-two-owned-replacements.pkl'),'literal_native_intended_gain_ledger_SHA256':sha(O/'native-intended-local-gain-ledger.json'),'all_g_h_candidate_and_every_physical_role_exact_R292':True,'only_two_native_intended_roles_locally_clipped':True,'fresh_contact_or_physical_true_Cu_test_not_repeated_because_physical_shapes_exact':True,'native_intended_only_does_not_establish_native_fill_or_flash':True,'native_jobs':0,'board_written':False,'adopted':False});write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'model':rec['model_SHA256'],'ledger':ledger}),flush=True)
if __name__=='__main__':main()
