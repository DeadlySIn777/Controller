import json
from pathlib import Path
r=json.loads(Path('reports/motherboard-power-entry-20261001/Source27-closer-bypass-native-proof-r584/receipt.json').read_text())
print(json.dumps(r['new_violations'],indent=2));print('NewCu',len(r['exact_new_Cu']),'oldRetired',len(r['exact_retired_Cu']),'Source',r['all_prior_Source_clusters_except_only_two_remapped_CLR_pads']);
