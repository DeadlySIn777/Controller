import json
from pathlib import Path
r=json.loads(Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r235/receipt.json').read_text())
for q in r['routes']:
 if q['role']in['U11026_actual_input_1','U11026_input_3_receiving_F','U11026_input_3_actual_source_B']:print(q['role'],q['points_mm'])
