import json,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
r=json.loads(Path('reports/motherboard-power-entry-20261001/health-supply-r99/receipt.json').read_text());b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
for v in r['exact_added_copper']:
 if v['role'].startswith(('U11020_own','U11020_actual_ground')):print(v['role'],v['uuid'],identity(ts[v['uuid']]))
print('allnear')
for f in b.GetFootprints():
 p=mm(f.GetPosition())
 if 338<p[0]<349 and 168<p[1]<181:print(f.GetReference(),p,f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer()))
