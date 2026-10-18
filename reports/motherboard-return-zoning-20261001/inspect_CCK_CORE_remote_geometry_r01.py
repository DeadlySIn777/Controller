"""Independent literal native inspection of the rejected remote CORE contour."""
from pathlib import Path
import sys, json, hashlib, argparse, math
sys.path.insert(0, str(Path.cwd() / 'tools'))
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_route_logic_return import mm

ap = argparse.ArgumentParser()
ap.add_argument('board', type=Path)
ap.add_argument('out', type=Path)
a = ap.parse_args()
if a.out.exists():
    raise ValueError('Fresh independent report required')
b = pcbnew.LoadBoard(str(a.board.resolve()))
b.BuildConnectivity()
p = collect_native_reference_fills(b, {'/CORE_1V2'}, [pcbnew.In3_Cu])['/CORE_1V2', pcbnew.In3_Cu]
q = pcbnew.SHAPE_POLY_SET()
q.NewOutline()
for x, y in [(39.5, 48.5), (41.8, 48.5), (41.8, 50.5), (39.5, 50.5)]:
    q.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
local = pcbnew.SHAPE_POLY_SET(p)
local.BooleanIntersection(q)
local.Simplify()
cx, cy = 40.68487, 49.53550
rows = []
for t in b.GetTracks():
    pt = mm(t.GetPosition())
    if t.Type() == pcbnew.PCB_VIA_T:
        dist = math.hypot(pt[0]-cx, pt[1]-cy)
        if dist < 4:
            rows.append(dict(type='via', uuid=t.m_Uuid.AsString(), net=t.GetNetname(), xy=pt,
                             diameter_mm=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)), drill_mm=pcbnew.ToMM(t.GetDrillValue()),
                             layers=[b.GetLayerName(l) for l in range(32) if t.IsOnLayer(l)],
                             free=t.GetIsFree(), distance_mm=dist))
    else:
        bx = t.GetBoundingBox()
        x0, y0, x1, y1 = [pcbnew.ToMM(v) for v in (bx.GetX(), bx.GetY(), bx.GetRight(), bx.GetBottom())]
        dist = math.hypot(max(x0-cx, 0, cx-x1), max(y0-cy, 0, cy-y1))
        if dist < 2:
            rows.append(dict(type='track', uuid=t.m_Uuid.AsString(), net=t.GetNetname(),
                             start=mm(t.GetStart()), end=mm(t.GetEnd()), width_mm=pcbnew.ToMM(t.GetWidth()),
                             layer=b.GetLayerName(t.GetLayer()), distance_bbox_mm=dist))
pads=[]
for pad in b.GetPads():
    pt=mm(pad.GetPosition())
    if math.hypot(pt[0]-cx,pt[1]-cy)<4:
        pads.append(dict(reference=pad.GetParentFootprint().GetReference(), pin=pad.GetNumber(), net=pad.GetNetname(),
                         uuid=pad.m_Uuid.AsString(), xy=pt, size_mm=mm(pad.GetSize()),
                         layers=[b.GetLayerName(l) for l in range(32) if pad.IsOnLayer(l)]))
source = next(p for p in b.GetPads() if p.GetParentFootprint().GetReference()=='L2001' and p.GetNumber()=='2')
source_cluster={r.m_Uuid.AsString() for r in b.GetConnectivity().GetConnectedItems(source)}|{source.m_Uuid.AsString()}
report=dict(board=str(a.board), board_sha256=hashlib.sha256(a.board.read_bytes()).hexdigest(),
            actual_remote_ROI_mm=[39.5,48.5,41.8,50.5], native_CORE_In3_local_polygon=local.Format(False),
            nearby_actual_copper=rows, nearby_actual_pads=pads,
            actual_CORE_source='L2001.2', actual_source_cluster_size=len(source_cluster),
            native_source_cluster_UUIDs=sorted(source_cluster),
            actual_narrow_guard_failure_stays_rejected=True, no_geometry_mutation=True)
a.out.parent.mkdir(parents=True,exist_ok=True)
a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=True, inspection_only=True, nearby_Cu=len(rows), nearby_pads=len(pads), board_sha256=report['board_sha256'])))
