import json
from pathlib import Path
P=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r216/drc.json')
d=json.loads(P.read_text());print(json.dumps([r for r in d['violations']if r['type']not in ['lib_footprint_issues','lib_footprint_mismatch']],indent=2))
