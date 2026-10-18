import json,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
rows=[]
for name,p in [('ROOT103','reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb'),('BankB_before_Source27','reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb')]:
 b=pcbnew.LoadBoard(p);fs={f.GetReference():f for f in b.GetFootprints()};rows.append(dict(board=name,refs={r:dict(pose=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()),pins={q.GetNumber():mm(q.GetPosition())for q in fs[r].Pads()if q.GetNumber()})for r in['U11011','U11034','C11085','C11086','R11079','U11029']}))
o=Path('reports/motherboard-power-entry-20261001/Source27-current-root-pose-inspection-r530');o.mkdir();(o/'poses.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
