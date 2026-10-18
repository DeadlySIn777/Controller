exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankA-ground-inspect.py').read().split('for r,pn in')[0])
for r in ['C11052','C11053','C11054','C11055','R11043','U2006','R11048','U6042','R11078']:
 print(r,mm(fs[r].GetPosition()))
 for p in fs[r].Pads():print(p.GetNumber(),p.GetNetname(),mm(p.GetPosition()))
