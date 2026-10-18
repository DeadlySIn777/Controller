import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
H=Path(__file__).resolve().parent
g,h,b,z,a=pickle.loads((H/'c-u19008-actual-regulated-search-base-r84/model.pkl').read_bytes())
uuids={r['uuid'] for r in json.loads((H/'u19008-coupled-power-wall-nomination-r82/outside-contact-ledger.json').read_text())}
print(json.dumps([t for t in h['tracks'] if t['uuid'] in uuids],indent=1))
