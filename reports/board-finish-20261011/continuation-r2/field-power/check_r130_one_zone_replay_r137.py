"""Exact single native zone replay: no tolerance or reference waiver."""
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
import guarded_declared_settings_projection_r58 as P
O=H/'regulated-one-zone-boolean-replay-r137'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();uid='baf2ed20-2696-4a02-9112-b6b304d3d38d';rows=[];shapes={}
 for label,base in [('ROOT_R22',H.parent/'safe-logic-five-and-fag-margin-r22'),('REG_R130',H/'safe-root22-regulated-source-contact-audit-r130')]:
  g,h,b,z,after=pickle.loads((base/'model.pkl').read_bytes());hs={**h,'zones':[q for q in h['zones'] if q['uuid']==uid]};actual,ledger=P.projected(g,hs,z);stored=unary_union(C.poly(next(q for q in after['zones'] if q['uuid']==uid)['fills']['In1.Cu']));replayed=unary_union(C.poly(next(q for q in actual['zones'] if q['uuid']==uid)['fills']['In1.Cu']));shapes[label]=(stored,replayed);rows.append({'label':label,'model_sha256':sha(base/'model.pkl'),'stored_sha256':P.digest(stored),'replayed_sha256':P.digest(replayed),'stored_minus_replayed_mm2':stored.difference(replayed).area,'replayed_minus_stored_mm2':replayed.difference(stored).area});write(O/(label+'-retreats.json'),ledger);print(label,rows[-1],flush=True)
 (a,ar),(bb,br)=shapes.values();write(O/'receipt.json',{'verdict':'EXACT_SINGLE_ZONE_REPLAY_DIAGNOSTIC','rows':rows,'replayed_ROOT_vs_REG_lost_mm2':ar.difference(br).area,'replayed_ROOT_vs_REG_added_mm2':br.difference(ar).area,'no_reference_tolerance_waiver':True,'board_written':False});print('R137',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
