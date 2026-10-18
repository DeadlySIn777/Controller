import json,collections
r=json.load(open('reports/motherboard-power-entry-20261001/Source27-B-controls-off-CORE-F-r524/actual-Cu.json'))
for q in r['routes']:
 print(q['role'],len(q['actual_Cu_UUIDs']),q['points_mm'][0],q['points_mm'][-1])
print(collections.Counter(v['role']for v in r['new_Cu']))
