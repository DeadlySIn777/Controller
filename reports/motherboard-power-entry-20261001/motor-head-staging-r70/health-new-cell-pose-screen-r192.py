import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()}
for f in [fs['U11013'],fs['U11025'],fs['U11026']]:print(f.GetReference(),mm(f.GetPosition()),side_box(f))
for pn in['4','6']:
 p=next(p for p in fs['U11020'].Pads()if p.GetNumber()==pn);print('CORE_LED',pn,[(q.GetParentFootprint().GetReference(),q.GetNumber(),mm(q.GetPosition()))for q in b.GetPads()if q.GetNetname()==p.GetNetname()])
f=fs['U11026'];c=fs['C11081'];valid=[]
for x in[331.5,332,332.5,333,333.5,334,334.5,335,335.5,336,336.5,337,337.5]:
 for y in[183,184,185,186,187,188,189,190,191,192,193,194,195,196,197]:
  f.SetPosition(xy((x,y)));c.SetPosition(xy((x+.8375,y-.775)))
  if not any(intersects(side_box(z),side_box(q),0)for z in[f,c]for q in fs.values()if q.GetReference()not in['U11026','C11081']and q.GetLayer()==z.GetLayer()):valid.append((x,y))
print('U26_FREE',valid,flush=True)
