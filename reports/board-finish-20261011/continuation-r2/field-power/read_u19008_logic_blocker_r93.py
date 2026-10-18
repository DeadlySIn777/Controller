import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
from shapely.geometry import Point
import contact_layout as C
H=Path(__file__).resolve().parent
g,h,b,z,a=pickle.loads((H/'c-u19008-actual-regulated-search-base-r84/model.pkl').read_bytes());v=next(v for v in h['vias'] if v['uuid']=='58446867-9078-4bf3-93c2-2c613644426e');disk=Point(v['x'],v['y']).buffer(v['d']/2)
print(json.dumps({'via':v,'old_contacts':[t for t in h['tracks'] if t['net']==v['net'] and C.body(t).intersects(disk)],'same_net_pad_contacts':[{k:p[k] for k in ('uuid','ref','num','net','layers')} for p in h['pads'] if p['net']==v['net'] and any(sh.intersects(disk) for rs in p['layers'].values() for sh in C.poly(rs))]},indent=1))
