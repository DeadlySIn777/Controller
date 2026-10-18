"""Rebuild two new failed inner feed walls against full old physical references."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_regulated_adaptive_feeds_r76.py').read_text()
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'","OUT=HERE/'regulated-reference-safe-source-replacements-r121';BASE=HERE/'regulated-indexed-reference-wall-repair-base-r123'")
s=s.replace("INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']","INNER=['In2.Cu','In3.Cu','In1.Cu','In4.Cu']")
s=s.replace("original={q['uuid']:copy.deepcopy(q) for q in planes}","reference_masks=pickle.loads((BASE/'reference-masks.pkl').read_bytes());reference_rows=[{'net':net,'layer':l,'shape':sh,'native_clearance_mm':max([float(z.get('clearance_mm',.15)) for z in h['zones'] if C.norm(z['net'])==net and l in z['fills']]+[.15])} for (net,l),sh in reference_masks.items()];original={q['uuid']:copy.deepcopy(q) for q in planes}")
s=s.replace("hardh={**h,'tracks':h['tracks']+hard['discrete']['tracks'],'vias':h['vias']+hard['discrete']['vias']};rec,trees", "j7path=HERE.parent/'sbc-power/core1v2-local-outer-join-nominees-r106/proposed-tracks.pkl';assert sha(j7path)=='ebce5be3f82d0c2de9bf6ee303d287efa78a9f85bc19358ee5249f01152b3073';j7tracks=pickle.loads(j7path.read_bytes());hardh={**h,'tracks':h['tracks']+hard['discrete']['tracks']+j7tracks,'vias':h['vias']+hard['discrete']['vias']};rec,trees")
s=s.replace("for bank,net,ref,pin,policy in PORTS:","for bank,net,ref,pin,policy in [x for x in PORTS if x[0] in ('FIELD5','B3V3')]:")
s=s.replace("and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'","and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93' and q['uuid'] not in hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])")
s=s.replace("obstacles={};legal={};cache=[]","obstacles={};legal={};cache=[];regional_free_cache={}")
s=s.replace("   for area in h['rule_areas']:\n    if area.get('no_zones')", "   walls += [P.bounded_buffer(q['shape'].intersection(query),max(gap(q['net']),q['native_clearance_mm']+.025)) for q in reference_rows if q['layer']==layer and not q['shape'].is_empty and q['shape'].intersects(query)]\n   for area in h['rule_areas']:\n    if area.get('no_zones')")
s=s.replace("for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):","for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):")
s=s.replace("for distance,l,aa,bb,sh in sorted(options,key=lambda q:q[0]):", "for distance,l,aa,bb,sh in sorted(options,key=lambda q:(q[1] in ('In1.Cu','In4.Cu'),q[0])):")
s=s.replace("free=inner_legal(l,win);choices=[]","key=(l,win.wkb);\n      if key not in regional_free_cache:\n       print('REG reference-safe free',bank,l,width,margin,round(distance,6),flush=True);regional_free_cache[key]=inner_legal(l,win)\n      free=regional_free_cache[key];choices=[]")
s=s.replace("try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))","print('REG reference-safe covered path',bank,l,width,margin,get_num_coordinates(part),flush=True)\n       try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))")
s=s.replace("native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)","construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)")
# Construct only the two explicitly withdrawn feed groups; existing-barrel
# restoration first, no repeat search for the seven independently diagnosed
# bare-pad local walls or any speculative new source barrel.
s=s.replace("xs=gs[gi];print(bank,gi,'begin'", "xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin')) in {('R11071','1'),('U19008','10')} for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("   if body is None:\n", "   if body is None:\n")
# Keep the unchanged fallback legal checks, but these nominated groups already
# own actual plated inner contacts; the final receipt distinguishes any new
# fallback barrel and does not grant flash/current evidence.
s=s.replace('controller-regulated-r76/','controller-regulated-reference-r121/')
s=s.replace("'all_old_return_contacts_actual_new_source_graph_global_reference_native_and_current_gates'", "'full_original_source_reference_hard_masks_used':True,'all_old_return_contacts_actual_new_source_graph_global_reference_native_and_current_gates'")
exec(compile(s,str(p/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
