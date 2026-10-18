"""One bounded ordinary inner-layer switch between exact reachable components."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'","OUT=HERE/'B3-exact-cross-layer-pair-r203';BASE=HERE/'B3-exact-IO3-preserving-search-base-r197'")
s=s.replace('for bank,net,ref,pin,policy in PORTS:',"for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='B3V3']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'","xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('U19008','10') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("for a in sorted([q for q in xs if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area):","for a in []: # only this explicit inner-layer cross-source test")
s=s.replace("q['uuid'] in original and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'","q['uuid'] in original and float(q.get('clearance_mm',.15))==.15 and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'")
s=s.replace("hardh={**h,'tracks':h['tracks']+hard['discrete']['tracks']", "late=HERE.parent/'sbc-power/IO3-group6-wider-existing-port-r193/accepted-zones.pkl';assert sha(late)=='01952e9a9374ac67da080769154bc828cfd6689bff207cb412d9a33d551e4362';hardplanes+=pickle.loads(late.read_bytes())\n hardh={**h,'tracks':h['tracks']+hard['discrete']['tracks']")
start=s.index('  def bridge(target):');end=s.index('  def via_legal(',start)
probe=r'''  def bridge(target):
   width=.20;dia=.5;drill=.2;components={};frees={};pairs=[];margin=25.
   for l in INNER:
    sh=target.get(l,Point().buffer(0))
    if sh.is_empty or source[l].is_empty:continue
    aa,bb=nearest_points(sh,source[l]);win=box(min(aa.x,bb.x)-margin,min(aa.y,bb.y)-margin,max(aa.x,bb.x)+margin,max(aa.y,bb.y)+margin).intersection(outline);free=inner_legal(l,win);frees[l]=free;ss=[];tt=[]
    for part in polys(free.buffer(-width/2-.005)):
     reach=part.buffer(-.00002)
     if reach.intersection(source[l]).area>1e-8:ss.append(part)
     if reach.intersection(sh).area>1e-8:tt.append(part)
    components[l]={'source':ss,'target':tt};print('R203 FACES',l,len(ss),len(tt),flush=True)
   for ls,cs in components.items():
    for lt,ct in components.items():
     if ls==lt:continue
     for sf in cs['source']:
      for tf in ct['target']:
       overlap=sf.intersection(tf)
       for op in polys(overlap):
        if op.area<.000001:continue
        pairs.append((op.distance(source[ls])+op.distance(target[lt]),ls,lt,sf,tf,op))
   print('R203 CONTINUOUS_CROSS_LAYER_OVERLAPS',len(pairs),flush=True)
   attempts=[];found=None
   def exact_barrel_region(op):
    win=box(*op.bounds).buffer(.001);walls=[]
    for l in LAYERS:
     for j in trees[l].query(win.buffer(.9),predicate='intersects'):
      q=rec[l][int(j)]
      if C.norm(q['net'])==net:continue
      rr=dia/2+gap(q['net'])+.00002
      if q['kind']=='via':v=nativevias[q['uuid']];walls.append(P.bounded_buffer(Point(v['x'],v['y']),rr+v['d']/2))
      elif q['kind']=='track':t=nativetracks[q['uuid']];walls.append(P.bounded_buffer(LineString([t['a'],t['b']]),rr+t['w']/2))
      else:walls.append(P.bounded_buffer(q['shape'],rr))
     for q in plane_layers[l]:
      if C.norm(q['net'])!=net and not maycarve(q) and q['shape'].intersects(win.buffer(.9)):walls.append(P.bounded_buffer(q['shape'],dia/2+proposal_gap(q)+.00002))
     for area in h['rule_areas']:
      if area.get('no_vias') and l in area['layers']:walls.extend(P.bounded_buffer(sh,dia/2+.025+.00002) for sh in C.poly(area['outline']) if sh.intersects(win.buffer(.9)))
     for area in reserved['keepouts']:
      if net not in exceptions.get(area['name'],set()) and l in area['layers']:walls.extend(P.bounded_buffer(sh,dia/2+.025+.00002) for sh in C.poly(area['outline']) if sh.intersects(win.buffer(.9)))
    for j in st.query(win.buffer(drill/2+.276),predicate='intersects'):walls.append(P.bounded_buffer(smd[int(j)]['shape'],drill/2+.275+.00002))
    for v in hardh['vias']:
     if Point(v['x'],v['y']).distance(win)<(drill+v['drill'])/2+.276:walls.append(P.bounded_buffer(Point(v['x'],v['y']),(drill+v['drill'])/2+.275+.00002))
    for pad in hardh['pads']:
     for hole in C.poly(pad.get('hole') or []):
      if hole.distance(win)<drill/2+.276:walls.append(P.bounded_buffer(box(*hole.bounds),drill/2+.275+.00002))
    return set_precision(op.difference(unary_union(walls)),1e-6)
   def local_path(layer,part,src,dst):
    st0=part.buffer(-.00002).intersection(src);en0=part.buffer(-.00002).intersection(dst)
    if st0.area<1e-8 or en0.area<1e-8:return None
    original=part;proof=None
    if get_num_coordinates(part)>25000:
     choices=[]
     for tol in (.05,.02,.01,.005,.001):
      for sub in polys(original.buffer(-2*tol).simplify(tol,preserve_topology=True).buffer(-.00002)):
       if original.covers(sub) and sub.intersection(st0).area>1e-8 and sub.intersection(en0).area>1e-8:choices.append((sub,tol))
      if choices:break
     if not choices:return None
     part,tol=max(choices,key=lambda q:q[0].area);proof={'exact_original_covers_reduced_face':True,'original_WKB_SHA256':P.digest(original),'reduced_WKB_SHA256':P.digest(part),'buffer_before_simplify_mm':2*tol,'simplify_mm':tol};st0=part.buffer(-.00002).intersection(st0);en0=part.buffer(-.00002).intersection(en0)
    aa,bb=nearest_points(st0,en0)
    try:pts,search=T.route(part,tuple(aa.coords[0]),tuple(bb.coords[0]))
    except(AssertionError,ValueError):return None
    pts=[[round(x,6),round(y,6)] for x,y in pts];line=LineString(pts);core=P.bounded_buffer(line,width/2)
    if not frees[layer].covers(core):return None
    native=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=64).intersection(frees[layer].buffer(-.00002))) if q.intersection(core).area>1e-9]),1e-6)
    ownholes=unary_union([q['shape'] for q in holes if q['plated'] and q['net']==raw]);physical=set_precision(native.difference(ownholes),1e-6)
    return {'layer':layer,'physical':physical,'intended':native,'length_mm':line.length,'points_mm':pts,'minimum_core_width_mm':width,'source_overlap_mm2':physical.intersection(src).area,'target_overlap_mm2':physical.intersection(dst).area,'search':search,'reduced_face_proof':proof}
   for _,ls,lt,sf,tf,op in sorted(pairs,key=lambda q:q[0]):
    legal=exact_barrel_region(op)
    print('R203 LEGAL_CROSS_BARREL_AREA',ls,lt,legal.area,flush=True)
    for cp in sorted(polys(legal),key=lambda q:q.distance(source[ls])+q.distance(target[lt]))[:40]:
     pts=[cp.representative_point(),nearest_points(cp.buffer(-.000002),source[ls])[0],nearest_points(cp.buffer(-.000002),target[lt])[0]] if not cp.buffer(-.000002).is_empty else[cp.representative_point()]
     for pt in pts:
      xy=[round(pt.x,6),round(pt.y,6)];pt=Point(xy)
      if not cp.covers(pt):continue
      ann=P.bounded_buffer(pt,dia/2).difference(P.bounded_buffer(pt,drill/2));r1=local_path(ls,sf,source[ls],ann)
      if not r1:continue
      r2=local_path(lt,tf,ann,target[lt])
      if not r2:continue
      found=(xy,ls,lt,r1,r2);break
     if found:break
    if found:break
   if found:
    xy,ls,lt,r1,r2=found;v={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-B3-cross-layer-source-r203/'+ls+'/'+lt)),'net':raw,'x':xy[0],'y':xy[1],'d':dia,'drill':drill,'flashed':LAYERS,'prospective_not_native':True};newqs=[];cuts=[]
    for i,rr in enumerate((r1,r2)):
     hole=P.bounded_buffer(Point(xy),drill/2);physical=set_precision(rr['physical'].difference(hole),1e-6);assert rr['intended'].covers(Point(xy));uid=str(uuid.uuid5(uuid.NAMESPACE_URL,v['uuid']+'/'+rr['layer']));newqs.append({'uuid':uid,'net':raw,'layer':rr['layer'],'shape':physical,'zone_outline_shape':rr['intended'],'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'label':'B3-cross-source-r203-'+str(i)})
    for q in planes:
     if not maycarve(q):continue
     shapes=[P.bounded_buffer(Point(xy),dia/2)]+[qq['zone_outline_shape'] for qq in newqs if qq['layer']==q['layer']];cutter=P.bounded_buffer(unary_union(shapes),gap(q['net']));before=q['shape'];prior=q.get('zone_outline_shape',before);after=set_precision(before.difference(cutter),1e-6);afteroutline=set_precision(prior.difference(cutter),1e-6)
     if before.equals(after) and prior.equals(afteroutline):continue
     cuts.append({'uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'before_physical_SHA256':P.digest(before),'after_physical_SHA256':P.digest(after),'before_intended_SHA256':P.digest(prior),'after_intended_SHA256':P.digest(afteroutline),'cutter':cutter,'new_q':{**q,'shape':after,'zone_outline_shape':afteroutline}})
    (OUT/'cross-layer-discrete.pkl').write_bytes(pickle.dumps({'vias':[v],'tracks':[]},protocol=5));(OUT/'cross-layer-zones.pkl').write_bytes(pickle.dumps(newqs,protocol=5));(OUT/'cross-layer-owned-return-cuts.pkl').write_bytes(pickle.dumps(cuts,protocol=5));write(OUT/'cross-layer-receipt.json',{'verdict':'EXACT_TWO_LAYER_SOURCE_NOMINATION_FULL_GRAPH_CURRENT_NATIVE_OPEN','input_model_sha256':sha(BASE/'model.pkl'),'source_port':'U11018.1','target_group_includes':'U19008.10','new_ordinary_via':v,'required_native_flashed_layers':[ls,lt],'source_existing_NEW_12d_ordinary_native_flashes_also_required':True,'all6_foreign_Cu_and_every_SMD_and_hole_.275_guards_used':True,'routes':[{k:v for k,v in rr.items() if k not in ('physical','intended')} for rr in (r1,r2)],'complete_B3_feed_policy_A':.09,'new_discrete_sha256':sha(OUT/'cross-layer-discrete.pkl'),'new_planes_sha256':sha(OUT/'cross-layer-zones.pkl'),'owned_return_cuts_sha256':sha(OUT/'cross-layer-owned-return-cuts.pkl'),'source_relationships_full76_oldrefs_and_sheet_barrel_thermal_fault_gates':'OPEN','board_written':False,'native_jobs':0});print('R203 CROSS_LAYER_NOMINATED',xy,ls,lt,sha(OUT/'cross-layer-receipt.json'),flush=True)
   else:write(OUT/'cross-layer-receipt.json',{'verdict':'NO_TWO_LAYER_NOMINATION_IN_DECLARED_25MM_WINDOWS_AND_FINITE_LEGAL_COMPONENT_CANDIDATES','input_model_sha256':sha(BASE/'model.pkl'),'continuous_component_pair_count':len(pairs),'guard_unchanged':True,'global_impossibility_claim':False,'board_written':False,'native_jobs':0})
   return None,None,None,None
'''
s=s[:start]+probe+s[end:]
s=s.replace('.read_text()',".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
