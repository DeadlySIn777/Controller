import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
p='reports/motherboard-power-entry-20261001/motor-bank-A-r78/debug.kicad_pcb';b=pcbnew.LoadBoard(p);b.BuildConnectivity();co=b.GetConnectivity();f={f.GetReference():f for f in b.GetFootprints()};pp={p.GetNumber():p for p in f['C11046'].Pads()};print('C46 SOURCE')
for v in co.GetConnectedItems(pp['1']):
 if v.Type()==pcbnew.PCB_PAD_T:print(v.GetParentFootprint().GetReference(),v.GetNumber())
for z in b.Zones():
 if z.GetNetname()=='/motherboard_power_entry/MOTION_5V_RAW':print('ZONE',z.m_Uuid.AsString(),b.GetLayerName(z.GetLayer()),z.GetAssignedPriority(),[(mm(z.Outline().Outline(i).CPoint(j)))for i in range(z.Outline().OutlineCount())for j in range(z.Outline().Outline(i).PointCount())])
