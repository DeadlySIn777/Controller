exec(open('reports/motherboard-power-entry-20261001/distribution-sources-r01/field-output-route-blocker.py').read())
for dx,dy in[(0,0),(-.7,0),(.7,0),(0,-.7),(0,.7),(-1.1,0),(1.1,0),(0,-1.1),(0,1.1)]:
 pt=(e[0]+dx,e[1]+dy);print(pt,'via',g.clear([pt,pt],n,pcbnew.F_Cu,.5),g.clear([pt,pt],n,pcbnew.B_Cu,.5),'F',[(q,g.clear(q,n,pcbnew.F_Cu,.3))for q in paths(s,pt)],'B',[(q,g.clear(q,n,pcbnew.B_Cu,.3))for q in paths(e,pt)])
