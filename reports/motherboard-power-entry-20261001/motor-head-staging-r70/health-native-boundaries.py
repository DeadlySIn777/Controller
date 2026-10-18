import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()));import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-r83/motor-bank-A-receiving-candidate.kicad_pcb');b.BuildConnectivity();co=b.GetConnectivity();fs={f.GetReference():f for f in b.GetFootprints()}
for net in ['/mc_local_power/MC_RAILS_OK_5V','/motherboard_motor_power/MOTOR_FIELD_HEALTH_A_RAW','/motherboard_motor_power/MOTOR_FIELD_HEALTH_B_RAW']:
 print(net)
 for p in b.GetPads():
  if p.GetNetname()==net:
   print(p.GetParentFootprint().GetReference(),p.GetNumber(),mm(p.GetPosition()),p.GetParentFootprint().GetValue(),'CO_PADS',len([v for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T]))
for r in ['C11072','C11073','C11075','C11076','R11048','R11050','R11052']:
 print('ROLE',r)
 for p in fs[r].Pads(): print(p.GetNumber(),p.GetNetname(),mm(p.GetPosition()))
