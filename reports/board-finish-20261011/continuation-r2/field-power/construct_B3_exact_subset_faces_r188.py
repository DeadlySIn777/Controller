"""Preserve stopped R177; bind all eight actual peer IO3 shapes and subset faces."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_B3_preserving_exact_old_IO3_r177.py').read_text(encoding='utf-8').replace('r177','r188').replace('R177','R188')
s=s.replace("original-IO3-r172-positive-snapshot-4/proposed-zones.pkl','9fbe57d1d4a5d6999e4500ab091480ad7e34afe47a1fa9b35d457c2f165937fd'","original-IO3-r172-positive-snapshot-8/proposed-zones.pkl','d576613bad70e94d04e47822b0b7c42f30e7f1a72e91d4a4a9cf1f8335eac16c'")
old="exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))"
new="""before='''       if get_num_coordinates(part)>160000:
        reduced=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);parts=[q for q in polys(reduced) if q.intersects(startshape) and q.intersects(goal)]
        if not parts:continue
        part=max(parts,key=lambda q:q.area);start,end=nearest_points(part.buffer(-.00002).intersection(startshape),part.buffer(-.00002).intersection(goal))'''
after='''       faceproof=None
       if get_num_coordinates(part)>25000:
        originalpart=part;reducedparts=[]
        for tol in (.05,.02,.01,.005,.001):
         reduced=originalpart.buffer(-tol*2).simplify(tol,preserve_topology=True).buffer(-.00002)
         for sub in polys(reduced):
          if not originalpart.covers(sub):continue
          st=sub.buffer(-.00000001).intersection(startshape);en=sub.buffer(-.00000001).intersection(goal)
          if st.area>1e-8 and en.area>1e-8:reducedparts.append((sub,st,en,tol))
         if reducedparts:break
        if not reducedparts:continue
        part,st,en,tol=max(reducedparts,key=lambda q:q[0].area);start,end=nearest_points(st,en);faceproof={'original_exact_face_WKB_SHA256':P.digest(originalpart),'reduced_face_WKB_SHA256':P.digest(part),'exact_original_face_covers_every_reduced_coordinate_and_edge':True,'buffer_twice_tolerance_before_simplify_mm':tol*2,'simplify_tolerance_mm':tol,'final_inset_mm':.00002,'original_coordinates':get_num_coordinates(originalpart),'reduced_coordinates':get_num_coordinates(part)}'''
assert s.count(before)==1;s=s.replace(before,after)
s=s.replace("       points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);core=P.bounded_buffer(line,width/2)","       if faceproof:search['strict_conservative_subset_face']=faceproof\n       points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points);core=P.bounded_buffer(line,width/2)")
s=s.replace("      for _,part,startshape,goal in sorted(choices,key=lambda q:q[0]):","      print('B3_FACE_SEARCH',l,width,margin,'jointfaces',len(choices),flush=True)\n      for _,part,startshape,goal in sorted(choices,key=lambda q:q[0]):")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))"""
assert old in s;s=s.replace(old,new)
exec(compile(s,str(H/'construct_B3_preserving_exact_old_IO3_r177.py'),'exec'))
