from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import mm,identity
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/motherboard-U25-two-local-barrels-candidate.kicad_pcb');L=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-native-B-sliver-location-r01/location.json')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-native-B-sliver-items-r01');assert not O.exists();O.mkdir()
b=pcbnew.LoadBoard(str(B));l=pcbnew.B_Cu;row=json.loads(L.read_text())['rows'][0];p=pcbnew.VECTOR2I(*row['literal_integer_points'][0]);box=pcbnew.BOX2I(p-pcbnew.VECTOR2I(1500000,1500000),pcbnew.VECTOR2I(3000000,3000000));items=[]
for q in list(b.GetTracks())+list(b.GetPads()):
 if not q.IsOnLayer(l)or not q.GetBoundingBox().Intersects(box):continue
 r=dict(uuid=q.m_Uuid.AsString(),type=q.Type(),net=q.GetNetname(),bounds=str(q.GetBoundingBox()))
 if q.Type()==pcbnew.PCB_PAD_T:r.update(reference=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),center_mm=mm(q.GetPosition()),size_mm=mm(q.GetSize()))
 else:r.update(identity=identity(q))
 items.append(r)
zones=[]
for z in b.Zones():
 if z.GetIsRuleArea()or not z.IsOnLayer(l):continue
 fill=z.GetFilledPolysList(l)
 for i in range(fill.OutlineCount()):
  c=fill.Outline(i)
  if c.BBox().Intersects(box):
   pts=[tuple(c.CPoint(j))for j in range(c.PointCount())];near=[dict(index=j,point_mm=[pcbnew.ToMM(x)for x in v])for j,v in enumerate(pts)if box.Contains(pcbnew.VECTOR2I(*v))]
   zones.append(dict(uuid=z.m_Uuid.AsString(),net=z.GetNetname(),name=z.GetZoneName(),piece=i,point_in_fill=fill.Contains(p),near_vertices=near,min_thickness_mm=pcbnew.ToMM(z.GetMinThickness())))
write(O/'items.json',dict(board_sha256=sha(B),location=row,items=items,zones=zones));print(json.dumps(dict(items=items,zones=zones)),flush=True)
