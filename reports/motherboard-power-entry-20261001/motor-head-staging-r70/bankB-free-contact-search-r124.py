import pcbnew,sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
from hardware_route_local_signals import GeometryIndex
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-control-repair-r120/motor-bank-A-control-repaired-candidate.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()};owned={'U11011','C11059','C11060','R11045','R11046','R11047','U11034','R11077','C11085','C11086','R11078','R11079','U11023','U11024','U11029','U11030','R11069','R11073'};idx=GeometryIndex();boxes={}
for r,f in fs.items():
 if r in owned or f.GetLayer()!=pcbnew.F_Cu:continue
 z=side_box(f);boxes[r]=z;idx.add((r,z),z)
found=[]
for cx in range(230,307,2):
 for cy in range(208,269,2):
  poses={'U11023':((cx,cy),0),'U11024':((cx,cy+5),0),'U11029':((cx+12,cy),180),'U11030':((cx+12,cy+5),180),'R11069':((cx-6,cy-.635),0),'R11073':((cx+19,cy+.635),180)};cl=[]
  for r,(pt,ang)in poses.items():
   fs[r].SetPosition(xy(pt));fs[r].SetOrientationDegrees(ang);bb=side_box(fs[r]);p=(bb[0],bb[1]);q=(bb[2],bb[3])
   if any(intersects(bb,z,0)for other,z in idx.candidates(p,q,0)):cl.append(r);break
  if not cl:found.append(dict(score=math.dist((cx,cy),(254.5,209))+math.dist((cx+12,cy),(299,197))*.2,poses=poses))
found.sort(key=lambda x:x['score']);print(json.dumps(found[:8],indent=2));Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankB-free-contacts-r124.json').write_text(json.dumps(found,indent=2))
