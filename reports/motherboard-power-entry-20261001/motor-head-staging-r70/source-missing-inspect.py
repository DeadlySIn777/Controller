exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankA-ground-inspect.py').read().split('for r,pn in')[0])
for p in b.GetPads():
 if p.m_Uuid.AsString()=='9070f156-1533-4524-98f4-9a5b5cf40554':
  print('OLD',p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname())
  for t in co.GetConnectedItems(p):
   if t.Type()==pcbnew.PCB_PAD_T:print(t.GetParentFootprint().GetReference(),t.GetNumber())
