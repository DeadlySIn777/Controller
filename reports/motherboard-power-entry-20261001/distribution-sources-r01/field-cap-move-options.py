import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import mm,xy,segment_distance
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/io3-positive-delivery-r08/io3-positive-delivery-candidate.kicad_pcb');cf=next(f for f in b.GetFootprints()if f.GetReference()=='C11069');cf.SetPosition(xy((347.575,180.85)));cf.SetOrientationDegrees(0);of=next(f for f in b.GetFootprints()if f.GetReference()=='C11070');of.SetPosition(xy((353.075,179.75)));g=Geometry(b);s=(349.05,180.85);e=(350,180.85);n='/motherboard_motors/FIELD_GND';gap=.36;bad=[]
for net,polys,top,bot,npth in g.pads.candidates(s,e,gap):
 if net!=n and (npth or bot)and any(hits(s,e,p,gap)for p in polys):bad.append(('pad',net,polys))
for net,a,c,w in g.tracks[pcbnew.B_Cu].candidates(s,e,gap):
 if net!=n and segment_distance(s,e,a,c)<gap+w/2:bad.append(('cu',net,a,c,w))
print(json.dumps(bad))
for k in [1,2]:
 p=next(p for p in cf.Pads()if p.GetNumber()==str(k));opts=[]
 for x in [mm(p.GetPosition())[0]-.9,mm(p.GetPosition())[0]+.9,mm(p.GetPosition())[0]-1.3,mm(p.GetPosition())[0]+1.3]:
  pt=(x,mm(p.GetPosition())[1])
  if all(g.clear([pt,pt],p.GetNetname(),l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu])and g.clear([mm(p.GetPosition()),pt],p.GetNetname(),pcbnew.B_Cu,.3):opts.append(pt)
 print(json.dumps(dict(pin=k,options=opts)))
