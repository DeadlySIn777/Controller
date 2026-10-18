"""Bounded protected-wall pair nomination; unchanged Cu remains authoritative."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'diagnose_U10009_outer_single_track_separator_r259.py').read_text(encoding='utf-8')
s=s.replace('U10009-exact-outer-single-track-separator-r259','U10009-exact-protected-wall-pair-separator-r264')
s=s.replace('import sys,pickle,json,re','import sys,pickle,json,re,itertools')
start=s.index(' for uid in candidateids:\n');end=s.index(" write(O/'receipt.json'",start)
s=s[:start]+''' free,all_connected,all_sites=reachable(set(candidateids));write(O/'all-nominated-wall-withdrawal-diagnostic.json',{'original_track_UUIDs':candidateids,'all_still_native_legal_via_area_mm2':all_sites.area,'accessible_mm2':all_connected.area,'no_deletion_credit':True})
 if not all_sites.is_empty:
  fixed=unary_union([r['cut'] for r in walls if r['UUID'] not in candidateids]);byuid={uid:unary_union([r['cut'] for r in walls if r['UUID']==uid]) for uid in candidateids}
  for pair in itertools.combinations(candidateids,2):
   free=win.difference(unary_union([fixed]+[sh for uid,sh in byuid.items() if uid not in pair]));connected=unary_union([q for q in polys(free.buffer(-.105)) if q.intersects(padshape)]);sites=connected.intersection(centres)
   row={'exact_original_track_UUIDs':list(pair),'raw_net':tracks[pair[0]]['net'],'original_track_records':[tracks[uid] for uid in pair],'opened_accessible_mm2':connected.area,'actual_still_legal_all6_via_centres_mm2':sites.area,'all_original_endpoints_interior_contacts_full_protected_current_required':True,'no_actual_old_Cu_change':True};checks.append(row)
   if not sites.is_empty:
    pockets=polys(sites)
    if pockets:
     point=min(pockets,key=lambda sh:sh.distance(anchor)).representative_point();row['nominee_xy_mm']=[round(point.x,6),round(point.y,6)];nominees.append(row.copy());print('R264 pair opens',pair,row['nominee_xy_mm'],flush=True)
   write(O/'separator-checkpoint.json',checks)
 '''+s[end:]
s=s.replace('SINGLE_TRACK_COUPLED_ESCAPE_NOMINATIONS_REQUIRE_REPLACEMENT','PAIR_PROTECTED_WALL_NOMINEES_REQUIRE_EXACT_REPLACEMENT').replace('NO_SINGLE_TRACK_ESCAPE_IN_DECLARED_12MM_WINDOW','NO_TWO_TRACK_ESCAPE_IN_DECLARED_12MM_WINDOW').replace('single_track_tests','pair_tests').replace('R259','R264')
exec(compile(s,str(H/'diagnose_U10009_outer_single_track_separator_r259.py'),'exec'))
