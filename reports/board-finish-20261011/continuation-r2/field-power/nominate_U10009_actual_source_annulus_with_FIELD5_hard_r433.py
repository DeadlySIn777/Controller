"""Test actual finite source annuli, preserving source-centre native intent.

An existing source annulus is a real attachment target rather than a forced
width-eroded centreline goal. Explicit full old landing geometry in the new
intended outline remains independently audited; no inherited margin passes.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'nominate_U10009_inner_feed_with_actual_FIELD5_hard_r427.py'
ns={'__file__':str(owner),'__name__':'_load_hard_FIELD5_nomination_without_run'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('U10009-retained-lower-VS-R407-hard-In3-In2-feed-nomination-r427','U10009-actual-finite-source-annulus-R407-hard-inner-feed-nomination-r433')
s=s.replace("sources=sorted([vm[u]for u in rootvia],key=lambda v:point.distance(Point(v['x'],v['y'])))[:10]", "sources=sorted([vm[u]for u in rootvia],key=lambda v:point.distance(Point(v['x'],v['y'])))[:24]")
old="""free=discrete_free(layer,.5,iw);innerfaces=[f for f in polys(free)if f.covers(point)and f.covers(goal)];trial={'new_site':list(point.coords[0]),'source_old_barrel':source['uuid'],'layer':layer,'same_free_faces':len(innerfaces)};trials.append(trial);put(O/'checkpoint.json',trials)
    for ff in innerfaces:
     try:ip,_=T.route(ff,tuple(point.coords[0]),tuple(goal.coords[0]));ip=[[round(x,6),round(y,6)]for x,y in ip];assert ff.covers(LineString(ip));chosen=(point,bp,source,layer,ip);break
"""
new="""free=discrete_free(layer,.5,iw);annuli=[r['shape']for r in root if r['kind']=='via'and r['uuid']==source['uuid']and r['layer']==layer];actual_annulus=unary_union(annuli);assert not actual_annulus.is_empty
    innerfaces=[f for f in polys(free)if f.covers(point)and f.intersects(actual_annulus)];trial={'new_site':list(point.coords[0]),'source_old_barrel':source['uuid'],'layer':layer,'same_free_faces':len(innerfaces),'actual_annulus_WKB_sha256':A.C.sha(actual_annulus.wkb),'actual_annulus_mm2':actual_annulus.area,'source_centre_eroded_free':free.covers(goal)};trials.append(trial);put(O/'checkpoint.json',trials)
    for ff in innerfaces:
     try:
      overlap=ff.intersection(actual_annulus).buffer(-.000002);assert not overlap.is_empty
      target=nearest_points(overlap,point)[0];target=Point(round(target.x,6),round(target.y,6));assert overlap.covers(target)
      ip,_=T.route(ff,tuple(point.coords[0]),tuple(target.coords[0]));ip=[[round(x,6),round(y,6)]for x,y in ip];assert ff.covers(LineString(ip));chosen=(point,bp,source,layer,ip);trial['actual_annular_route_goal_mm']=list(target.coords[0]);trial['target_source_actual_annulus_overlap_mm2']=overlap.area;break
"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('import contact_layout as L','import audit_aux_exact_raw as A\nimport contact_layout as L')
old="outline=set_precision(N.bounded_buffer(LineString(ip),.25),1e-6,mode='pointwise');physical=outline"
new="outline=set_precision(unary_union([N.bounded_buffer(LineString(ip),.25),N.bounded_disk(source,source['d']/2)]),1e-6,mode='valid_output');assert outline.covers(Point(source['x'],source['y']));physical=outline"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("vid+'/inner/R427/'+layer", "vid+'/inner/R433/'+layer")
s=s.replace("'hard_only_not_whole_field_model_overlay':True", "'hard_only_not_whole_field_model_overlay':True,'source_attachment':'EXACT_ACTUAL_FINITE_FLASHED_ANNULUS','full_own_source_landing_disk_intended_centre':'EXPLICIT_NEW_INTENT_TRUE_MARGIN_NATIVE_GATES_OPEN','rejected_source_centre_only_R427_receipt_sha256':sha(H/'U10009-retained-lower-VS-R407-hard-In3-In2-feed-nomination-r427/receipt.json')")
exec(compile(s,str(H/'nominate_U10009_retained_lower_VS_barrel_r397.py'),'exec'))
