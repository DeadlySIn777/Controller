from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r570.py');t=p.read_text().replace('r570','r572')
a=t.index('for por in');z=t.index('for pd,cap',a);por=t[a:z];t=t[:a]+t[z:];t=t.replace('caps=[',por+'caps=[')
a=t.index('for cap,owner,power,ground,raw in caps:\n route(mm(ps[cap,\'2\']');z=t.index('for pd,cap',a)
t=t[:a]+'''ground_cap=next(p for p in b0.GetPads()if p.GetParentFootprint().GetReference()=='C11083'and p.GetNumber()=='2');ground_ids={q.m_Uuid.AsString()for q in b0.GetConnectivity().GetConnectedItems(ground_cap)}
ground_original=[q for q in b.GetTracks()if isinstance(q,pcbnew.PCB_VIA)and q.m_Uuid.AsString()in ground_ids and q.m_Uuid.AsString()not in added27]
for cap,owner,power,ground,raw in caps:
 route(mm(ps[cap,'2'].GetPosition()),mm(ps[owner,ground].GetPosition()),ps[cap,'2'].GetNetname(),'Actual exact owning-GND local bypass '+cap)
 a=mm(ps[cap,'2'].GetPosition());n=ps[cap,'2'].GetNetname();choices=[]
 for q in ground_original:
  c=mm(q.GetPosition())
  if math.dist(a,c)>15:continue
  pt=next((p for p in paths(a,c)if g.clear(p,n,pcbnew.B_Cu,.25)),None)
  if pt is not None:choices.append((sum(math.dist(x,y)for x,y in zip(pt,pt[1:])),c,q.m_Uuid.AsString()))
 if choices:
  choices.sort();route(a,choices[0][1],n,'Actual retained numbered-Source-connected Ground barrel return '+cap)
 else:
  candidates=sorted((math.dist(a,mm(q.GetPosition())),mm(q.GetPosition()))for q in ground_original if math.dist(a,mm(q.GetPosition()))<12)
  assert candidates,('No retained Source Ground candidates',cap)
  route(a,candidates[0][1],n,'Actual retained nearest Source Ground return '+cap)
'''+t[z:]
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r572.py').write_text(t)
