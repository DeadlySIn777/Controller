import sys,json
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import mm,segment_distance
b=pcbnew.LoadBoard(sys.argv[1]);g=Geometry(b);fs={f.GetReference():f for f in b.GetFootprints()};spec=json.loads(Path(sys.argv[2]).read_text());out=[]
for r in spec['routes']:
 for side in ['from','to']:
  q=r[side];p=next(v for v in fs[q['ref']].Pads()if v.GetNumber()==str(q['pin']));s=tuple(q.get('point_mm',mm(p.GetPosition())));n=p.GetNetname();w=r['width_mm'];rows={}
  for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
   obs=[]
   for net,polys,top,bot,npth in g.pads.candidates(s,s,w/2+.16):
    if net==n and not npth:continue
    if(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(s,s,p,w/2+.16)for p in polys):obs.append({'type':'pad','net':net,'polygons':polys})
   for net,a,c,ww in g.tracks[l].candidates(s,s,w/2+.16):
    if net!=n and segment_distance(s,s,a,c)<w/2+.16+ww/2-1e-6:obs.append({'type':'track','net':net,'a':a,'b':c,'width':ww})
   rows[b.GetLayerName(l)]=obs
  out.append(dict(route=r['name'],side=side,pin=q,point=s,net=n,width_mm=w,obstacles=rows))
Path(sys.argv[3]).write_text(json.dumps(out,indent=2)+'\n')
