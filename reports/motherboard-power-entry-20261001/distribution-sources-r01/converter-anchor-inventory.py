import json,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-supply-cells-priority-r29/motor-supply-cells-candidate.kicad_pcb');names=['C11027','C11028','C11029','C11088','C11044','C11045','C11046','L11001','L11002','R11022','R11037','U11010','U11011','U11012'];out=[]
for f in b.GetFootprints():
 if f.GetReference()in names:out.append(dict(ref=f.GetReference(),position=mm(f.GetPosition()),angle=f.GetOrientationDegrees(),pads=[dict(pin=p.GetNumber(),net=p.GetNetname(),point=mm(p.GetPosition()),size=mm(p.GetSize()))for p in f.Pads()]))
print(json.dumps(out,indent=2))
