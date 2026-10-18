import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
from shapely import set_precision
from shapely.geometry import box,LineString
H=Path(__file__).resolve().parent;U='ed7b6af5-93e5-5f20-8977-d10ca721564d';W=box(284.28,178.7,284.34,179.08)
old=next(q for q in pickle.loads((H/'R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl').read_bytes())[3] if q['uuid']==U)
new=next(q for q in pickle.loads((H/'REG-two-native-intents-literal-gain-correction-r302/only-two-owned-replacements.pkl').read_bytes()) if q['uuid']==U)
def segs(sh):
 rows=[]
 for k,p in enumerate([sh] if sh.geom_type=='Polygon' else sh.geoms):
  for r,ring in enumerate([p.exterior,*p.interiors]):
   cs=list(ring.coords)
   for i in range(len(cs)-1):
    l=LineString([cs[i],cs[i+1]])
    if l.intersects(W):rows.append({'p':k,'ring':r,'i':i,'start':cs[i],'end':cs[i+1],'length':l.length})
 return rows
out={'old':segs(old['zone_outline_shape']),'new':segs(new['zone_outline_shape']),'old_physical':segs(old['shape']),'new_physical':segs(new['shape']),'loss_area':set_precision(old['shape'],0).intersection(W).difference(set_precision(new['zone_outline_shape'],0)).area}
(H/'ED-native-outline-reference-vertices-r305.json').write_text(json.dumps(out,indent=1)+'\n');print(json.dumps(out),flush=True)
