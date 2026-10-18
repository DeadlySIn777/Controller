import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy,identity
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_local_signals import paths,GeometryIndex
from hardware_route_logic_return import segment_distance
B=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-pose-screen-r274/literal-retired-U19-local-input.kicad_pcb')
b=pcbnew.LoadBoard(str(B));fs={f.GetReference():f for f in b.GetFootprints()};fs['U11019'].SetPosition(xy((343,175)));fs['U11019'].SetOrientationDegrees(180);fs['C11078'].SetPosition(xy((342.1625,174.225)));fs['C11078'].SetOrientationDegrees(90);ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};g=FastGeometry(b);ground=ps['U11019','2'].GetNetname();positive=ps['U11019','5'].GetNetname()
for pt,net in [((343,176.8),positive),((343.75,176.8),ground),((344.5875,175),ground),((342.9125,173.45),ground),((338.9125,173.45),ground),((333.5875,186.05),ps['C11081','2'].GetNetname())]:
 print('VIA',pt,net,'NATIVE',all(g.clear([pt,pt],net,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]),flush=True)
for a,z,n,l,w in [((342.1625,175),(343,176.8),positive,pcbnew.F_Cu,.25),((342.1625,175),(343,176.8),positive,pcbnew.B_Cu,.25),((343.8375,175),(343.75,176.8),ground,pcbnew.F_Cu,.25),((343.8375,175),(344.5875,175),ground,pcbnew.F_Cu,.25),((343,176.8),(345.85,178),positive,pcbnew.B_Cu,.3),((342.1625,173.45),(342.9125,173.45),ground,pcbnew.B_Cu,.25),((343.75,176.8),(342.4125,178),ground,pcbnew.F_Cu,.25)]:
 print('PATH',a,z,b.GetLayerName(l),[p for p in paths(a,z)if g.clear(p,n,l,w)][:3],flush=True)
