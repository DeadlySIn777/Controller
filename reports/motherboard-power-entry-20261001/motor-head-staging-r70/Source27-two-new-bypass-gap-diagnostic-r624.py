import sys,json,hashlib,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_check_return_corridors import circle,copy_poly
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import mm,identity
from hardware_zone_motherboard_returns import split_polygons
B=Path('reports/motherboard-power-entry-20261001/Source27-power-repair-native-proof-r616/motherboard-Source27-private-power-repair-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-two-new-bypass-gap-diagnostic-r624');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p)for p in[B,Path(__file__)]};b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();c=NativeCollectedAnnulusCheck(b,{});ts={t.m_Uuid.AsString():t for t in b.GetTracks()};rows=[]
def missing(poly,layer,role):
 fill=c.reference('/LOGIC_GND',layer);q=copy_poly(poly);q.BooleanSubtract(fill);pieces=[]
 for p in split_polygons(q):
  bb=p.BBox();x0,y0=mm(pcbnew.VECTOR2I(bb.GetX(),bb.GetY()));x1,y1=mm(pcbnew.VECTOR2I(bb.GetRight(),bb.GetBottom()));near=[]
  for t in b.GetTracks():
   if not isinstance(t,pcbnew.PCB_VIA):continue
   pos=mm(t.GetPosition());dx=max(x0-pos[0],pos[0]-x1,0);dy=max(y0-pos[1],pos[1]-y1,0)
   if math.hypot(dx,dy)<1.5:near.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),position_mm=pos,distance_to_gap_bbox_mm=math.hypot(dx,dy)))
  pieces.append(dict(bounds_mm=[x0,y0,x1,y1],area_mm2=p.Area()/1e12,native_polygon=p.Format(False),nearby_real_barrels=sorted(near,key=lambda x:x['distance_to_gap_bbox_mm'])))
 rows.append(dict(role=role,reference_layer=b.GetLayerName(layer),actual_missing_area_mm2=q.Area()/1e12,pieces=pieces))
t=ts['2a89c372-2653-4dd5-bc0d-a7e3f6c3f341'];missing(corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.10)),pcbnew.In4_Cu,'C89 actual owning-VDD B local branch')
v=ts['ce0a6f1a-17c0-40cc-942e-b66435e0ac23']
for layer in[pcbnew.In1_Cu,pcbnew.In4_Cu]:
 c.reference('/LOGIC_GND',layer);r=v.GetWidth(pcbnew.F_Cu)/2+c.zone_clearance['/LOGIC_GND',layer]+pcbnew.FromMM(.02);ring=circle(tuple(v.GetPosition()),r+pcbnew.FromMM(.20));ring.BooleanSubtract(circle(tuple(v.GetPosition()),r));missing(ring,layer,'C90 real Source-positive transfer annulus')
assert all(sha(Path(p))==h for p,h in inputs.items());(O/'review.json').write_text(json.dumps(dict(input_hashes=inputs,rows=rows,no_board_or_source_mutation=True,guard_unchanged=True),indent=2));print(json.dumps([(r['role'],r['reference_layer'],r['actual_missing_area_mm2'],[p['bounds_mm']for p in r['pieces']])for r in rows]),flush=True)
