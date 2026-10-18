"""Single-zone Boolean locality precheck with exact local cutter retention."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
from shapely.ops import unary_union
import contact_layout as C
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import regional_guarded_declared_projection_r140 as P
O=H/'regulated-regional-cutter-locality-precheck-r141'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();uid='baf2ed20-2696-4a02-9112-b6b304d3d38d';rows=[];shapes={};ledgers={}
 for label,base in [('ROOT_R22',H.parent/'safe-logic-five-and-fag-margin-r22'),('REG_R130',H/'safe-root22-regulated-source-contact-audit-r130')]:
  g,h,b,z,after=pickle.loads((base/'model.pkl').read_bytes());hs={**h,'zones':[q for q in h['zones'] if q['uuid']==uid]};actual,ledger=P.projected(g,hs,z);stored=unary_union(C.poly(next(q for q in after['zones'] if q['uuid']==uid)['fills']['In1.Cu']));replayed=unary_union(C.poly(next(q for q in actual['zones'] if q['uuid']==uid)['fills']['In1.Cu']));shapes[label]=replayed;ledgers[label]=next(q for q in ledger if q['layer']=='In1.Cu');rows.append({'label':label,'model_sha256':sha(base/'model.pkl'),'stored_sha256':P.digest(stored),'regional_sha256':P.digest(replayed),'stored_minus_regional_mm2':stored.difference(replayed).area,'regional_minus_stored_mm2':replayed.difference(stored).area});write(O/(label+'-retreats.json'),ledger);print(label,rows[-1],flush=True)
 a,bb=shapes.values();same=P.digest(a)==P.digest(bb);write(O/'receipt.json',{'verdict':'REGIONAL_REPLAY_LOCALITY_PASS' if same else 'REGIONAL_REPLAY_LOCALITY_FAIL','rows':rows,'exact_relevant_cutter_rows_equal':ledgers['ROOT_R22']['cutters']==ledgers['REG_R130']['cutters'],'regional_ROOT_vs_REG_lost_mm2':a.difference(bb).area,'regional_ROOT_vs_REG_added_mm2':bb.difference(a).area,'regional_ROOT_vs_REG_WKB_equal':same,'base_function_sha256':P.BASE_FUNCTION_SHA256,'derived_function_sha256':P.DERIVED_FUNCTION_SHA256,'no_reference_tolerance_waiver':True,'full_source_reference_contact_guard_gates':'OPEN','board_written':False});print('R141',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
