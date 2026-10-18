"""Read actual local copper and pad geometry around the combined RAW feed conflict."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
p=Path('reports/motherboard-pcb-integration-20261001/source26-motor-bank-A-merged-native-r88')
b=pcbnew.LoadBoard(str(p/'motherboard-bounded-merged-candidate.kicad_pcb'))
rows=[]
for t in b.GetTracks():
 points=[mm(t.GetStart()),mm(t.GetEnd())]
 if any(270<=x<=273.5 and 176<=y<=180 for x,y in points):rows.append(dict(identity=identity(t),layer=b.GetLayerName(t.GetLayer()),type=t.Type()))
pads=[]
for q in b.GetPads():
 x,y=mm(q.GetPosition())
 if 269<=x<=274 and 175<=y<=181:pads.append(dict(ref=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),net=q.GetNetname(),pos=[x,y],size=mm(q.GetSize()),layers=q.GetLayerSet().FmtBin()))
out=dict(copper=rows,pads=pads)
(p/'RAW-conflict-actual-neighbors.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
