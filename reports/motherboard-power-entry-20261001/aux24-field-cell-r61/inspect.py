import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import mm,segment_distance
b=pcbnew.LoadBoard(str(Path(__file__).with_name('rejected-field-debug.kicad_pcb')))
g=Geometry(b);pt=(376.4,208.5);n='/motherboard_power_entry/AUX24_A_ILIM';gap=.36
for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
 print('LAYER',b.GetLayerName(l))
 for net,polys,top,bot,npth in g.pads.candidates(pt,pt,gap):
  if net==n and not npth:continue
  if(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(pt,pt,p,gap)for p in polys):
   for pad in b.GetPads():
    if pad.GetNetname()==net and pad.IsOnLayer(l) and any(hits(pt,pt,[[mm(pad.GetEffectivePolygon(l).Outline(0).CPoint(i))for i in range(pad.GetEffectivePolygon(l).Outline(0).PointCount())]][0],gap)for _ in [0]):
     print('PAD',pad.GetParentFootprint().GetReference(),pad.GetNumber(),net,mm(pad.GetPosition()))
 for net,s,e,w in g.tracks[l].candidates(pt,pt,gap):
  if net!=n and segment_distance(pt,pt,s,e)<gap+w/2-1e-6:print('CU',net,s,e,w)
 for ref,p in g.barriers:
  if hits(pt,pt,p,.2):print('BARRIER',ref)
