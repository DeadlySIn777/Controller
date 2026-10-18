exec(open('reports/motherboard-power-entry-20261001/distribution-sources-r01/new-field-output-blocker.py').read())
print('simple',next((v for v in paths(s,e)if g.clear(v,n,pcbnew.F_Cu,.2)),None));print('start03',g.clear([s,s],n,pcbnew.F_Cu,.3),'end03',g.clear([e,e],n,pcbnew.F_Cu,.3))
for f in b.GetFootprints():
 if f.GetReference()in['U11015','C11070']:print(f.GetReference(),[(p.GetNumber(),mm(p.GetPosition()),p.GetNetname())for p in f.Pads()if p.GetNumber()])
print('direct blockers')
for net,a,c,w in g.tracks[pcbnew.F_Cu].candidates(s,e,.31):
 if net!=n and segment_distance(s,e,a,c)<.31+w/2:print('t',net,a,c,w)
for net,polys,top,bot,npth in g.pads.candidates(s,e,.31):
 if net!=n and (npth or top)and any(hits(s,e,q,.31)for q in polys):print('p',net,polys)
