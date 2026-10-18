import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import xy,mm
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()}
poses={'U11010':((272,179),0),'C11057':((270.2,177),90),'C11058':((275.25,178.5),0),'R11042':((267,181.5),0),'R11043':((267,195.5),0),'R11044':((267,184.5),0),'U11031':((259.5,188.5),0),'U11032':((264.5,188.5),0),'U11033':((255.5,188.5),0),'R11076':((258,191),0),'R11080':((254,191),0),'C11082':((274.5,198.5),0),'C11083':((264.5,185.5),0),'C11084':((259.5,185.5),0),'C11087':((255.5,185.5),0),'R11074':((274.5,195.5),0),'R11075':((274.5,198.5),0),'U11021':((282,201),0),'U11022':((282,205),0),'U11027':((289,201),180),'U11028':((289,205),180),'R11067':((276.8,199),0),'R11071':((295,200),0)}
for r,(p,a)in poses.items():fs[r].SetPosition(xy(p));fs[r].SetOrientationDegrees(a)
for r in poses:
 f=fs[r];clash=[v.GetReference()for v in b.GetFootprints()if v.GetReference()!=r and v.GetLayer()==f.GetLayer()and intersects(side_box(f),side_box(v),0)];print(r,'CLASH',clash,flush=True)
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankA-poses.json').write_text(json.dumps(poses,indent=2))
