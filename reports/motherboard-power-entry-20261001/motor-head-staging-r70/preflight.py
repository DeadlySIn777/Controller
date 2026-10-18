import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import xy,mm,identity
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
from hardware_route_current_delivery_native import Geometry
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb');b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};refs=['U11010','U11011','C11057','C11058','C11059','C11060'];co=b.GetConnectivity()
r=json.loads(Path('reports/motherboard-power-entry-20261001/motor-supply-cells-priority-r29/receipt.json').read_text());ret={v['uuid']for v in r['new_copper']if v['role'].startswith(('C11057_','C11058_','C11060_'))}
print('retirelocal',len(ret))
for t in list(b.GetTracks()):
 if t.GetNetname()in ['/motherboard_power_entry/MOTOR_FEED_ON_A','/motherboard_power_entry/MOTOR_FEED_ON_B']:ret.add(t.m_Uuid.AsString())
rr=[t for t in b.GetTracks()if t.m_Uuid.AsString()in ret]
for t in rr:b.Remove(t)
poses={'U11010':((276,179),0),'U11011':((276,186),0),'C11057':((274.2,177),90),'C11058':((279.25,178.5),0),'C11059':((274.2,184),90),'C11060':((279.25,185.5),0)}
for n,(p,a)in poses.items():fs[n].SetPosition(xy(p));fs[n].SetOrientationDegrees(a)
for n in refs:
 f=fs[n]; box=side_box(f);bad=[other.GetReference()for other in b.GetFootprints()if other.GetReference()!=n and other.GetLayer()==f.GetLayer()and intersects(box,side_box(other),0)];print(n,mm(f.GetPosition()),box,'COLLISIONS',bad)
g=Geometry(b)
for ref in refs:
 for p in fs[ref].Pads():
  pt=mm(p.GetPosition());n=p.GetNetname();print('PAD',ref,p.GetNumber(),pt,n)
for s,e,w,n,lay in [((266.2,171),(266,177),4,'/motherboard_power_entry/MOTION_5V_RAW',pcbnew.F_Cu),((266,177),(276,179),1.6,'/motherboard_power_entry/MOTION_5V_RAW',pcbnew.B_Cu),((276,179),(276,186),1.6,'/motherboard_power_entry/MOTION_5V_RAW',pcbnew.B_Cu),((271.8,171),(276,171),4,'/LOGIC_GND',pcbnew.F_Cu),((276,171),(282,177),6,'/LOGIC_GND',pcbnew.F_Cu),((282,177),(282,190),6,'/LOGIC_GND',pcbnew.F_Cu)]:print('PATH',s,e,w,n,b.GetLayerName(lay),g.clear([s,e],n,lay,w))
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/poses.json').write_text(json.dumps(poses,indent=2))
