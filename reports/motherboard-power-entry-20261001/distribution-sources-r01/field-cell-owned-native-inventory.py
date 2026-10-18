import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
from hardware_place_owned_capacitors_native import side_box
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');b.BuildConnectivity();co=b.GetConnectivity();rs={'U11015','R11056','R11057','R11058','C11068','C11069','C11070'}
for f in b.GetFootprints():
 if f.GetReference()in rs:print(json.dumps(dict(ref=f.GetReference(),pos=mm(f.GetPosition()),ang=f.GetOrientationDegrees(),box=side_box(f),pins=[dict(pin=p.GetNumber(),xy=mm(p.GetPosition()),net=p.GetNetname(),connected=[t.m_Uuid.AsString()for t in co.GetConnectedItems(p)if t.Type()!=pcbnew.PCB_ZONE_T])for p in f.Pads()])))
print('neighbors',json.dumps([dict(ref=f.GetReference(),pos=mm(f.GetPosition()),box=side_box(f))for f in b.GetFootprints()if 350<mm(f.GetPosition())[0]<425 and 200<mm(f.GetPosition())[1]<245]))
