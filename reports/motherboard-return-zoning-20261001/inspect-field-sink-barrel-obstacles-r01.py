import sys,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_logic_return import segment_hits_box,distance
from hardware_map_motherboard_domains import write
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-r83/motor-bank-A-receiving-candidate.kicad_pcb');g=Geometry(b);net='/motherboard_motors/FIELD_GND';rows=[]
for pt in [(329.1,189.5),(329.1,191.2),(329.6,189.7),(329.8,190.0),(328.5,189.8)]:
 pads=[];tracks=[]
 for p,box in g.pads.candidates(pt,pt,.51):
  if segment_hits_box(pt,pt,box,.4):pads.append(dict(ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),net=p.GetNetname(),box=box))
 for layer,index in g.tracks.items():
  for name,a,c,w in index.candidates(pt,pt,.51):
   if name!=net and distance(pt,a,c)<.25+w/2+.205:tracks.append(dict(layer=b.GetLayerName(layer),net=name,start=a,end=c,width=w))
 rows.append(dict(xy_mm=pt,clear=g.via(pt,net),pad_obstacles=pads,track_obstacles=tracks))
write(Path('reports/motherboard-return-zoning-20261001/field-sink-barrel-obstacles-r01.json'),rows)
