"""Suggest ground vias from actual filled islands and conservative geometry."""
from pathlib import Path
import json
router=Path(__file__).with_name('route_candidate.py')
exec(compile(router.read_text().split('nets={')[0],str(router),'exec'))
_,via_blocked=obstacles('/GND')
ground_pads=[(f.GetReference()+'.'+a.GetNumber(),a) for f in board.GetFootprints() for a in f.Pads() if a.GetNetname()=='/GND']
ground_vias=[a for a in board.GetTracks() if isinstance(a,p.PCB_VIA) and a.GetNetname()=='/GND']
suggestions=[]
for zone in board.Zones():
    layer=zone.GetLayer()
    if layer not in (p.F_Cu,p.B_Cu):continue
    poly=zone.GetFilledPolysList(layer)
    for i in range(poly.OutlineCount()):
        pads=[(r,a) for r,a in ground_pads if a.IsOnLayer(layer) and poly.Contains(a.GetPosition(),i)]
        if not pads or any(poly.Contains(a.GetPosition(),i) for a in ground_vias):continue
        bb=poly.COutline(i).BBox()
        candidates=[]
        for xx in range(max(0,round((p.ToMM(bb.GetLeft())-100)/S)),min(NX,round((p.ToMM(bb.GetRight())-100)/S)+1)):
            for yy in range(max(0,round((p.ToMM(bb.GetTop())-100)/S)),min(NY,round((p.ToMM(bb.GetBottom())-100)/S)+1)):
                if via_blocked[xx,yy]:continue
                point=p.VECTOR2I(p.FromMM(100+xx*S),p.FromMM(100+yy*S))
                if poly.Contains(point,i):
                    dist=min(math.hypot(p.ToMM(a.GetPosition().x-point.x),p.ToMM(a.GetPosition().y-point.y)) for _,a in pads)
                    candidates.append((dist,[round(xx*S,3),round(yy*S,3)]))
        candidates.sort()
        out={'layer':board.GetLayerName(layer),'pads':[r for r,_ in pads],'candidate':candidates[0][1] if candidates else None,'count':len(candidates)}
        print(out);suggestions.append(out)
(ROOT/'ground-stitch-proposal.json').write_text(json.dumps(suggestions,indent=2))
