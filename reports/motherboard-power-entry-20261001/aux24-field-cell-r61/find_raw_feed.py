import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_local_signals import paths
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');g=Geometry(b);n='/motherboard_power_entry/MOTION_5V_RAW'
for s,e,w in [((266.2,171),(266,177),4),((266,177),(358,174),8),((266,177),(358,174),6),((358,174),(343.5,186),2)]:
 print('POINTS',s,e,w,g.clear([s,s],n,pcbnew.F_Cu,w),g.clear([e,e],n,pcbnew.F_Cu,w),flush=True)
 p=next((p for p in paths(s,e)if g.clear(p,n,pcbnew.F_Cu,w)),None)
 if p is None and all(g.clear([v,v],n,pcbnew.F_Cu,w)for v in[s,e]):p=g.grid(s,e,n,pcbnew.F_Cu,w,step=1.,padding=45,max_nodes=12000)
 print('PATH',p,flush=True)
