import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import xy,mm
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()}
poses={'U11010':((272,179),0),'C11057':((270.2,177),90),'C11058':((275.25,178.5),0),'R11042':((267,181.5),0),'R11043':((267,193),0),'R11044':((267,184.5),0),'U11031':((257,196),0),'U11032':((264,197),0),'U11033':((252,196),0),'R11076':((257,201),0),'R11080':((252,201),0),'C11082':((267.5,199.5),0),'C11083':((264,194),0),'C11084':((257,193),0),'C11087':((252,193),0),'R11074':((269,220.5),0),'R11075':((269,199.5),0),'U11021':((274,229),0),'U11022':((274,234),0),'U11027':((286,229),180),'U11028':((286,234),180),'R11067':((268,228.365),0),'R11071':((293,229.635),0)}
for r,(p,a)in poses.items():
 if r.startswith('C')and fs[r].GetLayer()!=pcbnew.B_Cu:fs[r].Flip(fs[r].GetPosition(),False)
 fs[r].SetPosition(xy(p));fs[r].SetOrientationDegrees(a)
for r in poses:
 f=fs[r];clash=[v.GetReference()for v in b.GetFootprints()if v.GetReference()!=r and v.GetLayer()==f.GetLayer()and intersects(side_box(f),side_box(v),0)];print(r,'CLASH',clash,flush=True)
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankA-poses.json').write_text(json.dumps(poses,indent=2))


