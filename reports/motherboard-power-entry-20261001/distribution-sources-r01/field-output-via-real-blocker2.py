exec(open('reports/motherboard-power-entry-20261001/distribution-sources-r01/field-output-route-blocker.py').read().replace('motion-raw-delivery-r47','motion-raw-delivery-r50'))
pt=(350.5,180.9)
print('via',g.clear([pt,pt],n,pcbnew.F_Cu,.5),g.clear([pt,pt],n,pcbnew.B_Cu,.5))
print('bp',[q for q in paths(e,pt)if g.clear(q,n,pcbnew.B_Cu,.3)])
print('fp',[q for q in paths(s,pt)if g.clear(q,n,pcbnew.F_Cu,.3)])
for l in[pcbnew.F_Cu,pcbnew.B_Cu]:
 bad=[]
 for net,polys,top,bot,npth in g.pads.candidates(pt,pt,.41):
  if net!=n and (npth or(top if l==pcbnew.F_Cu else bot))and any(hits(pt,pt,q,.41)for q in polys):bad.append(('pad',net,polys))
 for net,a,c,w in g.tracks[l].candidates(pt,pt,.41):
  if net!=n and segment_distance(pt,pt,a,c)<.41+w/2:bad.append(('track',net,a,c,w))
 print(b.GetLayerName(l),json.dumps(bad))

