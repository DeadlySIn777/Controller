exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/find-ON-In2.py').read().split('class Inner:')[0])
for cx,cy in[(345.5,203.25),(354.6929,195.9571),(300,205),(270.85,180.8)]:
 print('WINDOW',cx,cy)
 for yy in range(-6,7):
  print(''.join('#'if fill.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(cx+xx*.5),pcbnew.FromMM(cy+yy*.5)))else'.'for xx in range(-8,9)))
