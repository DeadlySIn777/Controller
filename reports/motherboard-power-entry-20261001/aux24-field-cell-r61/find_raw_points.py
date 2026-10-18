exec(__import__('pathlib').Path('reports/motherboard-power-entry-20261001/aux24-field-cell-r61/find_raw_feed.py').read_text().split('for s,e,w in')[0])
import math
for role,seed,area in [('source',(266.2,171),[(x,y)for x in range(260,281,2)for y in range(175,200,2)]),('receiver',(337.5,186),[(x,y)for x in range(320,340,2)for y in range(174,202,2)])]:
 for w in[8,6,4]:
  v=sorted((p for p in area if g.clear([p,p],n,pcbnew.F_Cu,w)),key=lambda p:math.dist(p,seed));print(role,w,v[:12],flush=True)
