import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-actual-Source-collars-r14/motherboard-facing-health-Source-collars-candidate.kicad_pcb');ids=['2abd7d17-f54f-42af-ae0c-d3a8cc238aee','c11a1795-b5ee-4973-8d80-690235c74581','101c36f7-6e92-4bf8-833a-1dc8991187db','da3ee2fc-3b76-47c0-ab4d-da8cd2d563bd','e19f5a4a-8797-4ce8-a00d-4c884cc46739','84d7ee84-6b83-427c-889a-8b85dcea2e34'];ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
for u in ids:
 v=ts[u];pt=mm(v.GetPosition());near=[]
 for p in b.GetPads():
  if p.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
  px,py=mm(p.GetPosition());ang=math.radians(p.GetOrientationDegrees());dx=pt[0]-px;dy=pt[1]-py;x=dx*math.cos(ang)+dy*math.sin(ang);y=-dx*math.sin(ang)+dy*math.cos(ang);w,h=mm(p.GetSize());gap=math.hypot(max(abs(x)-w/2,0),max(abs(y)-h/2,0))-.1
  if gap<.2:near.append(dict(ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),point_mm=[px,py],size_mm=[w,h],angle=p.GetOrientationDegrees(),conservative_gap_mm=gap))
 print(u,pt,near,flush=True)
