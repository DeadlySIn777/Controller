"""Exact frozen-r07 rejection geometry and nearby native metal, no mutation."""
import sys,json,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import mm
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
P=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py');sp=importlib.util.spec_from_file_location('r07',P);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
BASE=Path('reports/motherboard-pcb-integration-20261001/IO3-BankA-complete-antipad-cleanup-baseline-r99a-r02/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb')
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(B));bf=collect_native_reference_fills(before,{'/IO_3V3'},[pcbnew.In2_Cu]);af=collect_native_reference_fills(after,{'/IO_3V3'},[pcbnew.In2_Cu]);p=bf['/IO_3V3',pcbnew.In2_Cu];q=af['/IO_3V3',pcbnew.In2_Cu]
old=m.duplicate(p);old.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened=m.duplicate(old);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(p);opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);narrow=m.subtract(p,opened);aq=m.duplicate(q);aq.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);escaped=m.subtract(narrow,aq);rows=[]
for piece in split_polygons(escaped):
 bb=piece.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];near=[]
 for t in after.GetTracks():
  if t.Type()!=pcbnew.PCB_VIA_T:continue
  xy=mm(t.GetPosition())
  if bounds[0]-2<=xy[0]<=bounds[2]+2 and bounds[1]-2<=xy[1]<=bounds[3]+2:near.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),xy_mm=xy))
 rows.append(dict(bounds_mm=bounds,area_mm2=piece.Area()/1e12,exact_native_polygon=piece.Format(False),nearest_actual_vias=near))
write(B.parent/'actual-global-IO3-r07-rejection-location.json',dict(board_sha256=sha(B),baseline_sha256=sha(BASE),frozen_r07_sha256=sha(P),guard_unchanged=True,rejected_polygons=rows));print(json.dumps(rows),flush=True)
