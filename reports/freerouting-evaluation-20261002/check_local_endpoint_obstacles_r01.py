"""Read-only diagnostic: selected native source pad centers against exported blockers."""
from pathlib import Path
import sys,json,hashlib,collections
root=Path.cwd();sys.path[:0]=[str(root/'tools'),str(Path(__file__).parent)]
import pcbnew
import hardware_route_selected_additive_r02 as e
from independent_obstacle_geometry import Polygon,unary_union
from shapely.geometry import Point
pre=root/'reports/freerouting-evaluation-20261002/ROOT103-visual-local-window-DSN-r06'
board=pre/'base.kicad_pcb';dsn=pre/'selected.dsn'
out=root/'reports/freerouting-evaluation-20261002/ROOT103-local-endpoint-obstacles-r01';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p)for p in(board,dsn,Path(__file__))}
tree=e.parse(dsn.read_text());structure=e.child(tree,'structure');bylayer=collections.defaultdict(list)
for k in e.children(structure,'keepout'):
 p=e.child(k,'polygon');layer=e.value(p[1]);coords=[(float(p[i]),float(p[i+1]))for i in range(3,len(p),2)]
 bylayer[layer].append((e.value(k[1]),Polygon(coords)))
unions={k:unary_union([p for name,p in rows])for k,rows in bylayer.items()}
b=pcbnew.LoadBoard(str(board));nets=set(json.loads((pre/'prepare.json').read_text())['selection']['selected_nets']);rows=[]
for p in b.GetPads():
 if p.GetNetname()not in nets:continue
 # KiCad DSN coordinates are um; its own resolution is retained unchanged.
 pos=p.GetPosition();q=Point(pos.x/1000,-pos.y/1000)
 layers=[]
 for layer in ('F.Cu','In2.Cu','In3.Cu','B.Cu'):
  blockers=[name for name,g in bylayer[layer]if g.covers(q)]
  layers.append(dict(layer=layer,pad_center_blocked=bool(blockers),covering_obstacles=blockers,distance_to_obstacle_um=unions[layer].distance(q)))
 rows.append(dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),net=p.GetNetname(),native_position_mm=[pos.x/1e6,pos.y/1e6],native_pad_size_mm=[p.GetSize().x/1e6,p.GetSize().y/1e6],front_copper_pad=p.IsOnLayer(pcbnew.F_Cu),back_copper_pad=p.IsOnLayer(pcbnew.B_Cu),layers=layers))
assert len(rows)==4 and all(sha(Path(p))==h for p,h in before.items())
r=dict(diagnostic_executed=True,input_sha256=before,rows=rows,scope='Pad-center blocker query only; not complete track-width/clearance/route reachability proof.',geometry_changed=False,manufacturing_ready=False)
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(rows),flush=True)
