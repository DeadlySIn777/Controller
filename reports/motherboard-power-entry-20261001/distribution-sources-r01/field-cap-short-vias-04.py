exec(open('reports/motherboard-power-entry-20261001/distribution-sources-r01/field-cap-current-blocker.py').read().split("print('path'")[0])
from hardware_route_local_signals import paths
p=next(p for p in f['U11015'].Pads()if p.GetNumber()=='6');a=mm(p.GetPosition());options=[]
for i in range(23):
 for j in range(21):
  v=(347.4+.15*i,179.8+.15*j)
  if not all(g.clear([v,v],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
  bp=next((q for q in paths(s,v)if g.clear(q,n,pcbnew.B_Cu,.4)),None)
  fp=next((q for q in paths(a,v)if g.clear(q,n,pcbnew.F_Cu,.4)),None)
  if bp and fp:options.append((sum(__import__('math').dist(x,y)for q in[bp,fp]for x,y in zip(q,q[1:])),v,bp,fp))
print(sorted(options)[:12],flush=True)

