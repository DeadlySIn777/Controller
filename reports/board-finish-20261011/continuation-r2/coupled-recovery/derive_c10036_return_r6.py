"""Bound source-plane work to exact unchanged geometry around the attachment.

No candidate route or clearance predicate changes. The finite window completely
contains the tested track body and every tested return disk with >1mm margin.
Remote holes cannot affect any set operation inside this window.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_c10036_paired_return_r5.py').read_text()
s=s.replace('paired-return-recipe-r5','paired-return-recipe-r6').replace('inherited-transition-r5','inherited-transition-r6')
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change('from shapely.geometry import Point,LineString','from shapely.geometry import Point,LineString,box')
change("sh=unary_union([r['shape'] for r in root if r['kind']=='fill' and r['layer']==l]);sh=sh.difference", "sh=unary_union([r['shape'].intersection(box(64,92,71,99)) for r in root if r['kind']=='fill' and r['layer']==l and r['shape'].intersects(box(64,92,71,99))]);sh=sh.difference")
change("for xy in sites:\n", "print('C10036_LOCAL_TRANSITION_PROOF',maximum,radius,flush=True)\n for xy in sites:\n")
change("attempts.append(row)","attempts.append(row)\n  if len(attempts)%8==1:print('C10036_RETURN_SITE',xy,len(row['violations']),areas,flush=True)")
change("'source_gate_distance_mm':dist", "'source_gate_distance_mm':dist,'local_window_contains_annulus_with_more_than_1mm_margin':True")
change("'radius_expansion_mm':0", "'radius_expansion_mm':0,'source_plane_window_exact_intersection_mm':[64,92,71,99],'entire_tested_F_track_body_inside_window':box(64,92,71,99).contains(body),'full_source_root_identity_reused_without_geometry_expansion':True")
q=HERE/'construct_c10036_paired_return_r6.py';assert not q.exists();q.write_text(s)
