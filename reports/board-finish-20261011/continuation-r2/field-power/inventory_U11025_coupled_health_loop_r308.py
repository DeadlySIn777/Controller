import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.geometry import box,LineString,Point
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;B=H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112';O=H/'U11025-exact-coupled-health-loop-inventory-r308';NET='/motherboard_motors/FIELD_GND'
def main():
 assert not O.exists();O.mkdir();g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());groups=pickle.loads((B/'groups.pkl').read_bytes())[NET];root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11003','2') for q in xs));win=box(307.5,150.5,315,157);pads=[q for q in h['pads'] if q['ref']=='U11025'];health=next(q['net'] for q in pads if q['num']=='3');healthtracks=[q for q in h['tracks'] if C.norm(q['net'])==C.norm(health)];healthvias=[q for q in h['vias'] if C.norm(q['net'])==C.norm(health)];local={}
 for k in ('pads','tracks','vias'):
  rows=[]
  for q in h[k]:
   if k=='tracks':sh=LineString([q['a'],q['b']]).buffer(q['w']/2)
   elif k=='vias':sh=Point(q['x'],q['y']).buffer(q['d']/2)
   elif 'F.Cu' in q['layers']:sh=unary_union(C.poly(q['layers']['F.Cu']))
   else:continue
   if (k!='tracks' or q['layer']=='F.Cu') and sh.intersects(win):rows.append(q)
  local[k]=rows
 source=unary_union([q['shape'] for q in root if q['layer']=='F.Cu']).intersection(win)
 payload={'model_SHA256':sha(B/'model.pkl'),'local':local,'U11025_pads':pads,'health_tracks':healthtracks,'health_vias':healthvias,'F_source_ground':source,'health_raw_net':health,'field_ground_raw_net':next(q['net'] for q in pads if q['num']=='2')};(O/'local-geometry.pkl').write_bytes(pickle.dumps(payload,protocol=5));(O/'actual-F-source-ground.wkb').write_bytes(source.wkb);out={'model_SHA256':sha(B/'model.pkl'),'local_geometry_SHA256':sha(O/'local-geometry.pkl'),'health_raw_net':health,'U11025_pads':[{'pin':q['num'],'UUID':q['uuid'],'raw_net':q['net'],'x':q['x'],'y':q['y'],'F_bounds':unary_union(C.poly(q['layers'].get('F.Cu',[]))).bounds} for q in pads],'health_tracks':healthtracks,'health_vias':healthvias,'local_counts':{k:len(v) for k,v in local.items()},'source_ground_bounds':source.bounds,'source_ground_area':source.area};(O/'receipt.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),**out}),flush=True)
if __name__=='__main__':main()
