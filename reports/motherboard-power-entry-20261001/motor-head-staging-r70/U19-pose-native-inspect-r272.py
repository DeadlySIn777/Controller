import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
from hardware_place_owned_capacitors_native import side_box
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
b=pcbnew.LoadBoard(str(B));fs={f.GetReference():f for f in b.GetFootprints()}
for r in ['U11019','C11078','U11020','C11079']:
 f=fs[r];print('PART',r,mm(f.GetPosition()),f.GetOrientationDegrees(),side_box(f))
 for p in f.Pads():
  pt=mm(p.GetPosition());n=p.GetNetname();print('PAD',p.GetNumber(),pt,n)
  others=[(q.GetParentFootprint().GetReference(),q.GetNumber(),mm(q.GetPosition()))for q in b.GetPads()if q.GetNetname()==n and q.m_Uuid.AsString()!=p.m_Uuid.AsString()]
  if len(others)<8:print('OTHER',others)
  a=[dict(uuid=t.m_Uuid.AsString(),identity=identity(t))for t in b.GetTracks()if t.GetNetname()==n and (isinstance(t,pcbnew.PCB_VIA)and mm(t.GetPosition())==pt or not isinstance(t,pcbnew.PCB_VIA)and pt in [mm(t.GetStart()),mm(t.GetEnd())])];print('ATTACHED',a)
