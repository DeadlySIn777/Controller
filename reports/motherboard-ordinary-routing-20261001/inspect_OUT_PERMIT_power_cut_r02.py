from pathlib import Path
import sys,json
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent.resolve())]
import pcbnew
import check_io3_backbone_preservation_r01 as p
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
base=Path('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb')
out=Path(__file__).parent/'actual-source26-root81-OUT-PERMIT-r06'
boards=[pcbnew.LoadBoard(str(x))for x in(base,out/'motherboard-OUT-PERMIT-common-In1-candidate.kicad_pcb')]
b,a=[collect_native_reference_fills(x,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu]for x in boards]
er=p.duplicate(b);er.Deflate(pcbnew.FromMM(.501),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
opened=p.duplicate(er);opened.Inflate(pcbnew.FromMM(.501),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(b)
narrow=p.subtract(b,opened);removed=p.subtract(b,a);expanded=p.duplicate(a);expanded.Inflate(2,pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);hit=p.subtract(narrow,expanded)
rows=[]
for poly in split_polygons(hit):
 box=poly.BBox();rows.append(dict(area_mm2=poly.Area()/1e12,bbox_mm=[box.GetLeft()/1e6,box.GetTop()/1e6,box.GetRight()/1e6,box.GetBottom()/1e6],native=poly.Format(False)))
report=dict(actual_removed_area_mm2=removed.Area()/1e12,actual_narrow_cut_area_mm2=hit.Area()/1e12,actual_cuts=rows)
(out/'actual-power-precision-escape-localization.json').write_text(json.dumps(report,indent=2))
print(json.dumps({**report,'actual_cuts':[{k:v for k,v in x.items()if k!='native'}for x in rows]},indent=2))
