import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json
from pathlib import Path
from shapely.ops import unary_union
import contact_layout as C
H=Path(__file__).resolve().parent
gg=pickle.loads((H/'c-u19008-actual-regulated-search-base-r84/source-groups.pkl').read_bytes())
rows=[]
for net,gs in gg.items():
 for i,xs in enumerate(gs):
  pads=[q for q in xs if q['kind']=='pad' and q['pin']]
  if not pads:continue
  rows.append({'net':net,'group':i,'pads':[{'ref':q['ref'],'pin':q['pin'],'uuid':q['uuid'],'layer':q['layer'],'xy':list(q['shape'].centroid.coords)[0]} for q in pads],'inner_barrel_records':[{'uuid':q['uuid'],'kind':q['kind'],'layer':q['layer'],'bounds':q['shape'].bounds} for q in xs if q['kind']!='fill' and q['layer'].startswith('In')]})
o=H/'regulated-group-diagnostic-r104';o.mkdir();(o/'groups.json').write_text(json.dumps(rows,indent=1)+'\n');print(json.dumps([r for r in rows if 'FIELD_5V' in r['net'] and r['group'] in (0,2)],indent=1))
