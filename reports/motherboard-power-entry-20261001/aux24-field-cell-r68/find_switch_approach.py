import sys,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_local_signals import paths
b=pcbnew.LoadBoard(str(Path(__file__).with_name('aux24-field-cell-candidate.kicad_pcb')));g=Geometry(b);n='/motherboard_power_entry/MOTION_5V_RAW'
for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
 for w in [8,6,4,2]:
  v=sorted((p for p in[(x,y)for x in range(320,359,2)for y in range(174,204,2)]if g.clear([p,p],n,l,w)),key=lambda p:math.dist(p,(343.5,186)));print(b.GetLayerName(l),w,v[:12],flush=True)
for s,e,l,w in[((326,198),(343.5,186),pcbnew.B_Cu,2),((266,167),(326,198),pcbnew.B_Cu,4)]:
 print('PATH_BEGIN',s,e,b.GetLayerName(l),w,flush=True);v=next((v for v in paths(s,e)if g.clear(v,n,l,w)),None)
 if v is None and all(g.clear([p,p],n,l,w)for p in [s,e]):v=g.grid(s,e,n,l,w,step=.5,padding=35,max_nodes=18000)
 print('PATH',v,flush=True)
