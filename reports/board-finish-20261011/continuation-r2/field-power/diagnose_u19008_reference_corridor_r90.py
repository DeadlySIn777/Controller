import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
g,h,b,z,a=pickle.loads((H/'c-u19008-actual-regulated-search-base-r84/model.pkl').read_bytes())
d=pickle.loads((H/'u19008-outside-reservation-branch-tree-r89/proposed-discrete.pkl').read_bytes());net=next(v['net'] for v in d['vias'] if C.norm(v['net'])=='/motherboard_do/FIELD_B_0V');body=from_wkb((H/'u19008-outside-reservation-branch-tree-r89/proposed-power-body.wkb').read_bytes());free=from_wkb((H/'u19008-outside-reservation-branch-tree-r89/reference-zone-free.wkb').read_bytes());rec,tree=F.build({**h,'zones':[]});bad=[]
for q in rec['In4.Cu']:
 if q['net']==net:continue
 gap=(.15 if h['domains_normalized'].get(C.norm(q['net']))==h['domains_normalized'].get(C.norm(net)) else .6)+.025
 if body.distance(q['shape'])<gap:bad.append({'kind':q['kind'],'uuid':q['uuid'],'net':q['net'],'ref':q.get('ref'),'pin':q.get('pin'),'distance_mm':body.distance(q['shape']),'gap_mm':gap,'intersection_guard_area_mm2':body.intersection(P.bounded_buffer(q['shape'],gap)).area})
for q in z:
 if q['layer']!='In4.Cu' or q['net']==net:continue
 gap=max(.15 if h['domains_normalized'].get(C.norm(q['net']))==h['domains_normalized'].get(C.norm(net)) else .6,float(q.get('clearance_mm',.15)))+.025
 if body.distance(q['shape'])<gap:bad.append({'kind':'proposed_zone','uuid':q['uuid'],'net':q['net'],'distance_mm':body.distance(q['shape']),'gap_mm':gap,'intersection_guard_area_mm2':body.intersection(P.bounded_buffer(q['shape'],gap)).area})
o=H/'u19008-reference-corridor-diagnostic-r90';o.mkdir();(o/'hard-blockers.json').write_text(json.dumps(bad,indent=1)+'\n');(o/'body-outside-reference-free.wkb').write_bytes(body.difference(free).wkb);print('Reference blocked area',body.difference(free).area,json.dumps(bad,indent=1))
