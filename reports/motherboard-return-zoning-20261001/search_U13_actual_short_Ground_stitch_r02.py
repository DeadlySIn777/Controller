"""Bounded off-land conventional Ground stitch for the actual U13.2 pin."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_logic_return import mm
from hardware_map_motherboard_domains import write,sha
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/motherboard-U25-two-local-barrels-candidate.kicad_pcb');O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U13-short-Ground-native-preflight-r02');assert not O.exists();O.mkdir()
b=pcbnew.LoadBoard(str(B));g=Geometry(b);kept=[]
for z in g.keepouts:
 q=z.Outline().BBox();a=[pcbnew.ToMM(v)for v in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom())]
 if not(a[2]<332 or a[0]>337 or a[3]<189 or a[1]>194):kept.append(z)
g.keepouts=kept;pad=next(p for f in b.GetFootprints()if f.GetReference()=='U11013'for p in f.Pads()if p.GetNumber()=='2');s=mm(pad.GetPosition());net=pad.GetNetname();rows=[]
for x in [334.65+i*.05 for i in range(8)]:
 for y in [190.8+i*.05 for i in range(9)]:
  q=round(x,5),round(y,5)
  if math.dist(s,q)<=1.2 and g.via(q,net)and g.clear([s,q],net,pcbnew.F_Cu,.25):rows.append(dict(position=q,actual_pin_path=[s,q],path_length_mm=math.dist(s,q)))
rows.sort(key=lambda r:r['path_length_mm']);write(O/'search.json',dict(passed=bool(rows),board_sha256=sha(B),actual_Source_pad='U11013.2',literal_return_net=net,candidates=rows,source_reference_native_annuli_and_power_checks_pending=True));print(json.dumps(dict(passed=bool(rows),best=rows[:3])),flush=True)
