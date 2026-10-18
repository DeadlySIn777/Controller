import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()));import pcbnew
from hardware_route_logic_return import mm
P=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(P));p=(327.5875,191.65)
for t in b.GetTracks():
 if any(math.dist(mm(v),p)<.5 for v in[t.GetStart(),t.GetEnd()]):print(t.m_Uuid.AsString(),t.GetNetname(),b.GetLayerName(t.GetLayer()),mm(t.GetStart()),mm(t.GetEnd()))
