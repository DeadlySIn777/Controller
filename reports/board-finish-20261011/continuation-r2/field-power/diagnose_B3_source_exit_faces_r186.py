"""Exact bounded source/target reachability before any further triangulation."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_B3_preserving_exact_old_IO3_r177.py').read_text(encoding='utf-8').replace('r177','r186').replace('R177','R186')
old="exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))"
new="""start=s.index('  def bridge(target):');end=s.index('  def via_legal(',start)
probe='''  def bridge(target):
   diagnostics=[]
   for l in INNER:
    sh=target.get(l,Point().buffer(0))
    if sh.is_empty or source[l].is_empty:continue
    aa,bb=nearest_points(sh,source[l])
    for margin in (8.,25.):
     win=box(min(aa.x,bb.x)-margin,min(aa.y,bb.y)-margin,max(aa.x,bb.x)+margin,max(aa.y,bb.y)+margin).intersection(outline);free=inner_legal(l,win)
     for width in (.35,.5):
      components=polys(free.buffer(-width/2-.005));source_faces=[];joint=0;target_faces=0
      for i,part in enumerate(components):
       reachable=part.buffer(-.00002);st=reachable.intersection(sh);goal=reachable.intersection(source[l]);hitS=goal.area>1e-8;hitT=st.area>1e-8
       if hitT:target_faces+=1
       if hitS:
        fp=OUT/(f'{l}-{margin}-{width}-source-{i}.wkb');fp.write_bytes(part.wkb);source_faces.append({'area_mm2':part.area,'bounds':list(part.bounds),'target_reached':hitT,'distance_to_window_boundary_mm':part.distance(win.boundary),'file':str(fp.resolve()),'sha256':sha(fp)})
       if hitS and hitT:joint+=1
      row={'layer':l,'minimum_core_width_mm':width,'margin_mm':margin,'source_reachable_faces':source_faces,'target_reachable_faces':target_faces,'same_source_target_face_count':joint,'actual_source_port_bounds':list(source[l].bounds),'closest_source_point':list(bb.coords[0]),'closest_target_point':list(aa.coords[0])};diagnostics.append(row);write(OUT/'source-face-checkpoint.json',diagnostics);print('SOURCE_FACE',l,width,margin,len(source_faces),target_faces,joint,flush=True)
   return None,None,None,None
'''
s=s[:start]+probe+s[end:]
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))"""
assert old in s;s=s.replace(old,new)
exec(compile(s,str(H/'construct_B3_preserving_exact_old_IO3_r177.py'),'exec'))
