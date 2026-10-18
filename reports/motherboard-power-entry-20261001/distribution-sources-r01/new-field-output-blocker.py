import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm,xy,segment_distance
from hardware_route_power_groups_native import hits
from hardware_route_local_signals import paths
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/aux24-field-cell-r57/rejected-field-debug.kicad_pcb');g=Geometry(b);ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()};cp=ps['C11070','1'];p=ps['U11015','10'];n=p.GetNetname();s=mm(p.GetPosition());e=mm(cp.GetPosition());print('endpoints',n,s,e,g.clear([s,s],n,pcbnew.F_Cu,.3),g.clear([e,e],n,pcbnew.B_Cu,.3))
for l,point in[(pcbnew.F_Cu,s),(pcbnew.F_Cu,e)]:
 gap=.31;bad=[]
 for net,polys,top,bot,npth in g.pads.candidates(point,point,gap):
  if net!=n and(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(point,point,q,gap)for q in polys):bad.append(('pad',net,polys))
 for net,a,c,w in g.tracks[l].candidates(point,point,gap):
  if net!=n and segment_distance(point,point,a,c)<gap+w/2:bad.append(('track',net,a,c,w))
 print(b.GetLayerName(l),json.dumps(bad))

