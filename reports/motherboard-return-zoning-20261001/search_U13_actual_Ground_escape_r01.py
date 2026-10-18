"""Exact Source-owned Ground path preserving the old U13.2 dependency."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_local_signals import paths
from hardware_route_logic_return import mm
from hardware_map_motherboard_domains import write,sha
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/motherboard-U25-two-local-barrels-candidate.kicad_pcb');O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U13-actual-Ground-native-preflight-r01');assert not O.exists();O.mkdir()
b=pcbnew.LoadBoard(str(B));g=Geometry(b);envelope=(324,181,344,203);kept=[]
for z in g.keepouts:
 q=z.Outline().BBox();a=[pcbnew.ToMM(v)for v in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom())]
 if not(a[2]<envelope[0]or a[0]>envelope[2]or a[3]<envelope[1]or a[1]>envelope[3]):kept.append(z)
g.keepouts=kept;pad=next(p for f in b.GetFootprints()if f.GetReference()=='U11013'for p in f.Pads()if p.GetNumber()=='2');via=next(t for t in b.GetTracks()if t.m_Uuid.AsString()=='9557a691-472b-4af0-87c3-b0e91cf52409');s,e=mm(pad.GetPosition()),mm(via.GetPosition());net=pad.GetNetname();assert net==via.GetNetname();rows=[]
for ps in paths(s,e):
 if g.clear(ps,net,pcbnew.F_Cu,.25):rows.append(dict(points=ps,length_mm=sum(math.dist(a,z)for a,z in zip(ps,ps[1:]))))
rows.sort(key=lambda r:r['length_mm']);write(O/'search.json',dict(passed=bool(rows),board_sha256=sha(B),actual_Source_pad='U11013.2',Source_Ground_via=via.m_Uuid.AsString(),literal_return_net=net,candidates=rows));print(json.dumps(dict(passed=bool(rows),best=rows[:3])),flush=True)
