exec(open('reports/motherboard-power-entry-20261001/motor-head-staging-r70/Source27-four-return-stitches-r546.py',encoding='utf-8-sig').read().split('for uid,point,target in')[0].replace("assert not OUT.exists();OUT.mkdir()","OUT=Path('reports/motherboard-power-entry-20261001/Source27-return-pair-obstruction-r550');OUT.mkdir()"))
from hardware_route_logic_return import segment_distance
from hardware_route_power_groups_native import hits
rows=[];sp=(259.8,206)
for dx,dy in[(0,-1),(1,0),(0,1),(-1,0),(-.7071,-.7071),(.7071,-.7071),(.7071,.7071),(-.7071,.7071)]:
 q=(sp[0]+dx*.95,sp[1]+dy*.95);obs=[];sh=pcbnew.SHAPE_CIRCLE(xy(q),pcbnew.FromMM(.25)+1)
 for p in b.GetPads():
  if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and any(p.IsOnLayer(l)and p.GetEffectiveShape(l).Collide(sh,0)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):obs.append(dict(type='actual drill registration',ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),point=mm(p.GetPosition())))
 for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]:
  if g.clear([q,q],n,l,.5):continue
  gap=.25+.16
  for net,a,c,w in g.tracks[l].candidates(q,q,gap):
   if net!=n and segment_distance(q,q,a,c)<gap+w/2-1e-6:obs.append(dict(type='actual Cu',net=net,start=a,end=c,width=w,layer=b.GetLayerName(l)))
  for ref,poly in g.barrier_index.candidates(q,q,.25):
   if hits(q,q,poly,.25):obs.append(dict(type='package barrier',ref=ref,polygon=poly))
 rows.append(dict(point=q,actual_layers=[(b.GetLayerName(l),g.clear([q,q],n,l,.5))for l in[pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu]],obstructions=obs))
(OUT/'obstructions.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
