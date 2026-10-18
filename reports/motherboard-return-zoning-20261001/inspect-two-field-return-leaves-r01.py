"""Read actual native dangling field-return endpoints; no board mutation."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb');b.BuildConnectivity()
cu={t.m_Uuid.AsString():t for t in b.GetTracks()};rows=[]
for uid in('70dd1c72-0fd9-4558-a66d-4e8ccc7a422e','7b44c836-5f95-44e0-9b0a-12f7fcbc6cd7'):
 t=cu[uid];endpoints=[mm(t.GetStart()),mm(t.GetEnd())]
 pads=[dict(ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),net=p.GetNetname(),xy=mm(p.GetPosition()),layer=b.GetLayerName(p.GetParentFootprint().GetLayer()))for p in b.GetPads()if min(math.dist(pt,mm(p.GetPosition()))for pt in endpoints)<4]
 vias=[dict(uuid=v.m_Uuid.AsString(),net=v.GetNetname(),xy=mm(v.GetPosition()))for v in b.GetTracks()if v.Type()==pcbnew.PCB_VIA_T and v.GetNetname()==t.GetNetname()and min(math.dist(pt,mm(v.GetPosition()))for pt in endpoints)<6]
 rows.append(dict(uuid=uid,net=t.GetNetname(),endpoints=endpoints,nearby_pads=pads,nearby_same_net_vias=vias))
p=Path(__file__).parent/'two-field-return-leaves-native-r01.json';p.write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
