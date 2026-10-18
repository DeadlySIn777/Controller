exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-In3-endpoint-inspection-r514.py',encoding='utf-8-sig').read().split('for a in[p,q]:')[0])
from hardware_route_logic_return import segment_distance
from hardware_route_power_groups_native import hits
for a in[p,q]:
 gap=.125+.16
 print('POINT',a)
 for net,c,d,w in g.tracks[pcbnew.In3_Cu].candidates(a,a,gap):
  if net!=n and segment_distance(a,a,c,d)<gap+w/2-1e-6:print('ACTUAL INNER COPPER OBSTRUCTION',net,c,d,w)
 for net,c,w in g.actual_inner_pad.candidates(a,a,gap):
  if net!=n and segment_distance(a,a,c,c)<gap+w-1e-6:print('ACTUAL INNER LAND OBSTRUCTION',net,c,w)
 for ref,poly in g.barrier_index.candidates(a,a,.125):
  if hits(a,a,poly,.125):print('ACTUAL PACKAGE BARRIER',ref,poly)
