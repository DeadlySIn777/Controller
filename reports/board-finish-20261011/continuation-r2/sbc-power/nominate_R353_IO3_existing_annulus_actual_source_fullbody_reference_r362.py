"""New finite screen: actual source reference is a hard routing constraint."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/nominate_R353_IO3_existing_actual_annulus_no_hole_bypass_r358.py'
s=p.read_text(encoding='utf-8').replace('r358','r362').replace('R358','R362')
s=s.replace('from shapely import set_precision','from shapely import set_precision')
s=s.replace("started=time.monotonic();assert not O.exists();O.mkdir();", "started=time.monotonic();assert not O.exists();O.mkdir();")
needle="ctx=K.hole_context(c)"
assert needle in s
s=s.replace(needle,"ctx=K.hole_context(c);lgcache=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354/actual-drilled-after-groups.pkl';assert sha(lgcache)=='339dbe2c2173388fa7384c697e6364dcf5b9c507e552e64836b08c55203ed4eb';lg=K.root(pickle.loads(lgcache.read_bytes())['/LOGIC_GND'],'J11001','2');references={ly:zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']==ly]))for ly in ('In1.Cu','In4.Cu')};refmap={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu','B.Cu':'In4.Cu'};vmap={v['uuid']:v for v in h['vias']}")
needle="blocked=unary_union(obs);free=clip.difference(blocked);face="
assert needle in s
s=s.replace(needle,"blocked=unary_union(obs);free=clip.difference(blocked);ref=references[refmap[ly]];caps=[];portcaps=[]\n    for p in (a,bb):\n     v=vmap[p['UUID']];observed=any(rr['kind']=='via'and rr['uuid']==v['uuid']and rr['layer']==refmap[ly]for xs in groups for rr in xs);radius=(v['d']/2 if observed else v['drill']/2)+.25+.025;caps.append(Point(v['x'],v['y']).buffer(radius,quad_segs=128));portcaps.append({'UUID':v['uuid'],'actual_reference_layer_annulus':observed,'own_original_radius_mm':radius})\n    cap=zero(unary_union(caps));allowed=zero(unary_union([ref.intersection(clip.buffer(1)),cap]));reference_centers=allowed.buffer(-width/2-.005,quad_segs=128);free=free.intersection(reference_centers);face=")
s=s.replace("'same_free_face':face is not None,", "'same_free_face':face is not None,'actual_reference_source': 'J11001.2','actual_reference_layer':refmap[ly],'exact_original_terminal_authority':portcaps,'fullwidth_body_and5um_guard_hard_inside_actual_reference_plus_exact_two_terminal_caps':True,")
needle="direct=LineString([start,end]);path=[start,end]if face.covers(direct)else TR.route_poly(face,start,end)"
assert needle in s
s=s.replace(needle,"routeface=next((p for p in parts(face.buffer(-.000002,quad_segs=64))if p.covers(Point(start))and p.covers(Point(end))),None)\n    if routeface is None:continue\n    direct=LineString([start,end]);path=[start,end]if routeface.covers(direct)else TR.route(routeface,start,end)[0]")
needle="ao=actual.intersection(ap).area;bo=actual.intersection(bp).area;assert ao>.025 and bo>.025;winner="
assert needle in s
s=s.replace(needle,"ao=actual.intersection(ap).area;bo=actual.intersection(bp).area;assert ao>.025 and bo>.025;reference_gap=actual.difference(cap).difference(ref);row['actual_full_body_outside_exact_named_terminal_reference_gap_EMPTY']=reference_gap.is_empty;row['actual_full_body_outside_exact_named_terminal_reference_gap_mm2']=reference_gap.area;put(O/'finite-port-layer-width-window-attempts.json',attempts)\n    if not reference_gap.is_empty:continue\n    winner=")
s=s.replace("'new_body_reference_current_drop_plating_partial_annulus_thermal_native':'OPEN'", "'actual_fullbody_outside_exact_two_original_terminal_reference_gap_EMPTY':True,'exact_reference_terminal_authority':portcaps,'finite_own_terminal_plane_transfer_current_drop_plating_thermal_native':'OPEN'")
s=s.replace("'NO_FIXED_CURRENT_CU_EXISTING_ANNULUS_IO3_BYPASS_IN_EXACT_FINITE_WINDOWS'", "'NO_EXISTING_ANNULUS_IO3_BYPASS_INSIDE_ACTUAL_SOURCE_REFERENCE_AND_FIXED_CU_EXACT_FINITE_WINDOWS'")
s=s.replace("if __name__=='__main__':main()", "if __name__=='__main__':\n try:main()\n except Exception:\n  import traceback\n  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__),'source_model_board_or_native_changes':0})\n  raise")
exec(compile(s,str(__file__),'exec'))
