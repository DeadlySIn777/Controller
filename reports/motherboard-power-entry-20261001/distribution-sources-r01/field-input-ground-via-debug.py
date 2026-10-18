exec(open('reports/motherboard-power-entry-20261001/distribution-sources-r01/field-input-ground-blocker.py').read())
pt=(347.225,183.9);print('via',g.clear([pt,pt],n,pcbnew.F_Cu,.5),g.clear([pt,pt],n,pcbnew.B_Cu,.5));print('B',next((q for q in paths(e,pt)if g.clear(q,n,pcbnew.B_Cu,.3)),None));print('F',next((q for q in paths(s,pt)if g.clear(q,n,pcbnew.F_Cu,.3)),None))
for l in[pcbnew.F_Cu,pcbnew.B_Cu]:
 bad=[]
 for net,polys,top,bot,npth in g.pads.candidates(pt,pt,.41):
  if net!=n and(npth or(top if l==pcbnew.F_Cu else bot))and any(hits(pt,pt,q,.41)for q in polys):bad.append(('pad',net,polys))
 for net,a,c,w in g.tracks[l].candidates(pt,pt,.41):
  if net!=n and segment_distance(pt,pt,a,c)<.41+w/2:bad.append(('track',net,a,c,w))
 print(b.GetLayerName(l),json.dumps(bad))
