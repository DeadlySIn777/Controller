exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/preflight.py').read().split('for s,e,w,n,lay')[0])
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import segment_distance
for s,e,w in [((271.8,171),(276,171),4),((276,171),(282,177),6),((282,177),(282,190),6)]:
 print('BLOCKED',s,e,w)
 n='/LOGIC_GND';lay=pcbnew.F_Cu;gap=w/2+.16
 for ref,poly in g.barriers:
  if hits(s,e,poly,w/2):print(' barrier',ref,poly)
 for net,poly,top,bot,np in g.pads.candidates(s,e,gap):
  if net!=n and(top or np)and any(hits(s,e,p,gap)for p in poly):print(' pad',net,poly)
 for net,a,c,ww in g.tracks[lay].candidates(s,e,gap):
  if net!=n and segment_distance(s,e,a,c)<gap+ww/2-1e-6:print(' track',net,a,c,ww)
for x in range(272,289,2):
 for y in range(171,194,2):
  if g.clear([(x,y),(x,y)],'/LOGIC_GND',pcbnew.F_Cu,4):print('CLEAR4',x,y)
