import pcbnew,sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/io3-positive-delivery-r08/io3-positive-delivery-candidate.kicad_pcb');f=next(f for f in b.GetFootprints()if f.GetReference()=='C11069')
for p in f.Pads():
 for l in[pcbnew.F_Cu,pcbnew.B_Cu]:
  s=p.GetEffectivePolygon(l);print(p.GetNumber(),b.GetLayerName(l),s.OutlineCount(),[[mm(s.Outline(k).CPoint(i))for i in range(s.Outline(k).PointCount())]for k in range(s.OutlineCount())])
print([x for x in dir(f)if'Court' in x])
