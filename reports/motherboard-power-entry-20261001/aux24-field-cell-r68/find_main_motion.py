exec(__import__('pathlib').Path('reports/motherboard-power-entry-20261001/aux24-field-cell-r68/find_switch_approach.py').read_text().split('for l in')[0])
for e,w in[((340,194),6),((340,194),4),((326,198),6),((326,198),4)]:
 s=(266,177);l=pcbnew.F_Cu;print('BEGIN',e,w,flush=True);p=next((p for p in paths(s,e)if g.clear(p,n,l,w)),None)
 if p is None and all(g.clear([p,p],n,l,w)for p in[s,e]):p=g.grid(s,e,n,l,w,step=1,padding=60,max_nodes=24000)
 print('PATH',p,flush=True)
 if p:break
