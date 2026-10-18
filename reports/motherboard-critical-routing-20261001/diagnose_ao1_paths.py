from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_route_logic_return import xy,mm,segment_hits_box,segment_distance
import hardware_prepare_dac_package_escape as neck
import hardware_check_return_corridors_r04 as ret
from hardware_check_return_corridors import covered
import hardware_route_critical_digital_wip_r05 as a
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/source26-r61-AO1-DAC-return-r04/motherboard-AO1-DAC-return-candidate.kicad_pcb');g=w.Geometry(b)
r=json.loads(neck.critical.SOURCE_REVIEW.read_text());fp=next(f for f in b.GetFootprints()if f.GetReference()=='U14626')
c=ret.NativeCollectedAnnulusCheck(b,{});fill=c.reference('/motherboard_analog_output/AO1_COM',b.GetLayerID('In1.Cu'))
for p in fp.Pads():
 if p.GetNumber()not in neck.PINS:continue
 row=neck.recipe(p,'U14626',r);net=row['net'];hits=[]
 for s,e in zip(row['points_mm'],row['points_mm'][1:]):
  for pp,box in g.pads.candidates(s,e,.4):
   if pp.IsOnLayer(pcbnew.F_Cu)and pp.GetNetname()!=net and segment_hits_box(s,e,box,.15+.15):hits.append(dict(pad=pp.GetParentFootprint().GetReference()+'.'+pp.GetNumber(),box=box))
  for name,v,z,width in g.tracks[pcbnew.F_Cu].candidates(s,e,.65):
   if name!=net and segment_distance(s,e,v,z)<.15+width/2+.15-1e-6:hits.append(dict(track=name,a=v,b=z,width=width))
 print(json.dumps(dict(pin=p.GetNumber(),geometry_hits=hits)))
 for length in(1,1.15,1.3,1.5,1.75):
  direction=neck.PINS[p.GetNumber()][0];start=row['points_mm'][-1];end=(mm(p.GetPosition())[0]+direction*length,start[1]);poly=a.engine.corridor_polygon(tuple(xy(start)),tuple(xy(end)),pcbnew.FromMM(.175+.4))
  print(json.dumps(dict(pin=p.GetNumber(),outlength=length,fill=covered(poly,fill),g=g.clear([start,end],net,pcbnew.F_Cu,.45))))
