exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/contact-source-clusters.py').read().split('for f in')[0])
refs=['U11031','U11032','R11042','R11044','R11067','R11071','R11074','R11075','R11076','C11082','C11083','C11084']
for f in b.GetFootprints():
 if f.GetReference()in refs:
  print(f.GetReference(),mm(f.GetPosition()))
  for p in f.Pads():
   v=[(t.GetParentFootprint().GetReference(),t.GetNumber())for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T];print(p.GetNumber(),p.GetNetname(),'sourcepieces',len(v),v[:10])
