import pickle,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'sbc-power'));sys.path.insert(0,str(H/'field-power'))
mp=H/'sbc-power/safe-ROOT22-CORE1V2-composition-r148/unprojected-model.pkl'
g,h,b,z,c=pickle.loads(mp.read_bytes())
cache=pickle.loads((H/'sbc-power/IO3-overlapping-owned-bridge-withdrawal-source-probe-r156/source-cache.pkl').read_bytes())
v=next(v for v in h['vias'] if v['uuid'].startswith('4df659b6'))
print('VIA',v,flush=True)
for l in h['copper_layers']:
 source=unary_union([p for p,a in zip(cache['after_parts'][l],cache['after_assign'][l]) if a==1])
 print(l,'root_parts',sum(a==1 for a in cache['after_assign'][l]),'distance',source.distance(Point(v['x'],v['y'])),'nearbounds',source.intersection(Point(v['x'],v['y']).buffer(80)).bounds,flush=True)
q=next(q for q in z if q['uuid']=='04d140c5-3a78-5a5f-96d3-fbe2978c8eee');print('OLDq',q.keys(),q['shape'].bounds,q['shape'].area)
