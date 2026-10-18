exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/contact-source-clusters.py').read().split('for f in')[0])
for f in b.GetFootprints():
 if f.GetReference()in['U11022','U11024','U11028','U11030']:
  print('CONTACT',f.GetReference())
  for p in f.Pads():print(p.GetNumber(),p.GetNetname(),[(v.GetParentFootprint().GetReference(),v.GetNumber())for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T])
