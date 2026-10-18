from pathlib import Path
import json
r=json.loads(Path('reports/motherboard-power-entry-20261001/motor-bank-A-r83/debug.json').read_text())
for p in r['routes']:
 if p['role']in ['U11031.4_to_U11032.1','U11033.4_to_U11034.1','A_ON_actual_referenced_control','A_PG_actual_pullup','C11082.1_to_U11032.6']or'VCC' in p['role']:print(p)
