import json
from pathlib import Path
r=json.loads(Path('reports/motherboard-power-entry-20261001/Source27-four-bypass-correct-orientation-r582/actual-Cu.json').read_text())
for q in r['new_Cu']:
 v=q['identity']
 if v[-1]is not None:print(q['role'],v[0],v[1],v[2],v[3],v[-1])
print('CAPPOSES',r['exact_four_new_cap_pose_changes'])
