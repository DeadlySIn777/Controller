exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/find-ON-F.py').read().split('for r,s in')[0])
for r,s in [('U11010','U11032'),('U11011','U11034')]:
 n=p[r,'5'].GetNetname()
 for role,pt in [('source',mm(p[s,'5'].GetPosition())),('recv',mm(p[r,'5'].GetPosition()))]:
  print(r,role,pt,'ptclear',g.clear([pt,pt],n,pcbnew.F_Cu,.2))
  print([(dx,dy,g.clear([pt,(pt[0]+dx,pt[1]+dy)],n,pcbnew.F_Cu,.2))for dx,dy in[(.5,0),(-.5,0),(0,.5),(0,-.5),(.5,.5),(-.5,.5),(.5,-.5),(-.5,-.5)]])
