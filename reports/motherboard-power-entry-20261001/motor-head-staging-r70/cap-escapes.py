exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/preflight.py').read().split('for s,e,w,n,lay')[0])
for ref in ['C11057','C11058','C11059','C11060']:
 p=[p for p in fs[ref].Pads()if p.GetNumber()=='2'][0];pt=mm(p.GetPosition());found=[]
 for dx in [0,-.6,-1,-1.5,-2,-3,1,1.5,2]:
  for dy in [0,-.6,-1,-1.5,-2,-3,1,1.5,2,3]:
   v=(pt[0]+dx,pt[1]+dy)
   if all(g.clear([v,v],p.GetNetname(),l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu])and g.clear([pt,v],p.GetNetname(),pcbnew.B_Cu,.4):found.append(v)
 print('GROUND_ESC',ref,pt,found)
for y in [176,179,183,186,189]:print('STRAP',y,g.clear([(271.8,171),(271.8,y)],'/LOGIC_GND',pcbnew.F_Cu,4))
