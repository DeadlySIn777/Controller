import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()));import pcbnew
from hardware_route_logic_return import mm
P=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(P));p=next(p for p in b.GetPads()if p.GetParentFootprint().GetReference()=='U11026'and p.GetNumber()=='4');print('N',p.GetNetname(),mm(p.GetPosition()))
for q in b.GetPads():
 if q.GetNetname()==p.GetNetname():print('PAD',q.GetParentFootprint().GetReference(),q.GetNumber(),mm(q.GetPosition()))
for t in b.GetTracks():
 if t.GetNetname()==p.GetNetname()and isinstance(t,pcbnew.PCB_VIA):print('VIA',t.m_Uuid.AsString(),mm(t.GetPosition()))
r=json.loads(Path('reports/motherboard-power-entry-20261001/health-supply-r99/receipt.json').read_text())
for q in r['routes']:
 if q['net']==p.GetNetname():print('R',q['role'],q['points_mm'])
