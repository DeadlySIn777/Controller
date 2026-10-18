exec(open('reports/motherboard-power-entry-20261001/distribution-sources-r01/field-output-route-blocker.py').read())
for e in[(349.3,180.5),(348.5,180.5),(348.9,180.1),(348.9,180.9)]:
 bad=[]
 for ref,poly in g.barriers:
  if hits(s,e,poly,.15):bad.append(('barrier',ref,poly))
 for net,polys,top,bot,npth in g.pads.candidates(s,e,.31):
  if net!=n and (npth or top)and any(hits(s,e,q,.31)for q in polys):bad.append(('pad',net,polys))
 for net,a,c,w in g.tracks[pcbnew.F_Cu].candidates(s,e,.31):
  if net!=n and segment_distance(s,e,a,c)<.31+w/2:bad.append(('track',net,a,c,w))
 print(e,json.dumps(bad))
