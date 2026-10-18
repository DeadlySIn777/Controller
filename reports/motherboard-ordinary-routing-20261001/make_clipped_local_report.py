from pathlib import Path
p=Path('reports/motherboard-ordinary-routing-20261001/route_local_root71_ordinary.py')
s=p.read_text().replace('added=[];groups=[];blocked=[];already=[]','fullfill=fill;added=[];groups=[];blocked=[];already=[]')
old="row=m['nets'][name];s,z=mm(p.GetPosition()),mm(q.GetPosition());path=next"
new="""row=m['nets'][name];s,z=mm(p.GetPosition()),mm(q.GetPosition())
 fill=pcbnew.SHAPE_POLY_SET();fill.Append(fullfill)
 box=pcbnew.SHAPE_POLY_SET();box.NewOutline()
 bounds=(min(s[0],z[0])-4,min(s[1],z[1])-4,max(s[0],z[0])+4,max(s[1],z[1])+4)
 for x,y in((bounds[0],bounds[1]),(bounds[2],bounds[1]),(bounds[2],bounds[3]),(bounds[0],bounds[3])):box.Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
 fill.BooleanIntersection(box);fill.Simplify()
 # This exact intersection only removes possible reference coverage. Final
 # segment/via proof uses the original complete eligible native fill union.
 path=next"""
if old not in s:raise ValueError('Literal report development source changed')
s=s.replace(old,new).replace('maximum_considered_source_span_mm=25,only_exact','maximum_considered_source_span_mm=25,exact_local_fill_clipping_margin_mm=4,local_clipping_only_removes_eligible_geometry=True,final_guard_uses_original_full_native_fill=True,only_exact')
Path('reports/motherboard-ordinary-routing-20261001/route_local_root71_ordinary_clipped.py').write_text(s)
