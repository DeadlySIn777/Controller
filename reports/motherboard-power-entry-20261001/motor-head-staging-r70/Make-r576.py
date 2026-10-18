from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r572.py');t=p.read_text().replace('r572','r576')
t=t.replace('from hardware_route_local_signals import paths','from hardware_route_local_signals import paths,GeometryIndex')
t=t.replace("b=pcbnew.LoadBoard(str(initial));g=m.InnerGeometry(b);",'''b=pcbnew.LoadBoard(str(initial));g=m.InnerGeometry(b)
for layer in[pcbnew.In1_Cu,pcbnew.In4_Cu]:
 g.tracks[layer]=GeometryIndex()
 for item in b.GetTracks():
  if item.IsOnLayer(layer):
   a,c=mm(item.GetStart()),mm(item.GetEnd());w=pcbnew.ToMM(item.GetWidth(layer)if isinstance(item,pcbnew.PCB_VIA)else item.GetWidth());g.tracks[layer].add((item.GetNetname(),a,c,w),(min(a[0],c[0])-w/2,min(a[1],c[1])-w/2,max(a[0],c[0])+w/2,max(a[1],c[1])+w/2))
''')
a=t.index('for cap,owner,power,ground,raw in caps:\n route(mm(ps[cap,\'2\']');z=t.index('dest=O/',a)
t=t[:a]+'''ground_anchors={}
def anchor_ground(key):
 if key in ground_anchors:return ground_anchors[key]
 p=ps[key];n=p.GetNetname();a=mm(p.GetPosition());assert n=='/LOGIC_GND';choices=[]
 for d in[.85,.9,1.,1.1,1.3,1.5]:
  for k in range(16):
   q=(round(a[0]+d*math.cos(k*math.pi/8),6),round(a[1]+d*math.sin(k*math.pi/8),6));sh=pcbnew.SHAPE_CIRCLE(xy(q),pcbnew.FromMM(.25)+1)
   if not all(g.clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]):continue
   if not g.clear([a,q],n,pcbnew.B_Cu,.25):continue
   if any(p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu])for p in b.GetPads()):continue
   if any(isinstance(p,pcbnew.PCB_VIA)and math.dist(q,mm(p.GetPosition()))<.4495 for p in b.GetTracks()):continue
   for source in ground_original:
    c=mm(source.GetPosition())
    if math.dist(q,c)>10:continue
    pt=next((v for v in paths(q,c)if g.clear(v,n,pcbnew.In4_Cu,.25)),None)
    if pt is not None:choices.append((sum(math.dist(x,y)for x,y in zip(pt,pt[1:]))+d,q,c,source.m_Uuid.AsString()))
 assert choices,('No actual own-domain Ground Source anchor',key,a);choices.sort();score,q,c,source=choices[0];via(q,n,'Actual off-land Source27 Ground receiving transfer '+str(key));route(a,q,n,'Actual short numbered Ground receiving escape '+str(key));route(q,c,n,'Actual own-domain retained Source Ground connection '+str(key),pcbnew.In4_Cu);ground_anchors[key]=q;return q
for cap,owner,power,ground,raw in caps:
 ca=anchor_ground((cap,'2'));oa=anchor_ground((owner,ground));route(ca,oa,'/LOGIC_GND','Actual local owning-IC bypass return '+cap,pcbnew.In4_Cu)
for pd,cap in [('R11082','C11090'),('R11083','C11092')]:
 a=anchor_ground((pd,'2'));c=ground_anchors[cap,'2'];route(a,c,'/LOGIC_GND','Actual pulldown Source return '+pd,pcbnew.In4_Cu)
'''+t[z:]
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-bypass-correct-orientation-r576.py').write_text(t)
