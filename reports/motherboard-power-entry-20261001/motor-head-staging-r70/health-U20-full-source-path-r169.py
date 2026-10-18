import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm
from hardware_route_local_signals import paths
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');g=FastGeometry(b);ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};p=ps['U11020','5'];n=p.GetNetname();s=mm(p.GetPosition());ground=(342.4125,175)
res=[]
for ix in range(-10,11):
 for iy in range(-10,11):
  z=(ground[0]+ix*.1,ground[1]+iy*.1);d=math.dist(ground,z)
  if not(.78<=d<=1.):continue
  if not all(g.clear([z,z],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):continue
  q=next((v for v in paths(s,z)if g.clear(v,n,pcbnew.F_Cu,.25)),None)
  if q is None:q=g.grid(s,z,n,pcbnew.F_Cu,.25,step=.1,padding=3,max_nodes=20000)
  if q:res.append(dict(via=z,source_path=q,ground=ground,distance=d));print(res[-1],flush=True)
Path('reports/motherboard-power-entry-20261001/ROOT94-health-four-loop-gap-r166/U20-sharing-real-Ground.json').write_text(json.dumps(res,indent=2));print('CANDIDATES',len(res),flush=True)
