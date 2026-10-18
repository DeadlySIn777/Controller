import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
gg=pickle.loads((HERE/'logic-field-mutual-contact-audit-r2/groups.pkl').read_bytes())['/motherboard_safety_sensor/FIELD_B_5V_PRE']
for i,xs in enumerate(gg):
    print(json.dumps({'group':i,'physical_pads':sorted({(q['ref'],q['pin'],q['uuid'],q['layer']) for q in xs if q['kind']=='pad'}),'Cu_count':len(xs),'objects':[{k:v for k,v in q.items() if k!='shape'}|{'bounds':q['shape'].bounds} for q in xs if q['kind']!='fill']}))
