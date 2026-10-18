import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import xy,segment_distance
from hardware_route_power_groups_native import hits
print('loading',flush=True)
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-return-motor-r53/motherboard-bounded-merged-candidate.kicad_pcb')
prefixes=['a9289433','84b293a9','400a60a3']
original=list(b.GetTracks());removed=[]
for t in original:
 if any(t.m_Uuid.AsString().startswith(p)for p in prefixes):removed.append(t);b.Remove(t)
print('geometry',flush=True)
g=Geometry(b)
print('paths',flush=True)
paths=[[(411.08,138),(403.08,138),(400.8,140.2),(400.8,143.8),(396.08,142)],[(380.08,145),(380.7,142.2),(370.4,142.2),(370.4,145),(367.08,145)]]
for ps in paths:
 print(json.dumps(dict(path=ps,segments=[g.clear([s,e],'/motherboard_motors/FIELD_GND',pcbnew.B_Cu,4)for s,e in zip(ps,ps[1:])])) )
 for s,e in zip(ps,ps[1:]):
  if g.clear([s,e],'/motherboard_motors/FIELD_GND',pcbnew.B_Cu,4):continue
  bad=[]
  for net,polys,top,bot,npth in g.pads.candidates(s,e,2.16):
   if net!='/motherboard_motors/FIELD_GND' and (npth or bot)and any(hits(s,e,p,2.16)for p in polys):bad.append(('pad',net))
  for net,a,c,w in g.tracks[pcbnew.B_Cu].candidates(s,e,2.16):
   if net!='/motherboard_motors/FIELD_GND'and segment_distance(s,e,a,c)<2.16+w/2:bad.append(('cu',net,a,c,w))
  for ref,poly in g.barriers:
   if hits(s,e,poly,2):bad.append(('barrier',ref))
  print(json.dumps(dict(segment=[s,e],bad=bad)))
