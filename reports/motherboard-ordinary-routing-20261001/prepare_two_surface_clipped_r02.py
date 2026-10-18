"""Exact subset clipping accelerates search; final full-native guard unchanged."""
from pathlib import Path
p=Path(__file__).parent;s=(p/'route_root81_two_surface_r01.py').read_text()
s=s.replace('added=[];groups=[];blocked=[]','full_fills=fills;added=[];groups=[];blocked=[]')
needle="    row=m['nets'][name];starts=escapes(p,row);ends=escapes(q,row);chosen=None"
assert s.count(needle)==1
s=s.replace(needle,"""    # Exact native intersection can remove coverage, never add it. Final
    # acceptance recomputes complete actual filled reference and annuli.
    start,end=mm(p.GetPosition()),mm(q.GetPosition())
    bounds=(min(start[0],end[0])-10,min(start[1],end[1])-10,max(start[0],end[0])+10,max(start[1],end[1])+10)
    box=pcbnew.SHAPE_POLY_SET();box.NewOutline()
    for pt in((bounds[0],bounds[1]),(bounds[2],bounds[1]),(bounds[2],bounds[3]),(bounds[0],bounds[3])):box.Append(pcbnew.FromMM(pt[0]),pcbnew.FromMM(pt[1]))
    fills={}
    for layer,poly in full_fills.items():
        clipped=pcbnew.SHAPE_POLY_SET();clipped.Append(poly);clipped.BooleanIntersection(box);clipped.Simplify();fills[layer]=clipped
    row=m['nets'][name];starts=escapes(p,row);ends=escapes(q,row);chosen=None""")
s=s.replace("native_refill_DRC_full_return_and_SOURCE_validation_pending=True","exact_native_fill_subset_clipping_search_only=True,native_refill_DRC_full_return_and_SOURCE_validation_pending=True")
(p/'route_root81_two_surface_r02.py').write_text(s);compile(s,str(p/'route_root81_two_surface_r02.py'),'exec')
(p/'actual-source26-root81-two-surface-r01'/'stopped-search.json').write_text('{"stopped":true,"reason":"Native global-polygon search costly; exact subset clipping replaces search only in immutable r02. No candidate saved or adopted.","board_or_source_modified":false}\n')
