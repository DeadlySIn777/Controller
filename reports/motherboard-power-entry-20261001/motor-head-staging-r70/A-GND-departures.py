exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/contact-source-clusters.py').read().split('for f in')[0])
from hardware_route_logic_return import identity,xy
for f in b.GetFootprints():
 if f.GetReference()in['R11076','R11080']:
  p=next(p for p in f.Pads()if p.GetNumber()=='2');pt=p.GetPosition();print(f.GetReference(),'GNDanchor',mm(pt))
  for t in b.GetTracks():
   if t.GetNetname()==p.GetNetname()and any(p.HitTest(k)for k in[t.GetStart(),t.GetEnd()]):print(identity(t))
