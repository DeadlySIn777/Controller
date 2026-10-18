"""Read-only exact narrow-feature diagnostic using frozen r07 Boolean order."""
import sys,json,hashlib,importlib.util,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_route_logic_return import identity,mm
B=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb')
A=Path('reports/motherboard-power-entry-20261001/Source27-power-repair-native-proof-r616/motherboard-Source27-private-power-repair-candidate.kicad_pcb')
H=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py')
O=Path('reports/motherboard-power-entry-20261001/Source27-exact-power-gap-localization-r620')
assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[B,A,H,Path(__file__)]}
spec=importlib.util.spec_from_file_location('frozen_r07',H);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
b=pcbnew.LoadBoard(str(B));a=pcbnew.LoadBoard(str(A))
bf=collect_native_reference_fills(b,{'/IO_3V3','/CORE_1V2'},[pcbnew.In2_Cu,pcbnew.In3_Cu]);af=collect_native_reference_fills(a,{'/IO_3V3','/CORE_1V2'},[pcbnew.In2_Cu,pcbnew.In3_Cu])
before=bf['/IO_3V3',pcbnew.In2_Cu];after=af['/IO_3V3',pcbnew.In2_Cu]
old=m.duplicate(before);old.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
opened=m.duplicate(old);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(before)
classified=m.duplicate(opened);classified.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
narrow=m.subtract(before,classified);precision=m.duplicate(after);precision.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
escaped=m.subtract(narrow,precision)
oldcu={t.m_Uuid.AsString():t for t in b.GetTracks()};newcu={t.m_Uuid.AsString():t for t in a.GetTracks()}
added={u:t for u,t in newcu.items()if u not in oldcu or identity(t)!=identity(oldcu[u])}
rows=[]
for i,piece in enumerate(split_polygons(escaped)):
 box=piece.BBox();x0,y0=mm(pcbnew.VECTOR2I(box.GetX(),box.GetY()));x1,y1=mm(pcbnew.VECTOR2I(box.GetRight(),box.GetBottom()))
 near=[]
 for uid,t in added.items():
  # Through barrels and exact In2 support affect this actual positive fill.
  if not isinstance(t,pcbnew.PCB_VIA)and t.GetLayer()!=pcbnew.In2_Cu:continue
  bb=t.GetBoundingBox();tx0,ty0=mm(pcbnew.VECTOR2I(bb.GetX(),bb.GetY()));tx1,ty1=mm(pcbnew.VECTOR2I(bb.GetRight(),bb.GetBottom()))
  dx=max(x0-tx1,tx0-x1,0);dy=max(y0-ty1,ty0-y1,0);distance=math.hypot(dx,dy)
  if distance<=2.:
   near.append(dict(uuid=uid,net=t.GetNetname(),layer=pcbnew.LayerName(t.GetLayer()),bounds_mm=[tx0,ty0,tx1,ty1],distance_to_gap_bbox_mm=distance,position_mm=mm(t.GetPosition())if isinstance(t,pcbnew.PCB_VIA)else None))
 rows.append(dict(index=i,area_mm2=piece.Area()/1e12,bounds_mm=[x0,y0,x1,y1],native_polygon=piece.Format(False),nearby_changed_conductors=sorted(near,key=lambda r:r['distance_to_gap_bbox_mm'])))
assert all(sha(Path(p))==h for p,h in inputs.items())
result=dict(passed=False,diagnostic_only=True,input_hashes=inputs,guard_unchanged=True,CORE1V2_native_fill_identical=m.symmetric_equal(bf['/CORE_1V2',pcbnew.In3_Cu],af['/CORE_1V2',pcbnew.In3_Cu]),escaped_narrow_native_polygons=escaped.Format(False),escaped_piece_count=len(rows),escaped_area_mm2=escaped.Area()/1e12,rows=rows,no_native_or_source_mutation=True)
(O/'review.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(pieces=len(rows),area_mm2=result['escaped_area_mm2'],bounds=[r['bounds_mm']for r in rows])),flush=True)
