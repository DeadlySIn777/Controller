from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r568.py');t=p.read_text().replace('r568','r570')
t=t.replace("def route(a,c,n,role):", "def route(a,c,n,role,l=pcbnew.B_Cu):").replace('g.clear(p,n,pcbnew.B_Cu,.25)','g.clear(p,n,l,.25)').replace('g.grid(a,c,n,pcbnew.B_Cu,.25','g.grid(a,c,n,l,.25').replace('t.SetLayer(pcbnew.B_Cu);','t.SetLayer(l);').replace("layer='B.Cu'",'layer=b.GetLayerName(l)')
a=t.index('for cap,owner,power,ground,raw in');z=t.index('for por in',a)
t=t[:a]+'''def via(pt,n,role):
 sh=pcbnew.SHAPE_CIRCLE(xy(pt),pcbnew.FromMM(.25)+1)
 assert not any(q.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(q.IsOnLayer(l)and q.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for q in b.GetPads()),('Actual shaped registration',pt)
 assert all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]),('All-Cu via',pt)
 assert not any(isinstance(q,pcbnew.PCB_VIA)and math.dist(pt,mm(q.GetPosition()))<.4495 for q in b.GetTracks()),('Hole gap',pt)
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v
caps=[('C11089','U11035','6','2','C11083'),('C11090','U11036','5','3','C11083'),('C11091','U11037','6','2','C11086'),('C11092','U11038','5','3','C11086')]
for cap,owner,power,ground,raw in caps:
 route(mm(ps[cap,'1'].GetPosition()),mm(ps[owner,power].GetPosition()),ps[cap,'1'].GetNetname(),'Short exact owning-VDD local bypass '+cap)
 a=mm(ps[cap,'1'].GetPosition());n=ps[cap,'1'].GetNetname();choices=[]
 for d in[.9,1.0,1.1,1.3,1.5]:
  for k in range(16):
   q=(round(a[0]+d*math.cos(k*math.pi/8),6),round(a[1]+d*math.sin(k*math.pi/8),6));sh=pcbnew.SHAPE_CIRCLE(xy(q),pcbnew.FromMM(.25)+1)
   if not all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]):continue
   if not g.clear([a,q],n,pcbnew.B_Cu,.25):continue
   if any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads()):continue
   if any(isinstance(p,pcbnew.PCB_VIA)and math.dist(q,mm(p.GetPosition()))<.4495 for p in b.GetTracks()):continue
   for source in raw_original:
    c=mm(source.GetPosition())
    if math.dist(q,c)>20:continue
    pt=next((p for p in paths(q,c)if g.clear(p,n,pcbnew.In2_Cu,.25)),None)
    if pt is not None:choices.append((sum(math.dist(x,y)for x,y in zip(pt,pt[1:]))+d,q,c,source.m_Uuid.AsString()))
 assert choices,('No actual inner Source feed',cap);choices.sort();score,q,c,source=choices[0];via(q,n,'Actual local bypass supply transfer '+cap);route(a,q,n,'Short actual cap feed '+cap);route(q,c,n,'Actual retained Source barrel inner feed '+cap,pcbnew.In2_Cu)
for cap,owner,power,ground,raw in caps:
 route(mm(ps[cap,'2'].GetPosition()),mm(ps[owner,ground].GetPosition()),ps[cap,'2'].GetNetname(),'Actual exact owning-GND local bypass '+cap)
 route(mm(ps[cap,'2'].GetPosition()),mm(ps[raw,'2'].GetPosition()),ps[cap,'2'].GetNetname(),'Actual same-domain existing Source return '+cap)
'''+t[z:]
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r570.py').write_text(t)
