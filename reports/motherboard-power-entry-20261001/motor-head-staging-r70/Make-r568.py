from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r564.py');t=p.read_text().replace('r564','r568')
t=t.replace("b0=pcbnew.LoadBoard(str(B));oldCu", "b0=pcbnew.LoadBoard(str(B));b0.BuildConnectivity();oldCu")
a=t.index("for cap,owner,power,ground,raw in");z=t.index("for por in",a)
t=t[:a]+'''raw_original=[]
source_cap=next(p for p in b0.GetPads()if p.GetParentFootprint().GetReference()=='C11083'and p.GetNumber()=='1');source_ids={q.m_Uuid.AsString()for q in b0.GetConnectivity().GetConnectedItems(source_cap)}
raw_original=[q for q in b.GetTracks()if isinstance(q,pcbnew.PCB_VIA)and q.m_Uuid.AsString()in source_ids and q.m_Uuid.AsString()not in added27]
for cap,owner,power,ground,raw in [('C11089','U11035','6','2','C11083'),('C11090','U11036','5','3','C11083'),('C11091','U11037','6','2','C11086'),('C11092','U11038','5','3','C11086')]:
 route(mm(ps[cap,'1'].GetPosition()),mm(ps[owner,power].GetPosition()),ps[cap,'1'].GetNetname(),'Short exact owning-VDD local bypass '+cap)
 route(mm(ps[cap,'2'].GetPosition()),mm(ps[owner,ground].GetPosition()),ps[cap,'2'].GetNetname(),'Actual exact owning-GND local bypass '+cap)
 a=mm(ps[cap,'1'].GetPosition());n=ps[cap,'1'].GetNetname();choices=[]
 for q in raw_original:
  c=mm(q.GetPosition())
  if math.dist(a,c)>15:continue
  pt=next((p for p in paths(a,c)if g.clear(p,n,pcbnew.B_Cu,.25)),None)
  if pt is not None:choices.append((sum(math.dist(x,y)for x,y in zip(pt,pt[1:])),c,q.m_Uuid.AsString()))
 if choices:
  choices.sort();target=choices[0][1];route(a,target,n,'Actual retained numbered-Source-connected RAW barrel feed '+cap)
 else:route(a,mm(ps[raw,'1'].GetPosition()),n,'Actual same-rail existing Source feed '+cap)
 route(mm(ps[cap,'2'].GetPosition()),mm(ps[raw,'2'].GetPosition()),ps[cap,'2'].GetNetname(),'Actual same-domain existing Source return '+cap)
'''+t[z:]
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r568.py').write_text(t)
