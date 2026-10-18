"""Read-only exact segment blockers for a proposed current path."""
import sys,json
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import segment_distance
b=pcbnew.LoadBoard(sys.argv[1]);g=Geometry(b);fs={f.GetReference():f for f in b.GetFootprints()};out=[]
for r in json.loads(Path(sys.argv[2]).read_text())['routes']:
 p=next(p for p in fs[r['from']['ref']].Pads()if p.GetNumber()==str(r['from']['pin']));n=p.GetNetname()
 for layer,ss in r['screened_path_sections'].items():
  l=b.GetLayerID(layer)
  for sec in ss:
   for a,z in zip(sec['points_mm'],sec['points_mm'][1:]):
    w=sec['width_mm'];gap=w/2+.16;obs=[]
    for net,polys,top,bot,npth in g.pads.candidates(a,z,gap):
     if net==n and not npth:continue
     if(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(a,z,p,gap)for p in polys):obs.append(dict(type='pad',net=net,polygons=polys))
    for net,s,e,ww in g.tracks[l].candidates(a,z,gap):
     if net!=n and segment_distance(a,z,s,e)<gap+ww/2-1e-6:obs.append(dict(type='track',net=net,a=s,b=e,width=ww))
    for ref,poly in g.barriers:
     if hits(a,z,poly,w/2):obs.append(dict(type='isolation_barrier',ref=ref,polygon=poly))
    if obs:out.append(dict(route=r['name'],layer=layer,segment=[a,z],obstacles=obs))
print(json.dumps(out,indent=2))
