from pathlib import Path
import sys,pickle,json
from shapely.geometry import Point
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
g,h,b,z,c=pickle.loads((H/'sbc-power/safe-ROOT22-CORE1V2-composition-r148/unprojected-model.pkl').read_bytes());v=next(v for v in h['vias'] if v['uuid'].startswith('4df659b6'));p=Point(v['x'],v['y']);rows=[]
for l in h['copper_layers']:
 for q in z:
  if q['layer']==l and q['net']!=v['net'] and p.distance(q['shape'])<1.2:rows.append({'kind':'owned_new','layer':l,'UUID':q['uuid'],'net':q['net'],'center_distance_mm':p.distance(q['shape'])})
 for q in h['zones']:
  if q['net']==v['net']:continue
  for s in C.poly(q['fills'].get(l,[])):
   if p.distance(s)<1.2:rows.append({'kind':'old_cached_native_fill','layer':l,'UUID':q['uuid'],'net':q['net'],'center_distance_mm':p.distance(s),'local':q['clearance_mm']})
print(json.dumps(rows,indent=1))
(H/'sbc-power/IO3-existing-via-local-layer-diagnostic-r163.json').write_text(json.dumps({'via':v,'rows':rows,'native_refill_not_claimed':True},indent=1)+'\n')
