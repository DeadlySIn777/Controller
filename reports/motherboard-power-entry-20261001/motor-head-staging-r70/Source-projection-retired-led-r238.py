import json
from pathlib import Path
r=json.loads(Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-control-B-F-r234/receipt.json').read_text());ids={q['uuid']for q in r['exact_retired_copper']}
for s in ['0981b314','98b66286','e3f10ceb']:
 print(s,[u for u in ids if u.startswith(s)])
