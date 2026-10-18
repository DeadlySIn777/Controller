import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy
from hardware_route_power_groups_native import hits
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/io3-positive-delivery-r08/io3-positive-delivery-candidate.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()};f=fs['C11069'];omit={'C11068','C11069','C11070'}
obstacles=[]
for q in b.GetPads():
 if q.GetParentFootprint().GetReference()in omit or not q.IsOnLayer(pcbnew.B_Cu):continue
 if not(338<mm(q.GetPosition())[0]<358 and 170<mm(q.GetPosition())[1]<193):continue
 poly=q.GetEffectivePolygon(pcbnew.B_Cu);obstacles.append((q.GetNetname(),poly))
tracks=[t for t in b.GetTracks()if t.IsOnLayer(pcbnew.B_Cu)and min(mm(t.GetStart())[0],mm(t.GetEnd())[0])<358 and max(mm(t.GetStart())[0],mm(t.GetEnd())[0])>338 and min(mm(t.GetStart())[1],mm(t.GetEnd())[1])<193 and max(mm(t.GetStart())[1],mm(t.GetEnd())[1])>170];courts=[(r,side_box(q))for r,q in fs.items()if r not in omit and q.GetLayer()==pcbnew.B_Cu];ans=[];vin=next(p for p in fs['U11015'].Pads()if p.GetNumber()=='1');gp=next(p for p in fs['U11015'].Pads()if p.GetNumber()=='6')
for rot in[0,90,180,270]:
 for ix in range(47):
  for iy in range(41):
   pt=(342+ix*.25,176+iy*.25);f.SetPosition(xy(pt));f.SetOrientationDegrees(rot);box=side_box(f)
   if any(intersects(box,b,0)for _,b in courts):continue
   ok=True
   for p in f.Pads():
    ps=p.GetEffectivePolygon(pcbnew.B_Cu);poly=[[mm(ps.Outline(k).CPoint(i))for i in range(ps.Outline(k).PointCount())]for k in range(ps.OutlineCount())]
    for net,pp in obstacles:
     if net==p.GetNetname():continue
     test=pcbnew.SHAPE_POLY_SET(ps);test.Inflate(pcbnew.FromMM(.16),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.01));test.BooleanIntersection(pp)
     if test.OutlineCount():ok=False;break
    if not ok:break
    for t in tracks:
     if t.GetNetname()==p.GetNetname():continue
     width=pcbnew.ToMM(t.GetWidth(pcbnew.B_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth());s,e=mm(t.GetStart()),mm(t.GetEnd())
     if any(hits(s,e,q,width/2+.25)for q in poly):ok=False;break
    if not ok:break
   if ok:
    p1=next(p for p in f.Pads()if p.GetNumber()=='1');p2=next(p for p in f.Pads()if p.GetNumber()=='2');score=math.dist(mm(p1.GetPosition()),mm(vin.GetPosition()))+math.dist(mm(p2.GetPosition()),mm(gp.GetPosition()));ans.append((score,pt,rot,mm(p1.GetPosition()),mm(p2.GetPosition())))
print(json.dumps(sorted(ans)[:35]))



