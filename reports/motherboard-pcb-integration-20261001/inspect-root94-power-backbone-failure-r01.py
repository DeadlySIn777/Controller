"""Locate actual narrowed IO3 geometry without changing acceptance criteria."""
from pathlib import Path
import sys,json
sys.path[:0]=[str(Path('tools').resolve()),str(Path('reports/motherboard-ordinary-routing-20261001').resolve())]
import pcbnew
import check_io3_backbone_preservation_r07 as p
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_populate_motherboard_pcb import sha,write
root=Path('reports/motherboard-pcb-integration-20261001')
before=root/'source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb'
after=root/'source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb'
b=pcbnew.LoadBoard(str(before));a=pcbnew.LoadBoard(str(after))
def fill(board):return collect_native_reference_fills(board,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu]
def bounds(shape):
 box=shape.BBox();return [pcbnew.ToMM(v)for v in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())]
oldraw,newraw=fill(b),fill(a)
old,new=p.duplicate(oldraw),p.duplicate(newraw)
for q in(old,new):q.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
np=list(split_polygons(new));failed=[]
for i,op in enumerate(split_polygons(old)):
 owners=[j for j,v in enumerate(np)if p.intersection(op,v).OutlineCount()]
 if len(owners)!=1:
  failed.append(dict(old_component=i,old_bbox=bounds(op),new_components=[dict(index=j,bbox=bounds(np[j]),actual_area_mm2=np[j].Area()/1e12)for j in owners]))
lost=p.subtract(old,new)
cuts=sorted([dict(bbox=bounds(piece),area_mm2=piece.Area()/1e12)for piece in split_polygons(lost)],key=lambda x:x['area_mm2'],reverse=True)
report=dict(board_sha256=sha(after),before_sha256=sha(before),failed_components=failed,eroded_power_lost_pieces=cuts,acceptance_guard_unchanged=True,adopted=False)
write(after.parent/'rejected-power-backbone-location.json',report)
print(json.dumps(dict(failed_components=failed,largest_eroded_losses=cuts[:25]),indent=2))
