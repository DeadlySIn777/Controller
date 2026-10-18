"""Locate actual rejected IO3 cuts; no tolerance or acceptance change."""
from pathlib import Path
import sys,json,math
sys.path[:0]=[str(Path('tools').resolve()),str(Path('reports/motherboard-ordinary-routing-20261001').resolve())]
import pcbnew
import check_io3_backbone_preservation_r07 as power
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_route_logic_return import mm,distance
p=Path(__file__).parent;out=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U19-merged-trial-r98')
before=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/IO3-BankA-unused-pour-cleanup-baseline-r95a/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb');after=pcbnew.LoadBoard(str(out/'motherboard-bounded-merged-candidate.kicad_pcb'))
b=collect_native_reference_fills(before,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu];a=collect_native_reference_fills(after,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu]
old=power.duplicate(b);old.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened=power.duplicate(old);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(b);opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
narrow=power.subtract(b,opened);expanded=power.duplicate(a);expanded.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);cut=power.subtract(narrow,expanded)
tracks=list(after.GetTracks())
rows=[]
for part in split_polygons(cut):
 contour=part.COutline(0);points=[tuple(contour.CPoint(i))for i in range(contour.PointCount())];xs,ys=zip(*points);bbox=[min(xs)/1e6,min(ys)/1e6,max(xs)/1e6,max(ys)/1e6];center=((bbox[0]+bbox[2])/2,(bbox[1]+bbox[3])/2)
 near=sorted([(distance(center,mm(t.GetStart()),mm(t.GetEnd())),t)for t in tracks],key=lambda q:q[0])[:4]
 rows.append(dict(area_mm2=part.Area()/1e12,bounds_mm=bbox,native_polygon=part.Format(False),nearby_new_Cu=[dict(distance_mm=d,uuid=t.m_Uuid.AsString(),net=t.GetNetname(),layer=after.GetLayerName(t.GetLayer()),start_mm=mm(t.GetStart()),end_mm=mm(t.GetEnd()))for d,t in near]))
result=dict(board_sha256=power.sha(out/'motherboard-bounded-merged-candidate.kicad_pcb'),rejected_native_power_cut_components=rows,exact_native_cut=cut.Format(False),diagnostic_only=True,no_acceptance_exception=True)
(out/'rejected-power-cut-location.json').write_text(json.dumps(result,indent=2));print(json.dumps([dict(area=r['area_mm2'],bounds=r['bounds_mm'],closest=r['nearby_new_Cu'][0])for r in rows],indent=2))

