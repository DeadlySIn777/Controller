"""Derive bridged constructive search from separately preserved R21."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'remaining_field_ground_feeds_r21.py').read_text(encoding='utf-8')
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change("OUT=HERE/'remaining-field-ground-feeds-r21'","OUT=HERE/'remaining-field-ground-feeds-r23'")
change('controller-field-remaining-r21/','controller-field-remaining-r23/')
change('from shapely.strtree import STRtree','from shapely.strtree import STRtree\nfrom shapely import set_precision,get_num_coordinates')
change('newvias=[];newtracks=[];newcu=[];rows=[]','newvias=[];newtracks=[];newcu=[];newzones=[];rows=[]')
change("foreign={l:[q for q in planes if q['layer']==l and C.norm(q['net'])!=net] for l in LAYERS}","foreign={l:[q for q in planes+newzones if q['layer']==l and C.norm(q['net'])!=net] for l in LAYERS}")
change("  wanted=[(i,xs) for i,xs in enumerate(groups) if xs is not root and any(q['kind']=='pad' and q['pin'] for q in xs)]", """  innerobs={};innerTrees={}
  for l in LAYERS[1:-1]:
   oo=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in foreign[l]]
   for p0 in g['pads']:
    if not p0['num'] or p0['net']!=raw:oo.extend([sh.buffer(.275) for sh in C.poly(p0.get('hole') or [])])
   for v0 in g['vias']:
    if v0['net']!=raw:oo.append(Point(v0['x'],v0['y']).buffer(v0['drill']/2+.275,quad_segs=32))
   for rule in g['rule_areas']:
    if rule.get('no_zones') and l in rule['layers']:oo.extend([sh.buffer(.025) for sh in C.poly(rule['outline'])])
   innerobs[l]=oo;innerTrees[l]=STRtree(oo)
  ownholes=unary_union([sh for p0 in g['pads'] if p0['num'] and p0['net']==raw for sh in C.poly(p0.get('hole') or [])]+[Point(v0['x'],v0['y']).buffer(v0['drill']/2,quad_segs=64) for v0 in g['vias'] if v0['net']==raw])
  def bridge(disk,hole):
   ann=disk.difference(hole);options=[]
   for l in('In1.Cu','In4.Cu','In2.Cu','In3.Cu'):
    if source[l].is_empty:continue
    if ann.intersection(source[l]).area>.025:return l,None,None,None
    a,b=nearest_points(ann,source[l]);options.append((a.distance(b),l,a,b))
   for dist,l,a,b in sorted(options,key=lambda q:q[0]):
    if dist>180:continue
    for margin in(8.,22.,45.):
     win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=innerTrees[l].query(win,predicate='intersects');legal=win.difference(unary_union([innerobs[l][int(j)] for j in ii]+[q['shape'].buffer(gap(q['net'])+.025) for q in newzones if q['layer']==l and C.norm(q['net'])!=net]));available=[]
     for width in(.5,.35):
      for part in polys(legal.buffer(-width/2-.005)):
       aa=part.buffer(-.00002).intersection(ann);bb=part.buffer(-.00002).intersection(source[l])
       if not aa.is_empty and not bb.is_empty:available.append((aa.distance(bb),part,aa,bb,width))
      if not available:continue
      _,part,aa,bb,width=min(available,key=lambda q:q[0]);start,end=nearest_points(aa,bb)
      if get_num_coordinates(part)>160000:
       smaller=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);pieces=[q for q in polys(smaller) if q.intersects(aa) and q.intersects(bb)]
       if not pieces:continue
       part=max(pieces,key=lambda q:q.area);start,end=nearest_points(part.buffer(-.00002).intersection(aa),part.buffer(-.00002).intersection(bb))
      try:pts,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
      except(AssertionError,ValueError):continue
      line=LineString(pts);core=line.buffer(width/2,quad_segs=32)
      if not legal.buffer(.000001).covers(core):continue
      nativeoutline=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]),1e-6);holes=unary_union([ownholes,hole]+[Point(v0['x'],v0['y']).buffer(v0['drill']/2,quad_segs=64) for v0 in newvias if v0['net']==raw]);effective=set_precision(nativeoutline.difference(holes),1e-6)
      if not legal.buffer(.000002).covers(effective) or not effective.buffer(.000002).covers(core.difference(holes)) or effective.intersection(ann).area<.01 or effective.intersection(source[l]).area<1e-8:continue
      return l,effective,nativeoutline,{'points_mm':pts,'length_mm':line.length,'minimum_core_width_mm':width,'source_rooted_Cu_overlap_mm2':effective.intersection(source[l]).area,'via_annular_Cu_overlap_mm2':effective.intersection(ann).area,'search':search,'sheet_only_R35um60C_ohm':.00057003672*line.length/width}
   return None,None,None,None
  wanted=[(i,xs) for i,xs in enumerate(groups) if xs is not root and any(q['kind']=='pad' and q['pin'] for q in xs)]""")
change("        inner=next((l for l in('In1.Cu','In4.Cu','In2.Cu','In3.Cu') if disk.difference(hole).intersection(source[l]).area>.025),None)\n        if inner is None:continue", "        inner=None")
change("         if rr is None:continue\n         uid=", "         if rr is None:continue\n         inner,bridgebody,nativeoutline,bridgeinfo=bridge(disk,hole)\n         if inner is None:continue\n         uid=")
change("newvias.append(v);uids=[]", "newvias.append(v);uids=[]\n         if bridgebody is not None:\n          zid=str(uuid.uuid5(uuid.UUID(uid),'inner-source-bridge'));newzones.append({'uuid':zid,'net':raw,'layer':inner,'shape':bridgebody,'zone_outline_shape':nativeoutline,'clearance_mm':.15,'physical_Cu_drill_subtracted':True});source[inner]=unary_union([source[inner],bridgebody])\n         else:zid=None")
change("'physical_source_overlap_mm2':disk.difference(hole).intersection(source[inner]).area,'outer_route'", "'physical_source_overlap_mm2':disk.difference(hole).intersection(source[inner]).area,'inner_bridge_UUID':zid,'inner_bridge_route':bridgeinfo,'outer_route'")
change("(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':newvias,'tracks':newtracks},protocol=5))", "(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':newvias,'tracks':newtracks},protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(newzones,protocol=5))")
change("'no_new_planes':True", "'new_source_rooted_inner_planes':len(newzones),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'new_plane_intended_outline_separate_from_drill_subtracted_physical_Cu':True")
out=HERE/'remaining_field_ground_feeds_r23.py';assert not out.exists();out.write_text(s,encoding='utf-8')
