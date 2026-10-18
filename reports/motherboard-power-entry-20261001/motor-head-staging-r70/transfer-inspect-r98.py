import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/health-supply-r95/motor-health-supply-candidate.kicad_pcb');b.BuildConnectivity();c=b.GetConnectivity()
for t in b.GetTracks():
 if t.m_Uuid.AsString()=='c507d769-eedf-4881-94a9-9d0456bc2681'or isinstance(t,pcbnew.PCB_VIA)and mm(t.GetPosition())==(312.,203.):
  print('ITEM',identity(t))
  if isinstance(t,pcbnew.PCB_VIA):print('FREE',t.GetIsFree(),'FLASH',t.FlashLayer(pcbnew.B_Cu),'CONNECTED',c.IsConnectedOnLayer(t,pcbnew.B_Cu))
  print('CON',[(v.Type(),v.m_Uuid.AsString(),v.GetNetname())for v in c.GetConnectedItems(t)][:12])


