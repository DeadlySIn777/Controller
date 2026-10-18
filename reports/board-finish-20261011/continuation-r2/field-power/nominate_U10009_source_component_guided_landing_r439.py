"""Choose a legal all-six landing in an actual protected source component."""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'nominate_U10009_inner_feed_with_actual_FIELD5_hard_r427.py'
ns={'__file__':str(owner),'__name__':'_load_hard_FIELD5_source_constructor'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('U10009-retained-lower-VS-R407-hard-In3-In2-feed-nomination-r427','U10009-source-component-guided-wider-ordinary-landing-nomination-r439')
s=s.replace("win=box(263.8,172.0,273.0,178.5)", "win=box(257.5,166.0,282.0,189.0)")
start=s.index(" outer=discrete_free('B.Cu',.3,win);")
end=s.index(' packet=None',start)
s=s[:start]+''' outer=discrete_free('B.Cu',.3,win);outerfaces=[ff for ff in polys(outer)if ff.covers(startpoint)]
 actualgroups=pickle.loads((H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl').read_bytes());root=K.root(actualgroups[rawnorm],'U11004','17');rootvia={r['uuid']for r in root if r['kind']=='via'};trials=[];chosen=None;candidates=[]
 sources=sorted([vm[u]for u in rootvia],key=lambda v:startpoint.distance(Point(v['x'],v['y'])))[:24]
 for source in sources:
  goal=Point(source['x'],source['y'])
  if startpoint.distance(goal)>80:continue
  for layer in ('In3.Cu','In2.Cu'):
   if layer not in source['flashed']:continue
   iw=box(min(win.bounds[0],goal.x)-6,min(win.bounds[1],goal.y)-6,max(win.bounds[2],goal.x)+6,max(win.bounds[3],goal.y)+6);free=discrete_free(layer,.5,iw);sourcefaces=[ff for ff in polys(free)if ff.covers(goal)];trial={'source_old_barrel':source['uuid'],'layer':layer,'source_face_count':len(sourcefaces),'joint_legal_landing_piece_count':0};trials.append(trial)
   for ff in sourcefaces:
    for bf in outerfaces:
     joint=landing.intersection(ff).intersection(bf).buffer(-.000002)
     pieces=polys(joint);trial['joint_legal_landing_piece_count']+=len(pieces)
     for piece in sorted(pieces,key=lambda sh:sh.distance(startpoint)):
      for pt in(nearest_points(piece,startpoint)[0],piece.representative_point(),piece.centroid):
       point=Point(round(pt.x,6),round(pt.y,6))
       if not piece.covers(point):continue
       candidates.append(point)
       try:
        bp,_=T.route(bf,tuple(startpoint.coords[0]),tuple(point.coords[0]));ip,_=T.route(ff,tuple(point.coords[0]),tuple(goal.coords[0]));bp=[[round(x,6),round(y,6)]for x,y in bp];ip=[[round(x,6),round(y,6)]for x,y in ip];assert bf.covers(LineString(bp))and ff.covers(LineString(ip));chosen=(point,bp,source,layer,ip);trial['accepted_site_mm']=list(point.coords[0]);break
       except(ValueError,AssertionError)as e:trial.setdefault('route_errors',[]).append(str(e))
      if chosen:break
     if chosen:break
    if chosen:break
   put(O/'checkpoint.json',trials);print('R439',source['uuid'],layer,'landing pieces',trial['joint_legal_landing_piece_count'],'accepted',bool(chosen),flush=True)
   if chosen:break
  if chosen:break
''' +s[end:]
s=s.replace("vid+'/inner/R427/'+layer", "vid+'/inner/R439/'+layer")
s=s.replace("'hard_only_not_whole_field_model_overlay':True", "'hard_only_not_whole_field_model_overlay':True,'source_component_guided_new_landing':True,'lower_bank_ordinary_window_mm':[257.5,166.,282.,189.],'rejected_fixed_landing_R433_receipt_sha256':sha(H/'U10009-actual-finite-source-annulus-R407-hard-inner-feed-nomination-r433/receipt.json')")
exec(compile(s,str(H/'nominate_U10009_retained_lower_VS_barrel_r397.py'),'exec'))
