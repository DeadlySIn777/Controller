from pathlib import Path
import json,sys
sys.path.insert(0,str(Path.cwd()/'tools'))
from hardware_zone_motherboard_returns import reference_envelopes
m=json.loads(Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U26-Source-field-screen-r01/domain-map.json').read_text())
print(json.dumps([e for e in reference_envelopes(m,'In1.Cu')if e['net']=='/LOGIC_GND'and e['bounds'][0]<333.3 and e['bounds'][2]>330.4 and e['bounds'][1]<188.5 and e['bounds'][3]>186.5],indent=2))
