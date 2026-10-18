import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
import contact_layout as C
import fast_contacts as F
from inventory import sha
P=Path(__file__).resolve().parent;bp=P/'local-and-b5-return-audit-r25';g=pickle.loads((bp/'geometry.pkl').read_bytes());net='/motherboard_power_entry/AUX24_A_DVDT';tracks=[q for q in g['tracks'] if C.norm(q['net'])==net];rr,tt=F.build(g,nets={net});rows=[C.identity(q)|{'bounds':q['shape'].bounds} for rs in rr.values() for q in rs if q['kind']!='track'];out=P/'u11015-dvdt-scope-r30';assert not out.exists();out.mkdir();receipt={'tracks':tracks,'other_physical_contacts':rows,'parent_r25_receipt_sha256':sha(bp/'receipt.json'),'native_jobs':0,'board_written':False};(out/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=1))
