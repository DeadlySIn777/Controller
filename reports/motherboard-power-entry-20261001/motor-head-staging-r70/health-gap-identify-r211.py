import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
P=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(P));ids={'2a03a378-a27e-4bda-905c-a8fbfe0bdaaf','3a11c11c-57f9-412a-9fd5-2f78d1ecce45','e71fd4a1-1fee-4092-b9ca-62566a894473'}
for p in b.GetPads():
 if p.m_Uuid.AsString()in ids:print(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),mm(p.GetPosition()))
P=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-cell-r202/motor-health-U20-cell-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(P))
for p in b.GetPads():
 if p.GetParentFootprint().GetReference()=='C11004':print('C11004',p.GetNumber(),p.GetNetname(),mm(p.GetPosition()),mm(p.GetSize()),p.GetOrientationDegrees())
