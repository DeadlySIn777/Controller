import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import xy,mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');n='/LOGIC_GND';fills=collect_native_reference_fills(b,{n},[pcbnew.In1_Cu,pcbnew.In4_Cu]);g=Geometry(b);s=(106.9375,287);signal='/motherboard_operator/MPG_ENABLE_CONDITIONED'
print('signal',[(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname())for p in b.GetPads()if mm(p.GetPosition())==s])
for layer in(pcbnew.In1_Cu,pcbnew.In4_Cu):
 f=fills[n,layer];print('actual pad',b.GetLayerName(layer),'centre',f.Contains(xy(s)),'r.25',covered(circle(tuple(xy(s)),pcbnew.FromMM(.25)),f))
for q in[(106.9375,286),(106.9375,285),(106.9375,284.5),(106.9375,284),(108,284.5),(108,284),(109,284),(104.5,284.5),(105.5,284.5)]:
 layers={}
 for layer in(pcbnew.In1_Cu,pcbnew.In4_Cu):
  f=fills[n,layer];ring=circle(tuple(xy(q)),pcbnew.FromMM(1.07));ring.BooleanSubtract(circle(tuple(xy(q)),pcbnew.FromMM(.87)))
  corridor=corridor_polygon(tuple(xy(s)),tuple(xy(q)),pcbnew.FromMM(.2));layers[b.GetLayerName(layer)]=dict(centre=f.Contains(xy(q)),strict_outer_ring=covered(ring,f),signal_branch_projection=covered(corridor,f))
 print(q,dict(barrel=g.via(q,signal),Fclear=g.clear([s,q],signal,pcbnew.F_Cu,.2),layers=layers),flush=True)
