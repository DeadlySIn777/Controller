"""Literal native local Ground escape from the field LED sink Source pin."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_owned_bypass_loops import Geometry
from hardware_bridge_owned_return_resources_r04 import legal_path
bp=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-clipped-reference-collars-r02/motherboard-motor-bank-A-clipped-reference-candidate.kicad_pcb')
b=pcbnew.LoadBoard(str(bp));g=Geometry(b);net='/motherboard_motors/FIELD_GND'
p=next(p for f in b.GetFootprints()if f.GetReference()=='U11026'for p in f.Pads()if p.GetNumber()=='2')
source=(pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y));signal=(329.0875,190.35)
rows=[]
for q in [(329.1,189.5),(329.2,189.5),(329.4,189.6),(329.1,191.2),(328.9,189.5)]:
 if not g.via(q,net)or math.dist(q,signal)>.9:continue
 # A local Source-ground escape cannot pass through the adjacent gate/VDD
 # lands. Try literal side escape and bounded native-clear detours.
 trial=[source,(325.7,191),(325.7,189),(q[0],189),q]
 path=trial if g.clear(trial,net,pcbnew.F_Cu,.2)else legal_path(source,q,net,pcbnew.F_Cu,g,10,True)
 if path:rows.append(dict(new_ground_via_xy_mm=q,actual_Source_ground_pin='U11026.2',source_xy_mm=source,actual_signal_via_xy_mm=signal,distance_mm=math.dist(q,signal),literal_F_Source_ground_escape_mm=path))
write(Path('reports/motherboard-return-zoning-20261001/motor-bank-A-field-sink-ground-proposal-r01.json'),dict(read_only=True,board_sha256=sha(bp),literal_return_net=net,rows=rows))
print('clear Source-backed field sink Ground escapes',len(rows),flush=True)
