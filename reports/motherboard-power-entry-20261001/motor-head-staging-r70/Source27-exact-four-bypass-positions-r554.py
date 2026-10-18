import json,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/Source27-A-slow-local-circuit-r552/motherboard-Source27-A-slow-local-candidate.kicad_pcb');ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};rows=[]
for c,u,p in [('C11089','U11035','6'),('C11090','U11036','5'),('C11091','U11037','6'),('C11092','U11038','5')]:
 rows.append(dict(cap=c,owner=u,power_cap=mm(ps[c,'1'].GetPosition()),power_owner=mm(ps[u,p].GetPosition()),return_cap=mm(ps[c,'2'].GetPosition()),return_owner=mm(ps[u,'2'if u in['U11035','U11037']else'3'].GetPosition())))
print(json.dumps(rows,indent=2))
