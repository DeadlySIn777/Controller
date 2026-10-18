import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/Source27-A-slow-local-circuit-r552/motherboard-Source27-A-slow-local-candidate.kicad_pcb')
f={f.GetReference():f for f in b.GetFootprints()};rows=[]
for r in ['C11089','C11090','C11091','C11092']:
 for p in f[r].Pads():
  q=mm(p.GetPosition());attached=[]
  for t in b.GetTracks():
   if t.GetNetname()==p.GetNetname() and (mm(t.GetStart())==q or mm(t.GetEnd())==q):attached.append(dict(identity=identity(t),uuid=t.m_Uuid.AsString()))
  rows.append(dict(ref=r,pin=p.GetNumber(),point=q,net=p.GetNetname(),attached=attached))
print(json.dumps(rows,indent=2))
