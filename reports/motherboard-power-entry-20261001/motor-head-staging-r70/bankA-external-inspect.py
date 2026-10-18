exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankA-ground-inspect.py').read().split('for r,pn in')[0])
for r in ['U11019','U11020','U11025','U11026','U11031','U11032','U11033','U11034','R11048','C11029','C11088','C11049','C11050','C11051','U11009','U11014']:
 f=fs[r];print(r,mm(f.GetPosition()))
 for p in f.Pads():print(p.GetNumber(),p.GetNetname(),mm(p.GetPosition()))
