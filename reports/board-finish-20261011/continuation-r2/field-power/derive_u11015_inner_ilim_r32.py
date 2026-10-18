from pathlib import Path
P=Path(__file__).resolve().parent;s=(P/'repair_u11015_three_net_outer_r31.py').read_text()
s=s.replace("OUT=HERE/'u11015-three-net-outer-repair-r31'", "OUT=HERE/'u11015-three-net-inner-ILIM-repair-r32'")
at=s.index(" smd=[")
helpers=''' pending_signal_cu=[]
 def outer_ilim(src,dst,extras):
  a,b=nearest_points(src,dst);width=.2
  for margin in(3.,8.,16.):
   win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=it.query(win,predicate='intersects');legal=win.difference(unary_union([io[int(j)] for j in ii]+extras));options=[]
   for part in polys(legal.buffer(-.105)):
    aa=part.buffer(-.00002).intersection(src.buffer(.075));bb=part.buffer(-.00002).intersection(dst.buffer(.075))
    if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
   if not options:continue
   _,part,aa,bb=min(options,key=lambda q:q[0]);a1,b1=nearest_points(aa,bb)
   try:points,search=T.route(part,tuple(a1.coords[0]),tuple(b1.coords[0]))
   except(AssertionError,ValueError):continue
   pts=[[round(x,6),round(y,6)] for x,y in points]
   if len(set(tuple(p) for p in pts))<2:continue
   line=LineString(pts);body=line.buffer(.1,quad_segs=32)
   if legal.buffer(.000001).covers(body) and body.intersection(src).area>.001 and body.intersection(dst).area>.001:return {'points':pts,'body':body,'search':search,'length_mm':line.length}
  return None
 def ilim_dive(groundbody,grounddisk,groundhole):
  sources=[];destinations=[];extras=[groundbody.buffer(.175),grounddisk.buffer(.175)];inner_masks={};inner_trees={}
  for l in LAYERS[1:-1]:
   oo=[q['shape'].buffer(igap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=ilim]+[q['shape'].buffer(igap(q['net'])+.025) for q in planes if q['layer']==l and C.norm(q['net'])!=ilim]
   for q in g['pads']:
    if not q['num'] or q['net']!=iraw:oo.extend([sh.buffer(.275) for sh in C.poly(q.get('hole') or [])])
   for v in g['vias']:
    if v['net']!=iraw:oo.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=32))
   oo.append(grounddisk.buffer(.175))
   for rule in g['rule_areas']:
    if rule.get('no_tracks') and l in rule['layers']:oo.extend([sh.buffer(.025) for sh in C.poly(rule['outline'])])
   for rule in res['keepouts']:
    if ilim not in exceptions.get(rule['name'],set()) and l in rule['layers']:oo.extend([sh.buffer(.025) for sh in C.poly(rule['outline'])])
   inner_masks[l]=oo;inner_trees[l]=STRtree(oo)
  def good_disk(xy):
   pt=Point(xy);disk=pt.buffer(.25,quad_segs=32);hole=pt.buffer(.1,quad_segs=64)
   if not outline.covers(disk) or disk.distance(grounddisk)<.175-1e-9 or hole.distance(groundhole)<.275-1e-9:return None
   if any(pt.distance(smd[int(j)])-.1<.275-1e-9 for j in st.query(pt.buffer(.376),predicate='intersects')):return None
   if any(pt.distance(ph[int(j)])-.1<.275-1e-9 for j in ht.query(pt.buffer(.376),predicate='intersects')):return None
   if any(math.hypot(xy[0]-v['x'],xy[1]-v['y'])-(.2+v['drill'])/2<.275-1e-9 for v in g['vias']):return None
   for l in LAYERS:
    if any(C.norm(rec[l][int(j)]['net'])!=ilim and disk.distance(rec[l][int(j)]['shape'])<igap(rec[l][int(j)]['net'])+.025-1e-9 for j in trees[l].query(disk.buffer(.65),predicate='intersects')):return None
    if any(q['layer']==l and C.norm(q['net'])!=ilim and disk.distance(q['shape'])<igap(q['net'])+.025-1e-9 for q in planes):return None
    for rule in g['rule_areas']:
     if rule.get('no_vias') and l in rule['layers'] and any(disk.intersects(sh.buffer(.025)) for sh in C.poly(rule['outline'])):return None
    for rule in res['keepouts']:
     if ilim not in exceptions.get(rule['name'],set()) and l in rule['layers'] and any(disk.intersects(sh.buffer(.025)) for sh in C.poly(rule['outline'])):return None
   return disk,hole
  for pad,pool in[(ip0,sources),(ip1,destinations)]:
   anchor=pad['shape'].representative_point()
   for radius in(.75,.8,.9,1.2,1.6,2.2,3.,4.,5.):
    for step in range(16):
     xy=(round(anchor.x+radius*math.cos(step*math.pi/8),6),round(anchor.y+radius*math.sin(step*math.pi/8),6));ok=good_disk(xy)
     if ok is None:continue
     disk,hole=ok;rr=outer_ilim(pad['shape'],disk,extras)
     if rr:pool.append({'xy':xy,'disk':disk,'hole':hole,'outer':rr})
    if len(pool)>=12:break
   if not pool:return None
  for a in sources[:16]:
   for b in destinations[:24]:
    if a['hole'].distance(b['hole'])<.275-1e-9:continue
    ann0=a['disk'].difference(a['hole']);ann1=b['disk'].difference(b['hole']);aa0,bb0=nearest_points(ann0,ann1)
    for l in('In3.Cu','In2.Cu','In4.Cu','In1.Cu'):
     for margin in(3.,8.,16.):
      win=box(min(aa0.x,bb0.x)-margin,min(aa0.y,bb0.y)-margin,max(aa0.x,bb0.x)+margin,max(aa0.y,bb0.y)+margin).intersection(outline);ii=inner_trees[l].query(win,predicate='intersects');legal=win.difference(unary_union([inner_masks[l][int(j)] for j in ii]));options=[]
      for part in polys(legal.buffer(-.105)):
       aa=part.buffer(-.00002).intersection(ann0);bb=part.buffer(-.00002).intersection(ann1)
       if not aa.is_empty and not bb.is_empty:options.append((aa.distance(bb),part,aa,bb))
      if not options:continue
      _,part,aa,bb=min(options,key=lambda q:q[0]);a1,b1=nearest_points(aa,bb)
      try:points,search=T.route(part,tuple(a1.coords[0]),tuple(b1.coords[0]))
      except(AssertionError,ValueError):continue
      pts=[[round(x,6),round(y,6)] for x,y in points];line=LineString(pts);body=line.buffer(.1,quad_segs=32)
      if not legal.buffer(.000001).covers(body) or body.intersection(ann0).area<.001 or body.intersection(ann1).area<.001:continue
      seed=f'controller-U11015-ILIM-dive-r32/{a["xy"]}/{b["xy"]}/{l}';vs=[];ts=[];cc=[]
      for role,q in[('source',a),('destination',b)]:
       vid=str(uuid.uuid5(uuid.NAMESPACE_URL,seed+'/'+role));v={'uuid':vid,'net':iraw,'x':q['xy'][0],'y':q['xy'][1],'d':.5,'drill':.2,'flashed':LAYERS,'prospective_not_native':True};vs.append(v)
       for layer in LAYERS:cc.append({'uuid':vid+'@'+layer,'net':iraw,'layer':layer,'shape':q['disk']})
       for j,(p0,p1) in enumerate(zip(q['outer']['points'],q['outer']['points'][1:])):
        if p0!=p1:ts.append({'uuid':str(uuid.uuid5(uuid.UUID(vid),'outer'+str(j))),'net':iraw,'layer':'B.Cu','a':p0,'b':p1,'w':.2,'prospective_not_native':True})
      for j,(p0,p1) in enumerate(zip(pts,pts[1:])):
       if p0!=p1:ts.append({'uuid':str(uuid.uuid5(uuid.UUID(vs[0]['uuid']),'inner'+str(j))),'net':iraw,'layer':l,'a':p0,'b':p1,'w':.2,'prospective_not_native':True})
      for t in ts:cc.append({'uuid':t['uuid'],'net':iraw,'layer':t['layer'],'shape':C.body(t)})
      return {'points':[],'body':unary_union([q['shape'] for q in cc if q['layer']=='B.Cu']),'length_mm':sum(C.body(t).length for t in ts),'inner_layer':l,'inner_points_mm':pts,'inner_length_mm':line.length,'width_mm':.2,'search':search,'extra_vias':vs,'extra_tracks':ts,'all_cu':cc,'native_flash_required':{'via_UUIDs':[v['uuid'] for v in vs],'layers':['B.Cu',l]}}
  return None
'''
s=s[:at]+helpers+s[at:]
s=s.replace("if ir is None:continue\n         dr=", "if ir is None:ir=ilim_dive(rr['body'],disk,hole)\n         if ir is None:continue\n         pending_signal_cu=ir.get('all_cu',[])\n         dr=")
s=s.replace("[q['shape'].buffer(gap(q['net'])+.025) for q in newzones if q['layer']==l and C.norm(q['net'])!=net]", "[q['shape'].buffer(gap(q['net'])+.025) for q in newzones+pending_signal_cu if q['layer']==l and C.norm(q['net'])!=net]")
s=s.replace("controller-U11015-three-net-r31/", "controller-U11015-three-net-inner-r32/")
at=s.index("         drids=[]")
s=s[:at]+'''         for sv in ir.get('extra_vias',[]):
          newvias.append(sv);vid=sv['uuid'];(OUT/(vid+'.via-chunk')).write_text('\\t(via\\n\\t\\t(at %.6f %.6f)\\n\\t\\t(size %.2f)\\n\\t\\t(drill %.2f)\\n\\t\\t(layers "F.Cu" "B.Cu")\\n\\t\\t(net "%s")\\n\\t\\t(uuid "%s")\\n\\t)\\n'%(sv['x'],sv['y'],.5,.2,iraw,vid),encoding='utf-8',newline='')
         for tt in ir.get('extra_tracks',[]):
          newtracks.append(tt);irids.append(tt['uuid']);(OUT/(tt['uuid']+'.segment-chunk')).write_text('\\t(segment\\n\\t\\t(start %.6f %.6f)\\n\\t\\t(end %.6f %.6f)\\n\\t\\t(width %.2f)\\n\\t\\t(layer "%s")\\n\\t\\t(net "%s")\\n\\t\\t(uuid "%s")\\n\\t)\\n'%(*tt['a'],*tt['b'],.2,tt['layer'],iraw,tt['uuid']),encoding='utf-8',newline='')
         newcu+=ir.get('all_cu',[])
''' +s[at:]
s=s.replace("{k:v for k,v in ir.items() if k!='body'}", "{k:v for k,v in ir.items() if k not in('body','all_cu')}")
(P/'repair_u11015_inner_ilim_r32.py').write_text(s,encoding='utf-8');compile(s,'repair_u11015_inner_ilim_r32.py','exec');print('derived',len(s))
