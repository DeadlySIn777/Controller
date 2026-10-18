"""Audit actual two-barrel layer reach before proposing any extra flash."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;B=H/'B3-exact-IO3-preserving-search-base-r177';O=H/'B3-actual-source-target-layer-census-r185';assert not O.exists();O.mkdir()
g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());actual=json.loads((C.BASE/'continuation-r2/native-198b-geometry/actual-via-flashes.json').read_text(encoding='utf-8'))['vias'];gs=F.graph(c,'/motherboard_do/DOB_FIELD_3V3');root=next(xs for xs in gs if any(q['kind']=='pad' and(q.get('ref'),q.get('pin'))==('U11018','1') for q in xs));target=next(xs for xs in gs if any(q['kind']=='pad' and(q.get('ref'),q.get('pin'))==('U19008','10') for q in xs));rows=[]
for prefix in ('049e91c3','12d237e3'):
 v=next(v for v in h['vias'] if v['uuid'].startswith(prefix));rows.append({'via':v,'original198b_actual_native_flashes':actual.get(v['uuid']),'root_layer_membership':sorted({q['layer'] for q in root if q['kind']=='via' and q['uuid']==v['uuid']}),'target_layer_membership':sorted({q['layer'] for q in target if q['kind']=='via' and q['uuid']==v['uuid']})})
scope=lambda xs:{l:{'records':sum(q['layer']==l for q in xs),'via_UUIDs':sorted({q['uuid'] for q in xs if q['layer']==l and q['kind']=='via'})} for l in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu')}
r={'verdict':'DIAGNOSTIC_NO_FLASH_OR_SOURCE_CREDIT_CHANGE','input_model_sha256':sha(B/'model.pkl'),'rows':rows,'actual_source_layers':scope(root),'actual_target_layers':scope(target),'R184_failed_extra_flash_assertion_preserved':True,'board_written':False,'native_jobs':0};(O/'receipt.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8');print(json.dumps(r,indent=1));print(sha(O/'receipt.json'))
