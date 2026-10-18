from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,distance
p=Path(__file__).parent/'actual-source26-root83-In2-batch-r12';b=pcbnew.LoadBoard(str(p/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'));point=(91.13,211.2)
rows=[]
for pad in b.GetPads():
 d=math.dist(point,mm(pad.GetPosition()))
 if d<3:rows.append(dict(kind='pad',d=d,ref=pad.GetParentFootprint().GetReference(),pin=pad.GetNumber(),net=pad.GetNetname(),point=mm(pad.GetPosition()),size=mm(pad.GetSize()),layers=[b.GetLayerName(l)for l in range(0,32)if pad.IsOnLayer(l)]))
for t in b.GetTracks():
 d=distance(point,mm(t.GetStart()),mm(t.GetEnd()))
 if d<2 and(t.Type()==pcbnew.PCB_VIA_T or t.IsOnLayer(pcbnew.In2_Cu)):rows.append(dict(kind='via'if t.Type()==pcbnew.PCB_VIA_T else'trace',d=d,uuid=t.m_Uuid.AsString(),net=t.GetNetname(),start=mm(t.GetStart()),end=mm(t.GetEnd()),width=t.GetWidth()/1e6))
(p/'local-power-cut-items.json').write_text(json.dumps(sorted(rows,key=lambda r:r['d']),indent=2));print(json.dumps(sorted(rows,key=lambda r:r['d']),indent=2))
