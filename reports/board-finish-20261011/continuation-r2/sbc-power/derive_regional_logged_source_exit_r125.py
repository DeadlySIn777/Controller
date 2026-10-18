"""Derive a bounded corridor search without changing source/clearance gates."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
s=(H/'construct_major_rail_coupled_source_exit_r121.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:120],s.count(a));s=s.replace(a,b)
replace("OUT=H/'sbc-power/major-rail-coupled-source-exit-feeds-r121';","OUT=H/'sbc-power/major-rail-regional-logged-source-exit-r125';")
replace(" hole_tree=STRtree([s for raw,s in all_holes]);adds=[];rows=[];attempts=[];bank_proofs=[];carves=[]", """ hole_tree=STRtree([s for raw,s in all_holes]);adds=[];rows=[];attempts=[];bank_proofs=[];carves=[];rejections=[]
 def reject(reason,**data):
  row={'reason':reason,**data};rejections.append(row)
  write(OUT/'rejections.json',rejections)
  print('SOURCE_EXIT_REJECT',reason,data,flush=True)
 def corridor_route(part,aa,bb):
  a,b=nearest_points(aa,bb);chord=LineString([a,b])
  if part.covers(chord):return list(chord.coords),{'method':'exact_covered_nearest_chord'}
  # Restrict each search to an exact subset of the unchanged legal centerline
  # region. A corridor does not authorize obstacle traversal or extra copper.
  failures=[]
  for reserve in (5.,15.,35.,None):
   region=part if reserve is None else part.intersection(chord.buffer(reserve,quad_segs=16))
   pieces=[p for p in polys(region) if p.covers(a) and p.covers(b)]
   if not pieces:
    failures.append({'corridor_half_width_mm':reserve,'reason':'disconnected_corridor_subset'});continue
   route_region=max(pieces,key=lambda p:p.area)
   print('SOURCE_EXIT_CORRIDOR',reserve,int(get_num_coordinates(route_region)),flush=True)
   try:points,search=T.route(route_region,tuple(a.coords[0]),tuple(b.coords[0]))
   except (AssertionError,ValueError) as error:
    failures.append({'corridor_half_width_mm':reserve,'reason':type(error).__name__,'detail':str(error)});continue
   assert part.covers(LineString(points))
   return points,{**search,'corridor_half_width_mm':reserve,'unchanged_original_centerline_region_strictly_covers_route':True,'earlier_subset_failures':failures}
  raise ValueError(str(failures))""")
replace("     a,b=nearest_points(aa,bb);chord=LineString([a,b])\n     if part.covers(chord):points=list(chord.coords);search={'method':'exact_covered_nearest_chord'}\n     else:\n      try:points,search=T.route(part,tuple(a.coords[0]),tuple(b.coords[0]))\n      except (AssertionError,ValueError):continue", """     try:points,search=corridor_route(part,aa,bb)
     except (AssertionError,ValueError) as error:
      reject('route_subsets_failed',net=net,vid=vid,layer=layer,width=width,detail=str(error));continue""")
replace("     if not region.buffer(.000001).covers(core):continue", """     if not region.buffer(.000001).covers(core):
      reject('quantized_route_core_outside_construction_region',net=net,vid=vid,layer=layer,width=width,removed_mm2=core.difference(region).area);continue""")
replace("     if z['shape'].intersection(ann).area<.01 or z['shape'].intersection(source[layer]).area<.01:continue", """     if z['shape'].intersection(ann).area<.01 or z['shape'].intersection(source[layer]).area<.01:
      reject('insufficient_exact_source_or_annulus_overlap',net=net,vid=vid,layer=layer,width=width,annulus_mm2=z['shape'].intersection(ann).area,source_mm2=z['shape'].intersection(source[layer]).area);continue""")
replace("       if not escape.covers(removed):continue", """       if not escape.covers(removed):
        reject('physical_carve_exceeds_exact_bounded_scope',net=net,vid=vid,layer=layer,width=width,outside_scope_mm2=removed.difference(escape).area,outside_scope_bounds=list(removed.difference(escape).bounds))
        failed=OUT/('failed-scope-'+str(len(rejections)));failed.mkdir()
        for label,shape in [('cutter',cutter),('removed',removed),('escape',escape),('new-feed',z['shape'])]:(failed/(label+'.wkb')).write_bytes(shape.wkb)
        continue""")
replace("       if after.is_empty or not escape.covers(before_outline.difference(after_outline)):continue", """       if after.is_empty or not escape.covers(before_outline.difference(after_outline)):
        reject('outline_carve_exceeds_scope_or_empty',net=net,vid=vid,layer=layer,width=width,after_empty=after.is_empty,outside_scope_mm2=before_outline.difference(after_outline).difference(escape).area,raw_to_grid_removed_mm2=before_outline.difference(set_precision(before_outline,1e-6)).area,raw_to_grid_added_mm2=set_precision(before_outline,1e-6).difference(before_outline).area)
        failed=OUT/('failed-outline-scope-'+str(len(rejections)));failed.mkdir()
        for label,shape in [('before-outline',before_outline),('after-outline',after_outline),('cutter',cutter),('escape',escape)]:(failed/(label+'.wkb')).write_bytes(shape.wkb)
        continue""")
replace("     if not target<=joined or not retained<=joined:continue", """     if not target<=joined or not retained<=joined:
      reject('source_projection_target_or_prior_pad_failure',net=net,vid=vid,layer=layer,width=width,missing_target=sorted(target-joined),missing_prior=sorted(retained-joined));continue""")
replace("     if not core_prior_exact<=core_exact:record['CORE_source_contacts_lost']=sorted(core_prior_exact-core_exact);continue", """     if not core_prior_exact<=core_exact:
      record['CORE_source_contacts_lost']=sorted(core_prior_exact-core_exact)
      reject('exact_prior_CORE_source_contacts_lost',net=net,vid=vid,layer=layer,width=width,lost_keys=record['CORE_source_contacts_lost']);continue""")
replace("     if floating:record['CORE_detached_new_components']=floating;continue", """     if floating:
      record['CORE_detached_new_components']=floating
      reject('retained_CORE_proposal_component_unrooted',net=net,vid=vid,layer=layer,width=width,pieces=floating);continue""")
replace("controller-major-rail-coupled-source-exit-r121/","controller-major-rail-regional-source-exit-r125/")
replace("'label':'Major rail coupled bounded owned source exit R121'","'label':'Major rail regional bounded owned source exit R125'")
replace("'attempts':attempts,'finite_construction_failure", "'attempts':attempts,'all_early_rejections':rejections,'finite_construction_failure")
replace("print('MAJOR_RAIL_COUPLED_SOURCE_R121_FROZEN'", "print('MAJOR_RAIL_REGIONAL_SOURCE_R125_FROZEN'")
out=H/'construct_major_rail_regional_logged_source_exit_r125.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec')
print('REGIONAL_LOGGED_SOURCE_EXIT_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
