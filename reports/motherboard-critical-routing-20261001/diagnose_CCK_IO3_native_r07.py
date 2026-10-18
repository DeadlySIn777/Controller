"""Read-only exact native lost-IO3-feature ledger; no routing guard changes."""
from pathlib import Path
import sys,json,math
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_CORE_preservation_r04 as core
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_route_logic_return import mm,identity
f=core.f;P=Path(__file__).parent;O=P/'CCK-IO3-lost-features-native-r07';O.mkdir(exist_ok=False)
B=P/'CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb'
A=P/'actual-source26-root84-FPGA-CCK-C1022-In2-knot-r08/motherboard-FPGA-flash-CCK-candidate.kicad_pcb'
b,a=pcbnew.LoadBoard(str(B)),pcbnew.LoadBoard(str(A));b.BuildConnectivity();a.BuildConnectivity()
bp=collect_native_reference_fills(b,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu]
ap=collect_native_reference_fills(a,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu]
eroded=f.duplicate(bp);eroded.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
opened=f.duplicate(eroded);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(bp);opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
narrow=f.subtract(bp,opened);precision=f.duplicate(ap);precision.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
lost=f.subtract(narrow,precision);removed=f.subtract(bp,ap)
old={x.m_Uuid.AsString() for x in b.GetTracks()};new=[t for t in a.GetTracks() if t.m_Uuid.AsString() not in old]
rows=[]
for n,p in enumerate(split_polygons(lost)):
    box=p.BBox();bounds=[pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom())];cx=(bounds[0]+bounds[2])/2;cy=(bounds[1]+bounds[3])/2
    def dist(t):
        if t.Type()==pcbnew.PCB_VIA_T:return math.dist(mm(t.GetPosition()),(cx,cy))
        u,v=mm(t.GetStart()),mm(t.GetEnd());dx,dy=v[0]-u[0],v[1]-u[1];q=max(0,min(1,((cx-u[0])*dx+(cy-u[1])*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
        return math.dist((u[0]+q*dx,u[1]+q*dy),(cx,cy))
    near=sorted(new,key=dist)[:3]
    rows.append(dict(index=n,bounds_mm=bounds,area_mm2=p.Area()/1e12,native_polygon=p.Format(False),nearest_new_Cu=[dict(uuid=t.m_Uuid.AsString(),distance_mm=dist(t),net=t.GetNetname(),native_identity=identity(t)) for t in near]))
native_zone_settings=[dict(uuid=z.m_Uuid.AsString(),minimum_thickness_mm=pcbnew.ToMM(z.GetMinThickness()),local_clearance_mm=pcbnew.ToMM(z.GetLocalClearance()))for z in a.Zones()if z.GetNetname()=='/IO_3V3'and z.IsOnLayer(pcbnew.In2_Cu)and not z.GetIsRuleArea()]
result=dict(native_IO3_zone_settings=native_zone_settings,passed=False,scope='Read-only diagnosis of unchanged r07 rejected IO3 definite thin features',before_sha256=core.sha(B),after_sha256=core.sha(A),frozen_power_helper_sha256=core.sha(core.FROZEN),lost_piece_count=len(rows),exact_lost_piece_ledger=rows,all_removed_native_polygon=removed.Format(False),all_removed_area_mm2=removed.Area()/1e12,original_guard_failure_preserved=True,no_acceptance_from_area_or_distance=True,manufacturing_ready=False)
(O/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(lost_piece_count=len(rows),bounds=[r['bounds_mm'] for r in rows],native_IO3_zone_settings=native_zone_settings)))
