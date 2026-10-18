import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-return-motor-r53/motherboard-bounded-merged-candidate.kicad_pcb')
rows=[]
for t in b.GetTracks():
 a,c=mm(t.GetStart()),mm(t.GetEnd())
 if t.GetNetname()=='/motherboard_motors/FIELD_GND' and t.IsOnLayer(pcbnew.B_Cu) and min(a[0],c[0])<410 and max(a[0],c[0])>350 and min(a[1],c[1])<157 and max(a[1],c[1])>130:rows.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),start=a,end=c))
print(json.dumps(rows,indent=2))
