"""Intersect via sites with the actual pad-connected outer route component."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'nominate_field_ground_bare_dogbones_r13.py';o=H/'nominate_field_ground_bare_dogbones_r17.py';assert not o.exists()
s=p.read_text();a="    for p in polys(region.intersection(N.bounded_buffer(source[l],.2))):\n     options.extend((point.distance(s),l,s)for s in [p.representative_point(),nearest_points(p,point)[0],p.centroid]if p.covers(s))"
b="""    for startpart in startparts:
     meeting=region.intersection(startpart).intersection(N.bounded_buffer(source[l],.2))
     for p in polys(meeting):
      options.extend((point.distance(s),l,s)for s in [p.representative_point(),nearest_points(p,point)[0],p.centroid]if p.covers(s))"""
assert s.count(a)==1;s=s.replace(a,b)
a="   startparts=[p for p in polys(routefree)if p.intersects(padshape.buffer(-.000020))];options=[]"
b=a+"\n   if not startparts:\n    free=win.intersection(outline).difference(unary_union(outer))\n    print('FAG_BARE_PAD_BLOCK_DIAGNOSTIC',pad['ref'],'pad_bounds',list(padshape.bounds),'available_pad_area_by_DIAGNOSTIC_ONLY_width',{str(w):free.buffer(-w/2-.000020).intersection(padshape.buffer(-.000020)).area for w in(.2,.15,.125,0.)},flush=True)"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('FAG_BARE_R13_FACE','FAG_BARE_R17_FACE').replace('controller-ground-bare-r13/','controller-ground-bare-r17/')
compile(s,str(o),'exec');o.write_text(s)
(H/'field-ground-continuous-r17-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'only_construct_ordinary_via_candidates_in_exact_pad_connected_outer_0p2_route_component':True,'smaller_widths_diagnostic_only_no_Cu_rule_or_candidate_at_less_than_0p2':True,'all_original_physical_native_reservation_and_foreign_NEWplane_blockers_preserved':True,'all_prior_actual_source_contacts_still_mandatory_in_scope':'PRESERVED','full_mutual_reference_native_current_gates':'OPEN','native_jobs':0,'board_written':False},indent=1)+'\n')
print(json.dumps({'script':str(o),'sha256':sha(o)}))
