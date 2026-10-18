import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/Source27-closer-bypass-native-proof-r584/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');b.BuildConnectivity();gs=[v for v in b.GetTracks()if isinstance(v,pcbnew.PCB_VIA)and v.GetNetname()=='/LOGIC_GND'];ids={'41be23ef-d390-4d13-a730-f8e2ead43e48','ce0a6f1a-17c0-40cc-942e-b66435e0ac23','5a0f5004-e761-43e0-b209-8497e6754258','418206a1-923d-4d4e-9fac-090c3b63c520'}
for v in b.GetTracks():
 if not isinstance(v,pcbnew.PCB_VIA):continue
 if v.m_Uuid.AsString()not in ids and 'MOTOR_FEED_CLEAR'in v.GetNetname():pass
 elif v.m_Uuid.AsString()not in ids:continue
 p=mm(v.GetPosition());nearest=sorted([(math.dist(p,mm(q.GetPosition())),q.m_Uuid.AsString(),mm(q.GetPosition()))for q in gs])[:2];print(v.m_Uuid.AsString(),v.GetNetname(),p,nearest)
