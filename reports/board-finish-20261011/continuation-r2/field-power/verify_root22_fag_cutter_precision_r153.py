"""Restore one documented construction grid without changing WKB vertices."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from shapely import set_precision,get_precision
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_declared_settings_projection_r58 as P
O=H/'root22-fag-cutter-precision-state-r153'
def main():
 assert not O.exists();O.mkdir();root=H.parent/'safe-logic-five-and-fag-margin-r22';g,h,b,z,candidate=pickle.loads((root/'model.pkl').read_bytes());q=next(q for q in z if q['uuid'].startswith('d5e1a664-'));receipt=json.loads((root/'receipt.json').read_text(encoding='utf-8'));original=next(r for r in receipt['full_projection_retreats'] if r['zone_uuid']=='54921f4b-0308-4821-9549-ff9360bf05ca' and r['layer']=='In2.Cu');original=next(r for r in original['cutters'] if r['uuid']==q['uuid']);before=q['shape'];restored=set_precision(before,1e-6,mode='pointwise');assert before.wkb==restored.wkb;raw=P.bounded_buffer(before,.625);fixed=P.bounded_buffer(restored,.625);ok=P.digest(fixed)==original['outward_cutter_WKB_SHA256'];ledger={'UUID':q['uuid'],'kind':'new_zone_outward_polygon','raw_net':q['net'],'layer':q['layer'],'physical_WKB_sha256_unchanged':P.digest(before),'loaded_grid_mm':get_precision(before),'documented_constructor_grid_mm':1e-6,'documented_constructor_source':str((H.parent/'compose_safe_logic_subset_and_fag_margin_r22.py').resolve()),'constructor_sha256':sha(H.parent/'compose_safe_logic_subset_and_fag_margin_r22.py'),'pointwise_restore_geometry_exact':True,'required_clearance_before_guard_mm':.6,'guard_mm':.025,'loaded_grid_cutter_sha256':P.digest(raw),'restored_grid_cutter_sha256':P.digest(fixed),'preserved_global_ROOT_R22_cutter_sha256':original['outward_cutter_WKB_SHA256'],'restored_primitive_hash_exact':ok,'all_other_primitive_guards_unchanged':True,'full_paired_76_net_restore_recheck_required':True};(O/'receipt.json').write_text(json.dumps(ledger,indent=1)+'\n',encoding='utf-8');print('R153',sha(O/'receipt.json'),json.dumps(ledger),flush=True)
if __name__=='__main__':main()
