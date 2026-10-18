"""Couple CM79 .20 ground with full1.25 CORE5 and three owned F stitch legs.

Every original/native via stays fixed; only three exact unadopted CM49 .20
legs are renominated. Original reserved power anchor remains exact old Cu.
No current/fault/native/manufacturing gate is claimed.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM79_fullwidth_old_power_anchor_novel_rule_scope_r294.py').read_text()
needle="s=s.replace('R288','R294')"
change=r'''
s=s.replace('CM79-fullwidth-exact-old-anchor-only-novel-native-rule-nomination-r294','CM79-fullwidth-CORE5-three-owned-stitch-endpoint-preserving-nomination-r303')
s=s.replace("rec,trees=F.build({**c,'zones':[]},layers={'F.Cu'});", "owned_removed={'a060edb3-81a1-538d-af2e-9a2229a2fdb3','4eb351fd-d29e-562b-95ba-98a5f14deb87','855a5b14-80a8-5583-86ff-6f64a1a2d868'};selected=[t for t in h['tracks']if t['uuid']in owned_removed];assert len(selected)==3;assert all(t['uuid']not in iv[3]and t['net']=='/LOGIC_GND'and t['layer']=='F.Cu'and t['w']==.2 for t in selected);rtracks=[]\n for t in selected:\n  rp=[t['a'],[t['a'][0],203.629990],[120.0,203.629990],t['b']]\n  rtracks.extend({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R303-owned-leg:'+t['uuid']+':'+str(i))),'net':t['net'],'layer':'F.Cu','w':.2,'a':aa,'b':bb}for i,(aa,bb)in enumerate(zip(rp,rp[1:]))if aa!=bb)\n restored_ground_body=unary_union([buf(LineString([t['a'],t['b']]),.1)for t in rtracks]);put(O/'exact-three-owned-CM49-original-leg-selectors.json',selected);put(O/'three-owned-CM49-proposed-endpoint-preserving-legs.json',rtracks);rec,trees=F.build({**c,'zones':[]},layers={'F.Cu'});")
# Bind the exact packet UUID from the independent witness instead of guessing
# its suffix; this replacement is performed after source generation only.
s=s.replace("'a060edb3-81a1-538d-af2e-9a2229a2fdb3'", "next(t['uuid']for t in h['tracks']if t['uuid'].startswith('a060edb3-'))")
s=s.replace("if rr['uuid']==uid or L.norm(rr['net'])==L.norm(net):continue", "if rr['uuid']==uid or rr['uuid']in owned_removed or L.norm(rr['net'])==L.norm(net):continue")
s=s.replace("pf=free(old['net'],1.25,clip,[gb])", "pf=free(old['net'],1.25,clip,[gb,restored_ground_body])")
s=s.replace("rrow={'radius_mm':radius,'whole_fullwidth_original_endpoint_face_count':len(faces)}", "rrow={'radius_mm':radius,'whole_fullwidth_original_endpoint_face_count':len(faces),'actual_old_A_axis_free':pf.covers(Point(old['a'])),'old_reserved_anchor_entry_axis_free':pf.covers(Point(anchor_start))}")
s=s.replace("if rule_bad:rrow['failure']='Novel power body enters exact frozen rule reserve';continue", "if rule_bad:rrow['failure']='Novel power body enters exact frozen rule reserve';continue\n   gf2=free('/LOGIC_GND',.2,box(110,198,136,208),[powerbody]);owned_bad=[t['uuid']for t in rtracks if not gf2.covers(LineString([t['a'],t['b']]))];rrow['three_owned_full_20_legs_outside_all_native_Cu_hole_rule_and_new_fullwidth_power_failure_UUIDs']=owned_bad\n   if owned_bad:continue")
s=s.replace("if t['uuid']!=uid]+gt+pt", "if t['uuid']!=uid and t['uuid']not in owned_removed]+gt+rtracks+pt")
s=s.replace("'new_tracks':gt+pt", "'new_tracks':gt+rtracks+pt,'owned_CM49_removed_track_UUIDs':sorted(owned_removed),'owned_CM49_barrels_relocated':0,'all_three_own_leg_actual_endpoints_exact':True,'owned_CM49_three_leg_new_track_count':len(rtracks)")
s=s.replace("'tracks':winner['new_tracks'],'vias':[],'removed_original_track_UUIDs':[uid]", "'tracks':winner['new_tracks'],'vias':[],'removed_original_track_UUIDs':[uid],'removed_only_unadopted_CM49_owner_track_UUIDs':sorted(owned_removed)")
s=s.replace("'existing_49_CM_owned_source_paths_and_barrels_untouched':True", "'existing_49_CM_barrels_and_all_unselected_paths_untouched':True,'only_three_owned_20F_stitch_legs_renominated_endpoint_preserving':True,'all49_CM_actual_source_physics_and_latest_field_rebind':'PENDING'")
s=s.replace('R294','R303')
'''
assert s.count(needle)==1;s=s.replace(needle,needle+'\n'+change)
exec(compile(s,str(__file__),'exec'))
