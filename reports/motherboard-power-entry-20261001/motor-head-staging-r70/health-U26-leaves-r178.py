import json,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity
r=json.loads(Path('reports/motherboard-power-entry-20261001/health-supply-r99/receipt.json').read_text());b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
for v in r['exact_added_copper']:
 if v['role'].startswith(('U11026_own','FIELD_sink_actual_own_supply')):print(v['role'],identity(ts[v['uuid']]))
