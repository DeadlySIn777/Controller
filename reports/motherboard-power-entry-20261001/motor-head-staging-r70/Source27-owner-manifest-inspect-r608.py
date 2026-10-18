import json
from pathlib import Path
op=Path('reports/motherboard-bypass-owners-20261001/complete727-source27-staged-r04/capacitor-owners.json');r=json.loads(op.read_text());rows={x['ref']:x for x in r['capacitors']}
for k in ['C11085','C11087','C11089','C11090','C11091','C11092']:print(k,json.dumps(rows[k],indent=2))
p=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/final-binding-r02/current110-bypass-manifest.json');m=json.loads(p.read_text());print('KEYS',m.keys());print('C87',json.dumps([g for g in m['owned_loops']if g['ref']=='C11087'],indent=2));print('NEWROUTES',len(json.loads(Path('reports/motherboard-power-entry-20261001/Source27-four-bypass-correct-orientation-r582/actual-Cu.json').read_text())['routes']))
