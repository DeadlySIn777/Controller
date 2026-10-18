exec(__import__('pathlib').Path('reports/motherboard-power-entry-20261001/aux24-field-cell-r68/find_switch_approach.py').read_text().split('for l in')[0])
from hardware_route_local_signals import paths
for e in[(340,194),(340,190),(334,186),(338,198),(346,182)]:
 for layer in[pcbnew.F_Cu,pcbnew.B_Cu]:
  s=(343.5,186);w=.8;p=next((p for p in paths(s,e)if g.clear(p,n,layer,w)),None)
  if p is None and all(g.clear([p,p],n,layer,w)for p in[s,e]):p=g.grid(s,e,n,layer,w,step=.25,padding=7,max_nodes=6500)
  print(b.GetLayerName(layer),e,p,flush=True)
