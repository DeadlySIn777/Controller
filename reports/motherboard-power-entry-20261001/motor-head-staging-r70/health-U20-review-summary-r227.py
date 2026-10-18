import json
from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-independent-r218/receipt.json');r=json.loads(p.read_text());print({k:r[k]for k in['passed','all_fitted_parts','all_fitted_pad_identities','all_old_Source_clusters_preserved','exact_added_Cu','exact_retired_Cu']});print('drills',len(r['actual_drill_land_reviews']),'cuts',len(r['persisted_physical_negative_controls']))
