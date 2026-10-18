"""Resume preserved source work with local-width ordering and exact cache."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_regulated_adaptive_feeds_r76.py').read_text()
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'", "OUT=HERE/'regulated-lazy-source-feeds-r105';BASE=HERE/'corrected-regulated-joint-search-base-r106'")
s=s.replace("obstacles={};legal={};cache=[]", "obstacles={};legal={};cache=[];regional_free_cache={}")
s=s.replace("for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):", "for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):")
s=s.replace("free=inner_legal(l,win);choices=[]", "key=(l,win.wkb);\n      if key not in regional_free_cache:\n       print('REG exact free window',bank,l,width,margin,round(distance,6),flush=True);regional_free_cache[key]=inner_legal(l,win)\n      free=regional_free_cache[key];choices=[]")
s=s.replace("try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))", "print('REG covered path search',bank,l,width,margin,get_num_coordinates(part),flush=True)\n       try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))")
s=s.replace("and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'", "and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93' and q['uuid'] not in hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])")
s=s.replace("controller-regulated-r76/", "controller-regulated-r105/")
exec(compile(s,str(p/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
